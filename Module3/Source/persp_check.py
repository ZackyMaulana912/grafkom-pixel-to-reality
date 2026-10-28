"""Module 3 -- Lab 2 no 3: perspective-correct vs naive texture coordinates.

1. Example E4 exactly: an edge from L (eye depth w=1, u=0) to R (w=9, u=1),
   100 pixels apart on one screen row. u at the screen midpoint is computed by
   raster3d's own interpolation functions, then read back from a real render.
2. A striped floor seen at a grazing angle, rendered naive and correct, from
   two camera positions, the second dollied 10 cm forward. With naive UVs the stripes are painted in
   the wrong place on the floor, and that wrong place moves with the camera:
   the texture "swims". The swim is measured in metres of floor.

Run:  python persp_check.py      -> numbers + out/floor_{naive,pc}{,_shift}.ppm
"""
from __future__ import annotations

import os

import numpy as np

import raster3d
from objio import Mesh
from ppm_io import write_ppm
from srgb import to_u8


def e4_numbers():
    l = (0.5, 0.5, 0.0)                                   # screen midpoint of edge L-R
    u = np.array([0.0, 1.0, 0.0])
    inv_w = 1.0 / np.array([1.0, 9.0, 1.0])
    pc = raster3d.perspective_correct(*l, u, inv_w)
    naive = raster3d.bary_mix(*l, u)
    print(f"E4 via raster3d: u at the screen midpoint  perspective-correct {pc:.4f}   naive {naive:.4f}")

    # the same edge in a real render: fovy 90 (f = 1), 200 x 200, L at x=50, R at x=150
    W = H = 200
    pos = np.array([[-0.5, 0.5, -1.0], [4.5, 4.5, -9.0], [0.0, -0.4, -1.0]])   # L, R, C
    m = Mesh(pos, np.array([[0, 0], [1, 0], [0, 1]]), [[0, 1, 2]], [[0, 1, 2]])
    uv = np.full((H, W, 2), np.nan)
    tex = np.full((4, 4, 3), 128, np.uint8)
    for naive_uv in (False, True):
        uv[:] = np.nan
        raster3d.render(m, w=W, h=H, tex_u8=tex, eye=(0, 0, 0), center=(0, 0, -1), fovy=90.0,
                        near=0.5, far=20.0, naive_uv=naive_uv, uv_out=uv)
        row = 50                                          # the edge L-R lies on y = 50
        col = uv[row, :, 0]
        xs = np.nonzero(np.isfinite(col))[0]
        print(f"   render ({'naive' if naive_uv else 'perspective-correct'}): row {row} covers x "
              f"{xs.min()}..{xs.max()}, u at pixel x=100 (centre 100.5) = {col[100]:.4f}")
    return pc, naive


def floor_mesh(depth=8.0, half=2.0, repeats=8.0):
    """Floor y = 0 from z = 0 to z = -depth, u along the depth (one unit per metre)."""
    pos = np.array([[-half, 0, 0], [half, 0, 0], [half, 0, -depth], [-half, 0, -depth]])
    uv = np.array([[0, 0], [0, 1], [repeats, 1], [repeats, 0]], float)
    return Mesh(pos, uv, [[0, 1, 2], [0, 2, 3]], [[0, 1, 2], [0, 2, 3]])


def stripes(n=64, bands=2):
    x = np.arange(n)
    on = ((x * bands) // n) % 2 == 0
    row = np.where(on, 0.9, 0.08)
    return to_u8(np.repeat(np.repeat(row[None, :, None], n, 0), 3, 2) ** (1 / 2.2))


def floor_swim(W=256, H=256):
    """u along the floor should equal the distance into the floor (metres).
    Error = |u - true distance| on the visible floor, per render."""
    m, tex = floor_mesh(), stripes()
    cams = {"": (0.0, 1.0, 1.0), "_shift": (0.0, 1.0, 0.9)}          # dolly in by 10 cm
    res = {}
    os.makedirs("out", exist_ok=True)
    for naive in (False, True):
        for tag, eye in cams.items():
            uv = np.full((H, W, 2), np.nan)
            col, dep, _ = raster3d.render(m, w=W, h=H, tex_u8=tex, eye=eye, center=(eye[0], 0.0, eye[2] - 5.0),
                                          fovy=60.0, near=0.1, far=20.0, light_dir=(0, 1, 0),
                                          ambient=1.0, naive_uv=naive, uv_out=uv)
            name = f"floor_{'naive' if naive else 'pc'}{tag}"
            write_ppm(f"out/{name}.ppm", col)
            # true floor distance per pixel: intersect the pixel's ray with y = 0
            from raytrace import primary_rays
            d = primary_rays(eye, (eye[0], 0.0, eye[2] - 5.0), 60.0, W, H).reshape(H, W, 3)
            t = -eye[1] / np.where(d[..., 1] < 0, d[..., 1], np.nan)
            true_u = -(eye[2] + t * d[..., 2])
            ok = np.isfinite(uv[..., 0]) & np.isfinite(true_u)
            err = np.abs(uv[..., 0] - true_u)[ok]
            res[name] = (err.mean(), err.max(), uv, true_u, ok)
            print(f"   {name:18s} floor pixels {ok.sum():6d}   |u - true| mean {err.mean():.4f} m   max {err.max():.4f} m")
    # the swim: at each pixel, (painted u - true u) is where the texture sits relative to the
    # floor; if that offset changes when the camera moves, the texture slides over the floor
    for kind in ("pc", "naive"):
        a, b = res[f"floor_{kind}"], res[f"floor_{kind}_shift"]
        both = a[4] & b[4]
        swim = np.abs((a[2][..., 0] - a[3]) - (b[2][..., 0] - b[3]))[both]
        print(f"   swim ({kind:5s}): texture slides over the floor by mean {swim.mean() * 100:.2f} cm, "
              f"max {swim.max() * 100:.2f} cm when the camera moves 10 cm")
    return res


def main():
    print("== Example E4 ==")
    e4_numbers()
    print("\n== striped floor, naive vs perspective-correct, camera moved 10 cm ==")
    floor_swim()
    print("wrote out/floor_pc.ppm, out/floor_pc_shift.ppm, out/floor_naive.ppm, out/floor_naive_shift.ppm")


if __name__ == "__main__":
    main()
