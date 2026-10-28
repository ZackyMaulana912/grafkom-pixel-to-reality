"""Module 3 -- the transform stack, from scratch (NumPy only).

CONVENTIONS, pinned once for the whole codebase (never mix another in):
  * column vectors, pre-multiply: p' = M @ p
  * a chain "first A, then B" is p' = B @ A @ p (read right to left)
  * right-handed world and view space; the camera looks down -z,
    so a point in front of the camera has z < 0 and w_clip = -z > 0
  * NDC is [-1, 1]^3 with near at z = -1 and far at z = +1 (OpenGL style);
    the projection flips z, so NDC itself is left-handed
  * viewport: NDC x -> pixel columns; NDC y is flipped (screen y points down);
    pixel (x, y) is sampled at its centre (x + 0.5, y + 0.5), as in Module 2
  * front faces are counter-clockwise seen from outside (objio enforces it)
  * OBJ texture v is flipped once, in objio, so v = 0 is the top image row
  * every angle parameter ends in _deg; radians() is the only conversion

Reproduces:
  E1  (2,3,4) --T(1,0,-1)--> (3,3,3) --Ry(90)--> (3,3,-3);  divide d=2 -> (2,2)
  E2  camera +x by 1  ==  model -x by 1   (identical points)
  E3  perspective(.,.,1,9): z=-1 -> -1, z=-9 -> +1, z=-3 -> 0.5
"""
from __future__ import annotations

import numpy as np


def radians(angle_deg):
    return np.radians(angle_deg)


def translate(t):
    """Column 4 carries the model's origin to t; columns 1-3 stay the identity axes."""
    M = np.eye(4)
    M[:3, 3] = t
    return M


def scale(s):
    s = np.asarray(s, dtype=float)
    return np.diag([s[0], s[1], s[2], 1.0])


def rot_x(angle_deg):
    c, s = np.cos(radians(angle_deg)), np.sin(radians(angle_deg))
    return np.array([[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1.0]])


def rot_y(angle_deg):
    """Yaw. Column 1 = (cos, 0, -sin): where model +x points afterwards."""
    c, s = np.cos(radians(angle_deg)), np.sin(radians(angle_deg))
    return np.array([[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1.0]])


def rot_z(angle_deg):
    c, s = np.cos(radians(angle_deg)), np.sin(radians(angle_deg))
    return np.array([[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1.0]])


def perspective(fovy_deg, aspect, near, far):
    """Eye z = -near -> NDC -1, z = -far -> NDC +1. Row 4 makes w = -z."""
    f = 1.0 / np.tan(radians(fovy_deg) / 2.0)
    P = np.zeros((4, 4))
    P[0, 0] = f / aspect
    P[1, 1] = f
    P[2, 2] = (far + near) / (near - far)
    P[2, 3] = (2 * far * near) / (near - far)
    P[3, 2] = -1.0
    return P


def reverse_z_depth(inv_w, near, far):
    """Reverse-Z window depth: near -> 1, far -> 0, d = n (f - w) / ((f - n) w).
    Affine in 1/w, so it interpolates linearly across a triangle like NDC z."""
    return (near * far / (far - near)) * inv_w - near / (far - near)


def look_at(eye, center, up=(0, 1, 0)):
    """V = pose^-1 = R^T T(-eye). Rows 1-3 are the camera's right, up and back
    axes written in world space; column 4 is the world origin seen from the camera."""
    eye = np.asarray(eye, float)
    fwd = np.asarray(center, float) - eye
    fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, np.asarray(up, float))
    right /= np.linalg.norm(right)
    true_up = np.cross(right, fwd)
    V = np.eye(4)
    V[0, :3], V[1, :3], V[2, :3] = right, true_up, -fwd
    V[0, 3] = -right @ eye
    V[1, 3] = -true_up @ eye
    V[2, 3] = fwd @ eye
    return V


def to_homogeneous(verts):
    """(N,3) points -> (N,4) with w = 1."""
    verts = np.asarray(verts, float)
    return np.c_[verts, np.ones(len(verts))]


def project(P, V, M, verts):
    """verts (N,3) -> clip (N,4) and ndc (N,3). The only division is by w."""
    clip = (P @ V @ M @ to_homogeneous(verts).T).T
    return clip, clip[:, :3] / clip[:, 3:4]


def viewport(ndc, w, h):
    """NDC [-1,1] -> pixels with y down. Returns (N,3): x, y, NDC depth."""
    ndc = np.asarray(ndc, float)
    x = (ndc[:, 0] * 0.5 + 0.5) * w
    y = (1.0 - (ndc[:, 1] * 0.5 + 0.5)) * h
    return np.c_[x, y, ndc[:, 2]]


def perspective_divide_2d(p3, d):
    """Bare similar triangles (Example E1): a point in front of a pinhole at the
    origin projects to (d x / |z|, d y / |z|) on the image plane z = -d."""
    x, y, z = p3
    return np.array([d * x / abs(z), d * y / abs(z)])
