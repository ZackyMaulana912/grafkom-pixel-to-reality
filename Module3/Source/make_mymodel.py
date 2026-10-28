"""Module 3 -- my own model: the room where my horse statue stands.

Every number comes from data/mymodel_ukuran.json (my measurements, plus the
estimates that file names). The statue is the outline I traced on photo
IMG_8882, extruded to a slab and textured with that same photo.

Conventions follow transforms.py: metres, y up, faces CCW seen from outside.
Positions are shared between faces, so a closed part has every edge used
twice in opposite directions (tests.py checks this).

Run:  .venv/bin/python make_mymodel.py      ->  data/mymodel.obj
"""
from __future__ import annotations

import argparse
import json

import numpy as np


class Builder:
    """Collects triangles; positions are de-duplicated, UVs are kept per corner."""

    def __init__(self, atlas_size):
        self.n = atlas_size
        self.pos, self.pos_id = [], {}
        self.uv, self.tris, self.groups = [], [], []
        self.group = "default"

    def _p(self, p):
        key = tuple(np.round(p, 6))
        if key not in self.pos_id:
            self.pos_id[key] = len(self.pos)
            self.pos.append(key)
        return self.pos_id[key]

    def _t(self, uv_px):
        """Atlas pixel (x right, y down) -> OBJ vt (v up; the loader flips it back)."""
        self.uv.append((uv_px[0] / self.n, 1.0 - uv_px[1] / self.n))
        return len(self.uv) - 1

    def tri(self, P, UV, outward):
        P = [np.asarray(p, float) for p in P]
        if np.cross(P[1] - P[0], P[2] - P[0]) @ np.asarray(outward, float) < 0:
            P, UV = [P[0], P[2], P[1]], [UV[0], UV[2], UV[1]]
        self.tris.append(([self._p(p) for p in P], [self._t(t) for t in UV]))
        self.groups.append(self.group)

    def quad(self, P, UV, outward):
        self.tri([P[0], P[1], P[2]], [UV[0], UV[1], UV[2]], outward)
        self.tri([P[0], P[2], P[3]], [UV[0], UV[2], UV[3]], outward)


def rect_uv(rect, inset=1.0):
    """Corners (s,t) = (0,0) (1,0) (1,1) (0,1) of an atlas rect, t=0 at its bottom.
    The 1-texel inset keeps bilinear filtering from reading the neighbouring region."""
    x0, y0, x1, y1 = rect
    x0, y0, x1, y1 = x0 + inset, y0 + inset, x1 - inset, y1 - inset
    return [(x0, y1), (x1, y1), (x1, y0), (x0, y0)]


def face(b, origin, s, t, rect, outward):
    o, s, t = (np.asarray(v, float) for v in (origin, s, t))
    b.quad([o, o + s, o + s + t, o + t], rect_uv(rect), outward)


def box(b, lo, hi, rect, skip=()):
    """Axis-aligned box. Face names: -x +x -y +y -z +z; `skip` leaves faces out
    where they touch another part (a hidden face there would z-fight)."""
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
    faces = {
        "-x": ((x0, y0, z0), (0, 0, dz), (0, dy, 0), (-1, 0, 0)),
        "+x": ((x1, y0, z1), (0, 0, -dz), (0, dy, 0), (1, 0, 0)),
        "-z": ((x1, y0, z0), (-dx, 0, 0), (0, dy, 0), (0, 0, -1)),
        "+z": ((x0, y0, z1), (dx, 0, 0), (0, dy, 0), (0, 0, 1)),
        "+y": ((x0, y1, z1), (dx, 0, 0), (0, 0, -dz), (0, 1, 0)),
        "-y": ((x0, y0, z0), (dx, 0, 0), (0, 0, dz), (0, -1, 0)),
    }
    for name, (o, s, t, n) in faces.items():
        if name not in skip:
            face(b, o, s, t, rect, n)


def ear_clip(poly):
    """Triangulate a simple polygon (N,2), counter-clockwise. Returns index triples."""
    idx = list(range(len(poly)))
    out = []

    def cross(o, a, c):
        return (a[0] - o[0]) * (c[1] - o[1]) - (a[1] - o[1]) * (c[0] - o[0])

    while len(idx) > 3:
        for k in range(len(idx)):
            i, j, m = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, c, e = poly[i], poly[j], poly[m]
            if cross(a, c, e) <= 0:                     # reflex corner, not an ear
                continue
            if any(cross(a, c, poly[q]) >= 0 and cross(c, e, poly[q]) >= 0 and
                   cross(e, a, poly[q]) >= 0 for q in idx if q not in (i, j, m)):
                continue
            out.append((i, j, m))
            idx.pop(k)
            break
        else:
            raise ValueError("ear clipping stuck: outline is not a simple polygon")
    out.append(tuple(idx))
    return out


def room(b, spec):
    r, rects = spec["room"], {k: v["rect"] for k, v in spec["atlas"]["regions"].items()}
    hw, hd, H, t = r["width_x"] / 2, r["depth_z"] / 2, r["height"], r["wall_thickness"]

    b.group = "floor"
    nx, nz = r["floor_tiles"]
    for i in range(nx):
        for k in range(nz):
            x0 = -hw + i * (2 * hw / nx)
            z1 = hd - k * (2 * hd / nz)
            face(b, (x0, 0, z1), (2 * hw / nx, 0, 0), (0, 0, -2 * hd / nz), rects["floor"], (0, 1, 0))

    b.group = "walls"
    box(b, (-hw - t, 0, -hd - t), (-hw, H, hd), rects["wall"], skip=("-y",))
    box(b, (-hw, 0, -hd - t), (hw, H, -hd), rects["wall"], skip=("-x", "+x", "-y"))
    box(b, (hw, 0, -hd - t), (hw + t, H, hd), rects["wall"], skip=("-x", "-y"))   # -x is behind the cabinet

    b.group = "cabinet"
    c = spec["cabinet"]
    x0 = hw - c["depth"]
    box(b, (x0, 0, -hd), (hw, H, hd), rects["door"], skip=("-x", "+x", "-z", "-y"))
    door = 2 * hd / c["doors"]
    for k in range(c["doors"]):                         # seen from the room, +z is to the right
        face(b, (x0, 0, -hd + k * door), (0, 0, door), (0, H, 0), rects["door"], (-1, 0, 0))

    b.group = "partition"
    p = spec["partition"]
    za, zb = hd, hd + p["depth"]
    xs = np.linspace(p["x_range"][0] + p["post_width"] / 2, p["x_range"][1] - p["post_width"] / 2, p["posts"])
    for x in xs:                                       # posts a touch deeper than shelves: no coplanar faces
        box(b, (x - p["post_width"] / 2, 0, za - 0.01), (x + p["post_width"] / 2, H, zb + 0.01), rects["wall"])
    for y in p["shelves_y"]:
        box(b, (xs[0], y, za), (xs[-1], y + p["shelf_thickness"], zb), rects["wall"])


def statue(b, spec):
    s, rects = spec["statue"], {k: v["rect"] for k, v in spec["atlas"]["regions"].items()}
    hw, hd = spec["room"]["width_x"] / 2, spec["room"]["depth_z"] / 2
    cx, cz = s["plan_centre"][0] - hw, hd - s["plan_centre"][1]  # plan (x right, y in) -> world
    bs = s["base"]

    b.group = "statue_base"
    box(b, (cx - bs["width_x"] / 2, 0, cz - bs["length_z"] / 2),
        (cx + bs["width_x"] / 2, bs["height"], cz + bs["length_z"] / 2), rects["marble"], skip=("-y",))

    b.group = "statue_body"
    px = np.asarray(s["outline_px"], float)
    bottom, top = px[:, 1].max(), px[:, 1].min()
    k = (s["total_height"] - bs["height"]) / (bottom - top)     # metres per photo pixel
    sign = 1.0 if s["head_towards"] == "+z" else -1.0           # head is on the photo's left
    zy = np.c_[cz - sign * (px[:, 0] - s["photo_base_centre_x"]) * k,
               bs["height"] + (bottom - px[:, 1]) * k]
    area2 = np.sum(zy[:, 0] * np.roll(zy[:, 1], -1) - np.roll(zy[:, 0], -1) * zy[:, 1])
    if area2 < 0:                                               # ear_clip wants CCW
        zy, px = zy[::-1], px[::-1]

    ph = spec["atlas"]["regions"]["statue"]
    (cx0, cy0, cx1, cy1), (rx0, ry0, rx1, ry1) = ph["crop"], ph["rect"]
    uv_px = np.c_[rx0 + (px[:, 0] - cx0) / (cx1 - cx0) * (rx1 - rx0),
                  ry0 + (px[:, 1] - cy0) / (cy1 - cy0) * (ry1 - ry0)]

    th = s["body_thickness"] / 2
    for x_side, n in ((cx + th, (1, 0, 0)), (cx - th, (-1, 0, 0))):
        for (i, j, m) in ear_clip(zy):
            b.tri([(x_side, zy[q][1], zy[q][0]) for q in (i, j, m)], [uv_px[q] for q in (i, j, m)], n)

    # side walls: the marble strip wrapped once around the outline
    mx0, my0, mx1, my1 = rects["marble"]
    seg = np.linalg.norm(np.roll(zy, -1, 0) - zy, axis=1)
    run = np.r_[0, np.cumsum(seg)] / seg.sum()
    for i in range(len(zy)):
        j = (i + 1) % len(zy)
        d = zy[j] - zy[i]
        out = (0.0, -d[0], d[1])                                 # outward normal of a CCW edge in (z, y)
        P = [(cx + th, zy[i][1], zy[i][0]), (cx + th, zy[j][1], zy[j][0]),
             (cx - th, zy[j][1], zy[j][0]), (cx - th, zy[i][1], zy[i][0])]
        u0 = mx0 + 1 + run[i] * (mx1 - mx0 - 2)
        u1 = mx0 + 1 + run[i + 1] * (mx1 - mx0 - 2)
        b.quad(P, [(u0, my0 + 1), (u1, my0 + 1), (u1, my1 - 1), (u0, my1 - 1)], out)


def write_obj(path, b, header):
    with open(path, "w") as fh:
        fh.write(f"# {header}\n# {len(b.pos)} positions, {len(b.uv)} uvs, {len(b.tris)} triangles\n")
        for p in b.pos:
            fh.write(f"v {p[0]:.6f} {p[1]:.6f} {p[2]:.6f}\n")
        for t in b.uv:
            fh.write(f"vt {t[0]:.6f} {t[1]:.6f}\n")
        group = None
        for (P, T), g in zip(b.tris, b.groups):
            if g != group:
                fh.write(f"g {g}\n")
                group = g
            fh.write("f " + " ".join(f"{p + 1}/{t + 1}" for p, t in zip(P, T)) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default="data/mymodel_ukuran.json")
    ap.add_argument("--out", default="data/mymodel.obj")
    args = ap.parse_args()
    spec = json.load(open(args.spec))
    b = Builder(spec["atlas"]["size"])
    room(b, spec)
    statue(b, spec)
    write_obj(args.out, b, spec["name"] + " (make_mymodel.py)")
    counts = {}
    for g in b.groups:
        counts[g] = counts.get(g, 0) + 1
    print(f"wrote {args.out}  ({len(b.pos)} positions, {len(b.tris)} triangles)")
    print("  " + ", ".join(f"{g} {n}" for g, n in counts.items()))


if __name__ == "__main__":
    main()
