"""Module 3 -- DIAGNOSE-AND-FIX: three broken renders, one change each, with proof.

The diagnosis was written first from diagnose_scene.py (evidence only) and
committed before this file was changed: docs/prediksi/diagnosis-scene-rusak.md.

  python broken_scene.py --bug inside-out   # winding / back-face convention
  python broken_scene.py --bug zfight       # near plane 1e-3 -> depth crush
  python broken_scene.py --bug stretched    # a non-uniform scale in the model matrix
  python broken_scene.py --pitfall          # same z-fight scene, depth formats + reverse-Z
  python broken_scene.py --all              # everything + out/bug_table.txt

Each bug is compared against the NORMAL render of its own scene (the truth):
z-buffer without culling for inside-out, a float64 depth buffer for zfight,
the intended model matrix for stretched.
"""
from __future__ import annotations

import argparse
import os

import numpy as np

import raster3d
from metrics import psnr, ssim
from objio import Mesh, load_obj
from ppm_io import read_ppm, write_ppm
from transforms import rot_y, scale, translate

GOOD_MODEL = translate((0, 0, 0)) @ rot_y(35) @ scale((1.4, 1.4, 1.4))
W = H = 192
OUT = "out/bugs"


def _load():
    return load_obj("data/pusaka_model.obj"), read_ppm("data/relief.ppm")


def wrong_pixels(a, b, thr=60):
    return int((np.abs(a.astype(int) - b.astype(int)).max(2) > thr).sum())


def bug_inside_out(mesh, tex):
    """Bad: the OBJ as stored (every face wound inward, T13) + back-face culling.
    Fix (one change): load it with enforce_ccw=True, i.e. the loader reverses a
    mesh whose signed volume is negative (Pitfall 12.6)."""
    cam = dict(w=W, h=H, tex_u8=tex, model=GOOD_MODEL)
    normal, _, _ = raster3d.render(mesh, **cam)
    bad, _, fb = raster3d.render(mesh, cull_back=True, **cam)
    fixed_mesh = load_obj("data/pusaka_model.obj", enforce_ccw=True)
    fixed, _, ff = raster3d.render(fixed_mesh, cull_back=True, **cam)
    note = (f"signed volume as stored {mesh.signed_volume():+.4f} -> after load {fixed_mesh.signed_volume():+.4f}; "
            f"fragments with culling {fb} -> {ff}")
    return bad, fixed, normal, note, {}


def _zfight_scene():
    """Two quads that CROSS: A flat at z=-9, B = A tilted 1.2 deg about its centre,
    so they swap order along one near-horizontal line (the starter's scene)."""
    cy, cz = 1.0, -9.0
    quad_a = np.array([[-3.0, -1, 0], [3, -1, 0], [3, 3, 0], [-3, 3, 0]]) + [0, 0, cz]
    a = np.radians(1.2)
    R = np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])
    quad_b = (quad_a - [0, cy, cz]) @ R.T + [0, cy, cz]
    return Mesh(np.vstack([quad_a, quad_b]), np.zeros((0, 2)), [[0, 1, 2], [0, 2, 3], [4, 6, 5], [4, 7, 6]], [])


TRI_COLS = [(230, 130, 40), (230, 130, 40), (60, 120, 210), (60, 120, 210)]   # A orange, B blue
ZCAM = dict(w=W, h=H, eye=(0, 1, 6), center=(0, 1, -1), far=200, tri_colors=TRI_COLS, light_dir=(0, 0.2, 1))


def zfight_render(near, **depth):
    return raster3d.render(_zfight_scene(), near=near, **ZCAM, **depth)


def bug_zfight(mesh, tex):
    """Bad: near = 1e-3 with a 16-bit depth buffer. Fix (one change): near = 1."""
    normal, _, _ = zfight_render(1e-3)                       # float64 depth: the truth
    bad, db, _ = zfight_render(1e-3, depth_bits=16)
    fixed, df, _ = zfight_render(1.0, depth_bits=16)
    rows = np.nonzero((np.abs(fixed.astype(int) - normal.astype(int)).max(2) > 60).any(1))[0]
    hist = {}
    for name, d in (("bad", db), ("fixed", df)):
        z = d[np.isfinite(d)]
        hist[name] = np.unique(np.round((z * 0.5 + 0.5) * 2 ** 16), return_counts=True)
    note = (f"distinct 16-bit depth codes on the quads: {len(hist['bad'][0])} -> {len(hist['fixed'][0])}; "
            f"rows holding the remaining wrong pixels: {rows.min() if len(rows) else '-'}..{rows.max() if len(rows) else '-'}")
    return bad, fixed, normal, note, hist


def bug_stretched(mesh, tex):
    """Bad: model = S(1.4) Ry(35) T(0) diag(2.2, 0.5, 1). Fix (one change): drop the diag."""
    wrong = scale((1.4, 1.4, 1.4)) @ rot_y(35) @ translate((0, 0, 0)) @ np.diag([2.2, 0.5, 1.0, 1.0])
    cam = dict(w=W, h=H, tex_u8=tex)
    bad, _, _ = raster3d.render(mesh, model=wrong, **cam)
    fixed_model = scale((1.4, 1.4, 1.4)) @ rot_y(35) @ translate((0, 0, 0))
    fixed, _, _ = raster3d.render(mesh, model=fixed_model, **cam)
    normal, _, _ = raster3d.render(mesh, model=GOOD_MODEL, **cam)
    swap = np.allclose(scale((1.4, 1.4, 1.4)) @ rot_y(35), rot_y(35) @ scale((1.4, 1.4, 1.4)))
    note = (f"column lengths {np.linalg.norm(wrong[:3, :3], axis=0).round(3)} -> "
            f"{np.linalg.norm(fixed_model[:3, :3], axis=0).round(3)}; swapping S(1.4) and Ry(35) "
            f"changes nothing ({swap}), so the order alone was never the bug (T9)")
    return bad, fixed, normal, note, {}


BUGS = {"inside-out": bug_inside_out, "zfight": bug_zfight, "stretched": bug_stretched}


def hist_image(codes, counts, lo, hi, w=384, h=140):
    img = np.full((h, w, 3), 255, np.uint8)
    top = counts.max()
    for c, n in zip(codes, counts):
        x = int((c - lo) / max(hi - lo, 1) * (w - 4)) + 2
        img[h - 1 - int(n / top * (h - 10)):, max(0, x - 1):x + 2] = (40, 90, 170)
    return img


def run(name, mesh, tex):
    bad, fixed, normal, note, hist = BUGS[name](mesh, tex)
    os.makedirs(OUT, exist_ok=True)
    for k, img in (("bad", bad), ("fixed", fixed), ("normal", normal)):
        write_ppm(f"{OUT}/bug_{name}_{k}.ppm", img)
    print(f"\n== {name} ==\n   {note}")
    if hist:
        for k in ("bad", "fixed"):
            codes, counts = hist[k]
            write_ppm(f"{OUT}/bug_{name}_hist_{k}.ppm", hist_image(codes, counts, codes.min(), codes.max()))
            print(f"   depth histogram ({k}): codes {int(codes.min())}..{int(codes.max())}, "
                  f"largest bin {counts.max()} of {counts.sum()} pixels")
    row = (name, ssim(bad, normal), psnr(bad, normal), wrong_pixels(bad, normal),
           ssim(fixed, normal), psnr(fixed, normal), wrong_pixels(fixed, normal))
    f = lambda p: "inf" if np.isinf(p) else f"{p:.1f}"
    print(f"   before: SSIM {row[1]:.3f}  PSNR {f(row[2])} dB  wrong px {row[3]}")
    print(f"   after : SSIM {row[4]:.3f}  PSNR {f(row[5])} dB  wrong px {row[6]}")
    return row


def pitfall():
    """K14: the z-fight scene at near = 1e-3 again, fixed WITHOUT touching near."""
    truth, _, _ = zfight_render(1e-3)
    print("\n== pitfall fix: depth storage at near = 1e-3 (scene zfight) ==")
    print(f"   {'depth buffer':34s} {'wrong px':>9s} {'SSIM':>7s}")
    rows = []
    for label, opts in (("16-bit fixed point (the bug)", dict(depth_format="u16")),
                        ("24-bit fixed point", dict(depth_format="u24")),
                        ("32-bit float, near -> -1 (NDC z)", dict(depth_format="f32")),
                        ("32-bit float, reverse-Z", dict(depth_format="f32", depth_mode="reverse")),
                        ("16-bit fixed point, reverse-Z", dict(depth_format="u16", depth_mode="reverse"))):
        img, _, _ = zfight_render(1e-3, **opts)
        rows.append((label, wrong_pixels(img, truth), ssim(img, truth)))
        print(f"   {label:34s} {rows[-1][1]:9d} {rows[-1][2]:7.3f}")
        if "reverse" in label and "float" in label:
            write_ppm(f"{OUT}/zfight_reverse_f32.ppm", img)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bug", choices=list(BUGS))
    ap.add_argument("--pitfall", action="store_true")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    mesh, tex = _load()
    os.makedirs(OUT, exist_ok=True)
    if args.bug:
        run(args.bug, mesh, tex)
    if args.pitfall:
        pitfall()
    if args.all or not (args.bug or args.pitfall):
        rows = [run(k, mesh, tex) for k in BUGS]
        prow = pitfall()
        with open(f"{OUT}/bug_table.txt", "w") as fh:
            fh.write("bug         SSIM_before PSNR_before wrong_before SSIM_after PSNR_after wrong_after\n")
            for r in rows:
                fh.write(f"{r[0]:11s} {r[1]:.3f} {r[2]:.1f} {r[3]} {r[4]:.3f} {r[5]:.1f} {r[6]}\n")
            for label, n, s in prow:
                fh.write(f"pitfall | {label} | wrong {n} | SSIM {s:.3f}\n")
        print(f"\nwrote {OUT}/bug_*.ppm and {OUT}/bug_table.txt")


if __name__ == "__main__":
    main()
