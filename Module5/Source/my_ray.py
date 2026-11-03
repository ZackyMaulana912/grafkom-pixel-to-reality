"""The ray through one pixel of my own phone photo (Lab 1 no 4).

Reads data/my_camera.json (iPhone 17 Pro, focal length from EXIF, my chosen
pixel), estimates the focal length in pixels and calls ray_generator.py for
the direction, so the by-hand numbers in docs/catatan/fase2-capture-ray.md
are checked against the same code the rest of the module uses.
"""
from __future__ import annotations

import json
import math
import os

import numpy as np

from ray_generator import pixel_to_camera_dir

HERE = os.path.dirname(os.path.abspath(__file__))
CAMERA_JSON = os.path.join(HERE, "data", "my_camera.json")
FRAME_35MM_DIAGONAL_MM = math.hypot(36.0, 24.0)


def load_camera(path=CAMERA_JSON):
    with open(path) as f:
        return json.load(f)


def focal_px_from_35mm(f35_mm, frame_w_px, frame_h_px):
    """35 mm equivalent focal length -> pixels, matched on the frame diagonal."""
    return f35_mm * math.hypot(frame_w_px, frame_h_px) / FRAME_35MM_DIAGONAL_MM


def my_ray(cam):
    """Returns (f_px, unnormalised camera-space direction, normalised direction)."""
    f = focal_px_from_35mm(cam["focal_length_35mm_equiv_mm"], *cam["sensor_frame_px"])
    (u, v), (cx, cy) = cam["pixel"], cam["principal_point_px"]
    d = pixel_to_camera_dir(u, v, f, f, cx, cy)
    return f, d, d / np.linalg.norm(d)


if __name__ == "__main__":
    cam = load_camera()
    f, d, n = my_ray(cam)
    (u, v), (cx, cy) = cam["pixel"], cam["principal_point_px"]
    print(f"{cam['device']}, {cam['image_width_px']}x{cam['image_height_px']} px, "
          f"{cam['focal_length_mm']} mm (35 mm equiv. {cam['focal_length_35mm_equiv_mm']} mm)")
    print(f"focal length (estimate)             = {f:.2f} px")
    print(f"pixel ({u}, {v}), principal point ({cx}, {cy})")
    print(f"unnormalised camera-space direction = ({d[0]:.5f}, {d[1]:.5f}, {d[2]:.5f})")
    print(f"normalised direction                = ({n[0]:.5f}, {n[1]:.5f}, {n[2]:.5f})")
    print(f"angle from the optical axis         = {math.degrees(math.acos(-n[2])):.2f} deg")
