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

Joint limits (optional): `limits[i] = (lo_deg, hi_deg)` bounds bone i's LOCAL angle. They are
enforced in both passes: in the forward pass bone by bone from the base (so the returned pose
always respects them), and in the backward pass by turning each bone about its child joint
when the angle there is out of range. A target the limits make unreachable ends with
reached = False after max_iter.
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


def _clamp_start(start, limits):
    return [a if lim is None else min(max(a, lim[0]), lim[1]) for a, lim in zip(start, limits)]


def fabrik(lengths, target, start_angles_deg=None, base=(0.0, 0.0), tol=1e-9, max_iter=1000, limits=None):
    """Solve IK for `lengths` towards `target`.

    Returns (local_angles_deg, iterations, errors, reached): errors[k] is the tip-to-target
    distance after iteration k (errors[0] before any iteration). An out-of-reach target
    (farther than the total length) is not clamped silently: the chain is stretched straight
    at it and reached is False.
    """
    start = start_angles_deg if start_angles_deg is not None else [0.0] * len(lengths)
    limits = limits or [None] * len(lengths)
    start = _clamp_start(start, limits)
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
            if i + 1 < len(lengths) and limits[i + 1] is not None:
                # keep the angle at joint i+1 (bone i+1 relative to bone i) inside its limits,
                # seen from the child side: turn bone i about joint i+1
                child = math.atan2(joints[i + 2][1] - joints[i + 1][1], joints[i + 2][0] - joints[i + 1][0])
                own = math.atan2(joints[i + 1][1] - joints[i][1], joints[i + 1][0] - joints[i][0])
                local = (math.degrees(child - own) + 180.0) % 360.0 - 180.0
                clamped = min(max(local, limits[i + 1][0]), limits[i + 1][1])
                if clamped != local:
                    g = child - math.radians(clamped)
                    joints[i] = (joints[i + 1][0] - lengths[i] * math.cos(g),
                                 joints[i + 1][1] - lengths[i] * math.sin(g))
        joints[0] = tuple(base)
        parent = 0.0
        for i in range(len(lengths)):                      # forward pass, limits applied here
            want = math.degrees(math.atan2(joints[i + 1][1] - joints[i][1], joints[i + 1][0] - joints[i][0]))
            local = (want - parent + 180.0) % 360.0 - 180.0
            if limits[i] is not None:
                local = min(max(local, limits[i][0]), limits[i][1])
            parent += local
            g = math.radians(parent)
            joints[i + 1] = (joints[i][0] + lengths[i] * math.cos(g), joints[i][1] + lengths[i] * math.sin(g))
        it += 1
        errors.append(math.dist(joints[-1], target))
    return joints_to_local_angles(joints), it, errors, errors[-1] <= tol


def analytic_seed(lengths, target, wrist_deg):
    """Start pose for a 3-bone arm: fix the wrist, treat forearm + hand as one rigid link, and
    take ik.py's theta2 >= 0 answer for (upper arm, that link). None if out of its reach."""
    from ik import UnreachableTarget, solve_two_bone_ik
    w = math.radians(wrist_deg)
    vx, vy = lengths[1] + lengths[2] * math.cos(w), lengths[2] * math.sin(w)   # elbow -> tip, in the forearm's frame
    try:
        t1, t2 = solve_two_bone_ik(lengths[0], math.hypot(vx, vy), target)
    except UnreachableTarget:
        return None
    return [t1, t2 - math.degrees(math.atan2(vy, vx)), wrist_deg]


def solve_arm_with_limits(lengths, target, limits, start_angles_deg=None, tol=1e-9, max_iter=200, seeds=7):
    """FABRIK with joint limits for my 3-bone arm, with restarts.

    FABRIK with one-sided hinge limits can get stuck: if the start pose sits on the wrong side,
    the elbow keeps asking to bend backwards and the limit keeps it straight. So: try the given
    start pose first; if it does not converge, restart from analytic seeds (analytic_seed) with the
    wrist spread over its range, and keep the best result. Returns (angles, iterations_total,
    errors_of_best_run, reached, tries).
    """
    lo, hi = limits[2]
    starts = [start_angles_deg] if start_angles_deg is not None else []
    starts += [analytic_seed(lengths, target, lo + (hi - lo) * k / (seeds - 1)) for k in range(seeds)]
    best, total, tries = None, 0, 0
    for st in starts:
        if st is None:
            continue
        tries += 1
        result = fabrik(lengths, target, st, tol=tol, max_iter=max_iter, limits=limits)
        total += result[1]
        if best is None or result[2][-1] < best[2][-1]:
            best = result
        if result[3]:
            break
    if best is None:  # no usable start (target outside every seed's reach): report it, do not crash
        best = fabrik(lengths, target, tol=tol, max_iter=max_iter, limits=limits)
        total, tries = best[1], 1
    return best[0], total, best[2], best[3], tries


# Rough general limits for a human arm, NOT measured on my arm: the elbow bends one way only,
# up to about 150 deg; the wrist about -70 (extension) to +80 (flexion). The shoulder is free
# in this plane. Replace with my own measurements if I take them.
ARM_LIMITS_DEG = [None, (0.0, 150.0), (-70.0, 80.0)]


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
    a, it, err, ok = fabrik(lengths, (50.0, 0.0), [0.0, 75.0, 5.0], limits=ARM_LIMITS_DEG, max_iter=200)
    print(f"with limits {ARM_LIMITS_DEG[1:]} (assumed, not measured), (50, 0) from (0, 75, 5): "
          f"{', '.join(f'{x:.2f}' for x in a)} deg, reached={ok}, stuck {err[-1]:.1f} cm away")
    a, it, err, ok, tries = solve_arm_with_limits(lengths, (50.0, 0.0), ARM_LIMITS_DEG, [0.0, 75.0, 5.0])
    print(f"  same target with analytic seeds: {', '.join(f'{x:.2f}' for x in a)} deg, reached={ok}, "
          f"{tries} tries, {it} iterations in total")
    a, it, err, ok = fabrik(lengths, (80.0, 0.0))
    print(f"my arm -> (80, 0) cm, beyond {sum(lengths):g} cm reach: reached={ok}, "
          f"stretched at {a[0]:.1f} deg, short by {err[-1]:.1f} cm")
