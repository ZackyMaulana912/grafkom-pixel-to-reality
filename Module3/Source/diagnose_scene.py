"""Module 3 -- evidence only for the three broken scenes (decision K14).

broken_scene.py prints its own root cause and fix. This file builds the same
broken renders and prints ONLY evidence: the render, its depth image, the
matrices that were used, a depth histogram, and the difference against a
normal render of the same scene. No cause, no fix, no "fixed" render.

Run:  python diagnose_scene.py            -> out/diag/*.ppm + printed evidence
"""
from __future__ import annotations

import os

import numpy as np

import broken_scene
import raster3d
from metrics import psnr, ssim
from objio import load_obj
from ppm_io import read_ppm, write_ppm
from transforms import perspective

OUT = "out/diag"
W = H = 192                                   # the size broken_scene.py renders at


def depth_image(depth):
    """NDC depth -> grey (near dark, far light); background white."""
    fin = np.isfinite(depth)
    g = np.ones_like(depth)
    if fin.any():
        lo, hi = depth[fin].min(), depth[fin].max()
        g[fin] = (depth[fin] - lo) / max(hi - lo, 1e-12) * 0.9
    return np.repeat((g * 255).round().astype(np.uint8)[..., None], 3, axis=2)


def diff_image(a, b, k=4):
    return np.clip(np.abs(a.astype(int) - b.astype(int)) * k, 0, 255).astype(np.uint8)


def histogram_image(values, bins, w=384, h=160):
    counts, edges = np.histogram(values, bins=bins)
    img = np.full((h, w, 3), 255, np.uint8)
    top = counts.max() if counts.max() else 1
    bw = w / len(counts)
    for i, c in enumerate(counts):
        bh = int(round(c / top * (h - 10)))
        img[h - bh:, int(i * bw):max(int((i + 1) * bw) - 1, int(i * bw) + 1)] = (40, 90, 170)
    return img, counts, edges


def save(name, img):
    write_ppm(os.path.join(OUT, name), img)


def report(name, bad, normal, extra=""):
    p = psnr(bad, normal)
    print(f"  vs normal render: SSIM {ssim(bad, normal):.3f}   PSNR "
          f"{'inf' if np.isinf(p) else f'{p:.1f}'} dB   pixels differing > 60 codes: "
          f"{int((np.abs(bad.astype(int) - normal.astype(int)).max(2) > 60).sum())}{extra}")


def signed_volume(mesh):
    """Sum of tetrahedra (origin, triangle). Positive when every face is wound
    counter-clockwise seen from outside, negative when every face points inward."""
    t = mesh.positions[mesh.faces]
    return float(np.einsum("ij,ij->i", t[:, 0], np.cross(t[:, 1], t[:, 2])).sum() / 6.0)


def inside_out(mesh, tex):
    print("\n== scene: inside-out ==")
    M = broken_scene.GOOD_MODEL
    rev = broken_scene.Mesh(mesh.positions, mesh.uvs, mesh.faces[:, ::-1].copy(),
                            mesh.face_uvs[:, ::-1].copy())
    shown, ds, fs = raster3d.render(rev, w=W, h=H, tex_u8=tex, model=M, cull_back=True)
    stored, dst, fst = raster3d.render(mesh, w=W, h=H, tex_u8=tex, model=M, cull_back=True)
    normal, dn, fn = raster3d.render(mesh, w=W, h=H, tex_u8=tex, model=M, cull_back=False)
    for k, img in (("bad", shown), ("depth", depth_image(ds)), ("stored", stored),
                   ("stored_depth", depth_image(dst)), ("normal", normal),
                   ("normal_depth", depth_image(dn)), ("diff", diff_image(shown, normal)),
                   ("stored_diff", diff_image(stored, normal))):
        save(f"inside-out_{k}.ppm", img)
    print("  model matrix:\n" + np.array2string(M, precision=3, suppress_small=True))
    print(f"  signed volume of the mesh as stored in the OBJ: {signed_volume(mesh):+.4f}"
          f"   (winding reversed: {signed_volume(rev):+.4f})")
    print("  normal render = z-buffer only, no culling (does not depend on winding)")
    for name, img, d, f in (("A: winding reversed + back-face cull (broken_scene's scene)", shown, ds, fs),
                            ("B: winding as stored + back-face cull", stored, dst, fst)):
        fin = np.isfinite(d) & np.isfinite(dn)
        print(f"  {name}")
        print(f"     fragments {f}, pixels covered {int(np.isfinite(d).sum())} (normal {int(np.isfinite(dn).sum())})"
              f", mean NDC depth {d[fin].mean():.4f} (normal {dn[fin].mean():.4f})"
              f", pixels FARTHER than normal: {int((d[fin] > dn[fin] + 1e-9).sum())}")
        report("inside-out", img, normal)


def zfight():
    print("\n== scene: zfight ==")
    m = broken_scene._zfight_scene()
    cam = dict(eye=(0, 1, 6), center=(0, 1, -1), cull_back=False, far=200,
               tri_colors=broken_scene.TRI_COLS, light_dir=(0, 0.2, 1))
    bad, db, _ = raster3d.render(m, w=W, h=H, near=1e-3, depth_bits=16, **cam)
    normal, dn, _ = raster3d.render(m, w=W, h=H, near=1e-3, depth_bits=None, **cam)
    for k, img in (("bad", bad), ("depth", depth_image(db)), ("normal", normal),
                   ("diff", diff_image(bad, normal))):
        save(f"zfight_{k}.ppm", img)
    P = perspective(45.0, W / H, 1e-3, 200)
    print(f"  camera eye (0,1,6) looking at (0,1,-1); near = 1e-3, far = 200; depth buffer 16-bit")
    print("  projection matrix:\n" + np.array2string(P, precision=6, suppress_small=True))
    fin = np.isfinite(db)
    z = db[fin]
    codes = np.unique(np.round((z * 0.5 + 0.5) * 2 ** 16))
    print(f"  NDC depth over the two quads: [{z.min():.7f}, {z.max():.7f}]"
          f"   distinct 16-bit codes used: {len(codes)}")
    eyez = np.array([-14.0, -15.0, -16.0])               # the quads sit about 15 m from the eye
    ndc = (P[2, 2] * eyez + P[2, 3]) / -eyez
    print(f"  NDC depth of eye z = -14, -15, -16 m: {np.array2string(ndc, precision=7)}"
          f"  -> 16-bit codes {np.round((ndc * 0.5 + 0.5) * 2 ** 16).astype(int)}")
    img, counts, edges = histogram_image((z * 0.5 + 0.5) * 2 ** 16, bins=np.arange(codes.min() - 0.5, codes.max() + 1.5))
    save("zfight_hist.ppm", img)
    print(f"  depth histogram (16-bit code: pixels): " +
          ", ".join(f"{int(e + 0.5)}: {c}" for e, c in zip(edges[:-1], counts) if c))
    blue = (np.abs(bad.astype(int) - np.array((60, 120, 210))).max(2) < 80) & fin
    blue_n = (np.abs(normal.astype(int) - np.array((60, 120, 210))).max(2) < 80) & np.isfinite(dn)
    print(f"  pixels showing the blue quad: {int(blue.sum())} (float-depth render: {int(blue_n.sum())})")
    report("zfight", bad, normal, "   (normal = the same near/far with a float depth buffer)")


def stretched(mesh, tex):
    print("\n== scene: stretched ==")
    from transforms import rot_y, scale, translate
    # the matrix broken_scene.py builds, rebuilt here so it can be printed and read
    Mb = scale((1.4, 1.4, 1.4)) @ rot_y(35) @ translate((0, 0, 0)) @ np.diag([2.2, 0.5, 1.0, 1.0])
    bad, db, _ = raster3d.render(mesh, w=W, h=H, tex_u8=tex, model=Mb)
    assert np.array_equal(bad, broken_scene.bug_stretched(mesh, tex)[0]), \
        "the printed matrix is not the one broken_scene.py used"
    Mg = broken_scene.GOOD_MODEL
    normal, dn, _ = raster3d.render(mesh, w=W, h=H, tex_u8=tex, model=Mg)
    for k, img in (("bad", bad), ("depth", depth_image(db)), ("normal", normal),
                   ("diff", diff_image(bad, normal))):
        save(f"stretched_{k}.ppm", img)
    for name, M in (("this scene", Mb), ("normal scene", Mg)):
        print(f"  model matrix ({name}):\n" + np.array2string(M, precision=3, suppress_small=True))
        print(f"    column lengths (how far model +x, +y, +z stretch): "
              f"{np.array2string(np.linalg.norm(M[:3, :3], axis=0), precision=3)}"
              f"   det {np.linalg.det(M[:3, :3]):.3f}")
    fin_b, fin_n = np.isfinite(db), np.isfinite(dn)
    for name, f in (("this scene", fin_b), ("normal", fin_n)):
        ys, xs = np.nonzero(f)
        print(f"  silhouette bbox ({name}): x {xs.min()}..{xs.max()}  y {ys.min()}..{ys.max()}"
              f"   ({xs.max() - xs.min() + 1} x {ys.max() - ys.min() + 1} px)")
    report("stretched", bad, normal)


def main():
    os.makedirs(OUT, exist_ok=True)
    mesh, tex = load_obj("data/pusaka_model.obj"), read_ppm("data/relief.ppm")
    inside_out(mesh, tex)
    zfight()
    stretched(mesh, tex)
    print(f"\nwrote {OUT}/<scene>_{{bad,depth,normal,diff}}.ppm and {OUT}/zfight_hist.ppm")


if __name__ == "__main__":
    main()
