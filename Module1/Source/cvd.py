"""Module 1 -- colour-vision-deficiency simulation from scratch (NumPy only).

Job: apply a fixed 3x3 matrix to LINEAR RGB to approximate how an image looks
to a viewer with deuteranopia / protanopia, then re-encode. Used to test a
chart / legend: if two categories collapse to the same colour, the chart
fails.

Reproduces: section "Colour-Vision Deficiency" -- the deuteranopia matrix, and
the rule "rows 1 and 2 are nearly equal, so red and green inputs come out
nearly identical".

Run:
  python cvd.py --selftest
  python cvd.py --image data/relief.ppm --type deuteranopia --out report/relief_deut.ppm
  python cvd.py --legend                 # builds + tests a 5-category legend
"""
from __future__ import annotations

import argparse
import sys

import numpy as np

from ppm_io import read_ppm, write_ppm
from srgb import srgb_to_linear, linear_to_srgb, to_float, to_u8

# Vienot / Brettel-style matrices, applied to LINEAR RGB.
MATS = {
    "deuteranopia": np.array([[0.625, 0.375, 0.000],
                              [0.700, 0.300, 0.000],
                              [0.000, 0.300, 0.700]]),
    "protanopia":   np.array([[0.567, 0.433, 0.000],
                              [0.558, 0.442, 0.000],
                              [0.000, 0.242, 0.758]]),
    "tritanopia":   np.array([[0.950, 0.050, 0.000],
                              [0.000, 0.433, 0.567],
                              [0.000, 0.475, 0.525]]),
}


def simulate(img_u8: np.ndarray, kind: str) -> np.ndarray:
    m = MATS[kind]
    lin = srgb_to_linear(to_float(img_u8))
    out = np.clip(lin @ m.T, 0.0, 1.0)
    return to_u8(linear_to_srgb(out))


def grayscale_test(img_u8: np.ndarray) -> np.ndarray:
    lin = srgb_to_linear(to_float(img_u8))
    y = lin @ np.array([0.2126, 0.7152, 0.0722])
    g = to_u8(linear_to_srgb(y))
    return np.dstack([g, g, g])


def _swatches(colors: list[tuple[int, int, int]], sw: int = 24) -> np.ndarray:
    row = np.concatenate([np.full((sw, sw, 3), c, np.uint8) for c in colors], axis=1)
    return row


def _min_pair_dist(sw_row: np.ndarray, sw: int = 24) -> float:
    """Smallest pairwise distance between swatch mean colours (RGB, 0..255)."""
    n = sw_row.shape[1] // sw
    means = [sw_row[:, k * sw:(k + 1) * sw].reshape(-1, 3).mean(0) for k in range(n)]
    return min(float(np.linalg.norm(means[i] - means[j]))
               for i in range(n) for j in range(i + 1, n))


def _distinct(sw_row: np.ndarray, sw: int = 24, thresh: float = 20.0) -> bool:
    return _min_pair_dist(sw_row, sw) >= thresh


def _selftest() -> None:
    # a pure-red / pure-green pair: deuteranopia should COMPRESS the gap a lot
    rg = _swatches([(220, 30, 30), (30, 180, 30)])
    d0 = _min_pair_dist(rg)
    d1 = _min_pair_dist(simulate(rg, "deuteranopia"))
    d2 = _min_pair_dist(simulate(rg, "protanopia"))
    assert d1 < 0.62 * d0, f"deuteranopia should compress red/green ({d1:.0f} vs {d0:.0f})"
    assert d2 < 0.62 * d0, f"protanopia should compress red/green ({d2:.0f} vs {d0:.0f})"

    # a blue / orange pair: should mostly SURVIVE both simulations
    bo = _swatches([(20, 90, 200), (240, 140, 20)])
    b0 = _min_pair_dist(bo)
    assert _min_pair_dist(simulate(bo, "deuteranopia")) > 0.65 * b0, "blue/orange should survive"
    assert _min_pair_dist(simulate(bo, "protanopia")) > 0.65 * b0, "blue/orange should survive"
    print(f"cvd self-test OK  (red/green gap {d0:.0f} -> deuter {d1:.0f} / protan {d2:.0f}; "
          f"blue/orange gap {b0:.0f} largely preserved)")


def _legend_demo() -> None:
    bad = [(200, 40, 40), (40, 170, 40), (210, 150, 30), (150, 90, 40), (90, 160, 40)]
    hue_ok = [(15, 60, 130), (250, 190, 20), (110, 20, 130), (20, 160, 160), (230, 90, 30)]
    # viridis sampled at 5 points -- monotone luminance ramp, so grayscale-safe too
    lum_ramp = [(68, 1, 84), (59, 82, 139), (33, 145, 140), (94, 201, 98), (253, 231, 37)]
    for name, cols in (("BAD (red/green heavy)", bad),
                       ("HUE-OK (survives CVD, fails grayscale)", hue_ok),
                       ("BEST (viridis: luminance ramp)", lum_ramp)):
        row = _swatches(cols)
        ok_norm = _distinct(row)
        ok_deut = _distinct(simulate(row, "deuteranopia"))
        ok_prot = _distinct(simulate(row, "protanopia"))
        ok_gray = _distinct(grayscale_test(row))
        print(f"{name:28s}  normal={ok_norm}  deuter={ok_deut}  "
              f"protan={ok_prot}  grayscale={ok_gray}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--image")
    ap.add_argument("--type", default="deuteranopia", choices=list(MATS))
    ap.add_argument("--out")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--legend", action="store_true")
    args = ap.parse_args()
    if args.legend:
        _legend_demo()
        return
    if args.selftest or not args.image:
        _selftest()
        return
    img = read_ppm(args.image)
    out = simulate(img, args.type)
    if args.out:
        write_ppm(args.out, out)
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
