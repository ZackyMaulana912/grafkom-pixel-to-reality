"""Module 1 -- prove the one-line gamma fix (Lab 2 no 2, after the diagnosis).

Written AFTER docs/prediksi/diagnosis-gamma.md was finished. It checks the four
predictions in that file against the real fix in resample.box_downscale_2x,
where the whole difference is one step:
    f = srgb_to_linear(f)     # decode before averaging (and encode after)

The reference is the light-preserving average from gamma_diagnosis.py (H2),
which was written before the fix was looked at, so it is an independent check.

Run:  .venv/bin/python gamma_fix_check.py
"""
from __future__ import annotations

import numpy as np

from gamma_diagnosis import diagnose, light
from metrics import psnr, ssim
from ppm_io import read_ppm
from resample import box_downscale_2x


def same(a: np.ndarray, b: np.ndarray) -> str:
    d = np.abs(a.astype(int) - b.astype(int))
    return f"{np.mean(d == 0) * 100:6.2f}% exact, max diff {d.max()}"


def main() -> None:
    src, thumb = read_ppm("data/relief.ppm"), read_ppm("data/thumb_buggy.ppm")
    h2 = diagnose(src, thumb)["h2"]
    without = box_downscale_2x(src, gamma_correct=False)   # the decode step switched off
    fixed = box_downscale_2x(src, gamma_correct=True)      # the decode step switched on

    print("== the one step, switched off and on ==")
    print(f"  without decode vs shipped thumb_buggy : {same(without, thumb)}")
    print(f"  with decode    vs H2 (light-preserving): {same(fixed, h2)}")

    print("\n== prediction 1: fixed == H2 within 1 code ==")
    p1 = np.abs(fixed.astype(int) - h2).max() <= 1
    print(f"  {same(fixed, h2)}  -> {'confirmed' if p1 else 'WRONG'}")

    print("\n== prediction 2: mean code rises from 144.20 to about 164.44 ==")
    print(f"  before {thumb.mean():.2f}  after {fixed.mean():.2f}")

    print("\n== prediction 3: mean light back to the source ==")
    ls, lb, lf = light(src).mean(), light(thumb).mean(), light(fixed).mean()
    print(f"  source {ls:.5f}  before {lb:.5f} ({(lb / ls - 1) * 100:+.2f}%)  "
          f"after {lf:.5f} ({(lf / ls - 1) * 100:+.3f}%)")

    print("\n== prediction 4: the difference is largest where the blocks are contrasty ==")
    b = src.reshape(128, 2, 128, 2, 3)
    contrast = (b.max(axis=(1, 3)).astype(int) - b.min(axis=(1, 3))).ravel()
    diff = np.abs(fixed.astype(int) - thumb.astype(int)).ravel()
    for lo, hi in ((32, 96), (96, 160), (160, 256)):
        m = (contrast >= lo) & (contrast < hi)
        print(f"  contrast {lo:3d}-{hi - 1:3d}: mean |after - before| {diff[m].mean():5.2f} codes")

    print("\n== PSNR / SSIM against the independent light-preserving reference H2 ==")
    for name, img in (("before (thumb_buggy)", thumb), ("after (fixed)", fixed)):
        p = psnr(img, h2)
        print(f"  {name:22s} PSNR {'inf' if np.isinf(p) else f'{p:.2f}'} dB   SSIM {ssim(img, h2):.4f}")


if __name__ == "__main__":
    main()
