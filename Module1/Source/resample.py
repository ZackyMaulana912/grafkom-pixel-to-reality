"""Module 1 -- resampling from scratch (NumPy only): nearest, bilinear, box.

Job: change an image's sample grid. Shows explicitly WHICH line makes a
downscale gamma-correct vs gamma-wrong.

Reproduces:
  Example E1  : resample_nearest(patch, 2) == the block-base matrix a_ij
  1-D bilinear identity : samples [0,100] at t=0.25,0.5,0.75 -> 25,50,75
  Fully Worked Example Step 3 : box_downscale_2x(img, gamma_correct=True/False)

Run:
  python resample.py --selftest
  python resample.py --image data/relief.ppm --factor 2 \
         --methods naive-box,linear-box --out report/
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

from ppm_io import read_ppm, write_ppm
from srgb import srgb_to_linear, linear_to_srgb, to_float, to_u8


# ---- nearest neighbour --------------------------------------------------
def resample_nearest(img: np.ndarray, factor: int) -> np.ndarray:
    """Integer downscale by `factor` -- keep the top-left sample of each block.
    This is DECIMATION: it throws (factor^2 - 1) of every factor^2 samples
    away and is what aliases."""
    return img[::factor, ::factor].copy()


# ---- 1-D bilinear (the hand-checkable core) ---------------------------
def lerp_1d(samples: np.ndarray, positions: np.ndarray) -> np.ndarray:
    """Linear interpolation of a 1-D signal at fractional positions."""
    samples = np.asarray(samples, dtype=np.float64)
    positions = np.asarray(positions, dtype=np.float64)
    i0 = np.floor(positions).astype(int)
    i1 = np.clip(i0 + 1, 0, len(samples) - 1)
    i0 = np.clip(i0, 0, len(samples) - 1)
    t = positions - np.floor(positions)
    return (1 - t) * samples[i0] + t * samples[i1]


# ---- 2-D bilinear resize --------------------------------------------
def resample_bilinear(img: np.ndarray, scale: float) -> np.ndarray:
    """Resize by an arbitrary positive `scale` using bilinear interpolation.
    Uses the pixel-centre convention: pixel (r,c) sits at (c+0.5, r+0.5)."""
    f = img.astype(np.float64)
    h, w = f.shape[:2]
    H, W = max(1, round(h * scale)), max(1, round(w * scale))
    ys = (np.arange(H) + 0.5) / scale - 0.5
    xs = (np.arange(W) + 0.5) / scale - 0.5
    y0 = np.clip(np.floor(ys).astype(int), 0, h - 1)
    x0 = np.clip(np.floor(xs).astype(int), 0, w - 1)
    y1 = np.clip(y0 + 1, 0, h - 1)
    x1 = np.clip(x0 + 1, 0, w - 1)
    ty = (ys - np.floor(ys))[:, None]
    tx = (xs - np.floor(xs))[None, :]
    if f.ndim == 3:
        ty = ty[..., None]
        tx = tx[..., None]
    top = (1 - tx) * f[np.ix_(y0, x0)] + tx * f[np.ix_(y0, x1)]
    bot = (1 - tx) * f[np.ix_(y1, x0)] + tx * f[np.ix_(y1, x1)]
    return np.round((1 - ty) * top + ty * bot).clip(0, 255).astype(np.uint8)


# ---- box downscale: the gamma switch --------------------------------
def box_downscale_2x(img_u8: np.ndarray, gamma_correct: bool = True) -> np.ndarray:
    """2x2 box average. With gamma_correct=True the average is taken in LINEAR
    light (correct); with False it is taken on sRGB codes (the bug)."""
    f = to_float(img_u8)
    if gamma_correct:
        f = srgb_to_linear(f)                 # <-- the line the bug omits
    h, w = f.shape[:2]
    f = f.reshape(h // 2, 2, w // 2, 2, -1).mean(axis=(1, 3)).reshape(h // 2, w // 2, -1)
    if f.shape[2] == 1:
        f = f[..., 0]
    if gamma_correct:
        f = linear_to_srgb(f)
    return to_u8(f)


def _selftest() -> None:
    from make_data import running_patch
    P = running_patch()

    # Example E1: nearest 2x downsample == block-base matrix a_ij = 16*(i+j)
    a = np.array([[16 * (i + j) for j in range(4)] for i in range(4)], dtype=np.uint8)
    assert np.array_equal(resample_nearest(P, 2), a), "nearest != a_ij"

    # 1-D bilinear identity
    got = lerp_1d([0, 100], [0.25, 0.5, 0.75])
    assert np.allclose(got, [25, 50, 75]), f"lerp_1d gave {got}"

    # box_downscale of a flat colour is unchanged either way
    flat = np.full((4, 4, 3), 120, dtype=np.uint8)
    assert np.array_equal(box_downscale_2x(flat, True), np.full((2, 2, 3), 120, np.uint8))
    assert np.array_equal(box_downscale_2x(flat, False), np.full((2, 2, 3), 120, np.uint8))

    # checker: 2x2 b/w -> the two methods DIFFER (the whole point)
    ck = np.array([[0, 255], [255, 0]], dtype=np.uint8)[..., None].repeat(3, 2)
    naive = int(box_downscale_2x(ck, gamma_correct=False)[0, 0, 0])
    corr = int(box_downscale_2x(ck, gamma_correct=True)[0, 0, 0])
    assert naive == 128 and 185 <= corr <= 190, f"checker: naive={naive} corr={corr}"
    print(f"resample self-test OK  (nearest==a_ij; lerp 25/50/75; "
          f"checker naive={naive} vs correct={corr})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--image")
    ap.add_argument("--factor", type=int, default=2)
    ap.add_argument("--methods", default="naive-box,linear-box")
    ap.add_argument("--out", default="report")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest or not args.image:
        _selftest()
        return

    os.makedirs(args.out, exist_ok=True)
    img = read_ppm(args.image)
    stem = os.path.splitext(os.path.basename(args.image))[0]
    outs = {}
    for m in args.methods.split(","):
        m = m.strip()
        if m == "nearest":
            r = resample_nearest(img, args.factor)
        elif m == "naive-box":
            r = box_downscale_2x(img, gamma_correct=False)
        elif m == "linear-box":
            r = box_downscale_2x(img, gamma_correct=True)
        elif m == "bilinear":
            r = resample_bilinear(img, 1.0 / args.factor)
        else:
            raise SystemExit(f"unknown method {m}")
        path = os.path.join(args.out, f"{stem}_{m}.ppm")
        write_ppm(path, r)
        outs[m] = r
        print(f"wrote {path}")

    if "naive-box" in outs and "linear-box" in outs:
        d = np.abs(outs["naive-box"].astype(int) - outs["linear-box"].astype(int))
        diff_vis = np.clip(d * 4, 0, 255).astype(np.uint8)
        write_ppm(os.path.join(args.out, f"{stem}_diff.ppm"), diff_vis)
        from metrics import psnr, ssim
        print(f"mean abs difference : {d.mean():.1f} code levels")
        print(f"max  abs difference : {int(d.max())} code levels")
        print(f"PSNR(naive vs linear): {psnr(outs['naive-box'], outs['linear-box']):.1f} dB")
        print(f"SSIM(naive vs linear): {ssim(outs['naive-box'], outs['linear-box']):.3f}")


if __name__ == "__main__":
    main()
