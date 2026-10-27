"""Module 1 -- import my own photos into data/ and data/manifest.csv.

Job: photos/small/*.jpg (committed, sRGB, no metadata) -> data/<name>.ppm, and
one manifest row per photo describing the ORIGINAL camera file (its real W, H
and bytes on disk come from photos/originals.csv), so the Lab 1 budget is
computed at the resolution the camera actually wrote.

Pillow only decodes the JPEG (decision K2); the PPM is written by ppm_io.

Run:  .venv/bin/python import_photos.py --src photos/small --out data
      (make data runs make_data.py first, then this)
"""
from __future__ import annotations

import argparse
import csv
import glob
import os

import numpy as np
from PIL import Image

from ppm_io import write_ppm

FIELDS = ["filename", "width", "height", "channels", "on_disk_bytes", "format", "note"]


def read_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def synthetic_format(name: str) -> str:
    return "PGM (sintetis)" if name.endswith(".pgm") else "PPM (sintetis)"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="photos/small")
    ap.add_argument("--out", default="data")
    args = ap.parse_args()

    base = os.path.dirname(os.path.normpath(args.src))
    originals = {r["filename"]: r for r in read_csv(os.path.join(base, "originals.csv"))}
    notes = {r["filename"]: r["keterangan"] for r in read_csv(os.path.join(base, "keterangan.csv"))}
    small = sorted(glob.glob(os.path.join(args.src, "*.jpg")))
    if not small:
        raise SystemExit(f"no photos in {args.src}/")
    os.makedirs(args.out, exist_ok=True)

    manifest_path = os.path.join(args.out, "manifest.csv")
    names = {os.path.basename(p) for p in small}
    rows = []
    if os.path.exists(manifest_path):
        # keep the synthetic rows from make_data.py, drop any earlier photo rows
        for r in read_csv(manifest_path):
            if r["filename"] in names:
                continue
            if not r.get("format"):
                r["format"] = synthetic_format(r["filename"])
            rows.append({k: r.get(k, "") for k in FIELDS})

    total = 0
    for p in small:
        name = os.path.basename(p)
        img = np.asarray(Image.open(p).convert("RGB"))
        ppm = os.path.splitext(name)[0] + ".ppm"
        total += write_ppm(os.path.join(args.out, ppm), img)
        o = originals[name]
        rows.append({
            "filename": name, "width": o["width"], "height": o["height"], "channels": 3,
            "on_disk_bytes": o["on_disk_bytes"],
            "format": f"JPEG, {o['camera']}, ISO {o['iso']}, {o['exposure_s']} s, f/{o['f_number']}",
            "note": f"{notes[name]} (versi kerja {img.shape[1]}x{img.shape[0]}: {ppm})",
        })

    crops_path = os.path.join(base, "crops.csv")
    if os.path.exists(crops_path):
        # the two Lab 3 crops are cut from the working copies, so a clean clone rebuilds them
        for c in read_csv(crops_path):
            src = os.path.join(args.src, c["source"])
            x, y, w, h = (int(c[k]) for k in ("x", "y", "width", "height"))
            img = np.asarray(Image.open(src).convert("RGB"))[y:y + h, x:x + w]
            n = write_ppm(os.path.join(args.out, c["name"]), img)
            rows = [r for r in rows if r["filename"] != c["name"]]
            rows.append({"filename": c["name"], "width": w, "height": h, "channels": 3,
                         "on_disk_bytes": n, "format": "PPM (potongan foto)",
                         "note": f"{c['keterangan']}; dari {c['source']} x={x} y={y}"})

    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=FIELDS)
        wr.writeheader()
        wr.writerows(rows)
    print(f"imported {len(small)} photos -> {args.out}/*.ppm ({total:,} bytes), "
          f"manifest.csv now has {len(rows)} rows")


if __name__ == "__main__":
    main()
