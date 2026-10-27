"""Module 1 -- histogram from raw arrays, from scratch (NumPy only).

Job: count how many pixels fall in each intensity bin, WITHOUT calling a
histogram or bincount function, then prove it matches numpy.histogram exactly.

How: sort the codes once, then for every bin find where its first code would
be inserted in the sorted list. The count of a bin is the distance between its
start and the next bin's start. Works for any bin count from 1 to 256.

Reproduces: Fully Worked Example Step 2 -- "sum of bins = W*H",
            "max err vs numpy.histogram = 0".

Run:
  python histogram.py --image data/relief.ppm --channel luma --bins 16
  python histogram.py --selftest
"""
from __future__ import annotations

import argparse

import numpy as np

from ppm_io import read_ppm


def to_luma_codes(img: np.ndarray) -> np.ndarray:
    """Quick Rec.601 luma on codes -- only for BINNING/visualisation, not a
    colour-correct conversion (see luma.py for that)."""
    if img.ndim == 2:
        return img
    w = np.array([0.299, 0.587, 0.114])
    return np.round(img.astype(np.float64) @ w).clip(0, 255).astype(np.uint8)


def bin_starts(bins: int) -> np.ndarray:
    """First code of each bin, plus 256 as the end marker.

    Bin k covers [k*256/bins, (k+1)*256/bins); for integer codes its first code
    is ceil(k*256/bins). Integer arithmetic only, so no float edge can land on
    the wrong side of a code.
    """
    k = np.arange(bins + 1, dtype=np.int64)
    return -(-k * 256 // bins)


def histogram_from_scratch(values_u8: np.ndarray, bins: int) -> np.ndarray:
    """Count uint8 values (0..255) into `bins` equal-width bins over [0, 256)."""
    if not 1 <= bins <= 256:
        raise ValueError(f"bins must be 1..256, got {bins}")
    values = np.asarray(values_u8)
    if values.dtype != np.uint8:
        raise ValueError("histogram_from_scratch expects uint8 codes")
    ordered = np.sort(values.reshape(-1))
    positions = np.searchsorted(ordered, bin_starts(bins), side="left")
    return np.diff(positions).astype(np.int64)


def _print_hist(counts: np.ndarray) -> None:
    starts = bin_starts(len(counts))
    scale = max(1, counts.max() // 40)
    for b, c in enumerate(counts):
        lo, hi = starts[b], starts[b + 1] - 1
        print(f"bin {b:3d} [{lo:3d}-{hi:3d}]: {c:8d}  {'#' * int(c // scale)}")
    print(f"sum of bins = {counts.sum()}")


def _selftest() -> None:
    # every code 0..255 appears, each a different number of times (1..256)
    every_code = np.repeat(np.arange(256, dtype=np.uint8), np.arange(1, 257))
    worst = 0
    for bins in range(1, 257):
        mine = histogram_from_scratch(every_code, bins)
        ref, _ = np.histogram(every_code, bins=bins, range=(0, 256))
        worst = max(worst, int(np.max(np.abs(mine - ref))))
        assert mine.sum() == every_code.size
    assert worst == 0, f"max err vs numpy.histogram = {worst}"
    print("histogram self-test OK  (max err vs numpy.histogram = 0 for every bin count 1..256)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--image")
    ap.add_argument("--channel", default="luma", choices=["luma", "r", "g", "b", "gray"])
    ap.add_argument("--bins", type=int, default=16)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest or not args.image:
        _selftest()
        return

    img = read_ppm(args.image)
    if args.channel in ("luma", "gray") or img.ndim == 2:
        vals = to_luma_codes(img)
    else:
        vals = img[..., "rgb".index(args.channel)]

    mine = histogram_from_scratch(vals, args.bins)
    ref, _ = np.histogram(vals, bins=args.bins, range=(0, 256))
    _print_hist(mine)
    print(f"W*H = {vals.size}   max err vs numpy.histogram = "
          f"{int(np.max(np.abs(mine - ref)))}")


if __name__ == "__main__":
    main()
