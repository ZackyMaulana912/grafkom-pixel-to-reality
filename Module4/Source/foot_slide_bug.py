"""Foot-slide case study: a walking character whose feet slip on the floor.

The root node is moved by game code at a scripted speed while a walk-cycle clip
plays. `--diagnose` prints only the evidence (root distance, animation distance and
their gap over time) for the reported speed; the cause and the fix are written up
in docs/prediksi/diagnosis-foot-slide.md.
"""
from __future__ import annotations

import argparse


STRIDE_PER_CYCLE = 1.0   # metres of forward travel the animation clip authored per cycle
CYCLE_RATE = 1.0         # cycles per second the AnimationPlayer plays the clip at


def root_motion_distance(scripted_speed: float, t: float) -> float:
    """Distance the root node has moved by time t, driven by a constant
    scripted speed (what a naive controller does)."""
    return scripted_speed * t


def animation_authored_distance(t: float, stride=STRIDE_PER_CYCLE, rate=CYCLE_RATE) -> float:
    """Distance the *feet* have actually walked by time t, according to the
    animation clip itself (stride length x number of cycles elapsed)."""
    return stride * rate * t


def foot_slide_at(t: float, scripted_speed: float) -> float:
    """The gap between where the root has moved to and where the animation's
    own foot contact says the character should be -- this gap is the visible
    sliding distance."""
    return root_motion_distance(scripted_speed, t) - animation_authored_distance(t)


def diagnose(scripted_speed: float, t_end: float = 5.0, dt: float = 1.0):
    """Report the foot-slide distance at each second up to t_end."""
    samples = []
    t = 0.0
    while t <= t_end + 1e-9:
        samples.append((t, foot_slide_at(t, scripted_speed)))
        t += dt
    return samples


REPORTED_SPEED = 1.5    # scripted root speed in the build where the feet were seen sliding


def print_diagnosis(scripted_speed=REPORTED_SPEED, t_end=5.0, dt=0.5):
    """Evidence only: the two distance curves and their gap, no fix and no assertions."""
    print(f"scripted_speed = {scripted_speed} m/s (root node, set by game code)")
    print(f"animation clip: STRIDE_PER_CYCLE = {STRIDE_PER_CYCLE} m per cycle, CYCLE_RATE = {CYCLE_RATE} cycles/s")
    print(f"{'t (s)':>6} {'cycles':>7} {'root (m)':>9} {'animation (m)':>14} {'gap (m)':>8}")
    for t, gap in diagnose(scripted_speed, t_end, dt):
        print(f"{t:6.1f} {CYCLE_RATE * t:7.2f} {root_motion_distance(scripted_speed, t):9.3f} "
              f"{animation_authored_distance(t):14.3f} {gap:+8.3f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="foot-slide case study")
    parser.add_argument("--diagnose", action="store_true", help="print the evidence only (no fix)")
    if parser.parse_args().diagnose:
        print_diagnosis()
        raise SystemExit(0)

    BUGGY_SPEED = 1.5   # scripted speed does not match the animation's own stride rate
    FIXED_SPEED = STRIDE_PER_CYCLE * CYCLE_RATE  # = 1.0 m/s: matches the animation exactly

    print("-- buggy: scripted_speed = 1.5 m/s, animation authors 1.0 m/s of travel --")
    for t, slide in diagnose(BUGGY_SPEED):
        print(f"  t={t:.0f}s  root={root_motion_distance(BUGGY_SPEED, t):.2f} m"
              f"  animation={animation_authored_distance(t):.2f} m"
              f"  foot-slide={slide:+.2f} m")

    print("\n-- fixed: scripted_speed set to STRIDE_PER_CYCLE * CYCLE_RATE = 1.0 m/s --")
    for t, slide in diagnose(FIXED_SPEED):
        print(f"  t={t:.0f}s  root={root_motion_distance(FIXED_SPEED, t):.2f} m"
              f"  animation={animation_authored_distance(t):.2f} m"
              f"  foot-slide={slide:+.2f} m")

    buggy_final = foot_slide_at(5.0, BUGGY_SPEED)
    fixed_final = foot_slide_at(5.0, FIXED_SPEED)
    print(f"\nfoot-slide after 5 s: buggy = {buggy_final:.2f} m, fixed = {fixed_final:.2f} m")
    assert abs(fixed_final) < 1e-9, "fix should zero the foot-slide gap"
    assert abs(buggy_final) > 2.0, "buggy case should show a large, visible gap"
