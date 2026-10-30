"""FK of my own arm (data/my_chain.json) -- Lab 1 no 3 and Lab 2 no 1.

Reads the measured chain, runs fk.py on the 2-bone (shoulder-elbow-wrist) and
3-bone (+ middle fingertip) versions, and re-derives the local angles from the
photo's pixel points so the angles in the JSON can be traced back to the photo.
"""
from __future__ import annotations

import json
import math
import os

from fk import Bone, forward_kinematics

CHAIN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "my_chain.json")


def load_chain(path=CHAIN_PATH):
    """Return (bones, raw_json) for my measured chain."""
    with open(path) as f:
        data = json.load(f)
    bones = [Bone(b["length"], b["local_angle_deg"]) for b in data["bones"]]
    return bones, data


def direction_deg(p, q):
    """Angle of the image vector p -> q, measured from +x with y flipped up (pixels grow downward)."""
    return math.degrees(math.atan2(-(q[1] - p[1]), q[0] - p[0]))


def angles_from_photo(data):
    """Global and local angles of the three bones, recomputed from the photo's pixel points."""
    pts = data["photo"]["points_px"]
    globals_deg = [
        direction_deg(pts["upper_arm_axis_a"], pts["upper_arm_axis_b"]),
        direction_deg(pts["elbow"], pts["wrist"]),
        direction_deg(pts["wrist"], pts["fingertip"]),
    ]
    locals_deg = [globals_deg[0]] + [b - a for a, b in zip(globals_deg, globals_deg[1:])]
    return globals_deg, locals_deg


def print_chain(title, bones, names, unit):
    positions, angles = forward_kinematics(bones)
    print(title)
    print(f"  {'bahu':<11} = ({positions[0][0]:8.3f}, {positions[0][1]:8.3f}) {unit}")
    for name, p, a in zip(names, positions[1:], angles):
        print(f"  {name:<11} = ({p[0]:8.3f}, {p[1]:8.3f}) {unit}   global angle = {a:6.1f} deg")
    return positions, angles


def main():
    bones, data = load_chain()
    unit = data["unit"]
    names = ["siku", "pergelangan", "ujung jari"]
    print(f"{data['name']}: " + ", ".join(f"{b.length:g} {unit} @ {b.local_angle_deg:+.1f} deg" for b in bones))
    print_chain("2-bone (bahu-siku-pergelangan):", bones[:2], names, unit)
    print_chain("3-bone (+ tangan sampai ujung jari tengah):", bones, names, unit)

    globals_deg, locals_deg = angles_from_photo(data)
    print("dari titik pixel foto:")
    for b, g, loc in zip(bones, globals_deg, locals_deg):
        print(f"  global {g:7.2f} deg  lokal {loc:7.2f} deg  (json {b.local_angle_deg:+.1f}, "
              f"selisih {loc - b.local_angle_deg:+.2f})")
    pts = data["photo"]["points_px"]
    px_per_unit = math.dist(pts["elbow"], pts["wrist"]) / bones[1].length
    hand_in_photo = math.dist(pts["wrist"], pts["fingertip"]) / px_per_unit
    print(f"  skala dari lengan bawah: {px_per_unit:.2f} px/{unit}; tangan di foto {hand_in_photo:.1f} {unit} "
          f"vs diukur {bones[2].length:g} {unit} ({100 * (hand_in_photo / bones[2].length - 1):+.1f}%)")


if __name__ == "__main__":
    main()
