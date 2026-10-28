"""Module 3 -- diagrams for the Studi Pendahuluan (plain SVG, no plotting library).

Every number drawn here is computed with transforms.py at run time, so the
pictures cannot drift from the code.

Run (from Source/):  .venv/bin/python figures/make_figures.py
                     -> ../docs/studi-pendahuluan/img/*.svg
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from transforms import perspective  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "docs", "studi-pendahuluan", "img")
FONT = 'font-family="Helvetica, Arial, sans-serif"'


def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">\n'
            f'<rect width="{w}" height="{h}" fill="#ffffff"/>\n{body}\n</svg>\n')


def text(x, y, s, size=13, anchor="middle", color="#222", weight="normal"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" {FONT} font-size="{size}" text-anchor="{anchor}" '
            f'fill="{color}" font-weight="{weight}">{s}</text>')


def arrow(x0, y0, x1, y1, color="#444"):
    return (f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{color}" '
            f'stroke-width="1.6" marker-end="url(#ah)"/>')


DEFS = ('<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#444"/></marker></defs>')


def space_chain():
    spaces = [("Object", "file OBJ"), ("World", "scene"), ("View", "kamera di origin"),
              ("Clip", "−w ≤ x,y,z ≤ w"), ("NDC", "[−1, 1]³"), ("Screen", "pixel + depth")]
    ops = ["× M", "× V", "× P", "÷ w", "viewport"]
    notes = ["4×4", "4×4", "4×4", "satu-satunya langkah non-linear", "scale + offset, y dibalik"]
    b = [DEFS]
    bw, gap, y = 112, 52, 40
    for i, (name, sub) in enumerate(spaces):
        x = 20 + i * (bw + gap)
        fill = "#fde9d9" if name in ("Clip", "NDC") else "#e3eefb"
        b.append(f'<rect x="{x}" y="{y}" width="{bw}" height="56" rx="8" fill="{fill}" stroke="#6a8bb5"/>')
        b.append(text(x + bw / 2, y + 24, name, 15, weight="bold"))
        b.append(text(x + bw / 2, y + 43, sub, 11, color="#555"))
        if i < len(ops):
            b.append(arrow(x + bw + 3, y + 28, x + bw + gap - 3, y + 28))
            b.append(text(x + bw + gap / 2, y - 6, ops[i], 13, weight="bold", color="#b04020"))
            b.append(text(x + bw + gap / 2, y + 80, notes[i], 10, color="#666"))
    b.append(text(510, 160, "clipping terhadap near plane terjadi di Clip space, SEBELUM ÷ w "
                  "(saat w ≤ 0, x/w berbalik tanda)", 12, color="#b04020"))
    return svg(1000, 180, "\n".join(b))


def pinhole():
    b = [DEFS]
    ox, oy, s = 70, 190, 34                          # pinhole at (ox, oy); 1 unit = s px along -z
    d, z, y = 2.0, 6.0, 3.0
    b.append(arrow(ox - 30, oy, ox + 11.5 * s, oy))
    b.append(text(ox + 11.5 * s, oy + 18, "−z (masuk ke scene)", 12, anchor="end"))
    b.append(arrow(ox, oy + 40, ox, oy - 150))
    b.append(text(ox - 10, oy - 150, "y", 13, anchor="end"))
    b.append(f'<line x1="{ox + d * s}" y1="{oy - 140}" x2="{ox + d * s}" y2="{oy + 30}" stroke="#888" stroke-dasharray="5,4"/>')
    b.append(text(ox + d * s, oy + 46, "bidang citra z = −d", 12))
    yp = d * y / z
    b.append(f'<polygon points="{ox},{oy} {ox + d * s},{oy} {ox + d * s},{oy - yp * s}" fill="#f7b267" fill-opacity="0.6" stroke="#c46a1c"/>')
    b.append(f'<polygon points="{ox},{oy} {ox + z * s},{oy} {ox + z * s},{oy - y * s}" fill="#9aa5b1" fill-opacity="0.25" stroke="#566"/>')
    b.append(f'<circle cx="{ox + z * s}" cy="{oy - y * s}" r="5" fill="#225"/>')
    b.append(text(ox + z * s + 10, oy - y * s - 8, "p = (x, y, z), z &lt; 0", 13, anchor="start"))
    b.append(f'<circle cx="{ox + d * s}" cy="{oy - yp * s}" r="4" fill="#c46a1c"/>')
    b.append(text(ox + d * s + 8, oy - yp * s - 8, "(x′, y′)", 13, anchor="start", color="#c46a1c"))
    b.append(f'<circle cx="{ox}" cy="{oy}" r="4" fill="#000"/>')
    b.append(text(ox - 6, oy + 22, "pinhole", 12, anchor="end"))
    b.append(text(ox + d * s / 2, oy + 16, "d", 13, color="#c46a1c", weight="bold"))
    b.append(text(ox + z * s / 2 + 30, oy + 30, "|z|", 13, weight="bold"))
    b.append(text(520, 60, "segitiga sebangun:", 14, anchor="start", weight="bold"))
    b.append(text(520, 86, "y′ / d = y / |z|", 14, anchor="start"))
    b.append(text(520, 110, "y′ = d·y / |z| ,  x′ = d·x / |z|", 14, anchor="start"))
    b.append(text(520, 140, "contoh di gambar: d = 2, z = −6, y = 3", 12, anchor="start", color="#555"))
    b.append(text(520, 160, f"→ y′ = 2·3/6 = {yp:g}", 12, anchor="start", color="#555"))
    return svg(820, 260, "\n".join(b))


def depth_curve():
    """Window depth (ndc+1)/2 against eye distance, from transforms.perspective."""
    b = [DEFS]
    x0, y0, W, H = 70, 30, 560, 260
    lo, hi = -2.0, 3.0                                # log10 metres: 0.01 .. 1000
    b.append(f'<rect x="{x0}" y="{y0}" width="{W}" height="{H}" fill="none" stroke="#999"/>')
    for e in range(int(lo), int(hi) + 1):
        x = x0 + (e - lo) / (hi - lo) * W
        b.append(f'<line x1="{x}" y1="{y0}" x2="{x}" y2="{y0 + H}" stroke="#eee"/>')
        b.append(text(x, y0 + H + 18, f"{10.0 ** e:g} m", 11))
    for v in (0, 0.25, 0.5, 0.75, 1.0):
        y = y0 + H - v * H
        b.append(text(x0 - 6, y + 4, f"{v:g}", 11, anchor="end"))
    curves = [((0.01, 1000.0), "#c0392b", "near 0,01 / far 1000"),
              ((1.0, 1000.0), "#2e86c1", "near 1 / far 1000")]
    for (n, f), col, lab in curves:
        P = perspective(60, 1.0, n, f)
        zs = np.logspace(np.log10(n), np.log10(f), 400)
        clip = P @ np.c_[np.zeros_like(zs), np.zeros_like(zs), -zs, np.ones_like(zs)].T
        d = (clip[2] / clip[3] + 1) / 2
        pts = " ".join(f"{x0 + (np.log10(z) - lo) / (hi - lo) * W:.1f},{y0 + H - dd * H:.1f}" for z, dd in zip(zs, d))
        b.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2.2"/>')
    P = perspective(60, 1.0, 0.01, 1000.0)
    c = P @ np.array([0, 0, -1.0, 1])
    d1 = (c[2] / c[3] + 1) / 2
    x1 = x0 + (0 - lo) / (hi - lo) * W
    b.append(f'<circle cx="{x1}" cy="{y0 + H - d1 * H}" r="4" fill="#c0392b"/>')
    b.append(text(x1 + 8, y0 + H - d1 * H + 18, f"1 m → depth {d1:.4f} (99,0% kode 24-bit sudah terpakai)", 11, anchor="start", color="#c0392b"))
    for i, (_, col, lab) in enumerate(curves):
        b.append(f'<line x1="{x0 + 330}" y1="{y0 + 170 + i * 20}" x2="{x0 + 360}" y2="{y0 + 170 + i * 20}" stroke="{col}" stroke-width="2.2"/>')
        b.append(text(x0 + 366, y0 + 174 + i * 20, lab, 11, anchor="start"))
    b.append(text(x0 + W / 2, y0 + H + 38, "jarak dari kamera (skala log)", 12))
    b.append(f'<text x="22" y="{y0 + H / 2}" {FONT} font-size="12" text-anchor="middle" transform="rotate(-90 22 {y0 + H / 2})">depth jendela 0..1</text>')
    return svg(660, 340, "\n".join(b))


def webgl_drawcall():
    b = [DEFS]
    stages = [("vertex buffer", "data"), ("vertex shader", "ditulis"), ("primitive assembly + clip", "tetap"),
              ("÷ w + viewport", "tetap"), ("rasteriser", "tetap"), ("fragment shader", "ditulis"),
              ("depth test / blend", "tetap"), ("framebuffer", "data")]
    col = {"ditulis": ("#d5f5e3", "#1e8449"), "tetap": ("#eaecee", "#5d6d7e"), "data": ("#fef9e7", "#9a7d0a")}
    bw, gap, y = 104, 22, 50
    for i, (name, kind) in enumerate(stages):
        x = 16 + i * (bw + gap)
        fill, stroke = col[kind]
        b.append(f'<rect x="{x}" y="{y}" width="{bw}" height="58" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
        words = name.split(" ")
        if len(name) > 14:
            mid = len(words) // 2
            b.append(text(x + bw / 2, y + 24, " ".join(words[:mid]), 12, weight="bold"))
            b.append(text(x + bw / 2, y + 39, " ".join(words[mid:]), 12, weight="bold"))
        else:
            b.append(text(x + bw / 2, y + 31, name, 12, weight="bold"))
        b.append(text(x + bw / 2, y + 76, kind, 11, color=stroke))
        if i < len(stages) - 1:
            b.append(arrow(x + bw + 2, y + 29, x + bw + gap - 2, y + 29))
    b.append(text(16, 26, "hijau = saya tulis sendiri (GLSL);  abu-abu = tetap di hardware GPU;  kuning = data", 12, anchor="start"))
    b.append(text(16 + 1.5 * (bw + gap), 160, "gl_Position = P · V · M · position", 12, color="#1e8449"))
    b.append(text(16 + 5.5 * (bw + gap), 160, "warna = texture(u, v) × Lambert", 12, color="#1e8449"))
    return svg(1020, 180, "\n".join(b))


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, fn in (("q1_space_chain", space_chain), ("q2_pinhole", pinhole),
                     ("q3_depth_curve", depth_curve), ("q5_webgl_drawcall", webgl_drawcall)):
        with open(os.path.join(OUT, name + ".svg"), "w") as fh:
            fh.write(fn())
    print(f"wrote 4 diagrams to {os.path.normpath(OUT)}/")


if __name__ == "__main__":
    main()
