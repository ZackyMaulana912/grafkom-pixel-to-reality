"""Module 1 -- which library default matches a correct downscale? (Lab 3 no 2)

Downscales an image 2x three ways and scores each against the linear-correct
result with PSNR and SSIM:
  linear-correct : resample.box_downscale_2x(gamma_correct=True)  (decode, average, encode)
  naive          : resample.box_downscale_2x(gamma_correct=False) (average the codes)
  Pillow BOX     : Image.resize(..., Image.BOX), the library default box filter

Pillow is the reference under test here, not part of the from-scratch path.

Run:  .venv/bin/python downscale_compare.py --out report/
"""
from __future__ import annotations

import argparse
import os

import numpy as np
from PIL import Image

from metrics import psnr, ssim
from ppm_io import read_ppm
from resample import box_downscale_2x

IMAGES = ["data/IMG_8884.ppm", "data/IMG_8893.ppm", "data/relief.ppm"]


def even(img: np.ndarray) -> np.ndarray:
    return img[: img.shape[0] // 2 * 2, : img.shape[1] // 2 * 2]


def compare(path: str) -> list[tuple]:
    img = even(read_ppm(path))
    h, w = img.shape[:2]
    correct = box_downscale_2x(img, gamma_correct=True)
    naive = box_downscale_2x(img, gamma_correct=False)
    pil = np.asarray(Image.fromarray(img).resize((w // 2, h // 2), Image.BOX))
    rows = []
    for name, out in (("naive (sRGB codes)", naive), ("Pillow Image.BOX", pil)):
        d = np.abs(out.astype(int) - correct.astype(int))
        rows.append((name, psnr(out, correct), ssim(out, correct), d.mean(), int(d.max()),
                     float(correct.mean() - out.mean())))
    d = np.abs(pil.astype(int) - naive.astype(int))
    rows.append(("Pillow BOX vs naive", psnr(pil, naive), ssim(pil, naive), d.mean(), int(d.max()),
                 float(naive.mean() - pil.mean())))
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="report")
    args = ap.parse_args()
    lines = ["# Downscale 2x: naive and Pillow BOX against the linear-correct result\n",
             "| image | method | PSNR | SSIM | mean abs diff | max abs diff | darker by (mean) |",
             "|---|---|---|---|---|---|---|"]
    for path in IMAGES:
        name = os.path.basename(path)
        print(f"== {name} ==")
        for method, p, s, mean_d, max_d, darker in compare(path):
            ptxt = "inf" if np.isinf(p) else f"{p:.2f} dB"
            print(f"  {method:20s} PSNR {ptxt:>9s}  SSIM {s:.4f}  mean |diff| {mean_d:5.2f}  "
                  f"max {max_d:3d}  darker by {darker:+.2f}")
            lines.append(f"| {name} | {method} | {ptxt} | {s:.4f} | {mean_d:.2f} | {max_d} | {darker:+.2f} |")
    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, "downscale_compare.md")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
