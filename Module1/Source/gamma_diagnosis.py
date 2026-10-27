"""Module 1 -- diagnose the washed-out 2x thumbnail from PIXEL VALUES ONLY.

Lab 2 no 2 asks for the diagnosis before looking at the fix, so this script
never imports gamma_resize_bug.py. It only reads two images:
  data/relief.ppm       the 256x256 source
  data/thumb_buggy.ppm  the 128x128 thumbnail that looks too dark

and tests two hypotheses for how each thumbnail pixel was made from its 2x2
source block:
  H1  average of the four sRGB CODES        (what a plain mean does)
  H2  average of the four LIGHT values      (decode -> mean -> encode)

A downscale should keep the average amount of light. Whichever hypothesis
reproduces the thumbnail exactly tells us what the code did.

Run:  .venv/bin/python gamma_diagnosis.py
"""
from __future__ import annotations

import argparse

import numpy as np

from histogram import histogram_from_scratch
from ppm_io import read_ppm
from srgb import linear_to_srgb, srgb_to_linear


def blocks_2x2(img: np.ndarray) -> np.ndarray:
    """(H, W, C) -> (H/2, W/2, 4, C): the four source samples behind each output pixel."""
    h, w, c = img.shape
    return img.reshape(h // 2, 2, w // 2, 2, c).transpose(0, 2, 1, 3, 4).reshape(h // 2, w // 2, 4, c)


def light(codes: np.ndarray) -> np.ndarray:
    return srgb_to_linear(codes.astype(np.float64) / 255.0)


def to_code(lin: np.ndarray) -> np.ndarray:
    return np.round(linear_to_srgb(lin) * 255).astype(np.uint8)


def diagnose(src: np.ndarray, thumb: np.ndarray) -> dict:
    b = blocks_2x2(src)
    h1 = np.round(b.astype(np.float64).mean(axis=2)).astype(np.uint8)   # mean of codes
    h2 = to_code(light(b).mean(axis=2))                                   # mean of light
    t = thumb.astype(np.int64)
    contrast = (b.max(axis=2).astype(np.int64) - b.min(axis=2)).ravel()
    darker_by = (h2.astype(np.int64) - t).ravel()
    return {
        "mean_code_src": float(src.mean()), "mean_code_thumb": float(thumb.mean()),
        "mean_light_src": float(light(src).mean()), "mean_light_thumb": float(light(thumb).mean()),
        "h1_exact": float(np.mean(h1 == thumb)), "h1_maxdiff": int(np.abs(h1.astype(int) - t).max()),
        "h2_exact": float(np.mean(h2 == thumb)), "h2_maxdiff": int(np.abs(h2.astype(int) - t).max()),
        "darker_by": darker_by, "contrast": contrast,
        "hist_thumb": histogram_from_scratch(thumb, 32),
        "hist_light": histogram_from_scratch(h2, 32),
        "h2": h2,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="data/relief.ppm")
    ap.add_argument("--thumb", default="data/thumb_buggy.ppm")
    args = ap.parse_args()

    src, thumb = read_ppm(args.src), read_ppm(args.thumb)
    d = diagnose(src, thumb)
    loss = 1 - d["mean_light_thumb"] / d["mean_light_src"]
    print("== 1. does the thumbnail keep the average? ==")
    print(f"  mean CODE : source {d['mean_code_src']:.4f}   thumbnail {d['mean_code_thumb']:.4f}")
    print(f"  mean LIGHT: source {d['mean_light_src']:.5f}  thumbnail {d['mean_light_thumb']:.5f}"
          f"   -> {loss * 100:.1f}% of the light is missing")

    print("\n== 2. which recipe reproduces each thumbnail pixel? ==")
    print(f"  H1 mean of 4 codes : {d['h1_exact'] * 100:6.2f}% exact, max diff {d['h1_maxdiff']} code")
    print(f"  H2 mean of 4 lights: {d['h2_exact'] * 100:6.2f}% exact, max diff {d['h2_maxdiff']} codes")

    db, ct = d["darker_by"], d["contrast"]
    print("\n== 3. how much darker than a light-preserving downscale (H2 - thumbnail) ==")
    print(f"  mean {db.mean():+.2f}  min {db.min():+d}  max {db.max():+d} codes;"
          f"  darker in {np.mean(db > 0) * 100:.1f}% of values, never brighter: {bool(np.all(db >= 0))}")
    for lo, hi in ((0, 32), (32, 96), (96, 160), (160, 256)):
        m = (ct >= lo) & (ct < hi)
        if m.any():
            print(f"  blocks with contrast {lo:3d}-{hi - 1:3d} codes: {m.sum():6d} values, "
                  f"darker by {db[m].mean():5.2f} on average")
    print(f"  correlation(block contrast, darkening) = {np.corrcoef(ct, db)[0, 1]:.3f}")

    ht, hl = d["hist_thumb"], d["hist_light"]
    peak = lambda h: int(np.argmax(h)) * 8
    print("\n== 4. histogram shift (32 bins of 8 codes, plot: figures/diagnosis_plot.py) ==")
    print(f"  mean code : thumbnail {thumb.mean():.2f}, light-preserving {d['h2'].mean():.2f}"
          f"  (shift {d['h2'].mean() - thumb.mean():+.2f})")
    print(f"  tallest bin starts at: thumbnail {peak(ht)}, light-preserving {peak(hl)}")


if __name__ == "__main__":
    main()
