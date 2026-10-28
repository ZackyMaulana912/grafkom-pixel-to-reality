"""Module 3 -- one scene file per model (decision K13).

The rasteriser, the ray tracer, worked_example.py and web/viewer.js all read
the same scenes/<name>.json, so a comparison between them can only differ in
how they render, never in what they render.

Usage:  sc = load_scene("scenes/mymodel.json");  M = model_matrix(sc) ...
"""
from __future__ import annotations

import json

import numpy as np

from transforms import look_at, perspective, rot_y, scale, translate


def load_scene(path):
    with open(path) as fh:
        return json.load(fh)


def model_matrix(sc):
    """M = T @ Ry @ S: scale first, then yaw, then move (read right to left)."""
    m = sc["model"]
    return translate(m["translate"]) @ rot_y(m["rot_y_deg"]) @ scale(m["scale"])


def view_matrix(sc):
    c = sc["camera"]
    return look_at(c["eye"], c["center"], c.get("up", (0, 1, 0)))


def projection_matrix(sc, w=None, h=None):
    c, f = sc["camera"], sc["frame"]
    w, h = w or f["w"], h or f["h"]
    return perspective(c["fovy_deg"], w / h, c["near"], c["far"])


def light(sc):
    return np.asarray(sc["light"]["dir"], float), float(sc["light"]["ambient"])
