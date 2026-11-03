"""Diagnose-and-fix (Lab 2 no 3): a capture of 2 views, 20 deg apart (0 and 20 deg),
against 8 views spread evenly around the ring (0..315 deg, step 45), on the same scene
with the same training settings.

  python nerf_bug.py --diagnose   trains ONLY the 2-view grid and prints its training
                                  evidence: the MSE curve and the training-view PSNR.
                                  No novel view, no 8-view run, no verdict.
  python nerf_bug.py              the full comparison on a held-out novel view.

The starter's explanation of the outcome was moved out of this file into
docs/catatan/fase4-view-coverage-pitfall.md (decision K14), so the diagnosis has to be
written from the evidence first.
"""
from __future__ import annotations

import os
import sys

import numpy as np

from capture import save_ppm
from nerf_toy import VoxelGrid, render_analytic, render_grid, train, ring_camera, psnr

W, H, FOV = 20, 16, 50.0
NEAR, FAR, N_SAMPLES = 1.0, 5.0, 32
RADIUS, CAM_HEIGHT = 3.0, 1.0
LR, N_ITERS = 100.0, 500
NOVEL_ANGLE_DEG = 190.0  # far from the buggy cluster (0,20); a fair stress test either way

BUGGY_ANGLES = [0, 20]
FIXED_ANGLES = [0, 45, 90, 135, 180, 225, 270, 315]


def _train_on(angles, seed=0, log_every=N_ITERS - 1):
    views = [ring_camera(a, radius=RADIUS, height=CAM_HEIGHT) for a in angles]
    targets = [render_analytic(W, H, FOV, cam, c2w, NEAR, FAR, N_SAMPLES) for cam, c2w in views]
    grid = VoxelGrid(resolution=12, seed=seed)
    history = train(grid, views, W, H, FOV, targets, NEAR, FAR, N_SAMPLES, lr=LR, n_iters=N_ITERS, log_every=log_every)
    train_psnrs = [psnr(render_grid(grid, W, H, FOV, cam, c2w, NEAR, FAR, N_SAMPLES)[0], t)
                   for (cam, c2w), t in zip(views, targets)]
    return grid, history, float(np.mean(train_psnrs))


def diagnose_and_fix():
    novel_cam, novel_c2w = ring_camera(NOVEL_ANGLE_DEG, radius=RADIUS, height=CAM_HEIGHT)
    novel_target = render_analytic(W, H, FOV, novel_cam, novel_c2w, NEAR, FAR, N_SAMPLES)

    buggy_grid, buggy_hist, buggy_train_psnr = _train_on(BUGGY_ANGLES)
    fixed_grid, fixed_hist, fixed_train_psnr = _train_on(FIXED_ANGLES)

    buggy_novel, _ = render_grid(buggy_grid, W, H, FOV, novel_cam, novel_c2w, NEAR, FAR, N_SAMPLES)
    fixed_novel, _ = render_grid(fixed_grid, W, H, FOV, novel_cam, novel_c2w, NEAR, FAR, N_SAMPLES)
    buggy_novel_psnr = psnr(buggy_novel, novel_target)
    fixed_novel_psnr = psnr(fixed_novel, novel_target)

    return dict(
        buggy_hist=buggy_hist, fixed_hist=fixed_hist,
        buggy_train_psnr=buggy_train_psnr, fixed_train_psnr=fixed_train_psnr,
        buggy_novel_psnr=buggy_novel_psnr, fixed_novel_psnr=fixed_novel_psnr,
        novel_target=novel_target, buggy_novel=buggy_novel, fixed_novel=fixed_novel,
    )


# the angles written down in docs/prediksi/diagnosis-view-coverage.md before this was run;
# 270 is a training view of the 8-view grid and is reported only for comparison
SWEEP_ANGLES = [10.0, 22.5, 60.0, 100.0, 160.0, 190.0, 250.0, 340.0, 270.0]


def sweep(angles=SWEEP_ANGLES):
    """Both grids, trained exactly as in diagnose_and_fix, scored on many angles.

    Returns rows (angle, 2-view PSNR, 8-view PSNR, training view of the 2-view grid?,
    training view of the 8-view grid?) plus the two training-view PSNRs."""
    buggy, _, buggy_train = _train_on(BUGGY_ANGLES)
    fixed, _, fixed_train = _train_on(FIXED_ANGLES)
    rows = []
    for angle in angles:
        cam, c2w = ring_camera(angle, radius=RADIUS, height=CAM_HEIGHT)
        target = render_analytic(W, H, FOV, cam, c2w, NEAR, FAR, N_SAMPLES)
        p2 = psnr(render_grid(buggy, W, H, FOV, cam, c2w, NEAR, FAR, N_SAMPLES)[0], target)
        p8 = psnr(render_grid(fixed, W, H, FOV, cam, c2w, NEAR, FAR, N_SAMPLES)[0], target)
        rows.append((angle, p2, p8, angle % 360 in BUGGY_ANGLES, angle % 360 in FIXED_ANGLES))
    return rows, buggy_train, fixed_train


def _nearest_deg(angle, views):
    return min(abs((angle - v + 180.0) % 360.0 - 180.0) for v in views)


def diagnose():
    """Training evidence of the 2-view grid only (K14): what I may look at before predicting."""
    _, history, train_psnr = _train_on(BUGGY_ANGLES, log_every=50)
    print(f"DIAGNOSE -- {len(BUGGY_ANGLES)} views {BUGGY_ANGLES} deg, {N_ITERS} iterations, lr={LR}")
    for it, mse in history:
        print(f"  iter {it:4d}  train MSE = {mse:.5f}")
    print(f"  mean training-view PSNR = {train_psnr:.2f} dB")
    print("(training evidence only: no novel view and no 8-view run in this mode)")


if __name__ == "__main__" and "--diagnose" in sys.argv[1:]:
    diagnose()
elif __name__ == "__main__" and "--sweep" in sys.argv[1:]:
    rows, buggy_train, fixed_train = sweep()
    print(f"training-view PSNR: 2 views {buggy_train:.2f} dB, 8 views {fixed_train:.2f} dB")
    print(" angle  nearest view 2v/8v   2 views   8 views    8v - 2v")
    for angle, p2, p8, t2, t8 in rows:
        note = "  <- training view of the 8-view grid, not held out" if t8 else ""
        print(f"{angle:6.1f}  {_nearest_deg(angle, BUGGY_ANGLES):6.1f} / {_nearest_deg(angle, FIXED_ANGLES):4.1f}"
              f"   {p2:6.2f}    {p8:6.2f}    {p8 - p2:+6.2f}{note}")
elif __name__ == "__main__":
    result = diagnose_and_fix()

    print(f"BUGGY  -- {len(BUGGY_ANGLES)} views {BUGGY_ANGLES} deg (a {BUGGY_ANGLES[1]-BUGGY_ANGLES[0]} deg baseline)")
    for it, mse in result["buggy_hist"]:
        print(f"  iter {it:4d}  train MSE = {mse:.5f}")
    print(f"  mean training-view PSNR = {result['buggy_train_psnr']:.2f} dB  (fits what it saw)")
    print(f"  held-out novel view ({NOVEL_ANGLE_DEG} deg) PSNR = {result['buggy_novel_psnr']:.2f} dB  <-- FLOATERS/COLLAPSE")

    print(f"\nFIXED  -- {len(FIXED_ANGLES)} views spread every 45 deg around the full ring")
    for it, mse in result["fixed_hist"]:
        print(f"  iter {it:4d}  train MSE = {mse:.5f}")
    print(f"  mean training-view PSNR = {result['fixed_train_psnr']:.2f} dB")
    print(f"  held-out novel view ({NOVEL_ANGLE_DEG} deg) PSNR = {result['fixed_novel_psnr']:.2f} dB")

    gap = result["fixed_novel_psnr"] - result["buggy_novel_psnr"]
    print(f"\nnovel-view PSNR improvement from spreading the views out: +{gap:.2f} dB")

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    os.makedirs(out_dir, exist_ok=True)
    save_ppm(os.path.join(out_dir, "bug_novel_target.ppm"), result["novel_target"])
    save_ppm(os.path.join(out_dir, "bug_novel_buggy.ppm"), result["buggy_novel"])
    save_ppm(os.path.join(out_dir, "bug_novel_fixed.ppm"), result["fixed_novel"])
    print("wrote out/bug_novel_{target,buggy,fixed}.ppm")

    assert gap > 1.0, "expected the 8-view fix to clearly beat the 2-view bug on the held-out novel view"
    print("\n[ok] spreading the capture around the ring measurably fixes novel-view quality")
