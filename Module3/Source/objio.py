"""Module 3 -- a minimal Wavefront OBJ loader, from scratch (no library).

Reads  v x y z | vt u v | f a/b a/b a/b ... (also a//n and plain a); `g`, `vn`
and anything else are ignored. Polygons are split with a fan, which is only
correct for convex faces (make_mymodel.py splits its concave statue outline
itself, so no such face reaches this loader).

Two conventions are settled HERE, once, so no other file has to think about them:
  * UV origin: OBJ puts v = 0 at the bottom of the image, image rows start at
    the top, so v is flipped on load (Pitfall: UV origin flip).
  * Winding: front faces are counter-clockwise seen from outside. With
    enforce_ccw=True a mesh whose signed volume is negative is taken as wound
    inside out and every face is reversed (Pitfall: winding / backface drift;
    finding T13 -- the starter's temple is stored that way). The renderers load
    through raster3d.load_scene_mesh(), which turns this on; the default stays off so the
    evidence in diagnose_scene.py keeps showing the file as it is.
"""
from __future__ import annotations

import numpy as np


class Mesh:
    def __init__(self, positions, uvs, faces, face_uvs):
        self.positions = np.asarray(positions, float)          # (V,3)
        self.uvs = np.asarray(uvs, float) if len(uvs) else np.zeros((0, 2))
        self.faces = np.asarray(faces, np.int64)               # (F,3) position indices
        self.face_uvs = np.asarray(face_uvs, np.int64) if len(face_uvs) else None
        self.rewound = False

    @property
    def n_tris(self):
        return len(self.faces)

    def triangle_positions(self):
        return self.positions[self.faces]                      # (F,3,3)

    def triangle_uvs(self):
        if self.face_uvs is None:
            return np.zeros((len(self.faces), 3, 2))
        return self.uvs[self.face_uvs]                         # (F,3,2)

    def signed_volume(self):
        """Sum of tetrahedra (origin, triangle): > 0 when faces point outward."""
        t = self.triangle_positions()
        return float(np.einsum("ij,ij->i", t[:, 0], np.cross(t[:, 1], t[:, 2])).sum() / 6.0)

    def reversed(self):
        m = Mesh(self.positions, self.uvs, self.faces[:, ::-1].copy(),
                 [] if self.face_uvs is None else self.face_uvs[:, ::-1].copy())
        m.rewound = not self.rewound
        return m


def _index(tok, n_pos, n_uv):
    """'a/b/c' -> 0-based (position, uv or None); negative indices count from the end."""
    parts = (tok.split("/") + ["", ""])[:3]
    pi = int(parts[0])
    pi = pi - 1 if pi > 0 else n_pos + pi
    ui = None
    if parts[1]:
        u = int(parts[1])
        ui = u - 1 if u > 0 else n_uv + u
    return pi, ui


def load_obj(path, flip_v=True, enforce_ccw=False):
    positions, uvs, faces, face_uvs = [], [], [], []
    with open(path) as fh:
        for line in fh:
            if line.startswith("v "):
                positions.append([float(x) for x in line.split()[1:4]])
            elif line.startswith("vt "):
                u, v = (float(x) for x in line.split()[1:3])
                uvs.append([u, 1.0 - v if flip_v else v])
            elif line.startswith("f "):
                idx = [_index(t, len(positions), len(uvs)) for t in line.split()[1:]]
                for k in range(1, len(idx) - 1):               # fan
                    faces.append([idx[0][0], idx[k][0], idx[k + 1][0]])
                    if idx[0][1] is not None:
                        face_uvs.append([idx[0][1], idx[k][1], idx[k + 1][1]])
    mesh = Mesh(positions, uvs, faces, face_uvs)
    if enforce_ccw and mesh.signed_volume() < 0:
        mesh = mesh.reversed()
    return mesh


def save_obj(path, positions, uvs, faces, face_uvs=None):
    """Kept for make_model.py (the starter's fallback temple)."""
    with open(path, "w") as fh:
        fh.write("# Module 3 -- deterministic Pusaka3D temple (make_model.py)\n")
        for p in positions:
            fh.write(f"v {p[0]:.5f} {p[1]:.5f} {p[2]:.5f}\n")
        for t in uvs:
            fh.write(f"vt {t[0]:.5f} {t[1]:.5f}\n")
        for i, f in enumerate(faces):
            if face_uvs is not None:
                a, b, c = f
                ua, ub, uc = face_uvs[i]
                fh.write(f"f {a+1}/{ua+1} {b+1}/{ub+1} {c+1}/{uc+1}\n")
            else:
                fh.write(f"f {f[0]+1} {f[1]+1} {f[2]+1}\n")
