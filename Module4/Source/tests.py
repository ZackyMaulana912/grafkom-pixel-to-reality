"""Module 4 test suite -- every from-scratch example checked against its
hand-worked number. Run: python tests.py -> ALL CHECKS PASSED (N ok)
"""
from __future__ import annotations

import ast
import json
import math
import os
import random

from fk import Bone, bone_matrices, forward_kinematics, running_example as fk_running_example
from ik import fk_error, solve_two_bone_ik, UnreachableTarget, running_example as ik_running_example
from spline import (
    catmull_rom_weights, sample_path, load_camera_path, load_my_path, load_path,
    running_example as spline_running_example,
)
from quaternion import (
    quat_from_axis_angle, slerp, quat_to_axis_angle, gimbal_lock_demo,
    running_example_slerp, euler_to_matrix, mat_max_diff, quat_mul, quat_norm, quat_rotate,
    quat_to_matrix, axis_matrix, lock_rule,
)
from foot_slide_bug import (
    diagnose, matched_speed, root_motion_distance, animation_authored_distance, REPORTED_SPEED,
    STRIDE_PER_CYCLE, CYCLE_RATE, SWAY, STRIDE_CHANGE, walk, constant_speed, root_motion,
)
from my_chain import load_chain, angles_from_photo
from godot_check import check_line

_checks = 0


def check(name, got, want, tol=1e-6):
    global _checks
    ok = abs(got - want) <= tol if isinstance(want, (int, float)) else got == want
    status = "ok" if ok else "FAIL"
    print(f"[{status}] {name}: got={got!r} want={want!r}")
    assert ok, f"{name}: got {got!r}, want {want!r}"
    _checks += 1


def check_point(name, got, want, tol=1e-3):
    for g, w in zip(got, want):
        check(f"{name} ({w})", g, w, tol)


def test_fk():
    positions, angles = fk_running_example()
    shoulder, elbow, hand = positions
    check_point("E1 fk shoulder", shoulder, (0.0, 0.0))
    check_point("E1 fk elbow", elbow, (2.598, 1.500))
    check_point("E1 fk hand", hand, (2.598, 3.500))
    check("E1 fk elbow global angle", angles[0], 30.0)
    check("E1 fk hand global angle", angles[1], 90.0)


def test_my_chain():
    """My arm (data/my_chain.json) against the hand calculation in docs/catatan/fase2-rantai-saya.md."""
    bones, data = load_chain()
    positions, angles = forward_kinematics(bones)
    check_point("my chain elbow (hand calc)", positions[1], (28.970, -1.316))
    check_point("my chain wrist (hand calc)", positions[2], (32.807, 22.376))
    check_point("my chain fingertip (hand calc)", positions[3], (26.860, 41.471))
    check("my chain fingertip global angle", angles[2], 107.3)
    two, _ = forward_kinematics(bones[:2])
    check_point("my 2-bone chain ends at the wrist", two[-1], positions[2], tol=1e-12)
    t1, t2 = solve_two_bone_ik(bones[0].length, bones[1].length, positions[2])
    check("IK of my measured wrist gives back the shoulder angle", t1, bones[0].local_angle_deg, tol=1e-9)
    check("IK of my measured wrist gives back the elbow angle", t2, bones[1].local_angle_deg, tol=1e-9)
    # the JSON angles are the photo angles rounded to 0.1 deg
    _, from_photo = angles_from_photo(data)
    for i, (b, a) in enumerate(zip(bones, from_photo)):
        check(f"my chain bone {i + 1} angle matches the photo", b.local_angle_deg, a, tol=0.05)


def test_ik():
    theta1, theta2, hand, target = ik_running_example()
    check("E2 ik theta1", theta1, -13.18, tol=0.01)
    check("E2 ik theta2", theta2, 70.53, tol=0.01)
    check_point("E2 ik FK-of-solution", hand, target, tol=1e-9)

    # Unreachable target must raise, not silently clamp.
    try:
        solve_two_bone_ik(1.0, 1.0, (10.0, 0.0))
    except UnreachableTarget:
        pass
    else:
        raise AssertionError("expected UnreachableTarget for a target outside [0,2]")
    print("[ok] unreachable target correctly raises UnreachableTarget")
    global _checks
    _checks += 1


def test_spline():
    q = spline_running_example()
    check_point("E3 catmull-rom q(0.5)", q, (3.0, 1.0))

    cps = load_camera_path()
    check("camera_path.json control point count", len(cps), 5)
    path = sample_path(cps, samples_per_segment=10)
    check_point("camera path starts at first control point", path[0], cps[0], tol=1e-9)
    check_point("camera path ends at last control point", path[-1], cps[-1], tol=1e-9)


def test_quaternion():
    q = running_example_slerp()
    check_point("E4 slerp(id, yaw90, 0.4)", q, (0.9511, 0.0, 0.3090, 0.0), tol=1e-3)
    axis, angle = quat_to_axis_angle(q)
    check("E4 slerp result angle", angle, 36.0, tol=1e-2)

    # slerp at the endpoints must return the endpoints exactly.
    identity = (1.0, 0.0, 0.0, 0.0)
    yaw90 = quat_from_axis_angle((0, 1, 0), 90.0)
    check_point("slerp t=0 -> q0", slerp(identity, yaw90, 0.0), identity, tol=1e-9)
    check_point("slerp t=1 -> q1", slerp(identity, yaw90, 1.0), yaw90, tol=1e-9)

    d12, d13 = gimbal_lock_demo()
    check("gimbal lock: pitch/roll trade-off invisible (pair 1)", d12, 0.0, tol=1e-12)
    check("gimbal lock: pitch/roll trade-off invisible (pair 2)", d13, 0.0, tol=1e-12)


HERE = os.path.dirname(os.path.abspath(__file__))
FROM_SCRATCH = ("fk.py", "ik.py", "spline.py", "quaternion.py", "foot_slide_bug.py", "my_chain.py",
                "godot_check.py")
ALLOWED_IMPORTS = {"__future__", "math", "json", "dataclasses", "os", "argparse", "sys", "fk", "ik", "spline",
                   "quaternion"}


def test_stdlib_only():
    """The from-scratch files may import only the standard library and each other (K2)."""
    for name in FROM_SCRATCH:
        tree = ast.parse(open(os.path.join(HERE, name)).read(), name)
        found = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom):
                found.add((node.module or "").split(".")[0])
        check(f"{name} imports only {sorted(ALLOWED_IMPORTS & found)}", sorted(found - ALLOWED_IMPORTS), [])


def test_fk_matrices():
    """Positions from the matrix product agree with the angle-sum definition."""
    rnd = random.Random(1)
    worst_pos = worst_ang = 0.0
    for _ in range(500):
        bones = [Bone(rnd.uniform(0.1, 5.0), rnd.uniform(-180.0, 180.0)) for _ in range(rnd.randint(1, 6))]
        positions, angles = forward_kinematics(bones)
        x = y = total = 0.0
        for bone, m, p, a in zip(bones, bone_matrices(bones), positions[1:], angles):
            total += bone.local_angle_deg
            x += bone.length * math.cos(math.radians(total))
            y += bone.length * math.sin(math.radians(total))
            worst_pos = max(worst_pos, math.hypot(p[0] - x, p[1] - y))
            diff = (math.degrees(math.atan2(m[1][0], m[0][0])) - a + 180.0) % 360.0 - 180.0
            worst_ang = max(worst_ang, abs(diff))
    check("fk matrix product = angle sum (positions, 500 random chains)", worst_pos, 0.0, tol=1e-9)
    check("fk matrix rotation = summed global angle (deg)", worst_ang, 0.0, tol=1e-9)


def test_ik_more():
    """Both reach limits, and IK -> FK lands on the target everywhere, also right at the limits."""
    for target in ((0.5, 0.0), (0.999, 0.0), (5.001, 0.0), (0.0, -6.0)):
        try:
            solve_two_bone_ik(3.0, 2.0, target)
        except UnreachableTarget:
            pass
        else:
            raise AssertionError(f"expected UnreachableTarget for {target}")
    print("[ok] inner and outer limits both raise UnreachableTarget (3, 2): d = 0.5, 0.999, 5.001, 6")
    global _checks
    _checks += 1
    check("arm fully straight at d = l1 + l2: theta2", solve_two_bone_ik(3.0, 2.0, (5.0, 0.0))[1], 0.0, tol=1e-9)
    check("arm fully folded at d = |l1 - l2|: theta2", solve_two_bone_ik(3.0, 2.0, (1.0, 0.0))[1], 180.0,
          tol=1e-9)
    rnd = random.Random(7)
    worst = 0.0
    for _ in range(20000):
        l1, l2 = rnd.uniform(0.2, 4.0), rnd.uniform(0.2, 4.0)
        lo, hi = abs(l1 - l2), l1 + l2
        d = rnd.choice((rnd.uniform(lo, hi), hi * (1 - 1e-12), lo + (hi - lo) * 1e-12))
        a = rnd.uniform(-math.pi, math.pi)
        target = (d * math.cos(a), d * math.sin(a))
        try:
            t1, t2 = solve_two_bone_ik(l1, l2, target)
        except UnreachableTarget:
            continue  # d rounded just past a limit when turned into x, y
        worst = max(worst, fk_error(l1, l2, t1, t2, target)[0])
    check("ik -> fk worst error over 20000 targets incl. near the limits", worst, 0.0, tol=1e-9)


def test_my_path():
    """My camera path: 6 points -> 51 samples, passing every control point at t = 0 of its segment."""
    cps = load_my_path()
    check("my_path.json control point count", len(cps), 6)
    path = sample_path(cps, samples_per_segment=10)
    check("my_path.json sample count", len(path), 51)
    for i, cp in enumerate(cps):
        check_point(f"my path passes control point {i}", path[10 * i], cp, tol=1e-12)
    # Module 3 room: left wall at x = -1.0, cabinet front at x = 0.6, end walls at z = -2.0 and 2.0
    dense = sample_path(cps, samples_per_segment=100)
    clearance = min(min(p[0] + 1.0, 0.6 - p[0], p[2] + 2.0, 2.0 - p[2]) for p in dense)
    check("my path keeps >= 0.2 m from the walls and the cabinet", clearance >= 0.2, True)
    centre = json.load(open(os.path.join(HERE, "data", "my_path.json")))["centre"]
    r = [math.hypot(p[0] - centre[0], p[2] - centre[2]) for p in dense]
    print(f"     (clearance {clearance:.3f} m, distance to the statue {min(r):.3f} .. {max(r):.4f} m)")
    for t in (0.0, 0.3, 0.5, 1.0):
        check(f"catmull-rom weights sum to 1 at t={t}", sum(catmull_rom_weights(t)), 1.0, tol=1e-12)


def test_camera_path_copies():
    """Godot cannot read res://../, so it has its own copy: control points must stay identical (K11)."""
    a = load_camera_path()
    b = load_path(os.path.join(HERE, "godot_project", "data", "camera_path.json"))
    check("data/ and godot_project/data/ camera_path.json control points identical", a == b, True)


def test_euler_orders():
    """The locked axis is the middle one of each order (derivation in docs/catatan/fase3-primitif.md)."""
    xzy = gimbal_lock_demo("XZY")
    check("XZY at roll = 90: pitch - yaw kept, pair 1", xzy[0], 0.0, tol=1e-12)
    check("XZY at roll = 90: pitch - yaw kept, pair 2", xzy[1], 0.0, tol=1e-12)
    m = lambda p, y, r: euler_to_matrix(p, y, r, "XZY")  # noqa: E731
    check("XZY at yaw = 90 is NOT locked (pitch - roll kept)", mat_max_diff(m(20, 90, 10), m(10, 90, 0)) > 0.1, True)
    yxz = gimbal_lock_demo("YXZ")
    check("Godot default YXZ at pitch = 90: yaw - roll kept", max(yxz), 0.0, tol=1e-12)
    g = lambda p, y, r: euler_to_matrix(p, y, r, "YXZ")  # noqa: E731
    check("YXZ at yaw = 90 is NOT locked (the starter Godot demo)", mat_max_diff(g(20, 90, 10), g(10, 90, 0)) > 0.1,
          True)
    check("lock_rule ZYX", lock_rule("ZYX"), ("Y", "Z", "X", -1))
    check("lock_rule XZY", lock_rule("XZY"), ("Z", "X", "Y", -1))
    check("lock_rule YXZ", lock_rule("YXZ"), ("X", "Y", "Z", -1))


def test_quaternion_algebra():
    """Product composes rotations, rotation matches the axis matrices, norm scales the result."""
    q = quat_mul(quat_from_axis_angle((0, 0, 1), 30.0), quat_from_axis_angle((0, 0, 1), 60.0))
    check_point("q(z,30) * q(z,60) = q(z,90)", q, quat_from_axis_angle((0, 0, 1), 90.0), tol=1e-12)
    for axis, v in (("X", (1, 0, 0)), ("Y", (0, 1, 0)), ("Z", (0, 0, 1))):
        check(f"quat_to_matrix = R{axis.lower()}(37)", mat_max_diff(quat_to_matrix(quat_from_axis_angle(v, 37.0)),
                                                                   axis_matrix(axis, 37.0)), 0.0, tol=1e-12)
    big = tuple(1.01 * c for c in quat_from_axis_angle((0, 0, 1), 30.0))
    check("|q| = 1.01 scales a rotated unit vector by 1.0201", math.hypot(*quat_rotate(big, (1.0, 0.0, 0.0))),
          1.0201, tol=1e-12)
    check("slerp result stays unit length", quat_norm(slerp((1.0, 0.0, 0.0, 0.0),
                                                           quat_from_axis_angle((1, 2, 3), 170.0), 0.37)), 1.0,
          tol=1e-12)


def test_godot_check_parser():
    """godot_check.py accepts Godot lines that match Python and flags ones that do not."""
    (_, elbow, hand), _ = forward_kinematics([Bone(3.0, 30.0), Bone(2.0, 60.0)])
    good = f"ARM_FK local=30,60 elbow={elbow[0]!r},{elbow[1]!r} hand={hand[0]!r},{hand[1]!r}"
    _, diff, tol = check_line(good)
    check("godot_check: matching FK line passes", diff <= tol, True)
    bad = f"ARM_FK local=30,60 elbow={elbow[0] + 1e-6!r},{elbow[1]!r} hand={hand[0]!r},{hand[1]!r}"
    _, diff, tol = check_line(bad)
    check("godot_check: FK line off by 1e-6 is above the 1e-9 tolerance", diff > tol, True)
    m = euler_to_matrix(20, 90, 10, "YXZ")
    basis = "BASIS x order=2 deg=20,90,10 m=" + ",".join(repr(v) for row in m for v in row)
    _, diff, tol = check_line(basis)
    check("godot_check: Godot order 2 is YXZ = Ry Rx Rz", diff <= tol, True)
    swapped = "BASIS x order=5 deg=20,90,10 m=" + ",".join(repr(v) for row in m for v in row)
    _, diff, tol = check_line(swapped)
    check("godot_check: the same matrix read as order 5 (ZYX) is flagged", diff > tol, True)
    _, diff, tol = check_line("GIMBAL euler_cube_max_change=0.000000060 quat_cube_max_change=0.99")
    check("godot_check: still Euler cube + moving quaternion cube passes", diff <= tol, True)
    _, diff, tol = check_line("GIMBAL euler_cube_max_change=0.08 quat_cube_max_change=0.99")
    check("godot_check: a moving Euler cube (the starter demo) is flagged", diff > tol, True)


def test_foot_slide_bug():
    """Before vs after the fix; the right speed is computed from the clip's constants, not typed in (T6)."""
    v = matched_speed()
    check("matched speed = STRIDE_PER_CYCLE x CYCLE_RATE", v, STRIDE_PER_CYCLE * CYCLE_RATE, tol=0.0)
    buggy = diagnose(REPORTED_SPEED, dt=0.5)
    check("foot-slide bug, reported speed, t=5s", buggy[-1][1], (REPORTED_SPEED - v) * 5.0, tol=1e-12)
    worst = max(abs(g - (REPORTED_SPEED - v) * t) for t, g in buggy)
    check("buggy gap = (scripted_speed - stride x rate) t at every sample", worst, 0.0, tol=1e-12)
    diffs = [b[1] - a[1] for a, b in zip(buggy, buggy[1:])]
    check("buggy gap grows at every sample", all(d > 0 for d in diffs), True)
    for dt in (0.5, 0.1, 1.0 / 60.0):
        after = diagnose(v, dt=dt)
        check(f"after the fix the gap is exactly 0.0 at all {len(after)} samples (dt={dt:.4f})",
              all(g == 0.0 for _, g in after), True)
    rnd = random.Random(3)
    clips = [(rnd.uniform(0.1, 3.0), rnd.uniform(0.1, 3.0), rnd.uniform(0.0, 100.0)) for _ in range(1000)]
    check("fixed gap is exactly 0.0 for 1000 random clips (stride, rate, t)",
          all(root_motion_distance(matched_speed(s, r), t) - animation_authored_distance(t, s, r) == 0.0
              for s, r, t in clips), True)


def test_pitfall_c_root_motion():
    """Pitfall (c): speed read from the baked curve keeps the gap at zero when the stride or rate changes."""
    curve = walk(STRIDE_CHANGE, root_motion(STRIDE_CHANGE))
    # 300 frame deltas are summed, so rounding of ~1e-14 can build up; a real slide is centimetres
    check("root-motion curve, stride 1.0 -> 0.8 at 2.5 s: max |gap| over 300 frames", max(abs(r[3]) for r in curve),
          0.0, tol=1e-12)
    flat = walk(STRIDE_CHANGE, constant_speed(matched_speed()))
    check("constant 1.0 m/s after the stride change: gap at 5 s = (1.0 - 0.8) x 2.5", flat[-1][3], 0.5, tol=1e-9)
    inside = max(abs(r[3]) for r in flat if r[0] <= 2.5)
    check("constant speed still slides inside each cycle by about SWAY / (2 pi) m", inside, SWAY / (2 * math.pi),
          tol=1e-3)
    rate_change = [(0.0, 1.0, 1.0), (1.7, 1.0, 1.25), (3.3, 0.9, 0.8)]
    other = walk(rate_change, root_motion(rate_change))
    check("root-motion curve with rate and stride changes mid-cycle: max |gap|", max(abs(r[3]) for r in other), 0.0,
          tol=1e-12)


if __name__ == "__main__":
    test_fk()
    test_my_chain()
    test_ik()
    test_ik_more()
    test_fk_matrices()
    test_spline()
    test_my_path()
    test_camera_path_copies()
    test_quaternion()
    test_quaternion_algebra()
    test_euler_orders()
    test_godot_check_parser()
    test_stdlib_only()
    test_foot_slide_bug()
    test_pitfall_c_root_motion()
    print(f"\nALL CHECKS PASSED ({_checks} ok)")
