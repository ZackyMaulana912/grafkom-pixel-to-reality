"""Module 3 -- run every from-scratch check. `python tests.py`. Exit 0 iff all pass.

The starter's eight checks are kept (E4 and E5 now go through the rasteriser's
own interpolation functions instead of np.interp, finding T3), followed by
checks for my model, the scene files, handedness, the near clip, the mipmap,
reverse-Z and the agreement of the two renderers.
"""
from __future__ import annotations

import os
import sys
import traceback

import numpy as np

from transforms import (translate, rot_y, look_at, perspective, project,
                        viewport, perspective_divide_2d, reverse_z_depth)


def check(name, fn):
    try:
        fn()
        print("OK   " + name)
        return True
    except Exception:
        print("FAIL " + name)
        traceback.print_exc()
        return False


# ------------------------------------------------------------- the starter's checks
def t_e1_running_point():
    p = np.array([2.0, 3.0, 4.0, 1.0])
    world = rot_y(90) @ translate((1, 0, -1)) @ p        # translate first, then yaw
    assert np.allclose(world, [3, 3, -3, 1], atol=1e-9), world
    assert np.allclose(perspective_divide_2d(world[:3], d=2), [2, 2], atol=1e-9)
    other = translate((1, 0, -1)) @ rot_y(90) @ p         # yaw first, then translate
    assert np.allclose(other, [5, 3, -3, 1], atol=1e-9), other


def t_e2_duality():
    p = np.array([5.0, 0.0, 0.0, 1.0])
    assert np.allclose(look_at(eye=(1, 0, 0), center=(1, 0, -1)) @ p, translate((-1, 0, 0)) @ p, atol=1e-9)


def t_e3_perspective_near_far():
    P = perspective(60, 1.0, 1.0, 9.0)
    for z, want in [(-1.0, -1.0), (-9.0, 1.0), (-3.0, 0.5)]:
        clip = P @ np.array([0, 0, z, 1.0])
        assert abs(clip[2] / clip[3] - want) < 1e-9, (z, clip)


def t_e4_perspective_correct_u():
    """Through raster3d's interpolation: L (u=0, w=1) and R (u=1, w=9) at the
    screen midpoint of the edge, i.e. barycentric weights (0.5, 0.5, 0)."""
    import raster3d
    u, inv_w = np.array([0.0, 1.0, 0.0]), 1.0 / np.array([1.0, 9.0, 1.0])
    assert abs(raster3d.perspective_correct(0.5, 0.5, 0.0, u, inv_w) - 0.1) < 1e-12
    assert abs(raster3d.bary_mix(0.5, 0.5, 0.0, u) - 0.5) < 1e-12


def t_e5_barycentric_depth():
    import raster3d
    z = raster3d.bary_mix(0.25, 0.25, 0.50, np.array([0.20, 0.50, 0.90]))
    assert abs(z - 0.625) < 1e-12, z


def t_projection_pipeline_shapes():
    verts = np.array([[0, 0, -2.0], [1, 0, -2.0], [0, 1, -3.0]])
    clip, ndc = project(perspective(50, 4 / 3, 0.1, 100), look_at((0, 0, 3), (0, 0, 0)), np.eye(4), verts)
    assert clip.shape == (3, 4) and ndc.shape == (3, 3)
    scr = viewport(ndc, 640, 480)
    assert scr.shape == (3, 3) and np.all(np.abs(scr[:, 0]) <= 1280)


def t_one_triangle_render():
    from objio import Mesh
    import raster3d
    m = Mesh(np.array([[-0.6, -0.6, -2.0], [0.6, -0.6, -2.0], [0.0, 0.6, -2.0]]), [], [[0, 1, 2]], [])
    col, dep, filled = raster3d.render(m, w=48, h=48, near=1.0, far=50.0, eye=(0, 0, 0),
                                       center=(0, 0, -1), light_dir=(0, 0, 1))
    assert 200 < filled < 48 * 48, filled
    assert np.isfinite(dep).sum() == filled
    fin = dep[np.isfinite(dep)]
    assert fin.max() - fin.min() < 1e-6


def t_reference_frame():
    """The starter's check, unchanged in spirit: my rasteriser on the temple as
    stored, against ref/temple_ref.ppm made by the unmodified starter (K12)."""
    import raster3d
    from objio import load_obj
    from ppm_io import read_ppm
    from metrics import psnr
    mesh, tex = load_obj("data/pusaka_model.obj"), read_ppm("data/relief.ppm")
    M = translate((0, 0, 0)) @ rot_y(35) @ np.diag([1.4, 1.4, 1.4, 1.0])
    col, _, _ = raster3d.render(mesh, w=160, h=160, tex_u8=tex, model=M)
    p = psnr(col, read_ppm("ref/temple_ref.ppm"))
    assert p == float("inf"), f"temple frame PSNR vs ref = {p:.1f} dB (expected byte-identical)"


# ----------------------------------------------------------------------- new checks
def t_scene_file_matches_ref():
    """scenes/temple.json + the winding-enforcing loader still give the ref frame."""
    import raster3d
    from ppm_io import read_ppm
    from scene import load_scene
    col, _, _ = raster3d.render_scene(load_scene("scenes/temple.json"), 160, 160)
    assert np.array_equal(col, read_ppm("ref/temple_ref.ppm"))


def t_my_model():
    """>= 200 triangles, no zero-area triangle, a UV on every corner, UVs inside
    the atlas, and consistent winding: every edge shared by exactly two
    triangles appears once in each direction."""
    from collections import Counter
    from objio import load_obj
    m = load_obj("data/mymodel.obj")
    assert m.n_tris >= 200, m.n_tris
    t = m.triangle_positions()
    area = 0.5 * np.linalg.norm(np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]), axis=1)
    assert area.min() > 1e-8, area.min()
    assert m.face_uvs is not None and len(m.face_uvs) == m.n_tris
    assert m.uvs.min() > 0 and m.uvs.max() < 1, "UVs must stay inside the atlas (no wrap)"
    directed = Counter((int(a), int(b)) for f in m.faces for a, b in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])))
    pairs = Counter(tuple(sorted(e)) for e in directed.elements())
    shared = [e for e, n in pairs.items() if n == 2]
    bad = [e for e in shared if directed[e] != 1 or directed[e[::-1]] != 1]
    assert len(shared) > 300 and not bad, (len(shared), bad[:3])


def t_my_texture():
    from ppm_io import read_header
    w, h, ch = read_header("data/mymodel_tex.ppm")
    assert (w, h, ch) == (512, 512, 3), (w, h, ch)


def t_handedness():
    """Q4(d): a mirror shows up as a negative determinant; an inside-out mesh as
    a negative signed volume. Both are numbers, no eyes needed."""
    from objio import load_obj
    from scene import load_scene, model_matrix, view_matrix
    for path in ("scenes/temple.json", "scenes/mymodel.json"):
        sc = load_scene(path)
        assert np.linalg.det(model_matrix(sc)[:3, :3]) > 0, path
        assert abs(np.linalg.det(view_matrix(sc)[:3, :3]) - 1) < 1e-9, path
    stored = load_obj("data/pusaka_model.obj")
    assert stored.signed_volume() < 0, "the starter temple is wound inward (T13)"
    assert load_obj("data/pusaka_model.obj", enforce_ccw=True).signed_volume() > 0
    assert load_obj("data/mymodel.obj").signed_volume() > 0


def t_near_clip():
    """A triangle crossing the near plane is cut in clip space: every output
    vertex has z + w >= 0, the cut vertices lie on the plane, and nothing behind
    the camera reaches the screen."""
    from objio import Mesh
    import raster3d
    P = perspective(60, 1.0, 0.5, 10.0)
    eye_pts = np.array([[-1, -0.5, -3.0], [1, -0.5, -3.0], [0, -0.5, 2.0]])     # one vertex behind
    clip = (P @ np.c_[eye_pts, np.ones(3)].T).T
    pieces = raster3d.clip_near(clip, np.eye(3))
    assert len(pieces) == 2
    for vc, _ in pieces:
        d = vc[:, 2] + vc[:, 3]
        assert np.all(d >= -1e-12) and np.sum(np.abs(d) < 1e-9) >= 1
    col, dep, filled = raster3d.render(Mesh(eye_pts, [], [[0, 1, 2]], []), w=64, h=64, near=0.5,
                                       far=10.0, eye=(0, 0, 0), center=(0, 0, -1))
    assert filled > 0 and np.all(dep[np.isfinite(dep)] >= -1 - 1e-9)


def t_mipmap():
    """Level k+1 is the 2x2 average of level k, in linear light."""
    from mipmap import build_pyramid
    rng = np.random.default_rng(0)
    t = rng.random((16, 16, 3))
    pyr = build_pyramid(t, 4)
    assert [p.shape[0] for p in pyr] == [16, 8, 4, 2]
    assert np.allclose(pyr[1][0, 0], t[:2, :2].mean(axis=(0, 1)))
    assert np.allclose(pyr[3].mean(), t.mean())


def t_reverse_z():
    n, f = 0.1, 10.0
    assert abs(reverse_z_depth(1 / n, n, f) - 1) < 1e-12 and abs(reverse_z_depth(1 / f, n, f)) < 1e-12


def t_overlap_order_free():
    """Two overlapping triangles: the z-buffer gives the same frame in either draw order."""
    from objio import Mesh
    import raster3d
    front = [[-0.7, -0.7, -1.5], [0.7, -0.7, -1.5], [0.0, 0.7, -1.5]]
    back = [[-0.2, -0.7, -3.0], [1.2, -0.7, -3.0], [0.5, 0.7, -3.0]]
    cam = dict(w=64, h=64, near=1.0, far=50.0, eye=(0, 0, 0), center=(0, 0, -1))
    a, _, _ = raster3d.render(Mesh(np.array(front + back), [], [[0, 1, 2], [3, 4, 5]], []),
                              tri_colors=[(255, 0, 0), (0, 0, 255)], **cam)
    b, _, _ = raster3d.render(Mesh(np.array(back + front), [], [[0, 1, 2], [3, 4, 5]], []),
                              tri_colors=[(0, 0, 255), (255, 0, 0)], **cam)
    assert np.array_equal(a, b)


def t_raster_vs_raytrace_mymodel():
    """Two independent renderers on my model (small frame to keep the test fast)."""
    import raster3d
    import raytrace
    from metrics import psnr
    from scene import load_scene
    sc = load_scene("scenes/mymodel.json")
    a, _, _ = raster3d.render_scene(sc, 128, 128)
    b, _ = raytrace.render_scene(sc, 128, 128)
    p = psnr(a, b)
    assert p > 60, f"raster vs ray tracer on my model: {p:.1f} dB"


def main():
    if not os.path.exists("data/pusaka_model.obj"):
        print("run make_model.py first (data/pusaka_model.obj is missing)")
        sys.exit(1)
    checks = [
        ("E1  running point (2,3,4) -> (3,3,-3); divide d=2 -> (2,2); other order (5,3,-3)", t_e1_running_point),
        ("E2  camera +x == model -x (identical points)", t_e2_duality),
        ("E3  perspective: z=-n -> ndc -1 ; z=-f -> ndc +1 ; z=-3 -> 0.5", t_e3_perspective_near_far),
        ("E4  raster3d: perspective-correct u at screen centre = 0.1 (naive 0.5)", t_e4_perspective_correct_u),
        ("E5  raster3d: barycentric depth 0.20/0.50/0.90 at (.25,.25,.5) = 0.625", t_e5_barycentric_depth),
        ("projection pipeline shapes + viewport", t_projection_pipeline_shapes),
        ("one-triangle z-buffer render fills a plausible region, flat depth", t_one_triangle_render),
        ("temple frame matches ref/temple_ref.ppm (byte-identical)", t_reference_frame),
        ("scenes/temple.json + CCW-enforcing loader -> same ref frame", t_scene_file_matches_ref),
        ("my model: >=200 tris, no zero area, UV everywhere, consistent winding", t_my_model),
        ("my texture: 512x512 RGB", t_my_texture),
        ("handedness: det(M) > 0, temple stored inside out, loader fixes it", t_handedness),
        ("near clip in clip space: cut vertices on z + w = 0", t_near_clip),
        ("mipmap: 4 levels, each a 2x2 linear-light average", t_mipmap),
        ("reverse-Z: near -> 1, far -> 0", t_reverse_z),
        ("z-buffer: same frame in either draw order", t_overlap_order_free),
        ("raster vs ray tracer on my model > 60 dB", t_raster_vs_raytrace_mymodel),
    ]
    results = [check(n, f) for n, f in checks]
    ok = sum(results)
    print(f"\n{'ALL CHECKS PASSED' if all(results) else 'SOME CHECKS FAILED'} ({ok} ok, {len(results) - ok} fail)")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
