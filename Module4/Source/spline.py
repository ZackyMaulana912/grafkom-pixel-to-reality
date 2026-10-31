"""Uniform Catmull-Rom spline through control points, from scratch.

A point on the segment P1 -> P2 is a weighted sum of the four neighbours
P0..P3; the weights below are the rows of the Catmull-Rom basis matrix applied to
(1, t, t^2, t^3). They always add up to 1, give (0, 1, 0, 0) at t = 0 and
(0, 0, 1, 0) at t = 1 (so the curve passes through P1 and P2), and give the
tangent (P2 - P0) / 2 at P1, shared by both segments that meet there (C1).

Points are tuples of any length (2D or 3D). The open path sampler duplicates the
first and last control point so the curve starts and ends exactly on them; the
closed sampler takes the neighbours cyclically instead, so the last segment runs
back to the first point with the same C1 tangent rule at every point.
"""
from __future__ import annotations

import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def catmull_rom_weights(t):
    """Weights of P0, P1, P2, P3 at parameter t in [0, 1]."""
    t2, t3 = t * t, t * t * t
    return (
        0.5 * (-t + 2.0 * t2 - t3),
        0.5 * (2.0 - 5.0 * t2 + 3.0 * t3),
        0.5 * (t + 4.0 * t2 - 3.0 * t3),
        0.5 * (-t2 + t3),
    )


def catmull_rom_weight_slopes(t):
    """d/dt of catmull_rom_weights(t): the weights of the tangent q'(t)."""
    t2 = t * t
    return (
        0.5 * (-1.0 + 4.0 * t - 3.0 * t2),
        0.5 * (-10.0 * t + 9.0 * t2),
        0.5 * (1.0 + 8.0 * t - 9.0 * t2),
        0.5 * (-2.0 * t + 3.0 * t2),
    )


def catmull_rom_tangent(p0, p1, p2, p3, t):
    """Tangent q'(t) on the segment between p1 and p2 (per unit t)."""
    w = catmull_rom_weight_slopes(t)
    return tuple(w[0] * a + w[1] * b + w[2] * c + w[3] * d for a, b, c, d in zip(p0, p1, p2, p3))


def catmull_rom_point(p0, p1, p2, p3, t):
    """Point at t on the segment between p1 and p2."""
    w = catmull_rom_weights(t)
    return tuple(w[0] * a + w[1] * b + w[2] * c + w[3] * d for a, b, c, d in zip(p0, p1, p2, p3))


def sample_path(control_points, samples_per_segment=20):
    """Sample the whole spline through >= 2 control points.

    Every segment is sampled at t = 0, 1/n, ..., (n-1)/n and the very last point is
    added once at the end, so k control points give (k - 1) * n + 1 samples. t steps
    are uniform per segment, which does NOT make the samples equally spaced in
    distance (see sample_spacing).
    """
    pts = [tuple(control_points[0])] + [tuple(p) for p in control_points] + [tuple(control_points[-1])]
    out = []
    for seg in range(len(pts) - 3):
        p0, p1, p2, p3 = pts[seg:seg + 4]
        for i in range(samples_per_segment):
            out.append(catmull_rom_point(p0, p1, p2, p3, i / samples_per_segment))
    out.append(pts[-2])
    return out


def closed_segments(control_points):
    """(p0, p1, p2, p3) of every segment of the closed loop, neighbours taken cyclically."""
    pts = [tuple(p) for p in control_points]
    n = len(pts)
    return [(pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]) for i in range(n)]


def sample_closed_path(control_points, samples_per_segment=20):
    """Sample a closed Catmull-Rom loop through >= 3 control points.

    k control points give k segments and k * n samples; sample i * n is exactly
    control point i, and the loop closes because the sample after the last one is
    control point 0 again (it is not repeated in the list).
    """
    out = []
    for p0, p1, p2, p3 in closed_segments(control_points):
        for i in range(samples_per_segment):
            out.append(catmull_rom_point(p0, p1, p2, p3, i / samples_per_segment))
    return out


def sample_spacing(samples):
    """Distances between consecutive samples (equal t steps vs actual distance)."""
    return [math.dist(a, b) for a, b in zip(samples, samples[1:])]


def load_path(path):
    """Control points of a path JSON file ({"control_points": [[x, y, z], ...]})."""
    with open(path) as f:
        return [tuple(p) for p in json.load(f)["control_points"]]


def load_camera_path(path=None):
    """The course's 5-point temple flyover (data/camera_path.json)."""
    return load_path(path or os.path.join(HERE, "data", "camera_path.json"))


def load_my_path(path=None):
    """My 6-point path around the horse statue (data/my_path.json)."""
    return load_path(path or os.path.join(HERE, "data", "my_path.json"))


def running_example():
    """Module 4 example E3: P0=(0,0) P1=(2,0) P2=(4,2) P3=(6,2), segment P1-P2 at t=0.5."""
    return catmull_rom_point((0.0, 0.0), (2.0, 0.0), (4.0, 2.0), (6.0, 2.0), 0.5)


def _fmt(p):
    return "(" + ", ".join(f"{c:.3f}" for c in p) + ")"


if __name__ == "__main__":
    q = running_example()
    print(f"q(0.5) on segment P1->P2 = ({q[0]:.3f}, {q[1]:.3f})")

    for name, cps in (("camera_path.json", load_camera_path()), ("my_path.json", load_my_path())):
        path = sample_path(cps, samples_per_segment=10)
        gaps = sample_spacing(path)
        print(f"{name}: {len(cps)} control points -> {len(path)} sampled points")
        print(f"  path start = {_fmt(path[0])}")
        print(f"  path end   = {_fmt(path[-1])}")
        print(f"  sample spacing min {min(gaps):.3f}, max {max(gaps):.3f} (equal t steps, unequal distance)")
    loop = sample_closed_path(load_my_path(), samples_per_segment=10)
    gaps = sample_spacing(loop + [loop[0]])
    print(f"my_path.json closed loop: {len(loop)} samples, spacing min {min(gaps):.3f}, max {max(gaps):.3f}")
    print("my_path.json samples (x, y, z) in m:")
    for i, p in enumerate(sample_path(load_my_path(), samples_per_segment=10)):
        print(f"  {i:2d} {_fmt(p)}")
