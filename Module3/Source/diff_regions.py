"""Module 3 -- where do two frames of the same scene disagree? (Lab 3 no 2)

Renders a triangle-ID image of the scene with raster3d.py and splits the
pixels into EDGE (the 3x3 neighbourhood holds more than one triangle: a
silhouette or a crease, where the GPU's MSAA blends) and INTERIOR (one
triangle all round, where a transform, depth or texture bug would show).
Then reports how much of the difference lives in each, plus the mean signed
difference in the interior (a brightness or rounding bias shows up there).

Run:  python diff_regions.py --scene scenes/mymodel.json out/mymodel_raster.ppm web/mymodel_three.ppm
"""
from __future__ import annotations

import argparse

import numpy as np

import raster3d
from ppm_io import read_ppm, write_ppm
from scene import load_scene


def triangle_ids(sc, w, h):
    mesh = raster3d.load_scene_mesh(sc)
    n = mesh.n_tris
    ids = [((k + 1) & 255, ((k + 1) >> 8) & 255, 128) for k in range(n)]
    kw = raster3d.scene_kwargs(sc, w, h)
    kw.update(ambient=1.0)                                  # flat colour = exact id
    col, dep, _ = raster3d.render(mesh, tri_colors=ids, **kw)
    tid = col[..., 0].astype(int) + 256 * col[..., 1].astype(int)
    tid[~np.isfinite(dep)] = 0
    return tid


def edge_mask(tid):
    pad = np.pad(tid, 1, mode="edge")
    m = np.zeros(tid.shape, bool)
    for dy in (0, 1, 2):
        for dx in (0, 1, 2):
            m |= pad[dy:dy + tid.shape[0], dx:dx + tid.shape[1]] != tid
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", required=True)
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--map", help="write a picture: red = edge difference, cyan = interior difference")
    args = ap.parse_args()
    A, B = read_ppm(args.a).astype(int), read_ppm(args.b).astype(int)
    tid = triangle_ids(load_scene(args.scene), A.shape[1], A.shape[0])
    edge = edge_mask(tid)
    d = np.abs(A - B).max(2)
    sq = ((A - B) ** 2).sum(2)
    for name, m in (("edge", edge), ("interior", ~edge)):
        print(f"{name:9s} pixels {m.sum():7d}   differing (>2 codes) {(d[m] > 2).sum():6d}   "
              f"mean |diff| {np.abs(A - B)[m].mean():5.2f}   max {d[m].max():3d}   "
              f"share of squared error {sq[m].sum() / max(sq.sum(), 1):6.1%}")
    signed = (B - A)[~edge].mean(0)
    print(f"interior mean signed difference (b - a) per channel: {np.round(signed, 2)}")
    big = (~edge) & (d > 16)
    print(f"interior pixels differing by more than 16 codes: {big.sum()}")
    if args.map:
        vis = np.zeros(A.shape, np.uint8)
        vis[edge & (d > 2)] = (255, 60, 60)
        vis[~edge & (d > 2)] = (60, 220, 255)
        write_ppm(args.map, vis)
        print(f"wrote {args.map}")


if __name__ == "__main__":
    main()
