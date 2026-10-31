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
  python cvd.py --legend --out report/   # also writes the before/after legend strips
  python cvd.py --compare --image data/relief.ppm   # course matrices vs Machado et al. 2009
"""
from __future__ import annotations

import argparse
import sys

import numpy as np

from ppm_io import read_ppm, write_ppm
from srgb import srgb_to_linear, linear_to_srgb, to_float, to_u8

# The course's matrices, applied to LINEAR RGB. Their source is not Vienot/Brettel: they are the
# "ColorMatrix" Channel Mixer values published by colorjack.com (archived 18 Dec 2008), fitted by
# hue to Matthew Wickline's formulas and meant for Photoshop-style RGB mixing. Kept unchanged
# because the module text uses them; MACHADO_2009 below is the published model they are checked
# against (docs/catatan/fase4-gamma-aliasing.md).
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


# Machado, Oliveira & Fernandes (2009), IEEE TVCG 15(6) 1291-1298, Table 1, severity 1.0
# (dichromacy), copied from the authors' page inf.ufrgs.br/~oliveira/pubs_files/CVD_Simulation/.
MACHADO_2009 = {
    "deuteranopia": np.array([[0.367322, 0.860646, -0.227968],
                              [0.280085, 0.672501, 0.047413],
                              [-0.011820, 0.042940, 0.968881]]),
    "protanopia":   np.array([[0.152286, 1.052583, -0.204868],
                              [0.114503, 0.786281, 0.099216],
                              [-0.003882, -0.048116, 1.051998]]),
    "tritanopia":   np.array([[1.255528, -0.076749, -0.178779],
                              [-0.078411, 0.930809, 0.147602],
                              [0.004733, 0.691367, 0.303900]]),
}


def simulate(img_u8: np.ndarray, kind: str, mats: dict = MATS) -> np.ndarray:
    m = mats[kind]
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


BAD_LEGEND = [(200, 40, 40), (40, 170, 40), (210, 150, 30), (150, 90, 40), (90, 160, 40)]
# viridis sampled at 5 points -- monotone luminance ramp, so grayscale-safe too.
# This is the legend the project's charts use; make test guards it.
LEGEND = [(68, 1, 84), (59, 82, 139), (33, 145, 140), (94, 201, 98), (253, 231, 37)]
VIEWS = {
    "normal": lambda row: row,
    "deuteranopia": lambda row: simulate(row, "deuteranopia"),
    "protanopia": lambda row: simulate(row, "protanopia"),
    "grayscale": grayscale_test,
}


def legend_distances(colors, sw: int = 24) -> dict[str, float]:
    """Smallest distance between any two legend entries, for each way of seeing it."""
    row = _swatches(colors, sw)
    return {view: _min_pair_dist(f(row), sw) for view, f in VIEWS.items()}


def assert_legend_safe(colors, thresh: float = 20.0) -> None:
    """Fail loudly, naming the view, if any two categories collapse below `thresh`."""
    collapsed = {v: round(d, 1) for v, d in legend_distances(colors).items() if d < thresh}
    assert not collapsed, f"legend categories collapse (min distance < {thresh}): {collapsed}"


def compare_models(colors, sw: int = 24) -> dict[str, dict[str, float]]:
    """Smallest legend distance under the course matrices and under Machado 2009, both in linear light."""
    row = _swatches(colors, sw)
    return {kind: {"course": _min_pair_dist(simulate(row, kind), sw),
                   "machado2009": _min_pair_dist(simulate(row, kind, MACHADO_2009), sw)}
            for kind in ("deuteranopia", "protanopia")}


def _compare_demo(image: str | None) -> None:
    for name, cols in (("BAD (red/green heavy)", BAD_LEGEND), ("project legend (viridis)", LEGEND)):
        for kind, d in compare_models(cols).items():
            print(f"{name:26s} {kind:13s} course {d['course']:6.1f}   machado2009 {d['machado2009']:6.1f}")
    rg = _swatches([(220, 30, 30), (30, 180, 30)])
    print(f"red/green pair: gap {_min_pair_dist(rg):.1f} -> deuteranopia course "
          f"{_min_pair_dist(simulate(rg, 'deuteranopia')):.1f}, machado2009 "
          f"{_min_pair_dist(simulate(rg, 'deuteranopia', MACHADO_2009)):.1f}")
    if image:
        img = read_ppm(image)
        for kind in ("deuteranopia", "protanopia"):
            d = np.abs(simulate(img, kind).astype(int) - simulate(img, kind, MACHADO_2009).astype(int))
            print(f"{image} {kind}: |course - machado2009| mean {d.mean():.2f}, max {d.max()} codes")


def write_legend_images(out: str) -> None:
    """Before/after legend strips (bad palette, project palette) in all four views."""
    import os
    os.makedirs(out, exist_ok=True)
    for tag, cols in (("bad", BAD_LEGEND), ("", LEGEND)):
        row = _swatches(cols, sw=48)
        for view, suffix in (("normal", ""), ("deuteranopia", "_deuter"),
                             ("protanopia", "_protan"), ("grayscale", "_gray")):
            name = f"legend{'_' + tag if tag else ''}{suffix}.ppm"
            write_ppm(os.path.join(out, name), VIEWS[view](row))
    print(f"wrote legend strips (bad + project palette, 4 views each) to {out}")


def _legend_demo() -> None:
    bad = BAD_LEGEND
    hue_ok = [(15, 60, 130), (250, 190, 20), (110, 20, 130), (20, 160, 160), (230, 90, 30)]
    lum_ramp = LEGEND
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
        dist = legend_distances(cols)
        print(" " * 30 + "min distance: " + ", ".join(f"{v} {d:.1f}" for v, d in dist.items()))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--image")
    ap.add_argument("--type", default="deuteranopia", choices=list(MATS))
    ap.add_argument("--out")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--legend", action="store_true")
    ap.add_argument("--compare", action="store_true", help="course matrices vs Machado et al. 2009")
    args = ap.parse_args()
    if args.compare:
        _compare_demo(args.image)
        return
    if args.legend:
        _legend_demo()
        if args.out:
            write_legend_images(args.out)
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
