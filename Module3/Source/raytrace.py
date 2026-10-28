"""Module 3 -- a one-frame ray tracer: pinhole rays + Moller-Trumbore, nearest hit,
the SAME texture sampler and Lambert light as raster3d.py.

The backward (image-order) direction of Module 2, in 3D: for every pixel one
ray through the pixel centre, tested against every triangle (no acceleration
structure, on purpose: the cost model in the prediction assumes this).
With --shadow, a second ray from each hit towards the light decides whether
the point is lit.

Run:  python raytrace.py --scene scenes/mymodel.json [--shadow]
      python raytrace.py --model data/pusaka_model.obj --w 256 --h 256   # starter form
"""
from __future__ import annotations

import argparse
import os
import time

import numpy as np

from ppm_io import read_ppm, write_ppm
from raster3d import load_scene_mesh, sample_bilinear
from srgb import linear_to_srgb, srgb_to_linear


def moller_trumbore(orig, dirs, v0, v1, v2):
    """Ray-triangle test vectorised over dirs (P,3); orig is one point or (P,3).
    Returns (t, u, v) with t = inf on a miss; the hit is orig + t dirs and its
    barycentric weights are (1-u-v, u, v) for (v0, v1, v2)."""
    eps = 1e-8
    e1, e2 = v1 - v0, v2 - v0
    pvec = np.cross(dirs, e2)
    det = pvec @ e1
    inv = np.where(np.abs(det) < eps, 0.0, 1.0 / np.where(det == 0, 1, det))
    tvec = orig - v0
    qvec = np.cross(tvec, e1)
    if tvec.ndim == 1:                     # one eye for all rays: the starter's arithmetic
        u = (pvec @ tvec) * inv
        v = (dirs @ qvec) * inv
        t = (qvec @ e2) * inv
    else:                                  # shadow rays: one origin per ray
        u = np.einsum("ij,ij->i", pvec, tvec) * inv
        v = np.einsum("ij,ij->i", dirs, qvec) * inv
        t = (qvec @ e2) * inv
    hit = (np.abs(det) >= eps) & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > eps)
    return np.where(hit, t, np.inf), u, v


def primary_rays(eye, center, fovy, w, h):
    """One unit ray per pixel centre (x + 0.5, y + 0.5): the inverse of the projection."""
    eye = np.asarray(eye, float)
    fwd = np.asarray(center, float) - eye
    fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, (0, 1, 0))
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    th = np.tan(np.radians(fovy) / 2)
    ii, jj = np.mgrid[0:h, 0:w]
    ndc_x = (jj + 0.5) / w * 2 - 1
    ndc_y = 1 - (ii + 0.5) / h * 2
    d = ndc_x[..., None] * right * th * (w / h) + ndc_y[..., None] * up * th + fwd
    d /= np.linalg.norm(d, axis=-1, keepdims=True)
    return d.reshape(-1, 3)


def render(mesh, *, w, h, tex_u8=None, model=None, eye=(2.6, 2.0, 3.4), center=(0, 0.7, 0),
           fovy=45.0, light_dir=(0.4, 0.9, 0.6), ambient=0.15, shadow=False, stats=None, **_):
    model = np.eye(4) if model is None else model
    world = (model @ np.c_[mesh.positions, np.ones(len(mesh.positions))].T).T[:, :3]
    tris, tuv = world[mesh.faces], mesh.triangle_uvs()
    eye = np.asarray(eye, float)
    D = primary_rays(eye, center, fovy, w, h)

    best_t = np.full(len(D), np.inf)
    best_f = np.full(len(D), -1, np.int64)
    best_uv = np.zeros((len(D), 2))
    for fi, (v0, v1, v2) in enumerate(tris):
        t, bu, bv = moller_trumbore(eye, D, v0, v1, v2)
        closer = t < best_t
        if closer.any():
            best_t[closer], best_f[closer] = t[closer], fi
            bw = 1 - bu[closer] - bv[closer]
            best_uv[closer] = bw[:, None] * tuv[fi, 0] + bu[closer, None] * tuv[fi, 1] + bv[closer, None] * tuv[fi, 2]

    L = np.asarray(light_dir, float)
    L /= np.linalg.norm(L)
    hit = best_f >= 0
    lit = np.ones(len(D), bool)
    if shadow and hit.any():
        # shadow rays: start a hair above the surface so a face does not shadow itself
        P0 = eye + best_t[hit, None] * D[hit]
        n_hit = np.cross(tris[best_f[hit], 1] - tris[best_f[hit], 0], tris[best_f[hit], 2] - tris[best_f[hit], 0])
        n_hit /= np.linalg.norm(n_hit, axis=1, keepdims=True) + 1e-12
        n_hit *= np.sign(np.einsum("ij,ij->i", n_hit, eye - P0))[:, None]
        origin = P0 + n_hit * 1e-4
        blocked = np.zeros(len(origin), bool)
        Ld = np.broadcast_to(L, origin.shape)
        for v0, v1, v2 in tris:
            t, _, _ = moller_trumbore(origin, Ld, v0, v1, v2)
            blocked |= np.isfinite(t)
        lit[hit] = ~blocked

    col = np.zeros((len(D), 3))
    tex_lin = None if tex_u8 is None else srgb_to_linear(tex_u8.astype(float) / 255)
    for fi in np.unique(best_f[hit]):
        m = best_f == fi
        v0, v1, v2 = tris[fi]
        n = np.cross(v1 - v0, v2 - v0)
        n /= np.linalg.norm(n) + 1e-12
        if n @ (eye - (v0 + v1 + v2) / 3.0) < 0:            # same rule as raster3d
            n = -n
        lambert = max(0.0, float(n @ L))
        shade = (ambient + (1 - ambient) * lambert * lit[m])[:, None]
        rgb = sample_bilinear(tex_lin, best_uv[m, 0], best_uv[m, 1]) if tex_lin is not None \
            else np.full((m.sum(), 3), 0.7)
        col[m] = np.clip(rgb * shade, 0, 1)
    if stats is not None:
        stats.update(pixels_hit=int(hit.sum()), ray_tests=len(D) * len(tris) * (2 if shadow else 1))
    img = linear_to_srgb(col).reshape(h, w, 3)
    return np.clip(img * 255, 0, 255).astype(np.uint8), best_t.reshape(h, w)


def render_scene(sc, w=None, h=None, mesh=None, tex=None, **opts):
    from raster3d import scene_kwargs
    mesh = mesh or load_scene_mesh(sc)
    tex = read_ppm(sc["model"]["texture"]) if tex is None and sc["model"].get("texture") else tex
    return render(mesh, tex_u8=tex, **scene_kwargs(sc, w, h), **opts)


def main():
    from scene import load_scene
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene")
    ap.add_argument("--model", help="starter form: this OBJ with scenes/temple.json's camera")
    ap.add_argument("--w", type=int)
    ap.add_argument("--h", type=int)
    ap.add_argument("--out")
    ap.add_argument("--shadow", action="store_true")
    args = ap.parse_args()
    if not (args.scene or args.model):
        raise SystemExit("give --scene or --model")
    sc = load_scene(args.scene or "scenes/temple.json")
    if args.model:
        sc["model"]["obj"] = args.model
    w = args.w or (256 if args.model else None)
    h = args.h or (256 if args.model else None)
    out = args.out or f"out/{sc['name']}_rt{'_shadow' if args.shadow else ''}.ppm"
    stats = {}
    t0 = time.perf_counter()
    img, t = render_scene(sc, w, h, shadow=args.shadow, stats=stats)
    dt = time.perf_counter() - t0
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    write_ppm(out, img)
    print(f"model: {len(load_scene_mesh(sc).faces)} triangles   {img.shape[1]}x{img.shape[0]}   "
          f"pixels hit: {stats['pixels_hit']}/{img.shape[0] * img.shape[1]}   {dt:.2f} s")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
