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
