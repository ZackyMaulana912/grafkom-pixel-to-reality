"""Module 3 -- build my texture atlas from my own Module 1 photos (decision K2).

Pillow is used for ONE thing: decoding the JPG files. Cropping, resizing and
packing are NumPy, and the resize is an exact area average in linear light
(Module 1: never average sRGB codes). The result is one sRGB P6 file that the
rasteriser, the ray tracer and the WebGL viewer all read byte for byte.

Run:  .venv/bin/python import_texture.py [--spec data/mymodel_ukuran.json]
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np
from PIL import Image

from ppm_io import write_ppm
from srgb import linear_to_srgb, srgb_to_linear, to_u8


def area_weights(n_in, n_out):
    """(n_out, n_in) matrix: row i averages the input cells covered by output cell i."""
    s = n_in / n_out
    lo = np.arange(n_out)[:, None] * s
    hi = lo + s
    j = np.arange(n_in)[None, :]
    overlap = np.clip(np.minimum(hi, j + 1) - np.maximum(lo, j), 0, None)
    return overlap / s


def area_resize(lin, w, h):
    """Exact box resample of a linear-light (H,W,3) float image to (h,w,3)."""
    wy = area_weights(lin.shape[0], h)
    wx = area_weights(lin.shape[1], w)
    rows = np.einsum("ij,jkc->ikc", wy, lin)          # two passes: rows, then columns
    return np.einsum("ikc,lk->ilc", rows, wx)


def build_atlas(spec, base_dir="."):
    atlas = spec["atlas"]
    n = atlas["size"]
    lin = np.full((n, n, 3), srgb_to_linear(0.5))      # mid grey where no region is
    photos = os.path.join(base_dir, atlas["photos_dir"])
    for name, r in atlas["regions"].items():
        rgb = np.asarray(Image.open(os.path.join(photos, r["photo"])).convert("RGB"))
        x0, y0, x1, y1 = r["crop"]
        crop = srgb_to_linear(rgb[y0:y1, x0:x1].astype(np.float64) / 255.0)
        rx0, ry0, rx1, ry1 = r["rect"]
        lin[ry0:ry1, rx0:rx1] = area_resize(crop, rx1 - rx0, ry1 - ry0)
    return to_u8(linear_to_srgb(lin))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default="data/mymodel_ukuran.json")
    ap.add_argument("--out", default="data/mymodel_tex.ppm")
    args = ap.parse_args()
    spec = json.load(open(args.spec))
    tex = build_atlas(spec)                     # photos_dir is relative to Source/
    nbytes = write_ppm(args.out, tex)
    print(f"wrote {args.out}  ({tex.shape[1]}x{tex.shape[0]}, {nbytes} bytes, "
          f"{len(spec['atlas']['regions'])} regions)")


if __name__ == "__main__":
    main()
