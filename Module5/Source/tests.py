"""Module 5 test suite. Run: python tests.py -> ALL CHECKS PASSED (N ok)

Includes a finite-difference check of the hand-derived analytic backward
pass (nerf_toy.backward_grid) -- the from-scratch "match a reference"
moment applied to the from-scratch code itself, since there is no external
autodiff library in play to check against.
"""
from __future__ import annotations

import numpy as np

from ray_generator import running_example as ray_running_example
from volume_render import running_example as vr_running_example
from nerf_toy import VoxelGrid, render_grid, backward_grid, ring_camera
import nerf_bug

_checks = 0


def check(name, got, want, tol=1e-6):
    ok = abs(got - want) <= tol
    status = "ok" if ok else "FAIL"
    print(f"[{status}] {name}: got={got!r} want={want!r}")
    assert ok, f"{name}: got {got!r}, want {want!r}"
    global _checks
    _checks += 1


def check_vec(name, got, want, tol=1e-3):
    for g, w in zip(got, want):
        check(f"{name} ({w})", g, w, tol)


def test_ray_generator():
    dir_cam, norm_dir = ray_running_example()
    check_vec("E1 pinhole ray, camera-space (unnormalised)", dir_cam, (0.8, 0.0, -1.0))
    check_vec("E1 pinhole ray, normalised", norm_dir, (0.625, 0.0, -0.781), tol=1e-3)
    check("E1 normalised ray has unit length", float(np.linalg.norm(norm_dir)), 1.0, tol=1e-9)


def test_volume_render():
    final_color, weights, transmittance, bg_weight = vr_running_example()
    check_vec("E2 volume-render weights", weights, (0.5, 0.25, 0.25))
    check("E2 background weight", bg_weight, 0.0, tol=1e-9)
    check("E2 weights + background sum to 1", float(weights.sum() + bg_weight), 1.0, tol=1e-9)
    check_vec("E2 final pixel colour", final_color, (0.5, 0.25, 0.25))


def test_ray_convention():
    """One pixel convention for the whole module (K12): the batched rays go through pixel
    centres (col + 0.5, row + 0.5) of the same scalar formula, nerf_toy has no copy of its
    own, and a ray projected back with Module 3's formula lands on its pixel centre."""
    import ray_generator
    import nerf_toy
    rng = np.random.default_rng(7)
    worst_batch = worst_toy = worst_back = worst_origin = 0.0
    for _ in range(20):
        w, h = (int(n) for n in rng.integers(2, 30, size=2))
        fx, fy = rng.uniform(5.0, 200.0, size=2)
        cx, cy = rng.uniform(0.0, w), rng.uniform(0.0, h)
        rot, _ = np.linalg.qr(rng.normal(size=(3, 3)))
        pos = rng.normal(size=3)
        origins, dirs = ray_generator.generate_rays(w, h, fx, fy, cx, cy, rot, pos)
        for row, col in ((0, 0), (h - 1, w - 1), (h // 2, w // 3)):
            d = rot @ ray_generator.pixel_to_camera_dir(col + 0.5, row + 0.5, fx, fy, cx, cy)
            worst_batch = max(worst_batch, float(np.abs(dirs[row, col] - d / np.linalg.norm(d)).max()))
            cam = rot.T @ dirs[row, col]  # back into camera space, then Module 3's projection
            u, v = cx + fx * cam[0] / -cam[2], cy - fy * cam[1] / -cam[2]
            worst_back = max(worst_back, abs(u - (col + 0.5)), abs(v - (row + 0.5)))
        fov = rng.uniform(20.0, 100.0)
        f = ray_generator.focal_from_fov(w, fov)
        mine = ray_generator.generate_rays(w, h, f, f, w / 2.0, h / 2.0, rot, pos)
        toy = nerf_toy.generate_rays(w, h, fov, pos, rot)
        worst_toy = max(worst_toy, float(np.abs(mine[1] - toy[1]).max()), float(np.abs(mine[0] - toy[0]).max()))
        worst_origin = max(worst_origin, float(np.abs(origins - pos).max()))
    check("ray origins are the camera position (max abs diff)", worst_origin, 0.0, tol=0.0)
    check("batched ray = scalar ray at the pixel centre (max abs diff)", worst_batch, 0.0, tol=1e-12)
    check("ray projected back lands on its pixel centre (max px)", worst_back, 0.0, tol=1e-9)
    check("nerf_toy.generate_rays = ray_generator.generate_rays (max abs diff)", worst_toy, 0.0, tol=0.0)
    from volume_render import E2_DELTAS, E2_OPAQUE, E2_SIGMAS, alphas_of
    check_vec("E2 alphas computed from sigma and delta", alphas_of(E2_SIGMAS, E2_DELTAS, E2_OPAQUE), (0.5, 0.5, 1.0),
              tol=1e-12)


def test_my_ray():
    """My own phone pixel (Lab 1 no 4): the program must match the by-hand numbers in
    docs/catatan/fase2-capture-ray.md, and the principal point must give the optical axis."""
    import my_ray
    cam = my_ray.load_camera()
    f, d, n = my_ray.my_ray(cam)
    check("my camera focal length, px (24 mm equiv. on a 6048x8064 frame)", f, 5591.38, tol=0.01)
    check_vec("my ray, camera-space (unnormalised)", d, (-0.19101, -0.36986, -1.0), tol=1e-5)
    check_vec("my ray, normalised", n, (-0.17634, -0.34145, -0.92321), tol=1e-5)
    cx, cy = cam["principal_point_px"]
    axis = my_ray.pixel_to_camera_dir(cx, cy, f, f, cx, cy)
    check_vec("principal point gives the optical axis", axis, (0.0, 0.0, -1.0), tol=1e-12)


def test_backward_matches_finite_difference():
    grid = VoxelGrid(resolution=4, seed=1)
    rng = np.random.default_rng(2)
    grid.sigma_raw = rng.normal(0, 1, size=grid.sigma_raw.shape)
    grid.color_raw = rng.normal(0, 1, size=grid.color_raw.shape)

    W, H, FOV = 4, 3, 50.0
    cam_pos, c2w = ring_camera(30.0, radius=3.0, height=1.0)
    target = np.random.default_rng(4).uniform(0, 1, size=(H, W, 3))

    def loss_and_render():
        image, cache = render_grid(grid, W, H, FOV, cam_pos, c2w, near=1.0, far=5.0, n_samples=8)
        return float(np.sum((image - target) ** 2)), image, cache

    _, image0, cache = loss_and_render()
    d_image = 2.0 * (image0 - target)
    grid.zero_grad()
    backward_grid(grid, cache, d_image)
    analytic_sigma_grad = grid.sigma_grad.copy()
    analytic_color_grad = grid.color_grad.copy()

    eps = 1e-4
    max_err = 0.0
    rng2 = np.random.default_rng(5)
    probe_idxs = [tuple(rng2.integers(0, 4, size=3)) for _ in range(6)]

    for idx in probe_idxs:
        orig = grid.sigma_raw[idx]
        grid.sigma_raw[idx] = orig + eps
        lp, _, _ = loss_and_render()
        grid.sigma_raw[idx] = orig - eps
        lm, _, _ = loss_and_render()
        grid.sigma_raw[idx] = orig
        numeric = (lp - lm) / (2 * eps)
        max_err = max(max_err, abs(numeric - analytic_sigma_grad[idx]))

    for idx in probe_idxs:
        for ch in range(3):
            full_idx = idx + (ch,)
            orig = grid.color_raw[full_idx]
            grid.color_raw[full_idx] = orig + eps
            lp, _, _ = loss_and_render()
            grid.color_raw[full_idx] = orig - eps
            lm, _, _ = loss_and_render()
            grid.color_raw[full_idx] = orig
            numeric = (lp - lm) / (2 * eps)
            max_err = max(max_err, abs(numeric - analytic_color_grad[full_idx]))

    print(f"[{'ok' if max_err < 1e-6 else 'FAIL'}] analytic vs finite-difference gradient, max|err| = {max_err:.2e}")
    assert max_err < 1e-6, f"analytic gradient does not match finite differences: max err {max_err:.2e}"
    global _checks
    _checks += 1


FROM_SCRATCH = ["ray_generator.py", "volume_render.py", "nerf_toy.py", "capture.py", "fit_nerf_toy.py",
                "nerf_bug.py", "my_ray.py"]
ALLOWED_IMPORTS = {"numpy", "json", "os", "sys", "math", "__future__",
                   "ray_generator", "volume_render", "nerf_toy", "capture", "fit_nerf_toy", "nerf_bug", "my_ray"}


def test_numpy_only():
    """K2: the from-scratch files import nothing but NumPy, the standard modules they need and
    each other -- no PyTorch, JAX, SciPy or autodiff can slip in unnoticed."""
    import ast
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    found = set()
    for name in FROM_SCRATCH:
        with open(os.path.join(here, name)) as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found |= {(name, a.name.split(".")[0]) for a in node.names}
            elif isinstance(node, ast.ImportFrom):
                found.add((name, (node.module or "").split(".")[0]))
    bad = sorted(f"{file}: {mod}" for file, mod in found if mod not in ALLOWED_IMPORTS)
    print(f"  imports seen: {sorted({mod for _, mod in found})}")
    check(f"from-scratch files import only NumPy + standard modules ({len(FROM_SCRATCH)} files, bad: {bad})",
          len(bad), 0, tol=0)


def test_composite_image_matches_composite():
    """The vectorised compositing in nerf_toy (every ray at once, with a background) gives the
    same numbers as volume_render.composite on one ray at a time, opaque samples included."""
    from nerf_toy import _composite_image
    from volume_render import composite
    rng = np.random.default_rng(11)
    alpha = rng.uniform(0.0, 1.0, size=(5, 4, 9))
    alpha[rng.uniform(size=alpha.shape) < 0.1] = 1.0
    color = rng.uniform(0.0, 1.0, size=(5, 4, 9, 3))
    background = np.array([0.2, 0.7, 1.0])
    image, weights, bg_weight = _composite_image(alpha, color, background)
    worst = 0.0
    for r in range(5):
        for c in range(4):
            col, w, _, bg = composite(alpha[r, c], color[r, c])
            worst = max(worst, float(np.abs(image[r, c] - (col + bg * background)).max()),
                        float(np.abs(weights[r, c] - w).max()), abs(float(bg_weight[r, c]) - bg))
    check("nerf_toy._composite_image = volume_render.composite per ray (max abs diff)", worst, 0.0, tol=1e-12)
    check("weights + background add up to 1 on every ray (max deviation)",
          float(np.abs(weights.sum(axis=-1) + bg_weight - 1.0).max()), 0.0, tol=1e-12)


def test_capture_files():
    """K11: the committed poses.json still matches the cameras capture.py builds, within 1e-9
    (the last digits differ between machines, so no byte compare), and load_ppm undoes save_ppm."""
    import json
    import os
    import tempfile
    import capture
    with open(os.path.join(capture.DATA_DIR, "poses.json")) as f:
        manifest = json.load(f)
    same = all(manifest[k] == v for k, v in (("width", capture.WIDTH), ("height", capture.HEIGHT),
                                              ("fov_deg", capture.FOV_DEG), ("n_samples", capture.N_SAMPLES)))
    check("poses.json image size, fov and samples match capture.py", float(same), 1.0, tol=0)
    worst = 0.0
    for frame, angle in zip(manifest["frames"], capture.RING_ANGLES):
        pos, c2w = ring_camera(angle, radius=capture.RADIUS, height=capture.HEIGHT_CAM)
        worst = max(worst, float(np.abs(np.array(frame["position"]) - pos).max()),
                    float(np.abs(np.array(frame["camera_to_world_rotation"]) - c2w).max()))
    check(f"poses.json cameras = ring_camera for {len(manifest['frames'])} views (max abs diff)", worst, 0.0, tol=1e-9)

    image = np.random.default_rng(3).uniform(-0.1, 1.1, size=(16, 20, 3))  # out-of-range on purpose
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "x.ppm")
        capture.save_ppm(path, image)
        back = capture.load_ppm(path)
        with open(path, "rb") as f:
            raw = f.read()
        with open(os.path.join(tmp, "c.ppm"), "wb") as f:  # same pixels, header with a comment
            f.write(b"P6\n# my comment\n20 16\n255\n" + raw[len(b"P6\n20 16\n255\n"):])
        commented = capture.load_ppm(os.path.join(tmp, "c.ppm"))
    want = np.clip(np.floor(image * 255.0 + 0.5), 0, 255) / 255.0
    check("load_ppm(save_ppm(image)) = image rounded to 8 bit (max abs diff)", float(np.abs(back - want).max()), 0.0,
          tol=1e-12)
    check("load_ppm skips a '#' comment in the header (max abs diff)", float(np.abs(commented - back).max()), 0.0,
          tol=0)


def _gradient_errors(shift):
    """Hand-derived vs central-difference gradient for EVERY voxel a sample touches (not a random
    few), on the 4x3 test image with every sigma_raw moved by `shift`. Errors are relative to the
    largest finite-difference gradient of that kind, so tiny gradients are judged fairly too."""
    grid = VoxelGrid(resolution=4, seed=1)
    rng = np.random.default_rng(2)
    grid.sigma_raw = rng.normal(0, 1, size=grid.sigma_raw.shape) + shift
    grid.color_raw = rng.normal(0, 1, size=grid.color_raw.shape)
    cam_pos, c2w = ring_camera(30.0, radius=3.0, height=1.0)
    target = np.random.default_rng(4).uniform(0, 1, size=(3, 4, 3))

    def loss():
        image, _ = render_grid(grid, 4, 3, 50.0, cam_pos, c2w, near=1.0, far=5.0, n_samples=8)
        return float(np.sum((image - target) ** 2))

    image, cache = render_grid(grid, 4, 3, 50.0, cam_pos, c2w, near=1.0, far=5.0, n_samples=8)
    grid.zero_grad()
    backward_grid(grid, cache, 2.0 * (image - target))
    hit = [np.unravel_index(i, grid.sigma_raw.shape) for i in np.unique(cache["flat_idx"])]
    eps = 1e-3  # truncation error ~eps^2 stays far below 1e-3; a smaller step only adds round-off noise
    out = {}
    for name, param, grad, idxs in (("sigma", grid.sigma_raw, grid.sigma_grad, hit),
                                    ("colour", grid.color_raw, grid.color_grad,
                                     [h + (ch,) for h in hit for ch in range(3)])):
        analytic, numeric = [], []
        for idx in idxs:
            orig = param[idx]
            param[idx] = orig + eps
            lp = loss()
            param[idx] = orig - eps
            lm = loss()
            param[idx] = orig
            numeric.append((lp - lm) / (2 * eps))
            analytic.append(grad[idx])
        analytic, numeric = np.array(analytic), np.array(numeric)
        scale = float(np.abs(numeric).max())
        out[name] = (float(np.abs(analytic - numeric).max()) / scale if scale > 0 else float(np.abs(analytic).max()),
                     bool(np.all(np.isfinite(analytic))))
    alpha = cache["alpha"]
    return out, len(hit), float(alpha.min()), float(1.0 - alpha.max())


def test_backward_every_voxel_and_extremes():
    """T3: the starter check probed 6 random voxels (one of them never hit by a ray) at sigma_raw
    near 0 only. Here every touched voxel is checked, also where alpha is almost 0, almost 1, and
    exactly 1. The starter's backward fails the middle two (23% and 300% off, wrong sign)."""
    cases = ((0.0, "normal"), (-18.0, "almost empty"), (30.0, "almost opaque"), (800.0, "fully opaque"))
    for shift, label in cases:
        errors, n_hit, a_min, one_minus = _gradient_errors(shift)
        print(f"  {label}: {n_hit} voxels touched, alpha min {a_min:.1e}, 1 - alpha max {one_minus:.1e}")
        for kind in ("sigma", "colour"):
            rel, finite = errors[kind]
            check(f"{kind} gradient, every touched voxel, {label} (sigma_raw {shift:+g}): finite", float(finite), 1.0,
                  tol=0)
            check(f"{kind} gradient, every touched voxel, {label} (sigma_raw {shift:+g}): rel err", rel, 0.0, tol=1e-3)


def test_view_coverage_diagnose_and_fix():
    result = nerf_bug.diagnose_and_fix()
    gap = result["fixed_novel_psnr"] - result["buggy_novel_psnr"]
    print(f"[{'ok' if gap > 1.0 else 'FAIL'}] 8-view vs 2-view novel-view PSNR gap = {gap:.2f} dB (want > 1.0 dB)")
    assert gap > 1.0, f"expected spreading the views to help novel-view PSNR by >1 dB, got {gap:.2f} dB"
    global _checks
    _checks += 1


if __name__ == "__main__":
    test_ray_generator()
    test_volume_render()
    test_ray_convention()
    test_my_ray()
    test_backward_matches_finite_difference()
    test_backward_every_voxel_and_extremes()
    test_composite_image_matches_composite()
    test_capture_files()
    test_numpy_only()
    test_view_coverage_diagnose_and_fix()
    print(f"\nALL CHECKS PASSED ({_checks} ok)")
