"""A toy differentiable volume renderer and its gradient-descent fitter (NumPy only).

The NeRF idea at a size that runs on a CPU in seconds: render a learnable voxel
grid with the compositing of volume_render.py, compare with the captured images,
and move every voxel downhill. There is no autodiff library: the backward pass is
derived by hand (docs/catatan/fase3-renderer-gradien.md) and checked against
finite differences in tests.py.

Scene and grid live in the cube [-1, 1]^3 (unitless world units, not metres).
Rays come from ray_generator.py, so the pixel convention is the one fixed there.
The grid uses nearest-voxel lookup, not trilinear, so each sample reads and
writes exactly one voxel.
"""
from __future__ import annotations

import numpy as np

import ray_generator

# ---------------------------------------------------------------------------
# Ground-truth analytic scene (what the synthetic cameras photograph)
# ---------------------------------------------------------------------------

_TIERS = [
    # (half_x, half_z, y_lo, y_hi, color)
    (0.90, 0.90, -1.00, -0.60, (0.55, 0.50, 0.45)),
    (0.65, 0.65, -0.60, -0.20, (0.50, 0.45, 0.40)),
    (0.40, 0.40, -0.20, 0.30, (0.45, 0.40, 0.38)),
    (0.15, 0.15, 0.30, 0.80, (0.78, 0.64, 0.20)),
]
SCENE_SIGMA = 15.0  # opaque enough that a handful of samples suffices


def scene_density_color(points):
    """Analytic (sigma, colour) at points (..., 3): solid boxes, empty space elsewhere."""
    x, y, z = points[..., 0], points[..., 1], points[..., 2]
    sigma = np.zeros(points.shape[:-1])
    color = np.zeros(points.shape[:-1] + (3,))
    for hx, hz, y_lo, y_hi, c in _TIERS:
        inside = (np.abs(x) <= hx) & (np.abs(z) <= hz) & (y >= y_lo) & (y <= y_hi)
        sigma = np.where(inside, SCENE_SIGMA, sigma)
        color = np.where(inside[..., None], c, color)
    return sigma, color


# ---------------------------------------------------------------------------
# Cameras on a ring around the scene, looking at its centre
# ---------------------------------------------------------------------------

def look_at_c2w(eye, target, up=(0.0, 1.0, 0.0)):
    """Camera-to-world rotation; columns are the camera's +x, +y, +z in world space
    (it looks down its own -z, as in ray_generator.py)."""
    forward = np.asarray(target, dtype=float) - np.asarray(eye, dtype=float)
    forward = forward / np.linalg.norm(forward)
    right = np.cross(forward, np.asarray(up, dtype=float))
    right = right / np.linalg.norm(right)
    return np.stack([right, np.cross(right, forward), -forward], axis=1)


def ring_camera(angle_deg, radius=3.0, height=1.0):
    """(position, rotation) of a camera on a horizontal ring, aimed slightly below the origin."""
    a = np.radians(angle_deg)
    eye = np.array([radius * np.cos(a), height, radius * np.sin(a)])
    return eye, look_at_c2w(eye, np.array([0.0, -0.1, 0.0]))


# ---------------------------------------------------------------------------
# Rays and samples
# ---------------------------------------------------------------------------

def generate_rays(width, height, fov_deg, cam_pos, c2w):
    """One ray per pixel centre, through ray_generator.py (the only ray code in the module)."""
    f = ray_generator.focal_from_fov(width, fov_deg)
    return ray_generator.generate_rays(width, height, f, f, width / 2.0, height / 2.0, c2w, cam_pos)


def sample_points(origins, dirs, near, far, n_samples):
    """Evenly spaced sample depths, the same for every ray (no random jitter, so runs repeat).

    Returns points (..., n_samples, 3), the depths and the step length delta."""
    t = np.linspace(near, far, n_samples)
    pts = origins[..., None, :] + dirs[..., None, :] * t[:, None]
    return pts, t, t[1] - t[0]


def _composite_image(alpha, color, background):
    """Front-to-back compositing of every ray at once, the same sums as volume_render.composite.

    alpha (..., N), color (..., N, 3) -> image (..., 3), weights (..., N), T_(N+1) (...)."""
    trans = np.cumprod(np.concatenate([np.ones_like(alpha[..., :1]), 1.0 - alpha], axis=-1), axis=-1)
    weights = trans[..., :-1] * alpha
    image = (weights[..., None] * color).sum(axis=-2) + trans[..., -1:] * np.asarray(background)
    return image, weights, trans[..., -1]


def render_analytic(width, height, fov_deg, cam_pos, c2w, near=1.0, far=5.0, n_samples=32,
                    background=(1.0, 1.0, 1.0)):
    """Render the analytic scene: the "photographs" the grid learns from."""
    origins, dirs = generate_rays(width, height, fov_deg, cam_pos, c2w)
    pts, _, delta = sample_points(origins, dirs, near, far, n_samples)
    sigma, color = scene_density_color(pts)
    return _composite_image(1.0 - np.exp(-sigma * delta), color, background)[0]


def psnr(a, b, data_range=1.0):
    """Peak signal-to-noise ratio in dB; 99.0 is a cap for (near) identical images, not a measurement."""
    mse = float(np.mean((a - b) ** 2))
    if mse <= 1e-12:
        return 99.0
    return 10.0 * np.log10(data_range ** 2 / mse)


# ---------------------------------------------------------------------------
# The learnable voxel grid
# ---------------------------------------------------------------------------

class VoxelGrid:
    """res^3 voxels over [-extent, extent]^3, each holding raw density and raw colour.

    sigma = softplus(sigma_raw) >= 0 and colour = sigmoid(color_raw) in [0, 1], so the
    optimiser can move the raw numbers freely. sigma_raw starts at 0 (sigma = ln 2), not at
    a very negative "empty" value: softplus'(x) = sigmoid(x), and sigmoid(-5) = 0.0067 would
    shrink every density gradient by that factor from the first step (module pitfall 12.1).
    """

    def __init__(self, resolution=10, extent=1.0, seed=0):
        rng = np.random.default_rng(seed)
        self.res = resolution
        self.extent = extent
        self.sigma_raw = np.zeros((resolution,) * 3)
        self.color_raw = rng.normal(0.0, 0.01, size=(resolution,) * 3 + (3,))
        self.sigma_grad = np.zeros_like(self.sigma_raw)
        self.color_grad = np.zeros_like(self.color_raw)

    def _voxel_index(self, points):
        # outside the cube a point reads the nearest boundary voxel (indices are clamped)
        idx = np.floor((points + self.extent) / (2 * self.extent) * self.res).astype(int)
        return np.clip(idx, 0, self.res - 1)

    @staticmethod
    def _softplus(x):
        return np.logaddexp(0.0, x)

    @staticmethod
    def _sigmoid(x):
        return 1.0 / (1.0 + np.exp(-x))

    def forward(self, points):
        """points (..., 3) -> sigma (...), colour (..., 3), flat voxel index (...), sigma_raw (...)."""
        ix, iy, iz = np.moveaxis(self._voxel_index(points), -1, 0)
        sigma_raw = self.sigma_raw[ix, iy, iz]
        color = self._sigmoid(self.color_raw[ix, iy, iz])
        return self._softplus(sigma_raw), color, (ix * self.res + iy) * self.res + iz, sigma_raw

    def zero_grad(self):
        self.sigma_grad.fill(0.0)
        self.color_grad.fill(0.0)

    def accumulate(self, flat_idx, d_sigma_raw, d_color_raw):
        """Add per-sample gradients into the voxels they came from (several samples share a voxel)."""
        np.add.at(self.sigma_grad.reshape(-1), flat_idx, d_sigma_raw)
        np.add.at(self.color_grad.reshape(-1, 3), flat_idx, d_color_raw)

    def step(self, lr):
        self.sigma_raw -= lr * self.sigma_grad
        self.color_raw -= lr * self.color_grad


def render_grid(grid, width, height, fov_deg, cam_pos, c2w, near=1.0, far=5.0, n_samples=32,
                background=(1.0, 1.0, 1.0)):
    """Forward pass through the grid. Returns the image and what backward_grid needs."""
    origins, dirs = generate_rays(width, height, fov_deg, cam_pos, c2w)
    pts, _, delta = sample_points(origins, dirs, near, far, n_samples)
    shape = pts.shape[:-1]  # (H, W, N)
    sigma, color, flat_idx, sigma_raw = grid.forward(pts.reshape(-1, 3))
    alpha = 1.0 - np.exp(-sigma.reshape(shape) * delta)
    color = color.reshape(shape + (3,))
    image, weights, bg_weight = _composite_image(alpha, color, background)
    trans = np.cumprod(np.concatenate([np.ones_like(alpha[..., :1]), 1.0 - alpha[..., :-1]], axis=-1), axis=-1)
    cache = dict(alpha=alpha, color=color, trans=trans, weights=weights, bg_weight=bg_weight,
                 sigma_raw=sigma_raw.reshape(shape), flat_idx=flat_idx.reshape(shape), delta=delta,
                 background=background)
    return image, cache


def backward_grid(grid, cache, d_image):
    """Hand-derived backward pass for one rendered image; adds dLoss/d(raw params) to the grid.

    d_image (H, W, 3) is dLoss/dImage. Per ray, with T_k the light reaching sample k and
    B_k the colour seen from just behind sample k (samples k+1..N composited over the
    background, starting from full light):
        dC/dc_k     = w_k = T_k alpha_k
        dC/dalpha_k = T_k (c_k - B_k)
    B is built back to front: B_N = c_bg, B_(k-1) = alpha_k c_k + (1 - alpha_k) B_k.
    No division by (1 - alpha_k), so an opaque sample (alpha = 1) needs no special case.
    Then alpha = 1 - exp(-sigma delta) gives dalpha/dsigma = delta (1 - alpha),
    softplus' = sigmoid, and sigmoid' = s (1 - s).
    """
    alpha, color, trans = cache["alpha"], cache["color"], cache["trans"]
    g = d_image[..., None, :]  # (H, W, 1, 3), one upstream gradient per ray
    behind = np.empty_like(color)
    acc = np.broadcast_to(np.asarray(cache["background"], dtype=float), color[..., 0, :].shape).copy()
    for k in range(alpha.shape[-1] - 1, -1, -1):
        behind[..., k, :] = acc
        acc = alpha[..., k, None] * color[..., k, :] + (1.0 - alpha[..., k, None]) * acc

    d_alpha = trans * ((color - behind) * g).sum(axis=-1)
    d_sigma_raw = d_alpha * cache["delta"] * (1.0 - alpha) * VoxelGrid._sigmoid(cache["sigma_raw"])
    d_color_raw = cache["weights"][..., None] * g * color * (1.0 - color)
    grid.accumulate(cache["flat_idx"].reshape(-1), d_sigma_raw.reshape(-1), d_color_raw.reshape(-1, 3))


def train(grid, views, width, height, fov_deg, targets, near=1.0, far=5.0, n_samples=32, lr=5.0,
          n_iters=300, log_every=50):
    """Plain gradient descent on all views at once. Returns [(iteration, mean squared error)].

    The step uses the gradient of sum((image - target)^2) / (pixels x views), which is 3 x the
    gradient of the reported per-channel MSE; lr absorbs that constant.
    """
    history = []
    n_pix = width * height * len(views)
    for it in range(n_iters):
        grid.zero_grad()
        total = 0.0
        for (cam_pos, c2w), target in zip(views, targets):
            image, cache = render_grid(grid, width, height, fov_deg, cam_pos, c2w, near, far, n_samples)
            diff = image - target
            total += float(np.sum(diff ** 2))
            backward_grid(grid, cache, 2.0 * diff / n_pix)
        grid.step(lr)
        if it % log_every == 0 or it == n_iters - 1:
            history.append((it, total / (n_pix * 3)))
    return history
