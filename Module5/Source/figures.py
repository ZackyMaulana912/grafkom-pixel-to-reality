"""Module 5 -- figures for the docs (the only file that uses matplotlib).

Every ray, transmittance and weight drawn here is computed at run time with
the from-scratch modules (ray_generator.py, volume_render.py), so a picture
cannot drift from the code it illustrates. Nothing in those modules imports
this file.

Run (from Source/):
  .venv/bin/python figures.py --set studi    -> ../docs/studi-pendahuluan/img/*.png
  .venv/bin/python figures.py --set readme   -> ../docs/img/*.png  (run capture.py first)
"""
from __future__ import annotations

import argparse
import os

import matplotlib

matplotlib.use("Agg")  # file output only, no window
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle  # noqa: E402

import nerf_toy  # noqa: E402
from capture import DATA_DIR, FOV_DEG, RING_ANGLES, load_ppm  # noqa: E402
from ray_generator import pixel_to_camera_dir  # noqa: E402
from volume_render import composite  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = {
    "studi": os.path.join(HERE, "..", "docs", "studi-pendahuluan", "img"),
    "readme": os.path.join(HERE, "..", "docs", "img"),
}

INK = "#222222"
RAY = "#2f6db5"
ACCENT = "#d9822b"
MUTED = "#8a8a8a"
GOOD = "#2e8b57"

# the two by-hand cases of Q1(b): the module's E1 and my own variation
E1 = dict(u=400.0, v=240.0, f=100.0, cx=320.0, cy=240.0)
MINE = dict(u=200.0, v=330.0, f=120.0, cx=320.0, cy=240.0)
RGB = [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)]


def save(fig, out_dir, name):
    """Write a PNG without a timestamp/version tag, so reruns give the same bytes."""
    path = os.path.join(out_dir, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", metadata={"Software": None})
    plt.close(fig)
    print(f"wrote {os.path.relpath(path, HERE)}")


def _dir(case):
    return pixel_to_camera_dir(case["u"], case["v"], case["f"], case["f"], case["cx"], case["cy"])


def _box(ax, xy, w, h, text, color, fontsize=10):
    ax.add_patch(FancyBboxPatch(xy, w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=color, ec=INK, lw=1.2))
    ax.text(xy[0] + w / 2, xy[1] + h / 2, text, ha="center", va="center", fontsize=fontsize, color=INK)


def _arrow(ax, p0, p1, color=INK, lw=1.4):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=14, lw=lw, color=color))


def fig_pinhole_ray(out_dir):
    """Q1: the inverted pinhole. Left: top view (x right, z forward = -z) for E1 and my pixel.
    Right: side view of my pixel, with the pixel row v growing downward, and three points
    on the ray that all project back to the same pixel."""
    fig, (top, side) = plt.subplots(1, 2, figsize=(11.0, 4.8))
    for ax, title in ((top, "Tampak atas (bidang x-z)"), (side, "Tampak samping (bidang y-z), pixel saya")):
        ax.set_title(title, fontsize=10.5)
        ax.set_aspect("equal")
        ax.axhline(0, color=MUTED, lw=0.6)
        ax.axvline(0, color=MUTED, lw=0.6)
        ax.plot(0, 0, "o", color=INK, ms=6, zorder=5)
        ax.annotate("kamera\n(asal ray)", (0, 0), xytext=(6, 6), textcoords="offset points", fontsize=8.5)

    # top view: horizontal axis = camera x, vertical axis = depth along -z
    top.plot([-1.6, 1.6], [1, 1], color=INK, lw=2)
    top.text(1.62, 1.0, " bidang gambar\n z = -1", va="center", fontsize=8.5)
    for case, color, name in ((E1, RAY, "E1: pixel (400, 240), f = 100"), (MINE, ACCENT, "saya: pixel (200, 330), f = 120")):
        d = _dir(case)
        top.plot([0, 2.6 * d[0]], [0, -2.6 * d[2]], color=color, lw=2, label=name)
        top.plot(d[0], -d[2], "o", color=color, ms=6)
        top.annotate(f"x = {d[0]:+.2f}", (d[0], -d[2]), xytext=(8 if d[0] > 0 else -46, -16 if d[0] > 0 else 6), textcoords="offset points",
                     color=color, fontsize=9)
    top.set_xlim(-2.8, 2.6)
    top.set_ylim(-0.3, 2.8)
    top.set_xlabel("x kamera (+x ke kanan)")
    top.set_ylabel("jarak ke depan kamera (arah -z)")
    top.legend(loc="upper left", fontsize=8.5, frameon=False)

    # side view: horizontal axis = depth along -z, vertical axis = camera y (up)
    d = _dir(MINE)
    side.plot([1, 1], [-1.3, 1.3], color=INK, lw=2)
    side.annotate("", xy=(1.15, 0.3), xytext=(1.15, 1.25), arrowprops=dict(arrowstyle="-|>", color=GOOD))
    side.text(1.25, 0.78, "baris pixel v\ntumbuh ke bawah", color=GOOD, fontsize=8.5, va="center")
    side.annotate("", xy=(-0.18, 1.0), xytext=(-0.18, 0.0), arrowprops=dict(arrowstyle="-|>", color=MUTED))
    side.text(-0.25, 0.5, "y kamera\nke atas", color=MUTED, fontsize=8.5, ha="right", va="center")
    side.plot([0, 5.2], [0, 5.2 * d[1]], color=ACCENT, lw=2)
    for t in (1.0, 2.0, 5.0):
        p = t * d
        side.plot(-p[2], p[1], "o", color=ACCENT, ms=6)
        side.annotate(f"t = {t:g}", (-p[2], p[1]), xytext=(6, -14), textcoords="offset points", fontsize=8.5)
    side.text(2.4, -0.75, f"semua titik t·d jatuh di pixel yang sama\nd = ({d[0]:.2f}, {d[1]:.2f}, {d[2]:.2f})",
              fontsize=8.5, color=INK)
    side.set_xlim(-0.9, 5.6)
    side.set_ylim(-4.2, 1.5)
    side.set_xlabel("jarak ke depan kamera (arah -z)")
    side.set_ylabel("y kamera")
    save(fig, out_dir, "q1_pinhole_ray.png")


def fig_pipeline(out_dir):
    """Q2: the volume-rendering pipeline, pixel -> ray -> samples -> alpha -> composite -> colour."""
    fig, ax = plt.subplots(figsize=(11.0, 2.6))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 2.4)
    ax.axis("off")
    steps = [
        ("Pixel (u, v)", "#eef2f7"),
        ("Ray o + t·d\n(pinhole dibalik)", "#eef5ff"),
        ("Sampel t1 ... tN\ndi sepanjang ray", "#ffffff"),
        ("σi, ci → αi\nαi = 1 - exp(-σi δi)", "#fdf6ec"),
        ("Komposit depan\nke belakang\nwi = Ti αi", "#fde7cc"),
        ("Warna pixel\nC = Σ wi ci\n+ T(N+1) c_bg", "#e8f4ec"),
    ]
    w, gap = 1.55, 0.25
    for i, (text, color) in enumerate(steps):
        x = 0.15 + i * (w + gap)
        _box(ax, (x, 0.75), w, 1.1, text, color, 8.6)
        if i:
            _arrow(ax, (x - gap, 1.3), (x, 1.3))
    ax.text(5.5, 0.3, "Tidak ada cabang khusus untuk permukaan keras: permukaan opaque hanyalah σ sangat besar, jadi α = 1",
            ha="center", fontsize=8.6, color=MUTED)
    save(fig, out_dir, "q2_pipeline.png")


def _samples_panel(ax, alphas, title, background):
    color, weights, trans, bg = composite(alphas, RGB)
    x = np.arange(len(alphas))
    ax.bar(x - 0.27, trans, 0.25, color="#d9d9d9", ec=INK, label="T (sebelum sampel)")
    ax.bar(x, alphas, 0.25, color="#ffffff", ec=INK, hatch="//", label="α")
    ax.bar(x + 0.27, weights, 0.25, color=RGB, ec=INK, label="bobot w = T·α")
    ax.bar([len(alphas) + 0.27], [bg], 0.25, color=background, ec=INK, hatch="..")
    for xi, wv in zip(list(x + 0.27) + [len(alphas) + 0.27], list(weights) + [bg]):
        ax.text(xi, wv + 0.03, f"{wv:.2f}", ha="center", fontsize=8.5)
    ax.set_xticks(list(x) + [len(alphas)])
    ax.set_xticklabels(["1 merah", "2 hijau", "3 biru", "background\nT(N+1)"], fontsize=8.5)
    ax.set_ylim(0, 1.18)
    ax.set_xlim(-0.6, len(alphas) + 0.75)
    final = color + bg * np.array(background)
    ax.set_title(f"{title}\njumlah bobot = {weights.sum() + bg:.3f}, warna akhir = "
                 f"({final[0]:.2f}, {final[1]:.2f}, {final[2]:.2f})", fontsize=9.5)
    ax.add_patch(Rectangle((len(alphas) - 0.05, 0.62), 0.5, 0.2, fc=np.clip(final, 0, 1), ec=INK, lw=0.8))
    ax.text(len(alphas) + 0.2, 0.86, "warna akhir", ha="center", fontsize=8.5)


def fig_three_samples(out_dir):
    """Q2(c): T, alpha and weight per sample for E2 and for my own alphas (white background)."""
    fig, (a, b) = plt.subplots(1, 2, figsize=(11.0, 4.0), sharey=True)
    _samples_panel(a, [0.5, 0.5, 1.0], "E2: α = (0.5, 0.5, 1.0)", (1.0, 1.0, 1.0))
    _samples_panel(b, [0.2, 0.6, 0.5], "Variasi saya: α = (0.2, 0.6, 0.5), background putih", (1.0, 1.0, 1.0))
    handles, labels = a.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=8.5, frameon=False, bbox_to_anchor=(0.5, -0.06))
    save(fig, out_dir, "q2_tiga_sampel.png")


def fig_anchoring(out_dir):
    """Q5: marker-based vs markerless (SLAM) anchoring, schematic."""
    fig, (m, s) = plt.subplots(1, 2, figsize=(11.0, 4.0))
    for ax, title in ((m, "Berbasis marker"), (s, "Markerless (SLAM)")):
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 6)
        ax.axis("off")
        ax.set_title(title, fontsize=11)
        ax.add_patch(Polygon([(0.5, 1.0), (9.5, 1.0), (8.0, 2.6), (2.0, 2.6)], fc="#f3efe6", ec=MUTED))
        ax.add_patch(Rectangle((0.6, 3.6), 1.4, 2.0, fc="#eef2f7", ec=INK))
        ax.text(1.3, 4.6, "HP", ha="center", fontsize=9)
    # marker: printed pattern of known size fixes position, orientation and scale
    m.add_patch(Rectangle((4.3, 1.5), 1.4, 0.7, fc="#222222", ec=INK))
    m.add_patch(Rectangle((4.6, 1.65), 0.4, 0.2, fc="#ffffff", ec="#ffffff"))
    m.add_patch(Rectangle((5.1, 1.85), 0.3, 0.2, fc="#ffffff", ec="#ffffff"))
    m.add_patch(Polygon([(4.6, 2.2), (5.4, 2.2), (5.0, 3.8)], fc=ACCENT, ec=INK, alpha=0.85))
    _arrow(m, (2.0, 4.4), (4.6, 2.3), RAY)
    m.text(5.0, 0.45, "marker cetak berukuran diketahui:\nposisi, arah, dan skala dibaca dari pola itu",
           ha="center", fontsize=8.6)
    # markerless: feature points + detected plane + a hit-test ray
    rng = np.random.default_rng(0)
    pts = rng.uniform([1.5, 1.2], [8.5, 2.4], size=(28, 2))
    s.plot(pts[:, 0], pts[:, 1], "+", color=GOOD, ms=7)
    s.add_patch(Polygon([(2.6, 1.3), (7.6, 1.3), (6.9, 2.3), (3.3, 2.3)], fc=(0.18, 0.55, 0.34, 0.15), ec=GOOD, ls="--"))
    s.add_patch(Polygon([(4.7, 1.9), (5.5, 1.9), (5.1, 3.5)], fc=ACCENT, ec=INK, alpha=0.85))
    _arrow(s, (2.0, 4.4), (5.1, 1.9), RAY)
    s.text(3.5, 3.6, "ray hit test", color=RAY, fontsize=8.6, rotation=-28)
    s.text(5.0, 0.45, "kamera + sensor gerak memetakan titik fitur dan bidang lantai;\n"
                      "skala dalam meter berasal dari pelacakan, bukan dari marker", ha="center", fontsize=8.6)
    save(fig, out_dir, "q5_anchoring.png")


def fig_capture_ring(out_dir):
    """Lab 2 no 1: the scene with my horse, large renders for the eye (top) and the eight
    20 x 16 training images exactly as read from data/pusaka_capture/ (bottom)."""
    fig = plt.figure(figsize=(11.0, 6.6))
    big = [0, 90, 180, 225]
    for i, angle in enumerate(big):
        ax = fig.add_subplot(3, 4, i + 1)
        cam, c2w = nerf_toy.ring_camera(angle)
        ax.imshow(np.clip(nerf_toy.render_analytic(200, 160, FOV_DEG, cam, c2w, n_samples=96), 0, 1))
        ax.set_title(f"{angle} deg" + (" (kuda tertutup candi)" if angle == 225 else ""), fontsize=9)
        ax.axis("off")
    for i, angle in enumerate(RING_ANGLES):
        ax = fig.add_subplot(3, 4, 5 + i)
        ax.imshow(load_ppm(os.path.join(DATA_DIR, f"view_{angle:03d}.ppm")), interpolation="nearest")
        ax.set_title(f"view_{angle:03d}.ppm", fontsize=8.5)
        ax.axis("off")
    fig.suptitle("Atas: render besar untuk dilihat (200 x 160). Bawah: 8 gambar latih 20 x 16 px apa adanya",
                 fontsize=10)
    save(fig, out_dir, "capture_ring.png")


_PAIR = {}


def _trained_pair():
    """The 2-view and 8-view grids of nerf_bug.py, trained once per run of this script."""
    if not _PAIR:
        import nerf_bug
        _PAIR["bug"] = nerf_bug
        _PAIR["2"] = nerf_bug._train_on(nerf_bug.BUGGY_ANGLES)[0]
        _PAIR["8"] = nerf_bug._train_on(nerf_bug.FIXED_ANGLES)[0]
    return _PAIR["bug"], _PAIR["2"], _PAIR["8"]


def _psnr_at(nb, grid, angle):
    cam, c2w = nerf_toy.ring_camera(angle, radius=nb.RADIUS, height=nb.CAM_HEIGHT)
    target = nerf_toy.render_analytic(nb.W, nb.H, nb.FOV, cam, c2w, nb.NEAR, nb.FAR, nb.N_SAMPLES)
    pred = nerf_toy.render_grid(grid, nb.W, nb.H, nb.FOV, cam, c2w, nb.NEAR, nb.FAR, nb.N_SAMPLES)[0]
    return nerf_toy.psnr(pred, target), target, pred


def fig_view_coverage(out_dir):
    """Lab 2 no 3: PSNR of both grids all around the ring, training views marked."""
    nb, g2, g8 = _trained_pair()
    angles = np.arange(0.0, 360.0, 2.5)
    p2 = [_psnr_at(nb, g2, a)[0] for a in angles]
    p8 = [_psnr_at(nb, g8, a)[0] for a in angles]
    fig, ax = plt.subplots(figsize=(11.0, 4.2))
    ax.plot(angles, p8, color=RAY, lw=2, label="8 view (tiap 45 derajat)")
    ax.plot(angles, p2, color=ACCENT, lw=2, label="2 view (0 dan 20 derajat)")
    for v in nb.FIXED_ANGLES:
        ax.axvline(v, color=RAY, lw=0.8, ls=":")
    for v in nb.BUGGY_ANGLES:
        ax.axvline(v, color=ACCENT, lw=1.2, ls="--")
    tested = [a for a in nb.SWEEP_ANGLES if a % 360 not in nb.FIXED_ANGLES]
    ax.plot(tested, [_psnr_at(nb, g2, a)[0] for a in tested], "o", color=ACCENT, ms=6)
    ax.plot(tested, [_psnr_at(nb, g8, a)[0] for a in tested], "o", color=RAY, ms=6, label="sudut di prediksi")
    ax.set_xlim(0, 360)
    ax.set_xticks(range(0, 361, 45))
    ax.set_xlabel("sudut kamera di lingkaran (derajat); garis putus = view latih")
    ax.set_ylabel("PSNR (dB)")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper right", fontsize=9, frameon=False)
    save(fig, out_dir, "view_coverage.png")


def fig_novel_views(out_dir):
    """The largest held-out gap (60 deg) as images: target, both predictions, |error| x4."""
    nb, g2, g8 = _trained_pair()
    p2, target, pred2 = _psnr_at(nb, g2, 60.0)
    p8, _, pred8 = _psnr_at(nb, g8, 60.0)
    panels = [("target 60 derajat", target), (f"2 view: {p2:.2f} dB", pred2), (f"8 view: {p8:.2f} dB", pred8),
              ("|selisih| x4, 2 view", np.abs(pred2 - target) * 4), ("|selisih| x4, 8 view", np.abs(pred8 - target) * 4)]
    fig, axs = plt.subplots(1, 5, figsize=(12.0, 2.6))
    for ax, (title, img) in zip(axs, panels):
        ax.imshow(np.clip(img, 0, 1), interpolation="nearest")
        ax.set_title(title, fontsize=9)
        ax.axis("off")
    save(fig, out_dir, "novel_60.png")


def fig_pitfall_init(out_dir):
    """Lab 2 no 4 (a): training MSE for four starting densities at two learning rates."""
    import pitfall_fix
    curves = pitfall_fix.init_experiment()
    colors = {-5.0: "#c0392b", -2.0: ACCENT, 0.0: GOOD, 2.0: RAY}
    fig, axs = plt.subplots(1, 2, figsize=(11.0, 3.9), sharey=True)
    for ax, lr in zip(axs, pitfall_fix.LEARNING_RATES):
        for start in pitfall_fix.INIT_VALUES:
            it, mse = zip(*curves[(lr, start)])
            ax.plot(it, mse, color=colors[start], lw=2, label=f"sigma_raw awal {start:+g}")
        ax.set_title(f"learning rate {lr:g}", fontsize=10)
        ax.set_xlabel("iterasi")
        ax.grid(alpha=0.3)
    axs[0].set_ylabel("MSE latih (8 view)")
    axs[0].legend(fontsize=8.5, frameon=False)
    save(fig, out_dir, "pitfall_init.png")


def fig_third_view(out_dir):
    """Lab 2 no 4 (b): what one extra view does, on the fixed held-out angles and around the ring."""
    import pitfall_fix
    rows = pitfall_fix.third_view_experiment()
    names = [r[0] for r in rows]
    held = [float(np.mean(r[3])) for r in rows]
    ring = [r[4] for r in rows]
    x = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(11.0, 3.9))
    ax.bar(x - 0.2, held, 0.38, color="#d9d9d9", ec=INK, label="rata-rata 8 sudut uji (prediksi)")
    ax.bar(x + 0.2, ring, 0.38, color=RAY, ec=INK, label="rata-rata seluruh lingkaran tiap 5 derajat")
    for xi, v in zip(x + 0.2, ring):
        ax.text(xi, v + 0.1, f"{v:.2f}", ha="center", fontsize=8.5)
    ax.set_xticks(x)
    ax.set_xticklabels(["2 view\n(0, 20)"] + [f"+ {n[2:]}" for n in names[1:-1]] + ["8 view"], fontsize=9)
    ax.set_ylim(9, 15)
    ax.set_ylabel("PSNR (dB)")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(loc="upper left", fontsize=8.5, frameon=False)
    save(fig, out_dir, "third_view.png")


SETS = {
    "studi": [fig_pinhole_ray, fig_pipeline, fig_three_samples, fig_anchoring],
    "readme": [fig_capture_ring, fig_view_coverage, fig_novel_views, fig_pitfall_init, fig_third_view],
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
