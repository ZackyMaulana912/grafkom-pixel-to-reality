"""Module 3 -- the from-scratch rasteriser (NumPy only).

Per triangle: model -> world (flat normal, Lambert), clip = P V M p, clip
against the near plane while w still means something, divide by w, viewport,
then Module 2's edge functions give barycentric weights at pixel centres.
Depth (NDC z, affine in screen space) is interpolated linearly; texture
coordinates are interpolated as u/w, v/w and 1/w and divided per pixel.

Options beyond the starter: a scene file (--scene), naive UVs (--naive-uv),
mipmapping (--mip), back-face culling (--cull), reverse-Z and depth storage
formats (depth_mode / depth_format), and a shadow map (--shadow).

Run:
  python raster3d.py --scene scenes/mymodel.json
  python raster3d.py --model data/pusaka_model.obj --w 512 --h 512   # starter form
  python raster3d.py --demo-triangle --w 64 --h 64
  python raster3d.py --demo-overlap  --w 64 --h 64
"""
from __future__ import annotations

import argparse
import os
import time

import numpy as np

from mipmap import build_pyramid, level_of_detail, sample_trilinear
from objio import Mesh, load_obj
from ppm_io import read_ppm, write_ppm
from srgb import linear_to_srgb, srgb_to_linear
from transforms import look_at, perspective, project, reverse_z_depth, viewport


# ------------------------------------------------------------- texture sampling
def sample_bilinear(tex_lin, u, v):
    """The starter's convention, kept so ref/temple_ref.ppm stays meaningful:
    u = 0 is the centre of texel 0 and u = 1 the centre of texel W-1, and u, v
    wrap with mod 1. (A GPU puts texel i's centre at (i + 0.5) / W; the WebGL
    viewer shifts its UVs to match this one -- see web/viewer.js.)"""
    H, W = tex_lin.shape[:2]
    x = np.mod(u, 1.0) * (W - 1)
    y = np.mod(v, 1.0) * (H - 1)
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    x1, y1 = np.clip(x0 + 1, 0, W - 1), np.clip(y0 + 1, 0, H - 1)
    fx, fy = (x - x0)[..., None], (y - y0)[..., None]
    x0, y0 = np.clip(x0, 0, W - 1), np.clip(y0, 0, H - 1)
    top = tex_lin[y0, x0] * (1 - fx) + tex_lin[y0, x1] * fx
    bot = tex_lin[y1, x0] * (1 - fx) + tex_lin[y1, x1] * fx
    return top * (1 - fy) + bot * fy


# ------------------------------------------------------------- interpolation
def bary_mix(l0, l1, l2, a):
    """Linear (screen-space) interpolation of a per-vertex value a[0..2]:
    right for NDC depth and for 1/w, wrong for texture coordinates."""
    return l0 * a[0] + l1 * a[1] + l2 * a[2]


def perspective_correct(l0, l1, l2, attr, inv_w):
    """Interpolate attr/w and 1/w linearly, then divide (Example E4)."""
    return bary_mix(l0, l1, l2, attr * inv_w) / bary_mix(l0, l1, l2, inv_w)


# ----------------------------------------------------------------- near clipping
def clip_near(vc, attrs):
    """Sutherland-Hodgman against the near plane z + w >= 0, in clip space,
    before any division. vc (3,4), attrs (3,k) are carried along linearly.
    Returns 0, 1 or 2 triangles as (vc, attrs) pairs."""
    def dist(p):
        return p[2] + p[3]

    poly = list(zip(vc, attrs))
    out = []
    for i in range(3):
        (cv, ca), (pv, pa) = poly[i], poly[i - 1]
        cin, pin = dist(cv) >= 0.0, dist(pv) >= 0.0
        if cin != pin:                                   # the edge crosses the plane
            t = dist(pv) / (dist(pv) - dist(cv))
            out.append((pv + t * (cv - pv), pa + t * (ca - pa)))
        if cin:
            out.append((cv, ca))
    return [(np.stack([out[0][0], out[k][0], out[k + 1][0]]),
             np.stack([out[0][1], out[k][1], out[k + 1][1]])) for k in range(1, len(out) - 1)]


# ------------------------------------------------------------------- shadow map
class ShadowMap:
    """Depth of the scene seen from the directional light (orthographic).
    A fragment is lit when it is not deeper than the map plus a small bias."""

    def __init__(self, world_tris, light_dir, size=1024, bias=0.01):
        L = np.asarray(light_dir, float) / np.linalg.norm(light_dir)
        centre = world_tris.reshape(-1, 3).mean(0)
        self.V = look_at(centre + L * 50.0, centre, (0, 0, 1) if abs(L[1]) > 0.99 else (0, 1, 0))
        pts = (self.V @ np.c_[world_tris.reshape(-1, 3), np.ones(world_tris.size // 3)].T).T[:, :3]
        self.lo, self.hi = pts[:, :2].min(0), pts[:, :2].max(0)
        self.size, self.bias = size, bias
        self.depth = np.full((size, size), np.inf)        # distance along -z of light space
        for t in pts.reshape(-1, 3, 3):
            self._draw(t)

    def _to_map(self, p):
        s = (p[..., :2] - self.lo) / (self.hi - self.lo) * self.size
        return s[..., 0], self.size - s[..., 1], -p[..., 2]

    def _draw(self, t):
        x, y, z = self._to_map(t)
        area = (x[1] - x[0]) * (y[2] - y[0]) - (y[1] - y[0]) * (x[2] - x[0])
        if area == 0:
            return
        x0, x1 = max(0, int(np.floor(x.min()))), min(self.size - 1, int(np.ceil(x.max())))
        y0, y1 = max(0, int(np.floor(y.min()))), min(self.size - 1, int(np.ceil(y.max())))
        if x0 > x1 or y0 > y1:
            return
        ys, xs = np.mgrid[y0:y1 + 1, x0:x1 + 1] + 0.5
        l0 = ((x[2] - x[1]) * (ys - y[1]) - (y[2] - y[1]) * (xs - x[1])) / area
        l1 = ((x[0] - x[2]) * (ys - y[2]) - (y[0] - y[2]) * (xs - x[2])) / area
        l2 = 1 - l0 - l1
        inside = (l0 >= 0) & (l1 >= 0) & (l2 >= 0)
        d = l0 * z[0] + l1 * z[1] + l2 * z[2]
        reg = self.depth[y0:y1 + 1, x0:x1 + 1]
        win = inside & (d < reg)
        reg[win] = d[win]

    def lit(self, world_pts):
        p = (self.V @ np.c_[world_pts, np.ones(len(world_pts))].T).T[:, :3]
        x, y, z = self._to_map(p)
        xi = np.clip(np.floor(x).astype(int), 0, self.size - 1)
        yi = np.clip(np.floor(y).astype(int), 0, self.size - 1)
        return z <= self.depth[yi, xi] + self.bias


# ----------------------------------------------------------------- the renderer
def render(mesh, *, w, h, tex_u8=None, model=None, tri_colors=None,
           eye=(2.6, 2.0, 3.4), center=(0, 0.7, 0), fovy=45.0,
           near=1.0, far=14.0, light_dir=(0.4, 0.9, 0.6), ambient=0.15,
           cull_back=False, depth_bits=None, depth_mode="ndc", depth_format=None,
           naive_uv=False, mip=False, shadow=False, stats=None, uv_out=None,
           quantize="floor"):
    """Returns (sRGB uint8 frame, stored depth, fragments written).

    depth_mode   "ndc" stores NDC z and keeps the smaller; "reverse" stores
                 reverse-Z window depth (near 1, far 0) and keeps the larger.
    depth_format None = float64; "f32"; or "u16"/"u24" fixed point.
                 depth_bits=n is the starter's spelling of "u<n>" on NDC depth.
    stats        optional dict, filled with counts for the caller.
    uv_out       optional (h, w, 2) array; receives the interpolated (u, v) of
                 the visible fragment, so texture swimming can be measured.
    quantize     "floor" truncates to uint8 like the starter (ref/temple_ref.ppm
                 depends on it); "round" rounds to nearest, like a GPU.
    """
    model = np.eye(4) if model is None else model
    eye_pos = np.asarray(eye, float)
    P, V = perspective(fovy, w / h, near, far), look_at(eye, center)
    pos_h = np.c_[mesh.positions, np.ones(len(mesh.positions))]
    world = (model @ pos_h.T).T[:, :3]
    clip = (P @ V @ model @ pos_h.T).T
    tris_uv = mesh.triangle_uvs()
    L = np.asarray(light_dir, float)
    L = L / np.linalg.norm(L)

    tex_lin = pyr = None
    if tex_u8 is not None:
        tex_lin = srgb_to_linear(tex_u8.astype(np.float64) / 255.0)
        if mip:
            pyr = build_pyramid(tex_lin, levels=4)
    if depth_bits is not None:
        depth_format = f"u{depth_bits}"
    reverse = depth_mode == "reverse"
    smap = ShadowMap(world[mesh.faces], L) if shadow else None

    color = np.zeros((h, w, 3), np.float64)
    depth = np.full((h, w), -np.inf if reverse else np.inf)
    filled = clipped = culled = 0

    for fi, vidx in enumerate(mesh.faces):
        wp = world[vidx]
        nrm = np.cross(wp[1] - wp[0], wp[2] - wp[0])
        nl = np.linalg.norm(nrm)
        if nl < 1e-12:
            continue
        nrm = nrm / nl
        if nrm @ (eye_pos - wp[0]) < 0:                 # shade the side we see
            nrm = -nrm
        lambert = max(0.0, float(nrm @ L))

        # carry [u, v, 1, world xyz] through the clip; 1 becomes 1/w below
        attrs = np.c_[tris_uv[fi], np.ones(3), wp]
        clipped += bool(np.any(clip[vidx, 2] + clip[vidx, 3] < 0))
        pieces = clip_near(clip[vidx], attrs)
        for cvc, cattr in pieces:
            wv = cvc[:, 3]
            ndc = cvc[:, :3] / wv[:, None]
            sx = (ndc[:, 0] * 0.5 + 0.5) * w
            sy = (1.0 - (ndc[:, 1] * 0.5 + 0.5)) * h
            sz = ndc[:, 2]
            inv_w = 1.0 / wv
            uvw = cattr[:, :2] * inv_w[:, None]           # u/w, v/w at the vertices

            minx, maxx = max(0, int(np.floor(sx.min()))), min(w - 1, int(np.ceil(sx.max())))
            miny, maxy = max(0, int(np.floor(sy.min()))), min(h - 1, int(np.ceil(sy.max())))
            if minx > maxx or miny > maxy:
                continue
            ax, ay, bx, by, cx, cy = sx[0], sy[0], sx[1], sy[1], sx[2], sy[2]
            area = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
            if area == 0:
                continue
            if cull_back and area > 0:                   # y down: CCW-from-outside has area < 0
                culled += 1
                continue

            ys, xs = np.mgrid[miny:maxy + 1, minx:maxx + 1]
            px, py = xs + 0.5, ys + 0.5
            # edge functions / area = barycentric weights of vertices 0, 1, 2
            l0 = ((cx - bx) * (py - by) - (cy - by) * (px - bx)) / area
            l1 = ((ax - cx) * (py - cy) - (ay - cy) * (px - cx)) / area
            l2 = 1.0 - l0 - l1
            inside = (l0 >= 0) & (l1 >= 0) & (l2 >= 0)
            if not inside.any():
                continue

            inv_w_i = bary_mix(l0, l1, l2, inv_w)
            frag_z = reverse_z_depth(inv_w_i, near, far) if reverse else bary_mix(l0, l1, l2, sz)
            frag_z = store_depth(frag_z, depth_format, reverse)

            reg = depth[miny:maxy + 1, minx:maxx + 1]
            win = inside & ((frag_z > reg) if reverse else (frag_z < reg))
            if not win.any():
                continue
            reg[win] = frag_z[win]

            if tex_lin is not None:
                if naive_uv:                             # Pitfall 12.4, on purpose
                    u_i, v_i = bary_mix(l0, l1, l2, cattr[:, 0]), bary_mix(l0, l1, l2, cattr[:, 1])
                else:
                    u_i = bary_mix(l0, l1, l2, uvw[:, 0]) / inv_w_i
                    v_i = bary_mix(l0, l1, l2, uvw[:, 1]) / inv_w_i
                if uv_out is not None:
                    uv_out[miny:maxy + 1, minx:maxx + 1][win] = np.stack([u_i, v_i], -1)[win]
                if pyr is not None:
                    lod = level_of_detail(u_i, v_i, tex_lin.shape[:2])
                    tex_rgb = np.zeros(u_i.shape + (3,))
                    tex_rgb[win] = sample_trilinear(pyr, u_i[win], v_i[win], lod[win], sample_bilinear)
                else:
                    tex_rgb = sample_bilinear(tex_lin, u_i, v_i)
            elif tri_colors is not None:
                tex_rgb = np.ones((*l0.shape, 3)) * srgb_to_linear(np.asarray(tri_colors[fi], float) / 255.0)
            else:
                tex_rgb = np.ones((*l0.shape, 3)) * 0.7

            if smap is None:
                shade = ambient + (1 - ambient) * lambert
            else:
                pw = np.stack([perspective_correct(l0, l1, l2, cattr[:, 3 + k], inv_w) for k in range(3)], -1)
                vis = np.zeros(l0.shape)
                vis[win] = smap.lit(pw[win])
                shade = (ambient + (1 - ambient) * lambert * vis)[..., None]

            lit = np.clip(tex_rgb * shade, 0, 1)
            cregion = color[miny:maxy + 1, minx:maxx + 1]
            cregion[win] = linear_to_srgb(lit)[win]
            filled += int(win.sum())

    if stats is not None:
        stats.update(fragments=filled, clipped_tris=int(clipped), culled=culled,
                     covered=int(np.isfinite(depth).sum()))
    out = np.clip(color * 255, 0, 255)
    out = np.round(out) if quantize == "round" else out          # floor: the starter's truncation
    return out.astype(np.uint8), depth, filled


def store_depth(z, fmt, reverse):
    """What the depth buffer can actually hold. Fixed point quantises the window
    depth (0..1); f32 rounds to single precision."""
    if fmt is None:
        return z
    if fmt == "f32":
        return z.astype(np.float32).astype(np.float64)
    q = float(2 ** int(fmt[1:]))
    if reverse:
        return np.round(z * q) / q
    return np.round((z * 0.5 + 0.5) * q) / q * 2.0 - 1.0


# ------------------------------------------------------------------ scene files
def load_scene_mesh(sc):
    """The renderers' loader: winding enforced CCW-from-outside (objio, T13)."""
    return load_obj(sc["model"]["obj"], enforce_ccw=True)


def scene_kwargs(sc, w=None, h=None):
    from scene import light, model_matrix
    c = sc["camera"]
    L, amb = light(sc)
    return dict(w=w or sc["frame"]["w"], h=h or sc["frame"]["h"], model=model_matrix(sc),
                eye=c["eye"], center=c["center"], fovy=c["fovy_deg"], near=c["near"],
                far=c["far"], light_dir=L, ambient=amb)


def render_scene(sc, w=None, h=None, mesh=None, tex=None, **opts):
    mesh = mesh or load_scene_mesh(sc)
    tex = read_ppm(sc["model"]["texture"]) if tex is None and sc["model"].get("texture") else tex
    return render(mesh, tex_u8=tex, **scene_kwargs(sc, w, h), **opts)


def depth_image(depth, reverse=False):
    """Grey depth picture: near dark, far light, background white."""
    fin = np.isfinite(depth)
    d = np.ones_like(depth)
    d[fin] = (1 - depth[fin]) if reverse else (depth[fin] + 1) * 0.5
    return np.repeat((np.clip(d, 0, 1) * 255).astype(np.uint8)[..., None], 3, axis=2)


def depth_path(out):
    """out/x_raster.ppm -> out/x_depth.ppm; any other name gets _depth (T5)."""
    head, tail = os.path.split(out)
    stem, ext = os.path.splitext(tail)
    stem = stem.replace("raster", "depth") if "raster" in stem else stem + "_depth"
    return os.path.join(head, stem + ext)


# ------------------------------------------------------------------------- demos
def _demo_triangle(w, h):
    """One textured triangle (Fully Worked Example, Step 2)."""
    pos = np.array([[-0.8, -0.6, -2.0], [0.9, -0.7, -3.5], [-0.2, 0.9, -2.5]])
    uv = np.array([[0, 0], [1, 0], [0.5, 1.0]])
    m = Mesh(pos, uv, [[0, 1, 2]], [[0, 1, 2]])
    tex = read_ppm("data/relief.ppm") if os.path.exists("data/relief.ppm") else None
    clip, ndc = project(perspective(60, w / h, 1.0, 50.0), np.eye(4), np.eye(4), pos)
    scr = viewport(ndc, w, h)
    print("triangle screen verts: " + " ".join(f"({x:.0f},{y:.0f})" for x, y in scr[:, :2])
          + "   uv: (0,0) (1,0) (0.5,1)")
    col, dep, filled = render(m, w=w, h=h, tex_u8=tex, near=1.0, far=50.0, eye=(0, 0, 0),
                              center=(0, 0, -1), light_dir=(0, 0, 1))
    fin = np.isfinite(dep)
    print(f"filled fragments: {filled}   depth range [{dep[fin].min():.2f}, {dep[fin].max():.2f}]")
    invw = 1.0 / clip[:, 3]
    pc = (uv * invw[:, None]).mean(0) / invw.mean()     # centroid: equal weights 1/3
    print(f"perspective-correct UV at centroid: ({pc[0]:.3f}, {pc[1]:.3f})   "
          f"(naive linear: ({uv[:, 0].mean():.3f}, {uv[:, 1].mean():.3f}))")
    os.makedirs("out", exist_ok=True)
    write_ppm("out/tri_raster.ppm", col)
    print("wrote out/tri_raster.ppm  (texture: data/relief.ppm, bilinear)")


def _demo_overlap(w, h):
    """Two overlapping triangles drawn back-to-front AND front-to-back: the
    z-buffer must give the same frame both ways (counted, not asserted in text)."""
    front = [[-0.7, -0.7, -1.5], [0.7, -0.7, -1.5], [0.0, 0.7, -1.5]]
    back = [[-0.2, -0.7, -3.0], [1.2, -0.7, -3.0], [0.5, 0.7, -3.0]]
    cols = [(230, 130, 40), (60, 120, 210)]
    cam = dict(w=w, h=h, near=1.0, far=50.0, eye=(0, 0, 0), center=(0, 0, -1), light_dir=(0, 0, 1))
    one = lambda tri, c: render(Mesh(np.array(tri), [], [[0, 1, 2]], []), tri_colors=[c], **cam)
    _, d_front, n_front = one(front, cols[0])
    _, d_back, n_back = one(back, cols[1])
    a, da, _ = render(Mesh(np.array(front + back), [], [[0, 1, 2], [3, 4, 5]], []), tri_colors=cols, **cam)
    b, _, _ = render(Mesh(np.array(back + front), [], [[0, 1, 2], [3, 4, 5]], []), tri_colors=cols[::-1], **cam)
    both = np.isfinite(d_front) & np.isfinite(d_back)
    print(f"front triangle NDC depth {d_front[np.isfinite(d_front)].mean():.3f}, "
          f"back triangle {d_back[np.isfinite(d_back)].mean():.3f}")
    print(f"overlap pixels: {int(both.sum())}   where BACK won the z-test: "
          f"{int((both & (da == d_back)).sum())}")
    print(f"pixels where BACK is visible (no overlap): {int((np.isfinite(d_back) & ~both).sum())}"
          f"   (back alone covers {n_back})")
    print(f"draw order swapped -> identical frame: {np.array_equal(a, b)}")
    os.makedirs("out", exist_ok=True)
    write_ppm("out/overlap.ppm", a)
    print("wrote out/overlap.ppm")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", help="scenes/<name>.json (camera, model, light, texture)")
    ap.add_argument("--model", help="starter form: this OBJ with scenes/temple.json's camera")
    ap.add_argument("--w", type=int)
    ap.add_argument("--h", type=int)
    ap.add_argument("--out")
    ap.add_argument("--naive-uv", action="store_true", help="linear UVs in screen space (Pitfall 12.4)")
    ap.add_argument("--mip", action="store_true", help="4-level mipmap, trilinear")
    ap.add_argument("--cull", action="store_true", help="back-face culling")
    ap.add_argument("--shadow", action="store_true", help="hard shadow from a shadow map")
    ap.add_argument("--demo-triangle", action="store_true")
    ap.add_argument("--demo-overlap", action="store_true")
    args = ap.parse_args()

    if args.demo_triangle:
        return _demo_triangle(args.w or 64, args.h or 64)
    if args.demo_overlap:
        return _demo_overlap(args.w or 64, args.h or 64)

    from scene import load_scene
    if not (args.scene or args.model):
        raise SystemExit("give --scene (or --model), or --demo-triangle / --demo-overlap")
    sc = load_scene(args.scene or "scenes/temple.json")
    if args.model:
        sc["model"]["obj"] = args.model
    out = args.out or f"out/{sc['name']}_raster.ppm"
    stats = {}
    t0 = time.perf_counter()
    col, dep, filled = render_scene(sc, args.w or (512 if args.model else None), args.h or (512 if args.model else None),
                                    naive_uv=args.naive_uv, mip=args.mip, cull_back=args.cull,
                                    shadow=args.shadow, stats=stats)
    dt = time.perf_counter() - t0
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    write_ppm(out, col)
    write_ppm(depth_path(out), depth_image(dep))
    mesh = load_scene_mesh(sc)
    fin = np.isfinite(dep)
    print(f"model: {mesh.n_tris} triangles{' (rewound to CCW on load)' if mesh.rewound else ''}"
          f"   framebuffer {col.shape[1]}x{col.shape[0]}   {dt:.2f} s")
    print(f"fragments written: {filled} (overdraw included)   pixels covered: {int(fin.sum())}"
          f"   triangles touched by the near clip: {stats['clipped_tris']}")
    if fin.any():
        print(f"depth (NDC) range [{dep[fin].min():.3f}, {dep[fin].max():.3f}]")
    print(f"wrote {out} and {depth_path(out)}")


if __name__ == "__main__":
    main()
