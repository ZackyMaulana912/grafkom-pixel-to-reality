"""Module 1 -- turn the full-resolution camera photos into the committed set.

Job: photos/original/*.jpg (iPhone, Display P3, ~6-7 MB each, NOT in git)
  -> photos/small/*.jpg     gamma-correct 5x box downscale, converted to sRGB,
                            all metadata stripped (the originals carry GPS)
  -> photos/originals.csv   W, H, bytes on disk, camera settings, used or not
  -> photos/checksums.sha256  proof of which full-resolution files were used

Pillow only decodes the camera JPEG and encodes the small JPEG (decision K2).
Everything in between is NumPy in float64: decode the P3 codes to linear light,
convert P3 -> sRGB primaries with a 3x3 matrix, box-average in linear light,
and quantise to uint8 once at the end.

Run:  .venv/bin/python prepare_photos.py            # needs photos/original/
      .venv/bin/python prepare_photos.py --verify   # also compare with Pillow ImageCms
"""
from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import io
import os

import numpy as np
from PIL import ExifTags, Image

from srgb import linear_to_srgb, srgb_to_linear

D65 = (0.3127, 0.3290)
PRIMARIES = {
    "srgb": ((0.640, 0.330), (0.300, 0.600), (0.150, 0.060)),
    "p3": ((0.680, 0.320), (0.265, 0.690), (0.150, 0.060)),
}


def rgb_to_xyz_matrix(primaries, white=D65) -> np.ndarray:
    """Linear RGB -> XYZ for the given xy primaries, scaled so RGB=1 maps to the white."""
    xyz = lambda x, y: np.array([x / y, 1.0, (1 - x - y) / y])
    p = np.stack([xyz(*c) for c in primaries], axis=1)
    s = np.linalg.solve(p, xyz(*white))
    return p * s


P3_TO_SRGB = np.linalg.inv(rgb_to_xyz_matrix(PRIMARIES["srgb"])) @ rgb_to_xyz_matrix(PRIMARIES["p3"])


def p3_codes_to_srgb_linear(u8: np.ndarray) -> np.ndarray:
    """Display P3 uint8 codes -> linear-light sRGB floats (out-of-gamut is clipped)."""
    lin_p3 = srgb_to_linear(u8.astype(np.float64) / 255.0)   # P3 uses the sRGB curve
    return np.clip(lin_p3 @ P3_TO_SRGB.T, 0.0, 1.0)


def downscale_linear(u8: np.ndarray, factor: int, rows_per_strip: int = 500):
    """Box-average factor x factor blocks in linear light; returns (sRGB uint8, clipped fraction).

    Works in strips so a 36 MP photo never needs a full float64 copy in memory.
    Edge rows/columns that do not fill a whole block are dropped.
    """
    h, w = (u8.shape[0] // factor) * factor, (u8.shape[1] // factor) * factor
    step = rows_per_strip - rows_per_strip % factor
    out = np.empty((h // factor, w // factor, 3), dtype=np.uint8)
    clipped = 0
    for y in range(0, h, step):
        block = u8[y:min(y + step, h), :w]
        lin_p3 = srgb_to_linear(block.astype(np.float64) / 255.0)
        lin = lin_p3 @ P3_TO_SRGB.T
        clipped += int(np.count_nonzero((lin < 0) | (lin > 1)))
        lin = np.clip(lin, 0.0, 1.0)
        bh = lin.shape[0] // factor
        avg = lin.reshape(bh, factor, w // factor, factor, 3).mean(axis=(1, 3))
        out[y // factor:y // factor + bh] = np.round(linear_to_srgb(avg) * 255).astype(np.uint8)
    return out, clipped / (h * w * 3)


def exif_fields(img: Image.Image) -> dict:
    ex = img.getexif()
    sub = ex.get_ifd(ExifTags.IFD.Exif)
    tag = {v: k for k, v in ExifTags.TAGS.items()}
    exposure = sub.get(tag["ExposureTime"])
    return {
        "camera": f"{ex.get(tag['Make'], '')} {ex.get(tag['Model'], '')}".strip(),
        "iso": sub.get(tag["ISOSpeedRatings"]),
        "exposure_s": f"1/{round(1 / float(exposure))}" if exposure else "",
        "f_number": round(float(sub.get(tag["FNumber"])), 2) if sub.get(tag["FNumber"]) else "",
        "taken": str(sub.get(tag["DateTimeOriginal"], "")).replace(":", "-", 2),
    }


def read_excluded(path: str) -> dict[str, str]:
    """photos/excluded.txt: '<filename>  <reason>' per line, '#' for comments."""
    out = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#"):
                name, _, reason = line.partition(" ")
                out[name] = reason.strip()
    return out


def verify_against_cms(path: str) -> None:
    """Compare the NumPy P3 -> sRGB conversion with Pillow's ICC engine on a centre crop."""
    from PIL import ImageCms
    img = Image.open(path)
    w, h = img.size
    crop = img.convert("RGB").crop((w // 2 - 256, h // 2 - 256, w // 2 + 256, h // 2 + 256))
    src = ImageCms.ImageCmsProfile(io.BytesIO(img.info["icc_profile"]))
    dst = ImageCms.createProfile("sRGB")
    ref = np.asarray(ImageCms.profileToProfile(
        crop, src, dst, renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC), dtype=np.int16)
    mine = np.round(linear_to_srgb(p3_codes_to_srgb_linear(np.asarray(crop))) * 255).astype(np.int16)
    diff = np.abs(mine - ref)
    print(f"verify {os.path.basename(path)}: NumPy vs ImageCms on 512x512 centre crop -> "
          f"max |diff| = {diff.max()} codes, mean = {diff.mean():.3f}, "
          f"{np.mean(diff <= 1) * 100:.2f}% within 1 code")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="photos/original")
    ap.add_argument("--small", default="photos/small")
    ap.add_argument("--factor", type=int, default=5)
    ap.add_argument("--quality", type=int, default=92)
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.src, "*.jpg")))
    if not files:
        raise SystemExit(f"no photos in {args.src}/ (the originals are not stored in git)")
    os.makedirs(args.small, exist_ok=True)
    excluded = read_excluded(os.path.join(os.path.dirname(args.small), "excluded.txt"))
    print("P3 -> sRGB matrix:\n" + np.array2string(P3_TO_SRGB, precision=6, suppress_small=True))
    if args.verify:
        verify_against_cms(files[0])

    rows, sums = [], []
    for f in files:
        name = os.path.basename(f)
        raw = open(f, "rb").read()
        digest = hashlib.sha256(raw).hexdigest()
        sums.append(f"{digest}  {name}\n")
        img = Image.open(io.BytesIO(raw))
        meta = exif_fields(img)
        used = name not in excluded
        rows.append({"filename": name, "width": img.size[0], "height": img.size[1],
                     "on_disk_bytes": len(raw), **meta, "sha256": digest,
                     "used": "ya" if used else "tidak", "reason": excluded.get(name, "")})
        if not used:
            print(f"{name}: skipped ({excluded[name]})")
            continue
        small, clipped = downscale_linear(np.asarray(img.convert("RGB")), args.factor)
        out = os.path.join(args.small, name)
        # no exif/xmp/icc: drops the GPS position; no profile means viewers assume sRGB
        Image.fromarray(small).save(out, "JPEG", quality=args.quality, subsampling=0)
        print(f"{name}: {img.size[0]}x{img.size[1]} -> {small.shape[1]}x{small.shape[0]}, "
              f"{os.path.getsize(out):,} B, out-of-sRGB-gamut values clipped: {clipped * 100:.3f}%")

    base = os.path.dirname(args.small)
    with open(os.path.join(base, "originals.csv"), "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)
    with open(os.path.join(base, "checksums.sha256"), "w") as fh:
        fh.writelines(sums)
    n_used = sum(r["used"] == "ya" for r in rows)
    print(f"{len(rows)} originals listed, {n_used} written to {args.small}/")


if __name__ == "__main__":
    main()
