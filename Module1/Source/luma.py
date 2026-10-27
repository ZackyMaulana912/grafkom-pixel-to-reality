"""Module 1 -- RGB -> grayscale, done correctly (NumPy only).

Correct recipe:  decode sRGB -> linear ; Rec.709 weights ; encode -> sRGB.

The three variants differ only in WHERE the weighted sum happens and WHICH
weights it uses, so they share one helper:
  rgb_to_grey               linear light, Rec.709  (physically correct luminance)
  rgb_to_grey_naive_weights sRGB codes,   Rec.709  (the common bug)
  rgb_to_grey_average       sRGB codes,   1/3 each (plain average)

Reproduces: Example E5 -- for RGB (200,100,50):
  correct (gamma-2 hand version) ~= 126
  naive Rec.709 weighted sum on codes ~= 118
  plain average ~= 117

Run:
  python luma.py --selftest
  python luma.py --image data/relief.ppm --out report/relief_grey.pgm --cross-check
"""
from __future__ import annotations

import argparse

import numpy as np

from ppm_io import read_ppm, write_ppm
from srgb import (srgb_to_linear, linear_to_srgb, srgb_to_linear_g2,
                  linear_to_srgb_g2, to_float, to_u8)

REC709 = (0.2126, 0.7152, 0.0722)
REC601 = (0.299, 0.587, 0.114)
EQUAL = (1 / 3, 1 / 3, 1 / 3)


def weighted_sum(rgb: np.ndarray, weights) -> np.ndarray:
    """w_r * R + w_g * G + w_b * B over the last axis."""
    wr, wg, wb = weights
    return wr * rgb[..., 0] + wg * rgb[..., 1] + wb * rgb[..., 2]


def rgb_to_grey(img_u8: np.ndarray, approx: bool = False) -> np.ndarray:
    """Correct luminance grey. approx=True uses the gamma-2 curve (hand math);
    approx=False uses the real sRGB curve (ship this)."""
    decode, encode = ((srgb_to_linear_g2, linear_to_srgb_g2) if approx
                      else (srgb_to_linear, linear_to_srgb))
    y_linear = weighted_sum(decode(to_float(img_u8)), REC709)
    return to_u8(encode(y_linear))


def rgb_to_grey_naive_weights(img_u8: np.ndarray) -> np.ndarray:
    """The common bug: Rec.709 weights applied straight to sRGB codes."""
    return to_u8(weighted_sum(to_float(img_u8), REC709))


def rgb_to_grey_average(img_u8: np.ndarray) -> np.ndarray:
    return to_u8(weighted_sum(to_float(img_u8), EQUAL))


def pillow_gap(img_u8: np.ndarray) -> np.ndarray:
    """|ours - Pillow convert('L')| per pixel. Pillow's "L" is Rec.601 luma on
    gamma codes, so a gap on saturated colours is expected, not a bug."""
    from PIL import Image
    ref = np.asarray(Image.fromarray(img_u8).convert("L"))
    return np.abs(rgb_to_grey(img_u8).astype(int) - ref.astype(int))


def _selftest() -> None:
    px = np.array([[[200, 100, 50]]], dtype=np.uint8)
    correct = int(rgb_to_grey(px, approx=True)[0, 0])
    real = int(rgb_to_grey(px)[0, 0])
    naive_w = int(rgb_to_grey_naive_weights(px)[0, 0])
    avg = int(rgb_to_grey_average(px)[0, 0])
    assert 124 <= correct <= 128, f"E5 correct grey {correct} not ~126"
    assert 116 <= naive_w <= 120, f"E5 naive-weights grey {naive_w} not ~118"
    assert avg == 117, f"E5 average {avg} != 117"

    # a flat grey must map to (about) itself
    g = np.full((4, 4, 3), 128, dtype=np.uint8)
    out = int(rgb_to_grey(g)[0, 0])
    assert abs(out - 128) <= 1, f"grey of flat 128 -> {out}"
    print(f"luma self-test OK  (E5: correct~{correct} (real sRGB curve {real}), "
          f"naive-weights~{naive_w}, avg={avg}; flat 128 -> {out})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--image")
    ap.add_argument("--out")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--cross-check", action="store_true")
    args = ap.parse_args()
    if args.selftest or not args.image:
        _selftest()
        return
    img = read_ppm(args.image)
    grey = rgb_to_grey(img)
    if args.out:
        write_ppm(args.out, grey)
        print(f"wrote {args.out}")
    if args.cross_check:
        d = pillow_gap(img)
        print(f"vs Pillow convert('L'): mean |diff| = {d.mean():.2f}, max = {int(d.max())}  "
              f"(gap is expected: Pillow = Rec.601 luma in gamma space; "
              f"ours = linear-light luminance)")


if __name__ == "__main__":
    main()
