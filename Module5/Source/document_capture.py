"""Document my own phone capture without committing the photos themselves.

The full-resolution JPGs stay on my laptop (they are the Module 1 photos of my
horse statue, git-ignored there). This script reads them once and writes, into
data/my_capture/:
  manifest.csv      one row per photo: size, camera, lens, focal length, time
  sha256sums.txt    checksum of every original file, so the set can be proven later
  contact_sheet.jpg all photos as small thumbnails, in shooting order

Pillow only reads the photos here; it is not on the ray/rendering path.
Run: .venv/bin/python document_capture.py [photo_dir]
"""
from __future__ import annotations

import csv
import hashlib
import os
import sys

from PIL import ExifTags, Image, ImageDraw, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PHOTOS = os.path.join(HERE, "..", "..", "Module1", "Source", "photos", "original")
OUT_DIR = os.path.join(HERE, "data", "my_capture")

THUMB_H = 200          # px, contact sheet thumbnail height
COLUMNS = 7
_TAG = {name: key for key, name in ExifTags.TAGS.items()}


def _exif(im):
    """Main + Exif-IFD tags of one image, by name."""
    main = im.getexif()
    tags = {ExifTags.TAGS.get(k, k): v for k, v in main.items()}
    tags.update({ExifTags.TAGS.get(k, k): v for k, v in main.get_ifd(_TAG["ExifOffset"]).items()})
    return tags


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def document(photo_dir):
    names = sorted(n for n in os.listdir(photo_dir) if n.lower().endswith((".jpg", ".jpeg")))
    os.makedirs(OUT_DIR, exist_ok=True)
    rows, sums, thumbs = [], [], []
    for name in names:
        path = os.path.join(photo_dir, name)
        with Image.open(path) as im:
            t = _exif(im)
            rows.append({
                "filename": name,
                "width": im.width,
                "height": im.height,
                "sensor_frame": f"{t.get('ExifImageWidth')}x{t.get('ExifImageHeight')}",
                "orientation": t.get("Orientation"),
                "make": t.get("Make"),
                "model": t.get("Model"),
                "lens": t.get("LensModel"),
                "focal_mm": f"{float(t.get('FocalLength')):.3f}",
                "focal_35mm_equiv": t.get("FocalLengthIn35mmFilm"),
                "taken": f"{t.get('DateTimeOriginal')} {t.get('OffsetTimeOriginal')}",
                "bytes": os.path.getsize(path),
            })
            thumb = ImageOps.exif_transpose(im).convert("RGB")
            thumb.thumbnail((THUMB_H * 4, THUMB_H))
            thumbs.append((name, thumb))
        sums.append(f"{_sha256(path)}  {name}")

    with open(os.path.join(OUT_DIR, "manifest.csv"), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    with open(os.path.join(OUT_DIR, "sha256sums.txt"), "w") as f:
        f.write("\n".join(sums) + "\n")

    cell_w = max(t.width for _, t in thumbs) + 8
    cell_h = THUMB_H + 22
    n_rows = -(-len(thumbs) // COLUMNS)
    sheet = Image.new("RGB", (COLUMNS * cell_w, n_rows * cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    for i, (name, thumb) in enumerate(thumbs):
        x, y = (i % COLUMNS) * cell_w, (i // COLUMNS) * cell_h
        sheet.paste(thumb, (x + (cell_w - thumb.width) // 2, y + 18))
        draw.text((x + 4, y + 3), f"{i + 1:02d} {os.path.splitext(name)[0]}", fill="black")
    sheet.save(os.path.join(OUT_DIR, "contact_sheet.jpg"), quality=85)
    return rows


if __name__ == "__main__":
    photo_dir = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PHOTOS)
    rows = document(photo_dir)
    print(f"documented {len(rows)} photos from {photo_dir}")
    print(f"  {rows[0]['model']}, {rows[0]['lens']}, {rows[0]['width']}x{rows[0]['height']} px, "
          f"{rows[0]['taken']} .. {rows[-1]['taken']}")
    print(f"wrote {os.path.relpath(OUT_DIR, HERE)}/manifest.csv, sha256sums.txt, contact_sheet.jpg")
