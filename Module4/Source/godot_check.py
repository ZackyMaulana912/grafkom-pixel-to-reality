"""Compare numbers printed by Godot with the Python primitives (Lab 2 no 3, T4).

Godot is run headless and its log is piped in:
  $GODOT --headless --path godot_project --quit-after 30 | .venv/bin/python godot_check.py
  $GODOT --headless --path godot_project --script res://tools/cek_basis.gd | .venv/bin/python godot_check.py

Two tolerances, because Godot has two kinds of numbers:
- The arm is computed with GDScript floats, which are 64-bit like Python's, and
  printed with 12 decimals, so it must agree to TOL_FLOAT64 = 1e-9.
- Basis (and Vector2/Vector3) components are stored as 32-bit floats. A matrix entry
  is at most 1 in size, so storing it rounds by at most 2^-24 ~ 6e-8; TOL_BASIS = 1e-5
  leaves a wide margin above that and is still far below any real difference (the
  T4 pairs that are NOT locked differ by more than 0.02).
"""
from __future__ import annotations

import math
import sys

from fk import Bone, forward_kinematics
from ik import solve_two_bone_ik
from quaternion import euler_to_matrix, mat_max_diff

TOL_FLOAT64 = 1e-9
TOL_BASIS = 1e-5
GODOT_ORDER = {0: "XYZ", 1: "XZY", 2: "YXZ", 3: "YZX", 4: "ZXY", 5: "ZYX"}  # @GlobalScope.EulerOrder
# Godot's intrinsic order X, Y, Z means rotating about local X first, i.e. M = Rx Ry Rz,
# which is exactly the left-to-right product order string used by quaternion.euler_to_matrix.


def _fields(line):
    out = {}
    for part in line.split()[1:]:
        key, _, value = part.partition("=")
        out[key] = value
    return out


def _nums(text):
    return [float(v) for v in text.split(",")]


def check_line(line):
    """Return (label, max difference to Python, tolerance) for one Godot log line, or None."""
    tag = line.split(" ", 1)[0]
    f = _fields(line)
    if tag == "ARM_FK":
        a1, a2 = _nums(f["local"])
        positions, _ = forward_kinematics([Bone(3.0, a1), Bone(2.0, a2)])
        godot = _nums(f["elbow"]) + _nums(f["hand"])
        python = [*positions[1], *positions[2]]
        diff = max(abs(g - p) for g, p in zip(godot, python))
        return f"FK lokal {a1:g}/{a2:g}: siku dan tangan", diff, TOL_FLOAT64
    if tag == "ARM_IK":
        target = tuple(_nums(f["target"]))
        t1, t2 = solve_two_bone_ik(3.0, 2.0, target)
        g1, g2 = _nums(f["theta"])
        hand = _nums(f["hand"])
        diff = max(abs(g1 - t1), abs(g2 - t2), math.dist(hand, target))
        return f"IK target {target}: theta1, theta2, tangan vs target", diff, TOL_FLOAT64
    if tag == "ARM_REACH":
        tx, ty = _nums(f["target"])
        python = abs(3.0 - 2.0) <= math.hypot(tx, ty) <= 5.0
        same = (f["reachable"] == "true") == python
        return f"jangkauan ({tx:g}, {ty:g}) = {f['reachable']}", 0.0 if same else 1.0, TOL_FLOAT64
    if tag == "BASIS":
        order = GODOT_ORDER[int(f["order"])]
        p, y, r = _nums(f["deg"])
        m = _nums(f["m"])
        godot = [m[0:3], m[3:6], m[6:9]]
        diff = mat_max_diff(godot, euler_to_matrix(p, y, r, order))
        return f"Basis {order} ({p:g}, {y:g}, {r:g}) vs euler_to_matrix", diff, TOL_BASIS
    return None


def main(lines):
    results = [res for res in (check_line(line.strip()) for line in lines) if res]
    for label, diff, tol in results:
        print(f"[{'ok' if diff <= tol else 'BEDA'}] {label}: selisih {diff:.2e} (toleransi {tol:g})")
    bad = sum(diff > tol for _, diff, tol in results)
    print(f"{len(results)} baris dibandingkan, {bad} di atas toleransinya")
    return 1 if bad or not results else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.stdin))
