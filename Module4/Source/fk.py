"""Forward kinematics of a planar bone chain, from scratch (standard library only).

Conventions for the whole module (fixed here once, quaternion.py repeats the 3D ones):
- A chain is a list of Bone(length, local_angle_deg).
- local_angle_deg is measured from the PARENT bone's direction; the first bone is
  measured from +x. Counter-clockwise is positive.
- Angles are degrees in every public function (suffix _deg) and are turned into
  radians only inside _rot().
- Points are column vectors; a joint's world transform is the product of the local
  transforms from the root down to it, read right to left as in Module 3.

Each bone contributes one local 3 x 3 homogeneous matrix R(theta) T(length, 0):
turn by its local angle, then walk along its own x axis. FK is just multiplying
those matrices from root to leaf; summing the angles is the 2D shortcut of the same
product, because R(a) R(b) = R(a + b).
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Bone:
    length: float
    local_angle_deg: float  # relative to the parent bone's direction


def _rot(angle_deg):
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    return ((c, -s, 0.0), (s, c, 0.0), (0.0, 0.0, 1.0))


def _move(dx, dy):
    return ((1.0, 0.0, dx), (0.0, 1.0, dy), (0.0, 0.0, 1.0))


def _mul(a, b):
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)) for i in range(3))


def bone_matrices(bones, base=(0.0, 0.0)):
    """World matrix of every joint after the base: [M_1, M_2, ...], M_i = M_(i-1) R(theta_i) T(l_i, 0)."""
    world = _move(*base)
    out = []
    for bone in bones:
        world = _mul(world, _mul(_rot(bone.local_angle_deg), _move(bone.length, 0.0)))
        out.append(world)
    return out


def forward_kinematics(bones, base=(0.0, 0.0)):
    """Return ([base, joint_1, ..., end effector], [global angle of bone 1, ..., bone n]) in degrees.

    Positions come from the matrix product; the global angle is the running sum of the
    local angles, which is exact and is what the matrices encode (tests.py checks both agree).
    """
    positions = [tuple(base)]
    positions += [(m[0][2], m[1][2]) for m in bone_matrices(bones, base)]
    global_angles, total = [], 0.0
    for bone in bones:
        total += bone.local_angle_deg
        global_angles.append(total)
    return positions, global_angles


def running_example():
    """Module 4 example E1: lengths 3 and 2, local angles 30 and 60 deg, shoulder at the origin."""
    return forward_kinematics([Bone(3.0, 30.0), Bone(2.0, 60.0)])


if __name__ == "__main__":
    (shoulder, elbow, hand), (g1, g2) = running_example()
    print(f"shoulder = ({shoulder[0]:.3f}, {shoulder[1]:.3f})")
    print(f"elbow    = ({elbow[0]:.3f}, {elbow[1]:.3f})   global angle = {g1:.1f} deg")
    print(f"hand     = ({hand[0]:.3f}, {hand[1]:.3f})   global angle = {g2:.1f} deg")
