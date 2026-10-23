"""Module 1 -- diagrams for the Studi Pendahuluan (Q1a, Q1b, Q1c, Q2a, Q2c).

Writes PNGs to ../docs/studi-pendahuluan/img/. The sRGB curve uses the same
srgb.py as the rest of the module, so the plotted numbers match the code.

Run (from Module1/Source):
  python3 -m venv figures/.venv && figures/.venv/bin/pip install -r figures/requirements.txt
  figures/.venv/bin/python figures/make_figures.py
"""
from __future__ import annotations

import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from srgb import srgb_to_linear  # noqa: E402

OUT = os.path.join(HERE, "..", "..", "docs", "studi-pendahuluan", "img")
DPI = 200


def save(fig, name: str) -> None:
    path = os.path.normpath(os.path.join(OUT, name))
    fig.savefig(path, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {path}")


def sampling_1d() -> None:
    """Q1a: continuous signal, samples every delta, 3-bit levels, stair-step rebuild."""
    x = np.linspace(0, 10, 1000)
    f = lambda t: 0.5 + 0.3 * np.sin(0.9 * t) + 0.12 * np.sin(2.3 * t + 0.5)
    delta = 1.0
    xs = np.arange(0, 10 + 1e-9, delta)
    levels = 8                      # 3-bit, so the quantisation steps are visible
    qs = np.round(f(xs) * (levels - 1)) / (levels - 1)

    fig, ax = plt.subplots(figsize=(8, 3.6))
    for k in range(levels):
        ax.axhline(k / (levels - 1), color="0.88", lw=0.8, zorder=0)
    ax.plot(x, f(x), color="tab:blue", lw=2, label="sinyal kontinu (cahaya asli)")
    ax.step(np.append(xs, xs[-1] + delta), np.append(qs, qs[-1]), where="post",
            color="tab:red", lw=1.6, label="rekonstruksi tangga (stair-step)")
    ax.vlines(xs, 0, f(xs), color="0.6", lw=0.8, ls=":")
    ax.plot(xs, f(xs), "o", color="tab:orange", ms=6, label="titik sampel", zorder=3)
    ax.annotate("", xy=(3, 0.04), xytext=(2, 0.04),
                arrowprops=dict(arrowstyle="<->", color="black"))
    ax.text(2.5, 0.07, r"$\Delta$ = jarak sampel", ha="center", fontsize=9)
    ax.text(11.1, 3 / 7, "garis abu-abu\n= level\nkuantisasi\n(3-bit = 8)", fontsize=8,
            va="center")
    ax.set_xlim(-0.2, 11)
    ax.set_ylim(0, 1.0)
    ax.set_xlabel("posisi x (pixel)")
    ax.set_ylabel("intensitas")
    ax.set_title("Sampling (sumbu x) dan kuantisasi (sumbu y) pada sinyal 1D")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=3, fontsize=8)
    save(fig, "q1a_sampling_1d.png")


def aliasing() -> None:
    """Q1b: 0.7 cycles/px and 0.3 cycles/px give the same samples."""
    x = np.linspace(0, 10, 2000)
    n = np.arange(0, 11)
    fig, ax = plt.subplots(figsize=(8, 3.0))
    ax.plot(x, np.cos(2 * np.pi * 0.7 * x), color="tab:blue", lw=1.4,
            label="pola asli 0.7 cycles/pixel")
    ax.plot(x, np.cos(2 * np.pi * 0.3 * x), color="tab:red", lw=1.6, ls="--",
            label="alias 0.3 cycles/pixel = |0.7 - 1|")
    ax.plot(n, np.cos(2 * np.pi * 0.7 * n), "o", color="black", ms=6,
            label="sampel tiap 1 pixel (sama untuk keduanya)", zorder=3)
    ax.set_xlabel("posisi (pixel)")
    ax.set_ylim(-1.15, 1.15)
    ax.set_title("Di atas batas Nyquist 0.5 cycles/pixel, pola menyamar jadi frekuensi rendah")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=3, fontsize=8)
    save(fig, "q1b_aliasing.png")


def banding() -> None:
    """Q1c: the same 512 px ramp at 8-bit and 5-bit."""
    x = np.arange(512)
    rows = []
    for bits in (8, 5):
        levels = 2 ** bits
        code = np.floor(x * levels / 512)
        rows.append(code / (levels - 1))
    fig, axes = plt.subplots(2, 1, figsize=(8, 2.2))
    for ax, row, bits in zip(axes, rows, (8, 5)):
        ax.imshow(np.tile(row, (24, 1)), cmap="gray", vmin=0, vmax=1, aspect="auto",
                  interpolation="nearest")
        band = 512 // 2 ** bits
        ax.set_yticks([])
        ax.set_xticks([0, 128, 256, 384, 511])
        ax.set_ylabel(f"{bits}-bit", rotation=0, ha="right", va="center")
        ax.set_title(f"{2 ** bits} level, tiap pita {band} px", fontsize=9, loc="left")
    axes[-1].set_xlabel("posisi (pixel)")
    fig.tight_layout()
    save(fig, "q1c_banding.png")


def rgb_cube() -> None:
    """Q2a: RGB cube with black, white, primaries, secondaries and grey diagonal."""
    fig = plt.figure(figsize=(6.0, 5.6))
    ax = fig.add_subplot(projection="3d")
    corners = np.array([[i, j, k] for i in (0, 1) for j in (0, 1) for k in (0, 1)])
    for a in corners:
        for b in corners:
            if np.sum(np.abs(a - b)) == 1 and tuple(a) < tuple(b):
                ax.plot(*zip(a, b), color="0.55", lw=1)
    names = {
        (0, 0, 0): "hitam (0,0,0)", (1, 1, 1): "putih (1,1,1)",
        (1, 0, 0): "merah (1,0,0)", (0, 1, 0): "hijau (0,1,0)", (0, 0, 1): "biru (0,0,1)",
        (0, 1, 1): "cyan (0,1,1)", (1, 0, 1): "magenta (1,0,1)", (1, 1, 0): "kuning (1,1,0)",
    }
    for (r, g, b), label in names.items():
        ax.scatter(r, g, b, s=170, color=(r, g, b), edgecolor="black", depthshade=False)
        ax.text(r, g, b + 0.09, label, fontsize=8, ha="center")
    t = np.linspace(0, 1, 30)
    ax.scatter(t, t, t, c=np.stack([t, t, t], 1), s=12, depthshade=False)
    ax.set_xlabel("R")
    ax.set_ylabel("G")
    ax.set_zlabel("B")
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_zticks([0, 1])
    ax.view_init(elev=20, azim=-35)
    ax.set_box_aspect((1, 1, 1))
    ax.set_title("Kubus RGB", fontsize=11)
    fig.text(0.5, 0.04, "Primary (merah, hijau, biru) dan secondary (cyan, magenta, kuning) "
             "ada di sudut kubus.\nTitik-titik abu-abu dari hitam ke putih adalah "
             "diagonal abu-abu, tempat R = G = B.", ha="center", fontsize=8)
    save(fig, "q2a_rgb_cube.png")


def hsv_cylinder() -> None:
    """Q2a: HSV cylinder drawn in 2D so every label stays visible.

    Hue = angle around the axis, saturation = distance from the axis,
    value = height. The top face is V = 1, the bottom face is V = 0 (black).
    """
    b = 0.32            # ellipse squash for the oblique view
    height = 1.5        # screen height of V = 0 -> 1
    res = 700
    xs = np.linspace(-1.05, 1.05, res)
    ys = np.linspace(-0.5, height + 0.5, res)
    X, Y = np.meshgrid(xs, ys)
    img = np.ones((res, res, 4))
    img[..., 3] = 0.0

    def hsv_rgb(h, s, v):
        # vectorised HSV -> RGB, h in [0,1)
        i = np.floor(h * 6).astype(int) % 6
        f = h * 6 - np.floor(h * 6)
        p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
        choices = [(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)]
        out = np.zeros(h.shape + (3,))
        for k, (r, g, bl) in enumerate(choices):
            m = i == k
            out[m] = np.stack([np.broadcast_to(r, h.shape)[m], np.broadcast_to(g, h.shape)[m],
                               np.broadcast_to(bl, h.shape)[m]], -1)
        return out

    # front half of the side wall: a point at angle a (sin a < 0) and height v
    inside_x = np.abs(X) <= 1
    depth = np.sqrt(np.clip(1 - X ** 2, 0, None))
    v_side = (Y + b * depth) / height
    side = inside_x & (v_side >= 0) & (v_side <= 1)
    ang_side = (-np.arccos(np.clip(X, -1, 1))) % (2 * np.pi)
    rgb = hsv_rgb(ang_side / (2 * np.pi), np.ones_like(X), np.clip(v_side, 0, 1))
    img[side, :3] = rgb[side]
    img[side, 3] = 1.0
    # top face (V = 1): screen y = height + b * depth_y
    dy = (Y - height) / b
    r = np.sqrt(X ** 2 + dy ** 2)
    top = r <= 1
    rgb = hsv_rgb((np.arctan2(dy, X) % (2 * np.pi)) / (2 * np.pi), np.clip(r, 0, 1),
                  np.ones_like(X))
    img[top, :3] = rgb[top]
    img[top, 3] = 1.0

    fig, ax = plt.subplots(figsize=(6.4, 5.6))
    ax.imshow(img, extent=(xs[0], xs[-1], ys[0], ys[-1]), origin="lower", zorder=1)
    t = np.linspace(0, 2 * np.pi, 400)
    ax.plot(np.cos(t), height + b * np.sin(t), color="black", lw=1, zorder=2)
    ax.plot(np.cos(t[200:]), b * np.sin(t[200:]), color="black", lw=1, zorder=2)
    ax.plot(np.cos(t[:200]), b * np.sin(t[:200]), color="black", lw=0.8, ls="--", zorder=2)
    ax.plot([-1, -1], [0, height], color="black", lw=1, zorder=2)
    ax.plot([1, 1], [0, height], color="black", lw=1, zorder=2)

    # value: arrow beside the cylinder
    ax.annotate("", xy=(-1.25, height), xytext=(-1.25, 0),
                arrowprops=dict(arrowstyle="->", lw=1.4))
    ax.text(-1.32, height / 2, "Value (V)\n0 = hitam\n1 = paling\nterang",
            ha="right", va="center", fontsize=9)
    ax.text(0, -b - 0.12, "alas: V = 0, semuanya hitam", ha="center", va="top", fontsize=8)
    # saturation: radius on the top face
    ax.plot([0, 0.97], [height, height], color="black", lw=1.6, zorder=3)
    ax.plot(0, height, "o", color="black", ms=4, zorder=3)
    ax.text(0.48, height + 0.05, "Saturation (S)", ha="center", va="bottom", fontsize=9,
            zorder=4, bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
    ax.text(0, height - 0.06, "S = 0\n(abu-abu)", ha="center", va="top", fontsize=7, zorder=4,
            bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.8))
    # hue: arc above the top face plus three reference angles
    arc = np.linspace(0, np.deg2rad(120), 60)
    ax.plot(1.12 * np.cos(arc), height + (b + 0.12) * np.sin(arc), color="black", lw=1.2)
    ax.annotate("", xy=(1.12 * np.cos(arc[-1]), height + (b + 0.12) * np.sin(arc[-1])),
                xytext=(1.12 * np.cos(arc[-3]), height + (b + 0.12) * np.sin(arc[-3])),
                arrowprops=dict(arrowstyle="->", lw=1.2))
    ax.text(0.95, height + 0.5, "Hue (H) = sudut\n0-360° di sekeliling sumbu",
            ha="left", fontsize=9)
    for deg, label, dx in ((0, "0° merah", 0.08), (120, "120° hijau", 0.0),
                           (240, "240° biru", 0.0)):
        a = np.deg2rad(deg)
        px, py = np.cos(a), height + b * np.sin(a)
        ax.plot(px, py, "o", color="black", ms=4, zorder=3)
        if deg == 120:
            # left of the dot, clear of the hue arrow above it
            ax.text(px - 0.1, py, label, ha="right", va="center", fontsize=8, zorder=4)
            continue
        off = 0.14 if np.sin(a) >= 0 else -0.14
        ax.text(px + dx, py + off, label, ha="left" if deg == 0 else "center",
                va="bottom" if off > 0 else "top", fontsize=8, zorder=4)
    ax.set_xlim(-2.1, 2.2)
    ax.set_ylim(-0.75, height + 0.85)
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.set_title("Silinder HSV", fontsize=11)
    save(fig, "q2a_hsv_cylinder.png")


def srgb_curve() -> None:
    """Q2c: sRGB decode curve with the 50% code marked."""
    c = np.linspace(0, 1, 500)
    lin = srgb_to_linear(c)
    half = float(srgb_to_linear(0.5))
    fig, ax = plt.subplots(figsize=(5.4, 5.0))
    ax.plot(c, c, color="0.6", lw=1, ls=":", label="garis lurus (kalau kode = cahaya)")
    ax.plot(c, c ** 2, color="tab:green", lw=1.2, ls="--", label="pendekatan gamma-2")
    ax.plot(c, lin, color="tab:blue", lw=2.2, label="kurva sRGB asli (decode)")
    ax.plot([0.5, 0.5], [0, half], color="tab:red", lw=1)
    ax.plot([0, 0.5], [half, half], color="tab:red", lw=1)
    ax.plot(0.5, half, "o", color="tab:red", zorder=3)
    ax.annotate(f"kode 0.5 (abu-abu tengah)\n= cahaya {half:.3f}\n(gamma-2: 0.25)", xy=(0.5, half),
                xytext=(0.56, 0.08), fontsize=9,
                arrowprops=dict(arrowstyle="->", color="tab:red"))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.set_xlabel("kode sRGB di file (0-1)")
    ax.set_ylabel("linear light (0-1)")
    ax.set_title("Kurva transfer sRGB")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(color="0.92")
    save(fig, "q2c_srgb_curve.png")


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    sampling_1d()
    aliasing()
    banding()
    rgb_cube()
    hsv_cylinder()
    srgb_curve()


if __name__ == "__main__":
    main()
