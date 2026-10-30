"""Analytic two-bone inverse kinematics (law of cosines), from scratch.

Same convention as fk.py: theta1 is the first bone's angle from +x, theta2 is the
elbow's LOCAL angle from the first bone's direction, both in degrees. So the answer
can be fed straight back into forward_kinematics() as a check.

The elbow angle comes from the law of cosines on the shoulder-elbow-target
triangle. The shoulder angle is then the direction to the target minus the
direction of the target as seen from a shoulder with theta1 = 0, i.e. the end of
(l1, 0) + l2 (cos theta2, sin theta2). Deriving theta1 from the theta2 actually
used keeps the hand on the shoulder-target line even when acos rounds; the law of
cosines at the shoulder instead was measured to miss by up to 1.4e-7 near full
reach (docs/catatan/fase3-primitif.md).
"""
from __future__ import annotations

import math

from fk import Bone, forward_kinematics


class UnreachableTarget(Exception):
    """The target lies outside the ring |l1 - l2| <= d <= l1 + l2."""


def _acos_checked(x):
    # x is only outside [-1, 1] by rounding here: reachability was tested before.
    return math.degrees(math.acos(max(-1.0, min(1.0, x))))


def solve_two_bone_ik(l1, l2, target):
    """Return (theta1_deg, theta2_deg) placing the end of [l1, l2] on target.

    This is the solution with theta2 >= 0 (the elbow bends counter-clockwise from the
    upper arm). Whether that elbow ends up above or below the shoulder-target line
    depends on the target, so it is not called "elbow up" here.
    Raises UnreachableTarget instead of clamping when the target is out of reach.
    """
    tx, ty = target
    d = math.hypot(tx, ty)
    lo, hi = abs(l1 - l2), l1 + l2
    if not lo <= d <= hi:
        raise UnreachableTarget(f"target at distance {d:.3f} is outside [{lo:.3f}, {hi:.3f}]")
    if d == 0.0:
        return 0.0, 180.0  # l1 == l2 and the target is the shoulder: fold back, any heading works
    # inside angle at the elbow: d^2 = l1^2 + l2^2 - 2 l1 l2 cos(alpha), theta2 = 180 - alpha
    alpha = _acos_checked((l1 * l1 + l2 * l2 - d * d) / (2.0 * l1 * l2))
    theta2 = 180.0 - alpha
    t2 = math.radians(theta2)
    reach_dir = math.degrees(math.atan2(l2 * math.sin(t2), l1 + l2 * math.cos(t2)))
    return math.degrees(math.atan2(ty, tx)) - reach_dir, theta2


def fk_error(l1, l2, theta1_deg, theta2_deg, target):
    """Distance between the FK end effector of the solved angles and the target."""
    positions, _ = forward_kinematics([Bone(l1, theta1_deg), Bone(l2, theta2_deg)])
    hand = positions[-1]
    return math.hypot(hand[0] - target[0], hand[1] - target[1]), hand


def running_example():
    """Module 4 example E2: lengths 3 and 2, target (4, 1)."""
    l1, l2, target = 3.0, 2.0, (4.0, 1.0)
    theta1, theta2 = solve_two_bone_ik(l1, l2, target)
    _, hand = fk_error(l1, l2, theta1, theta2, target)
    return theta1, theta2, hand, target


if __name__ == "__main__":
    theta1, theta2, hand, target = running_example()
    err, _ = fk_error(3.0, 2.0, theta1, theta2, target)
    print(f"target       = ({target[0]:.3f}, {target[1]:.3f})")
    print(f"theta1 (shoulder) = {theta1:.2f} deg")
    print(f"theta2 (elbow)    = {theta2:.2f} deg")
    print(f"FK(theta1,theta2) = ({hand[0]:.3f}, {hand[1]:.3f})  <- should match target")
    print(f"position error    = {err:.2e}")
    for bad in ((5.5, 0.0), (0.5, 0.0)):
        try:
            solve_two_bone_ik(3.0, 2.0, bad)
        except UnreachableTarget as exc:
            print(f"target {bad}: UnreachableTarget ({exc})")
