"""FABRIK: iterative IK for a planar chain of any length, from scratch (standard library only).

Same convention as fk.py: a chain is lengths plus local angles in degrees, and the answer
can be fed straight back into forward_kinematics() as a check.

FABRIK (Forward And Backward Reaching IK) works on joint positions, not angles. One
iteration is two passes:
  backward: put the end on the target, then pull every joint towards it so each bone gets
            its length back, from the tip down to the base;
  forward:  put the base back where it belongs, then do the same from the base up to the tip.
Repeat until the tip is within `tol` of the target. With more than two bones there are
infinitely many poses that reach the same point; FABRIK returns the one its passes settle
into from the starting pose, which is why the starting pose matters.
"""
from __future__ import annotations

import math

from fk import Bone, forward_kinematics


def _toward(frm, to, length):
    """The point `length` away from `frm` in the direction of `to`."""
    dx, dy = to[0] - frm[0], to[1] - frm[1]
    d = math.hypot(dx, dy)
    return (frm[0] + dx * length / d, frm[1] + dy * length / d)


def joints_to_local_angles(joints):
    """Local angles (deg) of the bones between consecutive joints, as fk.py expects."""
    out, parent = [], 0.0
    for a, b in zip(joints, joints[1:]):
        g = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        local = (g - parent + 180.0) % 360.0 - 180.0
        out.append(local)
        parent += local
    return out


def fabrik(lengths, target, start_angles_deg=None, base=(0.0, 0.0), tol=1e-9, max_iter=1000):
    """Solve IK for `lengths` towards `target`.

    Returns (local_angles_deg, iterations, errors, reached): errors[k] is the tip-to-target
    distance after iteration k (errors[0] before any iteration). An out-of-reach target
    (farther than the total length) is not clamped silently: the chain is stretched straight
    at it and reached is False.
    """
    start = start_angles_deg if start_angles_deg is not None else [0.0] * len(lengths)
    joints, _ = forward_kinematics([Bone(l, a) for l, a in zip(lengths, start)], base)
    joints = [tuple(p) for p in joints]
    if math.dist(base, target) > sum(lengths):
        g = math.degrees(math.atan2(target[1] - base[1], target[0] - base[0]))
        straight = [g] + [0.0] * (len(lengths) - 1)
        tip = forward_kinematics([Bone(l, a) for l, a in zip(lengths, straight)], base)[0][-1]
        return straight, 0, [math.dist(tip, target)], False
    errors = [math.dist(joints[-1], target)]
    it = 0
    while errors[-1] > tol and it < max_iter:
        joints[-1] = tuple(target)
        for i in range(len(lengths) - 1, -1, -1):          # backward pass
            joints[i] = _toward(joints[i + 1], joints[i], lengths[i])
        joints[0] = tuple(base)
        for i in range(len(lengths)):                      # forward pass
            joints[i + 1] = _toward(joints[i], joints[i + 1], lengths[i])
        it += 1
        errors.append(math.dist(joints[-1], target))
    return joints_to_local_angles(joints), it, errors, errors[-1] <= tol


if __name__ == "__main__":
    from ik import solve_two_bone_ik
    from my_chain import load_chain

    angles, it, err, ok = fabrik([3.0, 2.0], (4.0, 1.0))
    print(f"modul arm (3, 2) -> (4, 1), start straight: theta {angles[0]:.4f} / {angles[1]:.4f} deg, "
          f"{it} iterations, error {err[-1]:.2e}")
    t1, t2 = solve_two_bone_ik(3.0, 2.0, (4.0, 1.0))
    print(f"  analytic solutions: ({t1:.4f}, {t2:.4f}) and "
          f"({2 * math.degrees(math.atan2(1, 4)) - t1:.4f}, {-t2:.4f})")
    bones, _ = load_chain()
    lengths = [b.length for b in bones]
    tip = forward_kinematics(bones)[0][-1]
    for name, start in (("straight", None), ("photo pose", [b.local_angle_deg for b in bones]),
                        ("elbow bent the other way", [10.0, -60.0, 0.0])):
        a, it, err, ok = fabrik(lengths, tip, start)
        end = forward_kinematics([Bone(l, x) for l, x in zip(lengths, a)])[0][-1]
        print(f"my arm -> fingertip ({tip[0]:.3f}, {tip[1]:.3f}) cm from {name}: "
              f"{', '.join(f'{x:.2f}' for x in a)} deg, {it} iterations, FK error {math.dist(end, tip):.2e} cm")
    a, it, err, ok = fabrik(lengths, (80.0, 0.0))
    print(f"my arm -> (80, 0) cm, beyond {sum(lengths):g} cm reach: reached={ok}, "
          f"stretched at {a[0]:.1f} deg, short by {err[-1]:.1f} cm")
