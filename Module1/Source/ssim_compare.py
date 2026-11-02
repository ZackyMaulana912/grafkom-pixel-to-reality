"""Module 1 -- global SSIM vs windowed SSIM on my two crops (Optional Extension Lab of metrics.py).

The module's ssim() is one window over the whole image. On my wall crop it calls JPG q40
almost perfect although the 8x8 blocks are flat. ssim_windowed() (Wang et al. 2004) looks
at 11x11 neighbourhoods, so lost texture shows up -- but only where the texture is strong
compared to SSIM's constant C2 = (0.03 L)^2, i.e. a local standard deviation of about 7.6
codes. The wall's grain is about 0.5 codes, so the last column measures it directly: the
median ratio of local standard deviation (same 11x11 Gaussian window), decoded / original.
Same encoders and settings as format_compare.py; lossless formats are left out (both SSIMs
are exactly 1 there).

Writes report/ssim_windowed.md and report/ssim_vs_texture_dinding_jpg40.pgm for JPG q40 on
the wall: left the local SSIM (black = 0 or below, white = 1), right the texture kept
(local standard deviation decoded / original, black = 0%, white = 100% or more), both mean
over R, G, B, with a grey gap between them.

Run:  python ssim_compare.py --out report/
"""
from __future__ import annotations

import argparse
import os

import numpy as np

from format_compare import CASES, _encode
from metrics import _filter_valid, _gauss1d, psnr, ssim, ssim_map, ssim_windowed
from ppm_io import read_ppm, write_ppm

CROPS = ["data/crop_dinding.ppm", "data/crop_surai.ppm"]
LOSSY = [c for c in CASES if c[0] not in ("PNG", "WebP-lossless")]


def local_std(img: np.ndarray) -> np.ndarray:
    """Local standard deviation in the SSIM window, mean over R, G, B."""
    g = _gauss1d(11, 1.5)
    out = []
    for c in range(img.shape[2]):
        x = img[..., c].astype(np.float64)
        m = _filter_valid(x, g)
        out.append(np.sqrt(np.maximum(_filter_valid(x * x, g) - m * m, 0.0)))
    return np.mean(out, axis=0)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="report")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    notes = []
    lines = ["| crop | format | PSNR | SSIM global | SSIM windowed | worst local SSIM | texture kept |",
             "|---|---|---|---|---|---|---|"]
    for path in CROPS:
        img = read_ppm(path)
        name = os.path.splitext(os.path.basename(path))[0]
        grain = local_std(img)
        notes.append(f"- {name}: median local standard deviation {np.median(grain):.2f} codes "
                     f"(sqrt(C2) = {0.03 * 255:.2f})")
        for label, fmt, kw in LOSSY:
            n, back = _encode(img, fmt, **kw)
            if n is None:
                lines.append(f"| {name} | {label} | (codec not available) | | | | |")
                continue
            local = np.mean([ssim_map(img[..., c], back[..., c]) for c in range(3)], axis=0)
            row = (f"| {name} | {label} | {psnr(img, back):.1f} dB | {ssim(img, back):.4f} | "
                   f"{ssim_windowed(img, back):.4f} | {local.min():.4f} | "
                   f"{100 * np.median(local_std(back) / np.maximum(grain, 1e-9)):.0f}% |")
            lines.append(row)
            print(row)
            if name == "crop_dinding" and label == "JPG q40":
                kept = local_std(back) / np.maximum(grain, 1e-9)
                gap = np.full((local.shape[0], 6), 0.5)
                both = np.hstack([np.clip(local, 0.0, 1.0), gap, np.clip(kept, 0.0, 1.0)])
                write_ppm(os.path.join(args.out, "ssim_vs_texture_dinding_jpg40.pgm"),
                          (both * 255.0 + 0.5).astype(np.uint8))
    md = os.path.join(args.out, "ssim_windowed.md")
    with open(md, "w") as f:
        f.write("# Global SSIM vs windowed SSIM (Wang et al. 2004: 11x11 Gaussian, sigma 1.5)\n\n")
        f.write("\n".join(notes) + "\n\n" + "\n".join(lines) + "\n")
    print(f"wrote {md}")


if __name__ == "__main__":
    main()
