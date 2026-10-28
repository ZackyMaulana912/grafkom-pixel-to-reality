"""Module 3 -- re-save rendered PPM frames as PNG for the README (decision K4).

GitHub cannot show .ppm. Pillow only re-encodes the pixels; nothing is resized
or changed, so a PNG here is byte-for-byte the same picture as its PPM.

Run:  .venv/bin/python export_png.py --src out --out ../docs/img [names ...]
"""
from __future__ import annotations

import argparse
import glob
import os

from PIL import Image

from ppm_io import read_ppm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="out")
    ap.add_argument("--out", default="../docs/img")
    ap.add_argument("names", nargs="*", help="file names without .ppm (default: all)")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    if args.names:
        files = [os.path.join(args.src, n + ".ppm") for n in args.names]
    else:
        files = sorted(glob.glob(os.path.join(args.src, "*.ppm")))
    if not files:
        raise SystemExit(f"no .ppm in {args.src}/")
    for f in files:
        img = read_ppm(f)
        name = os.path.splitext(os.path.basename(f))[0] + ".png"
        Image.fromarray(img, "L" if img.ndim == 2 else "RGB").save(os.path.join(args.out, name), optimize=True)
    print(f"exported {len(files)} images to {args.out}/")


if __name__ == "__main__":
    main()
