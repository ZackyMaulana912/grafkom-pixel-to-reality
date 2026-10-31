"""Module 4 -- figures for the docs (the only file that uses matplotlib).

Every point drawn here is computed at run time with the from-scratch modules
(fk.py, ik.py, spline.py, quaternion.py), so a picture cannot drift from the
code it illustrates. Nothing in those modules imports this file.

Run (from Source/):
  .venv/bin/python figures.py --set studi    -> ../docs/studi-pendahuluan/img/*.png
  .venv/bin/python figures.py --set readme   -> ../docs/img/*.png
"""
from __future__ import annotations

import argparse
import math
import os

import matplotlib

matplotlib.use("Agg")  # file output only, no window
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Arc, Circle, FancyArrowPatch, FancyBboxPatch  # noqa: E402

from fk import Bone, forward_kinematics  # noqa: E402
from ik import solve_two_bone_ik  # noqa: E402
from quaternion import quat_dot, quat_from_axis_angle, quat_to_axis_angle, slerp  # noqa: E402
from foot_slide_bug import (  # noqa: E402
    REPORTED_SPEED, STRIDE_CHANGE, constant_speed, diagnose, matched_speed, root_motion, walk,
)
from my_chain import angles_from_photo, load_chain  # noqa: E402
from spline import load_camera_path, load_my_path, sample_closed_path, sample_path, sample_spacing  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = {
    "studi": os.path.join(HERE, "..", "docs", "studi-pendahuluan", "img"),
    "readme": os.path.join(HERE, "..", "docs", "img"),
}

INK = "#222222"
BONE1 = "#2f6db5"
BONE2 = "#d9822b"
MUTED = "#8a8a8a"
GOOD = "#2e8b57"
BAD = "#c0392b"


def save(fig, out_dir, name):
    """Write a PNG without a timestamp/version tag, so reruns give the same bytes."""
    path = os.path.join(out_dir, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", metadata={"Software": None})
    plt.close(fig)
    print(f"wrote {os.path.relpath(path, HERE)}")


def angle_arc(ax, center, radius, start_deg, end_deg, color, label, label_r=None):
    """Draw an angle arc between two directions and put its label at the middle."""
    lo, hi = sorted((start_deg, end_deg))
    ax.add_patch(Arc(center, 2 * radius, 2 * radius, theta1=lo, theta2=hi, color=color, lw=1.6))
    mid = math.radians((lo + hi) / 2)
    r = label_r if label_r is not None else radius * 1.35
    ax.text(center[0] + r * math.cos(mid), center[1] + r * math.sin(mid), label,
            color=color, ha="center", va="center", fontsize=11)


def fig_fk_chain(out_dir):
    """Q1: the 2-bone arm (3, 30 deg) + (2, 60 deg) with local vs global angles."""
    (s, e, h), (g1, g2) = forward_kinematics([Bone(3.0, 30.0), Bone(2.0, 60.0)])
    fig, ax = plt.subplots(figsize=(6.4, 5.4))
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.axvline(0, color=MUTED, lw=0.8)
    # dashed: where bone 2 would point with a local angle of 0 (parent direction)
    ext = (e[0] + 1.6 * math.cos(math.radians(g1)), e[1] + 1.6 * math.sin(math.radians(g1)))
    ax.plot([e[0], ext[0]], [e[1], ext[1]], ls="--", color=BONE1, lw=1)
    ax.plot([e[0], e[0] + 1.6], [e[1], e[1]], ls=":", color=MUTED, lw=1)
    ax.plot([s[0], e[0]], [s[1], e[1]], color=BONE1, lw=5, solid_capstyle="round")
    ax.plot([e[0], h[0]], [e[1], h[1]], color=BONE2, lw=5, solid_capstyle="round")
    for p, name in ((s, "bahu"), (e, "siku"), (h, "tangan")):
        ax.add_patch(Circle(p, 0.09, color=INK, zorder=5))
        ax.annotate(f"{name}\n({p[0]:.3f}, {p[1]:.3f})", p, xytext=(10, -4), textcoords="offset points",
                    fontsize=10, color=INK, va="top")
    angle_arc(ax, s, 0.8, 0, g1, BONE1, f"{g1:.0f}°")
    angle_arc(ax, e, 0.55, g1, g2, BONE2, "lokal 60°", label_r=0.95)
    angle_arc(ax, e, 1.15, 0, g2, MUTED, f"global {g2:.0f}°", label_r=1.55)
    ax.text(1.2, 1.05, "bone 1: panjang 3", color=BONE1, fontsize=10, rotation=g1, ha="center")
    ax.text(2.4, 2.6, "bone 2: panjang 2", color=BONE2, fontsize=10, rotation=90, ha="center")
    ax.set_xlim(-0.5, 4.6)
    ax.set_ylim(-0.5, 4.0)
    ax.set_aspect("equal")
    ax.set_title("Rantai 2-bone: sudut global = jumlah sudut lokal (30° + 60° = 90°)", fontsize=11)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    save(fig, out_dir, "q1_rantai_fk.png")


def fig_ik_two_solutions(out_dir):
    """Q2: reachable ring, law-of-cosines triangle, and both elbow solutions for target (4, 1)."""
    l1, l2, target = 3.0, 2.0, (4.0, 1.0)
    t1, t2 = solve_two_bone_ik(l1, l2, target)
    to_target = math.degrees(math.atan2(target[1], target[0]))
    mirror = (2 * to_target - t1, -t2)  # reflect the arm across the shoulder-target line
    fig, ax = plt.subplots(figsize=(6.6, 6.0))
    ax.add_patch(Circle((0, 0), l1 + l2, color=GOOD, alpha=0.10))
    ax.add_patch(Circle((0, 0), abs(l1 - l2), color="white"))
    ax.add_patch(Circle((0, 0), l1 + l2, fill=False, color=GOOD, ls="--", lw=1))
    ax.add_patch(Circle((0, 0), abs(l1 - l2), fill=False, color=BAD, ls="--", lw=1))
    ax.text(0, -(l1 + l2) + 0.25, f"batas luar d = l1 + l2 = {l1 + l2:.0f}", ha="center", color=GOOD, fontsize=9)
    ax.text(0, -abs(l1 - l2) - 0.35, f"batas dalam |l1 - l2| = {abs(l1 - l2):.0f}", ha="center", color=BAD,
            fontsize=9)
    ax.plot([0, target[0]], [0, target[1]], color=MUTED, ls=":", lw=1.2)
    d = math.hypot(*target)
    ax.text(1.3, 0.45, f"d = √17 = {d:.3f}", color=MUTED, fontsize=9, rotation=to_target)
    for (a1, a2), color, label in (((t1, t2), BONE1, "solusi starter"), (mirror, BONE2, "solusi cermin")):
        (s, e, h), _ = forward_kinematics([Bone(l1, a1), Bone(l2, a2)])
        assert math.hypot(h[0] - target[0], h[1] - target[1]) < 1e-9
        ax.plot([s[0], e[0], h[0]], [s[1], e[1], h[1]], color=color, lw=3.5, solid_capstyle="round",
                label=f"{label}: θ1 = {a1:.2f}°, θ2 = {a2:.2f}°, siku ({e[0]:.3f}, {e[1]:.3f})")
        ax.add_patch(Circle(e, 0.08, color=color, zorder=5))
        if color == BONE1:
            ax.annotate(f"sudut dalam siku\n= 180° - θ2 = {180 - a2:.2f}°", e, xytext=(-25, -40),
                        textcoords="offset points", fontsize=8.5, color=color)
    ax.add_patch(Circle((0, 0), 0.09, color=INK, zorder=6))
    ax.plot(*target, marker="*", ms=16, color=BAD, zorder=6)
    ax.annotate("target (4, 1)", target, xytext=(8, 6), textcoords="offset points", fontsize=10)
    ax.set_xlim(-5.4, 5.4)
    ax.set_ylim(-5.4, 5.4)
    ax.set_aspect("equal")
    ax.legend(loc="upper left", fontsize=8.5, framealpha=0.95)
    ax.set_title("IK 2-bone: wilayah terjangkau dan dua solusi untuk target yang sama", fontsize=11)
    save(fig, out_dir, "q2_ik_dua_solusi.png")


def fig_spline_vs_linear(out_dir):
    """Q3a: same control points, piecewise-linear (C0) vs Catmull-Rom (C1)."""
    cps = [(0.0, 0.0), (2.0, 0.0), (4.0, 2.0), (6.0, 2.0)]
    curve = sample_path(cps, samples_per_segment=30)
    fig, ax = plt.subplots(figsize=(6.6, 3.2))
    ax.plot([p[0] for p in cps], [p[1] for p in cps], color=MUTED, ls="--", lw=1.4,
            label="piecewise-linear: menekuk di tiap titik (C0)")
    ax.plot([p[0] for p in curve], [p[1] for p in curve], color=BONE1, lw=2.4,
            label="Catmull-Rom: tetap melewati titik, tanpa tekukan (C1)")
    ax.plot([p[0] for p in cps], [p[1] for p in cps], "o", color=INK, zorder=5)
    for i, p in enumerate(cps):
        ax.annotate(f"P{i}", p, xytext=(-6, 8), textcoords="offset points", fontsize=10)
    ax.plot(3.0, 1.0, marker="s", color=BAD, zorder=6)
    ax.annotate("q(0.5) = (3, 1)", (3.0, 1.0), xytext=(8, -12), textcoords="offset points", color=BAD,
                fontsize=9)
    ax.set_aspect("equal")
    ax.set_ylim(-1.3, 2.6)
    ax.legend(loc="lower right", fontsize=8.5)
    ax.set_title("Titik kontrol yang sama, dua cara menyambungkan", fontsize=11)
    save(fig, out_dir, "q3_spline_vs_linear.png")


def _ry(deg, p):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    x, y, z = p
    return (c * x + s * z, y, -s * x + c * z)  # same sign as Ry in quaternion.py


def _ring(ax, radius, plane, color, yaw=0.0, lw=2.6):
    pts = []
    for i in range(121):
        a = 2 * math.pi * i / 120
        u, v = radius * math.cos(a), radius * math.sin(a)
        p = {"yz": (0.0, u, v), "xy": (u, v, 0.0), "xz": (u, 0.0, v)}[plane]
        pts.append(_ry(yaw, p))
    ax.plot([p[0] for p in pts], [p[1] for p in pts], [p[2] for p in pts], color=color, lw=lw)


def _axis(ax, direction, length, color, label):
    x, y, z = direction
    ax.plot([-length * x, length * x], [-length * y, length * y], [-length * z, length * z], color=color,
            lw=1.6, ls="--")
    ax.text(1.12 * length * x, 1.12 * length * y, 1.12 * length * z, label, color=color, fontsize=9)


def fig_gimbal_lock(out_dir):
    """Q3b/Q4a: three gimbals of M = Rz(roll) Ry(yaw) Rx(pitch); yaw = 90 puts the inner axis on the outer one."""
    fig = plt.figure(figsize=(9.6, 4.6))
    for k, yaw in enumerate((0.0, 90.0)):
        ax = fig.add_subplot(1, 2, k + 1, projection="3d")
        _ring(ax, 1.00, "yz", "#7b4fa0")            # outer: turns about world z (roll)
        _ring(ax, 0.80, "xy", BONE2, yaw=yaw)       # middle: turns about y (yaw), carried by outer
        _ring(ax, 0.60, "xz", BONE1, yaw=yaw)       # inner: turns about x (pitch), carried by middle
        _axis(ax, (0, 0, 1), 1.25, "#7b4fa0", "roll (luar, z)")
        _axis(ax, (0, 1, 0), 1.25, BONE2, "yaw (tengah, y)")
        _axis(ax, _ry(yaw, (1, 0, 0)), 0.95, BONE1, "pitch (dalam)")
        ax.set_box_aspect((1, 1, 1))
        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-1.2, 1.2)
        ax.set_zlim(-1.2, 1.2)
        ax.view_init(elev=22, azim=-58)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_zticks([])
        title = ("yaw = 0°: tiga sumbu saling tegak lurus" if yaw == 0 else
                 "yaw = 90°: sumbu pitch jatuh di sumbu roll (lock)")
        ax.set_title(title, fontsize=10, color=INK if yaw == 0 else BAD)
    fig.suptitle("Gimbal untuk M = Rz(roll) · Ry(yaw) · Rx(pitch)", fontsize=11)
    save(fig, out_dir, "q3_gimbal_lock.png")


def _nlerp(q0, q1, t):
    q = tuple((1 - t) * a + t * b for a, b in zip(q0, q1))
    n = math.sqrt(sum(c * c for c in q))
    return tuple(c / n for c in q)


def fig_slerp_vs_linear(out_dir):
    """Q3d: angle reached vs t for slerp and normalised linear blend, plus the shrink of a plain matrix blend."""
    total = 160.0
    q0 = (1.0, 0.0, 0.0, 0.0)
    q1 = quat_from_axis_angle((0, 1, 0), total)
    ts = [i / 100 for i in range(101)]
    a_slerp = [quat_to_axis_angle(slerp(q0, q1, t))[1] for t in ts]
    a_nlerp = [quat_to_axis_angle(_nlerp(q0, q1, t))[1] for t in ts]
    # plain blend of the two rotation matrices: length of the blended x column
    c, s = math.cos(math.radians(total)), math.sin(math.radians(total))
    col = [math.hypot((1 - t) + t * c, t * s) for t in ts]
    assert quat_dot(q0, q1) > 0  # same hemisphere, so nlerp needs no sign flip here
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.0, 3.8))
    a1.plot(ts, [total * t for t in ts], color=MUTED, ls=":", lw=1.2, label="kecepatan konstan (ideal)")
    a1.plot(ts, a_slerp, color=BONE1, lw=2.4, label="slerp")
    a1.plot(ts, a_nlerp, color=BONE2, lw=2.0, ls="--", label="blend linear quaternion + normalisasi")
    a1.set_xlabel("t")
    a1.set_ylabel("sudut yang sudah ditempuh (derajat)")
    a1.set_title(f"Putaran {total:.0f}° terhadap sumbu y", fontsize=10)
    a1.legend(fontsize=8.5)
    a2.plot(ts, col, color=BAD, lw=2.2)
    a2.axhline(1.0, color=MUTED, ls=":", lw=1.2)
    a2.set_xlabel("t")
    a2.set_ylabel("panjang sumbu x model setelah blend")
    a2.set_ylim(0, 1.1)
    a2.set_title("Blend linear dua matriks rotasi: model menyusut", fontsize=10)
    save(fig, out_dir, "q3_slerp_vs_linear.png")


def _box(ax, xy, w, h, text, color, fontsize=10):
    ax.add_patch(FancyBboxPatch(xy, w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=color, ec=INK, lw=1.2))
    ax.text(xy[0] + w / 2, xy[1] + h / 2, text, ha="center", va="center", fontsize=fontsize, color=INK)


def _arrow(ax, p0, p1, text=None, rad=0.0):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=14, lw=1.4, color=INK,
                                 connectionstyle=f"arc3,rad={rad}"))
    if text:
        ax.text((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 + 0.12, text, ha="center", fontsize=8.5, color=MUTED)


def fig_game_loop(out_dir):
    """Q5: one frame of a real-time loop, marking where FK runs and where the Module 3 renderer takes over."""
    fig, ax = plt.subplots(figsize=(10.0, 4.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0.5, 4.4)
    ax.axis("off")
    _box(ax, (0.2, 2.2), 1.5, 1.0, "Input\nkeyboard,\nmouse, gamepad", "#eef2f7", 9)
    ax.add_patch(FancyBboxPatch((2.2, 1.35), 3.4, 2.7, boxstyle="round,pad=0.02,rounding_size=0.1",
                                fc="#fdf6ec", ec=BONE2, lw=1.6, ls="--"))
    ax.text(3.9, 3.85, "Update (dt)", ha="center", fontsize=10.5, color=BONE2, weight="bold")
    _box(ax, (2.4, 2.85), 1.45, 0.7, "AI / logika\ngame", "#ffffff", 9)
    _box(ax, (4.0, 2.85), 1.45, 0.7, "Fisika", "#ffffff", 9)
    _box(ax, (2.4, 1.55), 3.05, 1.0,
         "Animasi: sampel kurva → pose lokal\nFK root → leaf = matriks world\ntiap bone (IK di sini juga)",
         "#fde7cc", 8.5)
    ax.add_patch(FancyBboxPatch((6.1, 1.35), 2.4, 2.7, boxstyle="round,pad=0.02,rounding_size=0.1",
                                fc="#eef5ff", ec=BONE1, lw=1.6, ls="--"))
    ax.text(7.3, 3.85, "Render (Modul 3)", ha="center", fontsize=10.5, color=BONE1, weight="bold")
    _box(ax, (6.3, 2.55), 2.0, 1.0, "per mesh / bone:\np_clip = P · V · M · p", "#ffffff", 9)
    _box(ax, (6.3, 1.55), 2.0, 0.8, "rasterisasi,\nz-buffer, shading", "#ffffff", 9)
    _box(ax, (8.75, 2.2), 1.1, 1.0, "Present\nswap\nbuffer", "#eef2f7", 9)
    _arrow(ax, (1.7, 2.7), (2.2, 2.7))
    _arrow(ax, (5.6, 2.1), (6.1, 2.1), "M bone")
    _arrow(ax, (8.5, 2.7), (8.75, 2.7))
    ax.plot([9.3, 9.3, 0.95], [2.2, 0.75, 0.75], color=INK, lw=1.4)
    _arrow(ax, (0.95, 0.75), (0.95, 2.2))
    ax.text(5.1, 0.85, "frame berikutnya (sekitar 16,7 ms pada 60 fps)", ha="center", fontsize=8.5, color=MUTED)
    ax.text(5.0, 4.25, "Satu frame game loop", ha="center", fontsize=11, weight="bold")
    save(fig, out_dir, "q5_game_loop.png")


def fig_my_chain(out_dir):
    """My arm: joint points on the cropped photo (left) and FK of data/my_chain.json in cm (right)."""
    bones, data = load_chain()
    photo = data["photo"]
    x0, y0, x1, y1 = photo["crop_box_px"]
    w, h = photo["cropped_size_px"]
    sx, sy = w / (x1 - x0), h / (y1 - y0)
    to_crop = {k: ((p[0] - x0) * sx, (p[1] - y0) * sy) for k, p in photo["points_px"].items()}
    img = plt.imread(os.path.join(HERE, "data", photo["cropped_file"]))
    globals_deg, _ = angles_from_photo(data)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.4, 6.2), gridspec_kw={"width_ratios": [1, 1.15]})
    a1.imshow(img)
    a, b = to_crop["upper_arm_axis_a"], to_crop["upper_arm_axis_b"]
    a1.plot([a[0], b[0]], [a[1], b[1]], color="yellow", lw=2.5)
    e, wr, f = to_crop["elbow"], to_crop["wrist"], to_crop["fingertip"]
    a1.plot([e[0], wr[0]], [e[1], wr[1]], color=BONE2, lw=2.5)
    a1.plot([wr[0], f[0]], [wr[1], f[1]], color=GOOD, lw=2.5)
    for p, name in ((e, "siku"), (wr, "pergelangan"), (f, "ujung jari")):
        a1.plot(*p, "o", ms=9, mfc="none", mec=BAD, mew=2.2)
        a1.annotate(name, p, xytext=(8, 4), textcoords="offset points", color="white", fontsize=9,
                    bbox={"fc": "black", "alpha": 0.55, "lw": 0, "pad": 1.5})
    a1.annotate("arah lengan atas\n(bahu di luar foto)", a, xytext=(0, -38), textcoords="offset points",
                color="white", fontsize=8.5, bbox={"fc": "black", "alpha": 0.55, "lw": 0, "pad": 1.5})
    a1.set_axis_off()
    a1.set_title("Foto IMG_9035 (dipotong): titik sendi", fontsize=10)
    positions, angles = forward_kinematics(bones)
    colors = (BONE1, BONE2, GOOD)
    for i, color in enumerate(colors):
        p, q = positions[i], positions[i + 1]
        a2.plot([p[0], q[0]], [p[1], q[1]], color=color, lw=5, solid_capstyle="round",
                label=f"{data['bones'][i]['name']}: {bones[i].length:g} cm, lokal {bones[i].local_angle_deg:+.1f}°")
    for p, name in zip(positions, ("bahu", "siku", "pergelangan", "ujung jari")):
        a2.add_patch(Circle(p, 0.7, color=INK, zorder=5))
        a2.annotate(f"{name}\n({p[0]:.3f}, {p[1]:.3f})", p, xytext=(10, -2), textcoords="offset points",
                    fontsize=9, va="top")
    a2.axhline(0, color=MUTED, lw=0.8)
    a2.axvline(0, color=MUTED, lw=0.8)
    a2.set_xlim(-4, 48)
    a2.set_ylim(-8, 46)
    a2.set_aspect("equal")
    a2.set_xlabel("x (cm)")
    a2.set_ylabel("y (cm)")
    a2.legend(loc="upper center", bbox_to_anchor=(0.5, -0.11), fontsize=8)
    a2.set_title(f"FK dari my_chain.json (global {angles[0]:.1f}°, {angles[1]:.1f}°, {angles[2]:.1f}°)", fontsize=10)
    assert all(abs(g - a) < 0.05 for g, a in zip(globals_deg, angles))  # JSON angles = photo angles, 0.1 deg
    save(fig, out_dir, "my_chain_fk.png")


def fig_my_path(out_dir):
    """My camera path seen from above inside the Module 3 room, plus the spacing of its samples (T8)."""
    cps = load_my_path()
    path = sample_path(cps, samples_per_segment=10)
    dense = sample_path(cps, samples_per_segment=100)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.6, 5.6), gridspec_kw={"width_ratios": [1, 1.25]})
    # room outline from Module3/Source/data/mymodel_ukuran.json (x right, z towards the entrance)
    a1.add_patch(plt.Rectangle((-1.0, -2.0), 2.0, 4.0, fill=False, color=INK, lw=1.5))
    a1.add_patch(plt.Rectangle((0.6, -2.0), 0.4, 4.0, color="#c9b38f", alpha=0.6, label="lemari (0,4 m)"))
    a1.add_patch(plt.Rectangle((-0.5, 1.99), 1.59, 0.27, color=MUTED, alpha=0.5, label="sekat"))
    a1.add_patch(plt.Rectangle((-0.24, -0.15), 0.08, 0.30, color=BAD, label="patung kuda"))
    loop = sample_closed_path(cps, samples_per_segment=100)
    loop.append(loop[0])
    a1.plot([p[0] for p in loop], [p[2] for p in loop], color=GOOD, lw=1.2, ls="--", label="Catmull-Rom tertutup")
    a1.plot([p[0] for p in dense], [p[2] for p in dense], color=BONE1, lw=1.5, label="Catmull-Rom terbuka")
    a1.plot([p[0] for p in path], [p[2] for p in path], ".", color=BONE1, ms=4, label="51 sampel")
    a1.plot([p[0] for p in cps], [p[2] for p in cps], "o", color=BONE2, ms=8, label="6 titik kontrol")
    for i, p in enumerate(cps):
        a1.annotate(f"P{i}", (p[0], p[2]), xytext=(6, 4), textcoords="offset points", fontsize=9, color=BONE2)
    a1.annotate("awal", (path[0][0], path[0][2]), xytext=(-30, 12), textcoords="offset points", fontsize=8.5)
    a1.annotate("akhir", (path[-1][0], path[-1][2]), xytext=(-34, 8), textcoords="offset points", fontsize=8.5)
    a1.set_xlim(-1.2, 1.2)
    a1.set_ylim(-2.2, 2.5)
    a1.set_aspect("equal")
    a1.set_xlabel("x (m)")
    a1.set_ylabel("z (m), + ke arah pintu masuk")
    a1.legend(loc="lower left", fontsize=7.5)
    a1.set_title("Jalur saya dilihat dari atas, tinggi 1,15 m", fontsize=10)
    mine = sample_spacing(path)
    theirs = sample_spacing(sample_path(load_camera_path(), samples_per_segment=10))
    a2.plot(range(len(mine)), [g / max(mine) for g in mine], color=BONE1, marker=".",
            label=f"my_path (maks {max(mine):.3f} m)")
    a2.plot(range(len(theirs)), [g / max(theirs) for g in theirs], color=BONE2, marker=".",
            label=f"camera_path dosen (maks {max(theirs):.3f} m)")
    closed = sample_closed_path(cps, samples_per_segment=10)
    shut = sample_spacing(closed + [closed[0]])
    a2.plot(range(len(shut)), [g / max(mine) for g in shut], color=GOOD, marker=".", ls="--",
            label=f"my_path tertutup (maks {max(shut):.3f} m)")
    a2.set_ylim(0, 1.1)
    a2.set_xlabel("nomor langkah antar sampel")
    a2.set_ylabel("jarak langkah / jarak langkah terbesar")
    a2.legend(fontsize=8.5, loc="lower center")
    a2.set_title("Langkah t sama besar, jarak tempuh tidak (T8)", fontsize=10)
    save(fig, out_dir, "my_path.png")


def fig_ik_my_arm(out_dir):
    """IK on my own arm: the wrist measured in the photo is the target, IK must return the photo angles."""
    bones, data = load_chain()
    l1, l2 = bones[0].length, bones[1].length
    wrist = forward_kinematics(bones[:2])[0][-1]
    t1, t2 = solve_two_bone_ik(l1, l2, wrist)
    to_target = math.degrees(math.atan2(wrist[1], wrist[0]))
    fig, ax = plt.subplots(figsize=(6.6, 6.0))
    ax.add_patch(Circle((0, 0), l1 + l2, color=GOOD, alpha=0.10))
    ax.add_patch(Circle((0, 0), abs(l1 - l2), color="white"))
    ax.add_patch(Circle((0, 0), l1 + l2, fill=False, color=GOOD, ls="--", lw=1))
    ax.add_patch(Circle((0, 0), abs(l1 - l2), fill=False, color=BAD, ls="--", lw=1))
    ax.text(0, -(l1 + l2) + 2.0, f"terjangkau: {abs(l1 - l2):g} cm ≤ d ≤ {l1 + l2:g} cm", ha="center",
            color=GOOD, fontsize=9)
    for (a1, a2), color, ls, label in (((t1, t2), BONE1, "-", "hasil IK"),
                                       ((2 * to_target - t1, -t2), MUTED, "--", "solusi cermin")):
        (s, e, h), _ = forward_kinematics([Bone(l1, a1), Bone(l2, a2)])
        ax.plot([s[0], e[0], h[0]], [s[1], e[1], h[1]], color=color, ls=ls, lw=3.5 if ls == "-" else 2,
                label=f"{label}: θ1 = {a1:.2f}°, θ2 = {a2:.2f}°")
    ax.add_patch(Circle((0, 0), 0.9, color=INK, zorder=6))
    ax.plot(*wrist, marker="*", ms=16, color=BAD, zorder=6)
    ax.annotate(f"target = pergelangan di foto\n({wrist[0]:.3f}, {wrist[1]:.3f}) cm", wrist, xytext=(10, 6),
                textcoords="offset points", fontsize=9)
    ax.set_xlim(-56, 56)
    ax.set_ylim(-56, 56)
    ax.set_aspect("equal")
    ax.set_xlabel("x (cm)")
    ax.set_ylabel("y (cm)")
    ax.legend(loc="upper left", fontsize=8.5)
    ax.set_title(f"IK lengan saya ({l1:g} cm, {l2:g} cm) mengembalikan sudut foto "
                 f"({bones[0].local_angle_deg:+.1f}°, {bones[1].local_angle_deg:+.1f}°)", fontsize=10)
    save(fig, out_dir, "ik_my_arm.png")


def fig_foot_slide(out_dir):
    """Foot-slide gap before/after the fix, and pitfall (c): constant speed vs baked root-motion curve."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.6, 4.0))
    dt = 1.0 / 60.0
    before = diagnose(REPORTED_SPEED, dt=dt)
    after = diagnose(matched_speed(), dt=dt)
    a1.plot([t for t, _ in before], [g for _, g in before], color=BAD, lw=2.2,
            label=f"sebelum: {REPORTED_SPEED} m/s diketik di kode")
    a1.plot([t for t, _ in after], [g for _, g in after], color=GOOD, lw=2.2,
            label=f"sesudah: stride x rate = {matched_speed()} m/s")
    a1.axhline(0.05, color=MUTED, ls=":", lw=1)
    a1.text(3.2, 0.1, "5 cm", color=MUTED, fontsize=8.5)
    a1.set_xlabel("t (s)")
    a1.set_ylabel("celah root - kaki (m)")
    a1.set_title("Perbaikan: celah tepat 0 di setiap sampel", fontsize=10)
    a1.legend(fontsize=8.5, loc="upper left")
    flat = walk(STRIDE_CHANGE, constant_speed(matched_speed()))
    curve = walk(STRIDE_CHANGE, root_motion(STRIDE_CHANGE))
    a2.plot([r[0] for r in flat], [100 * r[3] for r in flat], color=BONE2, lw=1.8, label="kecepatan konstan 1,0 m/s")
    a2.plot([r[0] for r in curve], [100 * r[3] for r in curve], color=BONE1, lw=2.2,
            label="dibaca dari kurva root motion")
    a2.axvline(STRIDE_CHANGE[1][0], color=MUTED, ls="--", lw=1)
    a2.text(STRIDE_CHANGE[1][0] + 0.08, 30, f"stride {STRIDE_CHANGE[0][1]:g} → {STRIDE_CHANGE[1][1]:g} m",
            fontsize=8.5, color=MUTED)
    a2.set_xlabel("t (s), 60 fps")
    a2.set_ylabel("celah root - kaki (cm)")
    a2.set_title("Pitfall (c): stride berubah di tengah jalan", fontsize=10)
    a2.legend(fontsize=8.5, loc="upper left")
    save(fig, out_dir, "foot_slide_before_after.png")


SETS = {
    "studi": (fig_fk_chain, fig_ik_two_solutions, fig_spline_vs_linear, fig_gimbal_lock,
              fig_slerp_vs_linear, fig_game_loop),
    "readme": (fig_my_chain, fig_ik_my_arm, fig_my_path, fig_foot_slide),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--set", choices=sorted(SETS), default="studi")
    parser.add_argument("--out", help="output folder (default depends on --set)")
    args = parser.parse_args()
    out_dir = os.path.abspath(args.out or DEFAULT_OUT[args.set])
    os.makedirs(out_dir, exist_ok=True)
    for make in SETS[args.set]:
        make(out_dir)


if __name__ == "__main__":
    main()
