"""Pinhole ray generation: Module 3's projection run backwards (NumPy only).

Module 3 sent a camera-space point (x, y, z) to the pixel
    u = cx + f x / (-z),   v = cy - f y / (-z).
Every point t * (x, y, z) with t > 0 lands on the same pixel, so a pixel only
fixes a direction; the ray through it is origin + t * direction.

Conventions for the whole module (fixed here once; nerf_toy.py and my_ray.py
use these functions instead of their own copies):
- Camera space is OpenGL / Module 3: +x right, +y up, the camera looks down -z,
  and the image plane sits one focal length in front, at z = -1 in focal units.
- (u, v) are continuous image coordinates in pixels: u grows to the right, v
  grows DOWNWARD (row order), so the y term is negated. Pixel (col, row) covers
  [col, col + 1) x [row, row + 1); its centre is (col + 0.5, row + 0.5).
- pixel_to_camera_dir takes (u, v) exactly as given. generate_rays shoots one
  ray through the centre of every pixel, i.e. it calls the same function with
  (col + 0.5, row + 0.5). That half pixel is the only difference between them.
- cam_to_world is a 3 x 3 rotation whose columns are the camera's +x, +y, +z
  axes in world space; world directions are normalised before use.
- Focal lengths and the principal point are in pixels.
"""
from __future__ import annotations

import numpy as np


def pixel_to_camera_dir(u, v, fx, fy, cx, cy):
    """Unnormalised camera-space direction through image point (u, v).

    Works on scalars or on arrays of equal shape; the last axis of the result is xyz.
    """
    u = np.asarray(u, dtype=float)
    v = np.asarray(v, dtype=float)
    x = (u - cx) / fx
    y = -(v - cy) / fy  # rows grow down, camera y grows up
    return np.stack([x, y, -np.ones_like(x)], axis=-1)


def camera_to_world_ray(dir_cam, cam_to_world, cam_pos):
    """Rotate a camera-space direction into world space; the camera position is the origin."""
    return np.array(cam_pos, dtype=float), cam_to_world @ dir_cam


def focal_from_fov(width, fov_deg):
    """Focal length in pixels for a horizontal field of view across `width` pixels."""
    return 0.5 * width / np.tan(np.radians(fov_deg) / 2.0)


def generate_rays(width, height, fx, fy, cx, cy, cam_to_world, cam_pos):
    """One ray per pixel centre: (origins, directions), each (height, width, 3),
    directions in world space and normalised."""
    cols, rows = np.meshgrid(np.arange(width) + 0.5, np.arange(height) + 0.5)
    dirs = pixel_to_camera_dir(cols, rows, fx, fy, cx, cy) @ np.asarray(cam_to_world).T
    dirs = dirs / np.linalg.norm(dirs, axis=-1, keepdims=True)
    return np.broadcast_to(np.asarray(cam_pos, dtype=float), dirs.shape), dirs


def running_example():
    """E1: f = 100 px, principal point (320, 240), image point (400, 240), identity pose."""
    dir_cam = pixel_to_camera_dir(400.0, 240.0, 100.0, 100.0, 320.0, 240.0)
    return dir_cam, dir_cam / np.linalg.norm(dir_cam)


if __name__ == "__main__":
    dir_cam, norm_dir = running_example()
    print("pixel (400, 240), f=100, principal point (320, 240)")
    print(f"unnormalised camera-space direction = ({dir_cam[0]:.3f}, {dir_cam[1]:.3f}, {dir_cam[2]:.3f})")
    print(f"normalised direction                = ({norm_dir[0]:.3f}, {norm_dir[1]:.3f}, {norm_dir[2]:.3f})")
