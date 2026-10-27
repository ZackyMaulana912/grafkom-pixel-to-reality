"""Module 1 -- export report images as PNG for the GitHub README (decision K4).

GitHub cannot show .ppm/.pgm, so every report image is re-saved as PNG under
../docs/img/. Pillow only re-encodes the pixels; nothing is resized or changed.

Run:  .venv/bin/python export_png.py --src report --out ../docs/img
"""
from __future__ import annotations

import argparse
import glob
import os

from PIL import Image

from ppm_io import read_ppm


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="report")
    ap.add_argument("--out", default="../docs/img")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    files = sorted(glob.glob(os.path.join(args.src, "*.ppm")) + glob.glob(os.path.join(args.src, "*.pgm")))
    if not files:
        raise SystemExit(f"no .ppm/.pgm in {args.src}/ -- run make report first")
    for f in files:
        img = read_ppm(f)
        name = os.path.splitext(os.path.basename(f))[0] + ".png"
        Image.fromarray(img, "L" if img.ndim == 2 else "RGB").save(os.path.join(args.out, name), optimize=True)
    print(f"exported {len(files)} images to {args.out}/")


if __name__ == "__main__":
    main()
