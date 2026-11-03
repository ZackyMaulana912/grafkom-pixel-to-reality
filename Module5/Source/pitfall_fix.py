"""Lab 2 no 4: two improvements driven by the module's pitfalls, run as new experiments.

(a) Pitfall 12.1, the starting density. The 8-view capture (the PPM files) is fitted with
    sigma_raw starting at -5, -2, 0 and +2, at two learning rates (5, the default of
    nerf_toy.train, and 100, the one fit_nerf_toy.py and nerf_bug.py use), and the
    training MSE is logged every 10 iterations.
(b) Pitfall 12.3, view coverage. One third view is added to the 2-view capture [0, 20]
    at several angles, from inside the cluster to the far side, and every grid is scored
    on the same held-out angles as nerf_bug.py --sweep.

Run: python pitfall_fix.py            both
     python pitfall_fix.py --init     (a) only
     python pitfall_fix.py --third    (b) only
"""
from __future__ import annotations

import sys

import numpy as np

import nerf_bug
from fit_nerf_toy import load_capture
from nerf_toy import VoxelGrid, psnr, render_analytic, render_grid, ring_camera, train

INIT_VALUES = [-5.0, -2.0, 0.0, 2.0]
LEARNING_RATES = [5.0, 100.0]
INIT_ITERS = 300
LOG_EVERY = 10

THIRD_ANGLES = [5.0, 45.0, 90.0, 135.0, 180.0, 270.0]
TEST_ANGLES = [a for a in nerf_bug.SWEEP_ANGLES if a % 360 not in nerf_bug.FIXED_ANGLES]  # held out everywhere
RING_STEP = 5.0  # second score: every 5 deg around the ring, the grid's own training views left out


def init_experiment():
    """{(lr, sigma_raw_0): [(iteration, training MSE), ...]} on the 8-view capture."""
    manifest, views, targets = load_capture()
    w, h, fov = manifest["width"], manifest["height"], manifest["fov_deg"]
    curves = {}
    for lr in LEARNING_RATES:
        for start in INIT_VALUES:
            grid = VoxelGrid(resolution=12, seed=0)
            grid.sigma_raw.fill(start)  # colour_raw keeps the same random start in every run
            curves[(lr, start)] = train(grid, views, w, h, fov, targets, manifest["near"], manifest["far"],
                                        manifest["n_samples"], lr=lr, n_iters=INIT_ITERS, log_every=LOG_EVERY)
    return curves


def _score(grid, angles):
    out = []
    for angle in angles:
        cam, c2w = ring_camera(angle, radius=nerf_bug.RADIUS, height=nerf_bug.CAM_HEIGHT)
        args = (nerf_bug.W, nerf_bug.H, nerf_bug.FOV, cam, c2w, nerf_bug.NEAR, nerf_bug.FAR, nerf_bug.N_SAMPLES)
        out.append(psnr(render_grid(grid, *args)[0], render_analytic(*args)))
    return out


def third_view_experiment():
    """Rows (name, training angles, training-view PSNR, PSNR per TEST_ANGLES, mean PSNR around the ring)."""
    configs = [("2 view", nerf_bug.BUGGY_ANGLES)]
    configs += [(f"+ {a:g} deg", nerf_bug.BUGGY_ANGLES + [a]) for a in THIRD_ANGLES]
    configs += [("8 view", nerf_bug.FIXED_ANGLES)]
    rows = []
    for name, angles in configs:
        grid, _, train_psnr = nerf_bug._train_on(angles)
        ring = [a for a in np.arange(0.0, 360.0, RING_STEP) if a not in angles]
        rows.append((name, angles, train_psnr, _score(grid, TEST_ANGLES), float(np.mean(_score(grid, ring)))))
    return rows


def _print_init(curves):
    print(f"(a) sigma_raw start vs training MSE, 8-view capture, {INIT_ITERS} iterations")
    marks = [0, 10, 50, 100, INIT_ITERS - 1]
    print("   lr   start  " + "  ".join(f"it {m:3d}" for m in marks) + "   drop")
    for (lr, start), hist in curves.items():
        mse = dict(hist)
        print(f"{lr:5g}  {start:+5.0f}   " + "  ".join(f"{mse[m]:.4f}" for m in marks)
              + f"   {mse[0] - mse[INIT_ITERS - 1]:.4f}")


def _print_third(rows):
    print("(b) a third view added to [0, 20] deg; PSNR (dB) on held-out angles "
          + ", ".join(f"{a:g}" for a in TEST_ANGLES))
    base, base_ring = np.mean(rows[0][3]), rows[0][4]
    print(f"  capture        train   held-out mean (vs 2 view)   ring mean every {RING_STEP:g} deg (vs 2 view)   per angle")
    for name, _, train_psnr, scores, ring in rows:
        print(f"  {name:12s}  {train_psnr:6.2f}      {np.mean(scores):6.2f} ({np.mean(scores) - base:+5.2f})"
              f"              {ring:6.2f} ({ring - base_ring:+5.2f})              " + " ".join(f"{s:5.2f}" for s in scores))


if __name__ == "__main__":
    flags = set(sys.argv[1:])
    if not flags or "--init" in flags:
        _print_init(init_experiment())
    if not flags or "--third" in flags:
        _print_third(third_view_experiment())
