"""Module 1 -- box blur from scratch (NumPy only).

Job: average each pixel with its neighbours. Two variants:
  box_blur_2x2 : non-overlapping 2x2 average -> half size (E1)
  box_blur_3x3 : overlapping 3x3 average, same size (edge-replicated)

How:
  2x2 -- the four samples of every block are four strided views of the image
         (top-left, top-right, bottom-left, bottom-right); add them, divide by 4.
  3x3 -- a summed-area table S, where S[y, x] is the sum of everything above
         and left of (y, x). Any window sum is then 4 lookups:
         S[bottom, right] - S[top, right] - S[bottom, left] + S[top, left].

Reproduces: Example E1 -- on the running patch, the 2x2 result is
  [[  6, 22, 38, 54],
   [ 22, 38, 54, 70],
   [ 38, 54, 70, 86],
   [ 54, 70, 86,102]]   and the patch mean is 54.

NOTE: these blur on the values AS GIVEN. For colour images you almost always
want to decode to linear first -- see resample.py.

Run:  python boxblur.py --selftest
"""
from __future__ import annotations

import sys

import numpy as np


def box_blur_2x2(img: np.ndarray) -> np.ndarray:
    """Non-overlapping 2x2 mean, half the size. H and W must be even."""
    f = img.astype(np.float64)          # uint8 + uint8 would wrap above 255
    h, w = f.shape[:2]
    if h % 2 or w % 2:
        raise ValueError(f"need even dimensions, got {h}x{w}")
    total = f[0::2, 0::2] + f[0::2, 1::2] + f[1::2, 0::2] + f[1::2, 1::2]
    return np.round(total / 4.0).astype(np.uint8)


box_blur_2x2_downscale = box_blur_2x2   # name used by the starter


def summed_area_table(f: np.ndarray) -> np.ndarray:
    """S with one extra zero row and column on top/left, so S[y, x] = f[:y, :x].sum()."""
    pad = ((1, 0), (1, 0)) + (((0, 0),) if f.ndim == 3 else ())
    return np.pad(f, pad).cumsum(axis=0).cumsum(axis=1)


def box_blur_3x3(img: np.ndarray) -> np.ndarray:
    """Overlapping 3x3 mean, same output size, edges replicated."""
    f = img.astype(np.float64)
    h, w = f.shape[:2]
    pad = ((1, 1), (1, 1)) + (((0, 0),) if f.ndim == 3 else ())
    s = summed_area_table(np.pad(f, pad, mode="edge"))
    window = s[3:3 + h, 3:3 + w] - s[0:h, 3:3 + w] - s[3:3 + h, 0:w] + s[0:h, 0:w]
    return np.round(window / 9.0).astype(np.uint8)


def _selftest() -> None:
    from make_data import running_patch
    P = running_patch()
    assert int(round(P.mean())) == 54, f"patch mean {P.mean()} != 54"

    expected = np.array([[6, 22, 38, 54],
                         [22, 38, 54, 70],
                         [38, 54, 70, 86],
                         [54, 70, 86, 102]], dtype=np.uint8)
    got = box_blur_2x2(P)
    assert np.array_equal(got, expected), f"2x2 blur\n{got}\n!=\n{expected}"

    # 3x3 against the neighbour mean written out by hand on the same patch
    inner = (0 + 4 + 16 + 8 + 12 + 24 + 16 + 20 + 32) / 9            # P[1,1]: rows 0-2, cols 0-2
    corner = (0 + 0 + 4 + 0 + 0 + 4 + 8 + 8 + 12) / 9                # P[0,0] with edge replication
    b3 = box_blur_3x3(P)
    assert b3[1, 1] == round(inner) == 15, f"3x3 at (1,1): {b3[1, 1]} vs {inner:.2f}"
    assert b3[0, 0] == round(corner) == 4, f"3x3 at (0,0): {b3[0, 0]} vs {corner:.2f}"

    # 3x3 blur of a constant image is that constant
    c = np.full((6, 6), 77, dtype=np.uint8)
    assert np.array_equal(box_blur_3x3(c), c), "3x3 blur changed a constant"
    print("boxblur self-test OK  (mean=54; 2x2 result matches Example E1; "
          f"3x3 = hand mean at (1,1) {inner:.2f} -> 15 and corner {corner:.2f} -> 4; "
          "3x3 preserves a constant)")


if __name__ == "__main__":
    if "--selftest" in sys.argv or len(sys.argv) == 1:
        _selftest()
