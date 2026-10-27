"""Module 1 -- quantisation, banding and dithering (Lab 2 no 3), NumPy only.

Job: build a 512 px black -> white gradient at 8-bit and 5-bit, MEASURE the
width of the flat bands, then dither the 5-bit one and show what changes.

Two ways to cut a ramp into L levels, both used on purpose:
  equal bins  level = floor(x * L / W)       every level gets W/L pixels exactly
                                              -> 2 px at 8-bit, 16 px at 5-bit (Example E2)
  rounding    level = round(v * (L - 1))      the module's code formula, v = x/(W-1);
                                              the two end levels only get half a share

Dithering: ordered (Bayer 4x4). Before rounding, add a threshold that differs
per pixel in a fixed 4x4 pattern, so a value between two levels becomes a mix
of both. The eye averages the mix back into the in-between value. No random
numbers, so the output is identical on every run.

Reproduces: Example E2 -- 8-bit bands 2 px, 5-bit bands 16 px.

Run:
  python dither.py --selftest
  python dither.py --out report/
"""
from __future__ import annotations

import argparse
import os

import numpy as np

from histogram import histogram_from_scratch
from ppm_io import write_ppm

WIDTH, HEIGHT = 512, 64

# 4x4 Bayer index matrix: every value 0..15 once, neighbours as far apart as possible
BAYER4 = np.array([[0, 8, 2, 10],
                   [12, 4, 14, 6],
                   [3, 11, 1, 9],
                   [15, 7, 13, 5]])


def ramp(width: int = WIDTH, height: int = HEIGHT) -> np.ndarray:
    """Ideal intensity v in [0, 1] from black (left) to white (right), float64."""
    v = np.arange(width, dtype=np.float64) / (width - 1)
    return np.tile(v, (height, 1))


def levels_to_codes(level: np.ndarray, bits: int) -> np.ndarray:
    """Level 0..L-1 -> displayable 8-bit code, spread over the full 0..255."""
    return np.round(level * 255 / (2 ** bits - 1)).astype(np.uint8)


def quantise_equal_bins(bits: int, width: int = WIDTH, height: int = HEIGHT) -> np.ndarray:
    level = np.arange(width) * 2 ** bits // width
    return np.tile(levels_to_codes(level, bits), (height, 1))


def quantise_round(v: np.ndarray, bits: int) -> np.ndarray:
    return levels_to_codes(np.round(v * (2 ** bits - 1)), bits)


def dither_ordered(v: np.ndarray, bits: int) -> np.ndarray:
    """floor(v*(L-1) + t) with t from the tiled Bayer matrix, t in (0, 1).

    Without dither t would be 0.5 everywhere, which is plain rounding. Averaged
    over a 4x4 tile t is still 0.5, so the local mean is kept while the band edge
    is broken up.
    """
    h, w = v.shape
    t = (BAYER4 + 0.5) / 16
    t = np.tile(t, (h // 4 + 1, w // 4 + 1))[:h, :w]
    level = np.clip(np.floor(v * (2 ** bits - 1) + t), 0, 2 ** bits - 1)
    return levels_to_codes(level, bits)


def band_widths(row: np.ndarray) -> list[int]:
    """Lengths of the runs of identical values along one row, left to right."""
    edges = np.flatnonzero(np.diff(row.astype(np.int64)) != 0) + 1
    return np.diff(np.concatenate([[0], edges, [len(row)]])).tolist()


def tile_mean_error(codes: np.ndarray, v: np.ndarray, tile: int = 4) -> float:
    """Mean |error| in 8-bit codes after averaging tile x tile blocks -- a stand-in
    for the eye blurring neighbouring pixels together."""
    h, w = codes.shape
    blocks = lambda a: a[:h - h % tile, :w - w % tile].reshape(
        h // tile, tile, w // tile, tile).mean(axis=(1, 3))
    return float(np.abs(blocks(codes.astype(np.float64)) - blocks(v * 255)).mean())


def measure() -> dict:
    v = ramp()
    out = {
        "g8": quantise_equal_bins(8),
        "g5": quantise_equal_bins(5),
        "g5_round": quantise_round(v, 5),
        "g5_dither": dither_ordered(v, 5),
    }
    stats = {name: {
        "bands": band_widths(img[0]),
        "levels": int(np.count_nonzero(histogram_from_scratch(img, 256))),
        "hist": histogram_from_scratch(img, 256),
        "longest_run": max(max(band_widths(r)) for r in img),
        "tile_err": tile_mean_error(img, v),
    } for name, img in out.items()}
    return {"images": out, "stats": stats}


def _selftest() -> None:
    m = measure()
    s = m["stats"]
    assert set(s["g8"]["bands"]) == {2} and s["g8"]["levels"] == 256, "8-bit bands not 2 px"
    assert set(s["g5"]["bands"]) == {16} and s["g5"]["levels"] == 32, "5-bit bands not 16 px"
    # the rounding formula: half-width bands at both ends
    r = s["g5_round"]["bands"]
    assert r[0] == r[-1] == 9 and set(r[1:-1]) <= {16, 17}, f"rounded 5-bit bands {r}"
    # dither uses the same 32 codes, but no flat run is anywhere near 16 px any more
    d = s["g5_dither"]
    used = set(np.flatnonzero(d["hist"]))
    assert used <= set(np.flatnonzero(s["g5"]["hist"])) and d["levels"] == 32
    assert d["longest_run"] < 16, f"dithered longest run {d['longest_run']}"
    assert d["tile_err"] < s["g5_round"]["tile_err"] / 2, "dither did not bring the local mean closer"
    print(f"dither self-test OK  (bands 8-bit 2 px, 5-bit 16 px; dithered longest flat run "
          f"{d['longest_run']} px; 4x4 mean error {s['g5_round']['tile_err']:.2f} -> "
          f"{d['tile_err']:.2f} codes)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest or not args.out:
        _selftest()
        return

    m = measure()
    os.makedirs(args.out, exist_ok=True)
    gap = np.full((8, WIDTH), 255, dtype=np.uint8)
    names = ("g8", "g5", "g5_dither")
    stacked = np.vstack([x for n in names for x in (m["images"][n], gap)][:-1])
    write_ppm(os.path.join(args.out, "gradient_8vs5.pgm"), stacked)
    for n in names:
        write_ppm(os.path.join(args.out, f"gradient_{n[1:]}.pgm"), m["images"][n])
    print(f"wrote gradient_8vs5.pgm (8-bit / 5-bit / 5-bit dithered) and the single strips to {args.out}")

    for n, label in (("g8", "8-bit, equal bins"), ("g5", "5-bit, equal bins"),
                     ("g5_round", "5-bit, round(v*31)"), ("g5_dither", "5-bit, Bayer dither")):
        st = m["stats"][n]
        bands = st["bands"]
        shown = f"{bands[:3]} ... {bands[-3:]}" if len(bands) > 6 else str(bands)
        print(f"{label:20s} levels {st['levels']:3d}  first row bands {shown}  "
              f"longest flat run {st['longest_run']:2d} px  4x4 mean error {st['tile_err']:.2f} codes")
    h_plain, h_dith = m["stats"]["g5"]["hist"], m["stats"]["g5_dither"]["hist"]
    codes = np.flatnonzero(h_plain)
    print("histogram (pixels per code) for the first 6 of the 32 codes:")
    print("  code      ", " ".join(f"{c:5d}" for c in codes[:6]))
    print("  5-bit     ", " ".join(f"{h_plain[c]:5d}" for c in codes[:6]))
    print("  dithered  ", " ".join(f"{h_dith[c]:5d}" for c in codes[:6]))


if __name__ == "__main__":
    main()
