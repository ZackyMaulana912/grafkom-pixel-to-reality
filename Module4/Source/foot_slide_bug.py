"""Foot-slide case study: a walking character whose feet slip on the floor.

The root node is moved by game code at a scripted speed while a walk-cycle clip
plays. `--diagnose` prints only the evidence (root distance, animation distance and
their gap over time) for the reported speed. The diagnosis, written before the fix,
is docs/prediksi/diagnosis-foot-slide.md; the fix and the pitfall (c) experiment are
in docs/catatan/fase4-foot-slide-pitfall.md.

Fix (one change): the root speed is no longer a number typed into game code but
matched_speed() = stride per cycle x cycles per second, read from the clip.
Pitfall (c): root_motion_walk() moves the root by what a baked root-motion curve
says the feet covered each frame, so the gap stays zero even when the stride changes.
"""
from __future__ import annotations

import argparse
import math


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


def matched_speed(stride=STRIDE_PER_CYCLE, rate=CYCLE_RATE):
    """Root speed that covers exactly the ground the clip's feet cover: stride x rate."""
    return stride * rate


def print_diagnosis(scripted_speed=REPORTED_SPEED, t_end=5.0, dt=0.5):
    """Evidence only: the two distance curves and their gap, no fix and no assertions."""
    print(f"scripted_speed = {scripted_speed} m/s (root node, set by game code)")
    print(f"animation clip: STRIDE_PER_CYCLE = {STRIDE_PER_CYCLE} m per cycle, CYCLE_RATE = {CYCLE_RATE} cycles/s")
    print(f"{'t (s)':>6} {'cycles':>7} {'root (m)':>9} {'animation (m)':>14} {'gap (m)':>8}")
    for t, gap in diagnose(scripted_speed, t_end, dt):
        print(f"{t:6.1f} {CYCLE_RATE * t:7.2f} {root_motion_distance(scripted_speed, t):9.3f} "
              f"{animation_authored_distance(t):14.3f} {gap:+8.3f}")


# --- pitfall (c): speed read from a baked root-motion curve ---------------------

SWAY = 0.3  # how much the forward speed rises and falls inside one step (0 = constant)


def unit_cycle_curve(keys=30):
    """Baked root-motion keys for one cycle of a 1 m stride: (phase, metres).

    A real walk does not move forward at a constant speed inside a cycle; here the
    speed is 1 - SWAY cos(2 pi phase), sampled at `keys` keyframes like a baked clip.
    """
    return [(i / keys, i / keys - SWAY * math.sin(2 * math.pi * i / keys) / (2 * math.pi)) for i in range(keys + 1)]


def curve_at(keys, phase):
    """Linear interpolation of the baked keys at phase in [0, 1]."""
    n = len(keys) - 1
    i = min(int(phase * n), n - 1)
    (p0, d0), (p1, d1) = keys[i], keys[i + 1]
    return d0 + (d1 - d0) * (phase - p0) / (p1 - p0)


def clip_distance(t, schedule, keys):
    """Ground covered by the feet by time t, for a clip whose stride/rate change at given times.

    schedule = [(t_start, stride, rate), ...] sorted by t_start, first t_start = 0.
    The phase runs on continuously; each stretch adds stride x (curve progress) metres.
    """
    total, phase = 0.0, 0.0
    for k, (t0, stride, rate) in enumerate(schedule):
        t1 = schedule[k + 1][0] if k + 1 < len(schedule) else float("inf")
        if t <= t0:
            break
        end = phase + rate * (min(t, t1) - t0)
        whole0, whole1 = math.floor(phase), math.floor(end)
        progress = (whole1 - whole0) + curve_at(keys, end - whole1) - curve_at(keys, phase - whole0)
        total += stride * progress
        phase = end
    return total


def walk(schedule, controller, t_end=5.0, fps=60, keys=None):
    """Simulate frame by frame; return [(t, root, feet, gap)] for every frame.

    controller(t, dt) returns how far the root moves this frame.
    """
    keys = keys or unit_cycle_curve()
    dt = 1.0 / fps
    root, out = 0.0, [(0.0, 0.0, 0.0, 0.0)]
    for frame in range(1, round(t_end * fps) + 1):
        t = frame * dt
        root += controller(t - dt, dt)
        feet = clip_distance(t, schedule, keys)
        out.append((t, root, feet, root - feet))
    return out


def constant_speed(speed):
    """Controller of the first fix: a constant speed, however it was chosen."""
    return lambda t, dt: speed * dt


def root_motion(schedule, keys=None):
    """Controller of pitfall (c): move by what the baked curve says the feet covered this frame."""
    keys = keys or unit_cycle_curve()
    return lambda t, dt: clip_distance(t + dt, schedule, keys) - clip_distance(t, schedule, keys)


STRIDE_CHANGE = [(0.0, STRIDE_PER_CYCLE, CYCLE_RATE), (2.5, 0.8, CYCLE_RATE)]  # shorter steps from t = 2.5 s


def print_fix():
    print(f"-- before: scripted_speed = {REPORTED_SPEED} m/s (typed in game code) --")
    print(f"-- after:  scripted_speed = matched_speed() = STRIDE_PER_CYCLE x CYCLE_RATE = {matched_speed()} m/s --")
    print(f"{'t (s)':>6} {'gap before (m)':>15} {'gap after (m)':>14}")
    after = diagnose(matched_speed(), dt=0.5)
    for (t, g0), (_, g1) in zip(diagnose(REPORTED_SPEED, dt=0.5), after):
        print(f"{t:6.1f} {g0:+15.3f} {g1!r:>14}")
    zero = all(g == 0.0 for _, g in after)
    print(f"gap after the fix is exactly 0.0 at every sample: {zero}")
    return zero


def print_pitfall_c():
    print("\n-- pitfall (c): stride drops from 1.0 m to 0.8 m per cycle at t = 2.5 s, 60 fps --")
    runs = {
        "constant 1.0 m/s": walk(STRIDE_CHANGE, constant_speed(matched_speed())),
        "baked root-motion curve": walk(STRIDE_CHANGE, root_motion(STRIDE_CHANGE)),
    }
    print(f"{'t (s)':>6}" + "".join(f" {name:>24}" for name in runs))
    for i in range(0, 301, 30):
        print(f"{i / 60:6.1f}" + "".join(f" {run[i][3]:+24.4f}" for run in runs.values()))
    for name, run in runs.items():
        before = max(abs(r[3]) for r in run if r[0] <= 2.5)
        after = max(abs(r[3]) for r in run if r[0] > 2.5)
        print(f"{name}: max |gap| up to 2.5 s = {before:.2e} m, after = {after:.2e} m, at 5 s = {run[-1][3]:+.4f} m")
    return runs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="foot-slide case study")
    parser.add_argument("--diagnose", action="store_true", help="print the evidence only (no fix)")
    if parser.parse_args().diagnose:
        print_diagnosis()
        raise SystemExit(0)
    print_fix()
    print_pitfall_c()
