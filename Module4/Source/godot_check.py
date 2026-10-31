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
  T4 pairs that are NOT locked differ by more than 0.02). Curve points and skeleton
  joints are Vector3 too (values up to 8 m, rounding below 1e-6 m), so they use
  TOL_BASIS as well, in metres.
"""
from __future__ import annotations

import math
import sys

from fk import Bone, forward_kinematics
from ik import solve_two_bone_ik
from my_chain import load_chain
from quaternion import euler_to_matrix, mat_max_diff
from spline import load_camera_path, load_my_path, sample_closed_path, sample_path

TOL_FLOAT64 = 1e-9
TOL_BASIS = 1e-5
# Angles read back from 32-bit quaternions with acos: near w = 1, acos turns a rounding of
# ~6e-8 in w into ~3e-4 rad, so single angles are compared to 0.01 deg and sums of 120 steps to 0.2 deg.
TOL_ANGLE_DEG = 0.01
TOL_PATH_DEG = 0.2


def _matrix_angle_deg(m):
    trace = m[0][0] + m[1][1] + m[2][2]
    return math.degrees(math.acos(max(-1.0, min(1.0, (trace - 1.0) / 2.0))))
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
    if tag == "CURVE":
        pts = [tuple(float(v) for v in p.split(",")) for p in f["points"].split(";")]
        cps = load_my_path() if f["file"] == "my_path.json" else load_camera_path()
        if f.get("closed") == "true":
            want = sample_closed_path(cps, samples_per_segment=10)
            want.append(want[0])  # Godot repeats point 0 to close the polyline
        else:
            want = sample_path(cps, samples_per_segment=10)
        if len(pts) != len(want):
            return f"kurva {f['file']}: {len(pts)} titik, Python {len(want)}", 1.0, TOL_BASIS
        diff = max(math.dist(a, b) for a, b in zip(pts, want))
        kind = "tertutup" if f.get("closed") == "true" else "terbuka"
        return f"kurva {f['file']} ({kind}): {len(pts)} titik vs spline.py", diff, TOL_BASIS
    if tag == "MYARM":
        joints = [tuple(float(v) for v in p.split(",")) for p in f["joints"].split(";")]
        bones, data = load_chain()
        k = 0.01 if data["unit"] == "cm" else 1.0
        positions, _ = forward_kinematics([Bone(b.length * k, b.local_angle_deg) for b in bones])
        if len(joints) != len(positions):
            return f"rig lengan saya: {len(joints)} sendi, Python {len(positions)}", 1.0, TOL_BASIS
        diff = max(math.dist(j, (p[0], p[1], 0.0)) for j, p in zip(joints, positions))
        return f"rig lengan saya (Skeleton3D, {len(joints)} sendi) vs fk.py", diff, TOL_BASIS
    if tag == "WALKER":
        slide, rise = float(f["max_abs_slide"]), float(f["max_rise"])
        if f["mode"] == "root_motion":
            # the planted foot must not move at all, up to 32-bit rounding of positions near 6 m
            ok = slide <= TOL_BASIS and rise <= TOL_BASIS
            return f"walker root motion: kaki menapak geser {slide:.1e} m, naik-turun {rise:.1e} m", \
                0.0 if ok else 1.0, TOL_BASIS
        return f"walker kecepatan tetap {f['speed']} m/s: geser {slide:.3f} m (pembanding, tidak dinilai)", 0.0, \
            TOL_BASIS
    if tag == "KNIGHT_WALK":
        slide = float(f["max_slide_root_motion"])
        return f"Knight root motion: kaki menapak geser {slide:.1e} m (kecepatan tetap: " \
               f"{float(f['max_slide_constant']):.4f} m)", 0.0 if slide <= TOL_BASIS else 1.0, TOL_BASIS
    if tag == "RIG_LOCK":
        same, other, y = (float(f[k]) for k in ("yaw_minus_roll_pairs_max_diff", "yaw_plus_roll_pair_diff",
                                                "arm_dir_max_abs_y"))
        ok = same <= TOL_BASIS and other > 0.01 and y <= TOL_BASIS
        return f"bahu di pitch 90: yaw-roll tetap {same:.1e} m, yaw+roll {other:.3f} m, arah lengan y {y:.1e}", \
            0.0 if ok else 1.0, TOL_BASIS
    if tag == "RIG_INTERP":
        t = float(f["t"])
        euler = _matrix_angle_deg(euler_to_matrix(90 * t, 0, 90 * t, "YXZ"))
        diff = max(abs(float(f["euler_angle"]) - euler), abs(float(f["slerp_angle"]) - 120 * t))
        return f"interpolasi t={t:g}: Euler {euler:.4f} deg, slerp {120 * t:.4f} deg (Python)", diff, TOL_ANGLE_DEG
    if tag == "RIG_PATH":
        # Rx(a) Rz(a) turns at |x + Rx(a) z| = sqrt(2) times da/dt, so the Euler path is 90 sqrt(2) deg long
        diff = max(abs(float(f["euler_path_deg"]) - 90 * math.sqrt(2)), abs(float(f["slerp_path_deg"]) - 120.0))
        return f"panjang jalur: Euler {float(f['euler_path_deg']):.3f} vs 90 sqrt(2) = {90 * math.sqrt(2):.3f}, " \
               f"slerp {float(f['slerp_path_deg']):.3f} vs 120", diff, TOL_PATH_DEG
    if tag == "RIG_LIFT":
        y = _nums(f["dir_after"])[1]
        return f"angkat 10 deg dengan quaternion dari B: arah lengan y = {y:.6f}", \
            abs(abs(y) - math.sin(math.radians(10))), TOL_BASIS
    if tag == "GIMBAL":
        euler, quat = float(f["euler_cube_max_change"]), float(f["quat_cube_max_change"])
        # the red cube must stand still (float32 rounding only) while the blue one really turns
        ok = euler <= TOL_BASIS and quat > 0.1
        return f"kubus Euler diam ({euler:.1e}), kubus quaternion bergerak ({quat:.3f})", 0.0 if ok else 1.0, TOL_BASIS
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
