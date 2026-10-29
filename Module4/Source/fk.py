"""Forward kinematics for a planar (2D) bone chain -- from scratch, no engine.

A chain is a list of (length, local_angle_deg) pairs. local_angle_deg is the
joint's rotation *relative to its parent link's direction* (so the chain is a
sequence of composed rotations, exactly like a Godot/Unity bone hierarchy: each
child's global orientation is its parent's orientation plus its own local
rotation). Reproduces the Module 4 running example.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class Bone:
    length: float
    local_angle_deg: float  # relative to the parent link's direction


def forward_kinematics(bones: list[Bone], base=(0.0, 0.0)):
    """Return the joint positions [base, joint1, joint2, ...] and the
    *global* (world) angle of each link, in degrees.

    joint_i = joint_{i-1} + length_i * (cos(theta_i), sin(theta_i))
    theta_i = theta_{i-1} + local_angle_i   (theta_0 = 0)
    """
    x, y = base
    positions = [(x, y)]
    global_angle = 0.0
    global_angles = []
    for bone in bones:
        global_angle += bone.local_angle_deg
        rad = math.radians(global_angle)
        x += bone.length * math.cos(rad)
        y += bone.length * math.sin(rad)
        positions.append((x, y))
        global_angles.append(global_angle)
    return positions, global_angles


def running_example():
    """Module 4 running example: a 2-bone arm, lengths 3 and 2, shoulder at
    the origin, local joint angles 30 deg and 60 deg."""
    bones = [Bone(3.0, 30.0), Bone(2.0, 60.0)]
    positions, angles = forward_kinematics(bones)
    return positions, angles


if __name__ == "__main__":
    positions, angles = running_example()
    shoulder, elbow, hand = positions
    print(f"shoulder = ({shoulder[0]:.3f}, {shoulder[1]:.3f})")
    print(f"elbow    = ({elbow[0]:.3f}, {elbow[1]:.3f})   global angle = {angles[0]:.1f} deg")
    print(f"hand     = ({hand[0]:.3f}, {hand[1]:.3f})   global angle = {angles[1]:.1f} deg")
