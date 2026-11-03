"""Ground truth for hotspot occlusion: is a hotspot really visible from a camera? (NumPy only)

A hotspot is visible when (1) the surface it sits on faces the camera (a point on a surface
turned away is seen from inside the solid, so never), and (2) a ray from the hotspot, lifted
0.1 mm along its normal so it does not hit its own triangle, reaches the camera without
meeting any other triangle. Rule (1) matters at grazing angles: a larger lift lets the ray
slip past the edge of a thin part such as the tail and count a turned-away point as visible.
The same ray idea as ray_generator.py, now used to check visibility instead of colour.
verify_ar_app.py --occlusion compares this with what <model-viewer> shows.
"""
from __future__ import annotations

import json
import os
import struct

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LIFT_M = 1e-4


def load_mesh(path=os.path.join(HERE, "assets", "kuda.glb")):
    """Triangles (T, 3, 3) in metres, glTF axes, from the first primitive of a GLB."""
    with open(path, "rb") as f:
        data = f.read()
    json_len = struct.unpack_from("<I", data, 12)[0]
    gltf = json.loads(data[20:20 + json_len])
    binary = data[28 + json_len:]
    prim = gltf["meshes"][0]["primitives"][0]

    def read(index, dtype, width):
        acc = gltf["accessors"][index]
        view = gltf["bufferViews"][acc["bufferView"]]
        start = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
        return np.frombuffer(binary, dtype=dtype, count=acc["count"] * width, offset=start)

    pos = read(prim["attributes"]["POSITION"], "<f4", 3).reshape(-1, 3).astype(float)
    idx_type = {5121: "<u1", 5123: "<u2", 5125: "<u4"}[gltf["accessors"][prim["indices"]]["componentType"]]
    return pos[read(prim["indices"], idx_type, 1).astype(np.int64).reshape(-1, 3)]


def camera_position(theta, phi, radius, target):
    """<model-viewer>'s orbit (radians, metres) -> camera position: theta 0 looks from +z, 90 deg from +x."""
    return np.asarray(target, dtype=float) + radius * np.array(
        [np.sin(phi) * np.sin(theta), np.cos(phi), np.sin(phi) * np.cos(theta)])


def is_visible(point, normal, camera, tris):
    """True if the hotspot's surface faces the camera and nothing of the mesh is in between."""
    origin = np.asarray(point, float) + LIFT_M * np.asarray(normal, float)
    to_cam = np.asarray(camera, float) - origin
    dist = np.linalg.norm(to_cam)
    d = to_cam / dist
    if float(np.dot(d, normal)) <= 0.0:
        return False
    v0, e1, e2 = tris[:, 0], tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]
    p = np.cross(d, e2)
    det = np.einsum("ij,ij->i", e1, p)
    ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
    s = origin - v0
    u = np.einsum("ij,ij->i", s, p) * inv
    q = np.cross(s, e1)
    v = (q @ d) * inv
    t = np.einsum("ij,ij->i", e2, q) * inv
    hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-6) & (t < dist)
    return not bool(hit.any())


# --- choosing better normals ---------------------------------------------------------------
# <model-viewer> shows a hotspot whenever dot(normal, direction to camera) >= 0. The normal the
# ray-cast placement gives is the face normal at the hit point, and on a curved part it can lean
# towards a side from which the point is blocked (the raised foreleg leans towards the tail).
# The normal only steers visibility, so it may be any direction that makes the dot test agree
# with the real occlusion as often as possible. It is chosen on TUNE cameras that are disjoint
# from the cameras the browser test uses (verify_ar_app.py --occlusion: polar 75 and 25 deg,
# azimuth on multiples of 5 deg), so the browser test stays a fair check.

# <model-viewer>'s automatic camera target and radius for each model, as reported by
# getCameraTarget() / getCameraOrbit() in a 390 x 800 portrait page
TARGET, RADIUS = (0.0, 0.3086, 0.0), 1.572                       # kuda.glb
CAR_TARGET, CAR_RADIUS = (-0.2653, 0.5942, 0.0046), 11.082       # amr23.glb
TUNE_POLAR_DEG = (40.0, 60.0, 80.0, 95.0)
TUNE_AZIMUTH_DEG = np.arange(2.5, 360.0, 5.0)
MAX_TILT_DEG = 75.0           # keep the chosen normal within this angle of the surface normal


def tune_cameras(target=TARGET, radius=RADIUS):
    return [camera_position(np.radians(t), np.radians(p), radius, target)
            for p in TUNE_POLAR_DEG for t in TUNE_AZIMUTH_DEG]


def _sphere(n=4000):
    """n nearly even directions on the unit sphere (Fibonacci lattice), deterministic."""
    i = np.arange(n) + 0.5
    z = 1 - 2 * i / n
    r = np.sqrt(1 - z * z)
    phi = np.pi * (1 + 5 ** 0.5) * i
    return np.stack([r * np.cos(phi), r * np.sin(phi), z], axis=1)


def tune_normal(point, surface_normal, tris, cameras):
    """The direction whose dot test best matches the real visibility over `cameras`.

    Returns (normal, mismatches before, mismatches after, number of cameras)."""
    point, surface_normal = np.asarray(point, float), np.asarray(surface_normal, float)
    truth = np.array([is_visible(point, surface_normal, c, tris) for c in cameras])
    dirs = np.array([c - point for c in cameras])
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    cand = _sphere()
    cand = cand[cand @ surface_normal >= np.cos(np.radians(MAX_TILT_DEG))]
    cand = np.vstack([surface_normal, cand])  # the surface normal itself competes and wins ties
    errors = ((cand @ dirs.T >= 0) != truth).sum(axis=1)
    best = int(np.argmin(errors))
    return cand[best], int(errors[0]), int(errors[best]), len(cameras)


def tune_hotspot_file(path=os.path.join(HERE, "assets", "hotspots_kuda.json"),
                      glb=os.path.join(HERE, "assets", "kuda.glb"), target=TARGET, radius=RADIUS):
    """Rewrite the normals of a hotspot file in place; the face normal is kept as surface_normal."""
    with open(path) as f:
        data = json.load(f)
    tris, cameras = load_mesh(glb), tune_cameras(target, radius)
    for h in data["hotspots"]:
        surface = h.get("surface_normal", h["normal"])
        normal, before, after, n = tune_normal(h["position"], surface, tris, cameras)
        h["surface_normal"] = surface
        h["normal"] = [round(float(c), 4) for c in normal]
        tilt = np.degrees(np.arccos(np.clip(np.dot(normal, surface) / np.linalg.norm(surface), -1, 1)))
        print(f"{h['id']:7s} mismatches on {n} tune cameras: {before:3d} -> {after:3d}, "
              f"normal {h['normal']} ({tilt:.0f} deg from the surface normal)")
    data["normals"] = ("chosen by occlusion.py --tune so model-viewer's normal test matches the real occlusion; "
                       "surface_normal is the face normal where the placement ray hit")
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


if __name__ == "__main__":
    import sys
    if "--tune" in sys.argv[1:]:
        tune_hotspot_file()
    if "--tune-car" in sys.argv[1:]:
        tune_hotspot_file(os.path.join(HERE, "assets", "hotspots_amr23.json"),
                          os.path.join(HERE, "assets", "amr23.glb"), CAR_TARGET, CAR_RADIUS)
