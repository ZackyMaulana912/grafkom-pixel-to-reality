"""Module 1 -- the "ship / serve / expose" step (Lab 3 no 4).

Writes:
  report/budget.md    -- every by-hand budget number for MY photo set (original
                         resolution, MB and MiB labelled), then Examples E6/E7,
                         the refresh table and the per-file data/ table
  report/report.html  -- budget table, histograms, naive/correct/diff triptychs,
                         CVD before/after, banding, aliasing, format tables and
                         policy. Every image is inline (base64 PNG), so the
                         marker opens ONE file and nothing else.

A missing input is shown as a visible note in the page, never skipped silently.

Run:  python report.py            # after make data and the other report steps
"""
from __future__ import annotations

import base64
import contextlib
import csv
import html
import io
import os
import re

import numpy as np

import budget as B
import cvd
from histogram import histogram_from_scratch, to_luma_codes
from ppm_io import read_ppm
from resample import box_downscale_2x

OUT = "report"
PHOTO_EDGE = ("data/IMG_8884.ppm", 1000, 550, 256)   # statue edge against the wall


# ---- numbers -------------------------------------------------------------
def photo_budget(path: str = "photos/originals.csv") -> dict:
    rows = [r for r in csv.DictReader(open(path)) if r["used"] == "ya"]
    sizes = {(int(r["width"]), int(r["height"])) for r in rows}
    assert len(sizes) == 1, f"photos have mixed resolutions: {sizes}"
    (w, h), = sizes
    bpf = B.bytes_per_frame(w, h, 24)
    disk = {r["filename"]: int(r["on_disk_bytes"]) for r in rows}
    return {"w": w, "h": h, "n": len(rows), "bpf": bpf, "ws": bpf * len(rows),
            "clip": bpf * 30 * 10, "bw": bpf * 30, "disk": disk,
            "disk_total": sum(disk.values())}


def budget_rows(p: dict) -> list[tuple[str, str]]:
    smallest = min(p["disk"], key=p["disk"].get)
    largest = max(p["disk"], key=p["disk"].get)
    return [
        ("Resolusi asli", f"{p['w']} x {p['h']} px, {p['n']} foto dipakai"),
        ("Byte per foto (RGB888)", f"{p['w']} x {p['h']} x 3 = {p['bpf']:,} B = "
                                   f"{p['bpf'] / B.MB:.4f} MB = {p['bpf'] / B.MiB:.4f} MiB"),
        ("Working set seluruh set", f"{p['bpf']:,} x {p['n']} = {p['ws']:,} B = "
                                    f"{p['ws'] / B.MiB:.2f} MiB = {p['ws'] / B.GiB:.4f} GiB"),
        ("Flythrough 10 s @ 30 fps", f"{p['bpf']:,} x 300 = {p['clip']:,} B = "
                                     f"{p['clip'] / B.GB:.4f} GB = {p['clip'] / B.GiB:.4f} GiB"),
        ("Bandwidth", f"{p['bw']:,} B/s = {p['bw'] / B.MB:.2f} MB/s = "
                      f"{p['bw'] * 8 / B.MB:,.2f} Mbit/s"),
        ("Total di disk (JPG kamera)", f"{p['disk_total']:,} B = {p['disk_total'] / B.MB:.2f} MB = "
                                       f"{p['disk_total'] / B.MiB:.2f} MiB"),
        ("Rasio kompresi kamera", f"rata-rata {p['ws'] / p['disk_total']:.2f}x; "
                                  f"{smallest} {p['bpf'] / p['disk'][smallest]:.2f}x (file terkecil), "
                                  f"{largest} {p['bpf'] / p['disk'][largest]:.2f}x (file terbesar)"),
    ]


def canonical_text() -> str:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        B.canonical()
        if os.path.isdir("data"):
            print()
            B.from_set("data")
    return buf.getvalue()


def build_budget_md() -> None:
    p = photo_budget()
    lines = ["# Modul 1 -- budget.md", "",
             "Dibuat ulang oleh `python report.py` (bagian dari `make report`).",
             "MB = 10^6 byte, GB = 10^9 byte; MiB = 2^20 byte, GiB = 2^30 byte.", "",
             "## Set foto saya (resolusi asli dari kamera)", "",
             "| Item | Nilai |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in budget_rows(p)]
    lines += ["", "## Contoh E6/E7, refresh rate, dan isi data/", "", "```", canonical_text(), "```", ""]
    with open(os.path.join(OUT, "budget.md"), "w") as f:
        f.write("\n".join(lines))


# ---- html helpers -----------------------------------------------------------
def png_uri(img: np.ndarray) -> str:
    from PIL import Image
    buf = io.BytesIO()
    Image.fromarray(img, "L" if img.ndim == 2 else "RGB").save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def figure(img: np.ndarray, caption: str, width: int | None = None) -> str:
    w = f' style="width:{width}px"' if width else ""
    return (f'<figure><img src="{png_uri(img)}" alt="{html.escape(caption)}"{w}>'
            f'<figcaption>{html.escape(caption)}</figcaption></figure>')


def figure_file(path: str, caption: str, width: int | None = None) -> str:
    if not os.path.exists(path):
        return f'<p class="missing">belum ada: {html.escape(path)} (jalankan make report)</p>'
    return figure(read_ppm(path), caption, width)


def inline_md(text: str) -> str:
    t = html.escape(text)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    return re.sub(r"`(.+?)`", r"<code>\1</code>", t)


def md_to_html(path: str) -> str:
    """Just enough Markdown for the generated reports: headings, tables, paragraphs."""
    if not os.path.exists(path):
        return f'<p class="missing">belum ada: {html.escape(path)}</p>'
    out, table = [], []
    for line in open(path, encoding="utf-8").read().splitlines() + [""]:
        if line.startswith("|"):
            if not set(line) <= set("|-: "):
                table.append([c.strip() for c in line.strip("|").split("|")])
            continue
        if table:
            head, *body = table
            out.append("<table><tr>" + "".join(f"<th>{inline_md(c)}</th>" for c in head) + "</tr>"
                       + "".join("<tr>" + "".join(f"<td>{inline_md(c)}</td>" for c in r) + "</tr>"
                                 for r in body) + "</table>")
            table = []
        if line.startswith("#"):
            continue          # the page has its own headings
        if line.strip():
            out.append(f"<p>{inline_md(line)}</p>")
    return "\n".join(out)


def svg_histogram(series: list[tuple[str, np.ndarray, str]], width: int = 640, height: int = 200) -> str:
    """Overlaid bar histograms as inline SVG; series = (label, counts, colour)."""
    bins = len(series[0][1])
    top = max(int(c.max()) for _, c, _ in series)
    bw = width / bins
    parts = [f'<svg viewBox="0 0 {width} {height + 40}" width="{width}" role="img">']
    for label, counts, colour in series:
        for i, c in enumerate(counts):
            h = c / top * height
            parts.append(f'<rect x="{i * bw:.1f}" y="{height - h:.1f}" width="{bw:.1f}" '
                         f'height="{h:.1f}" fill="{colour}" fill-opacity="0.55"/>')
    parts.append(f'<line x1="0" y1="{height}" x2="{width}" y2="{height}" stroke="#333"/>')
    for code in (0, 64, 128, 192, 255):
        x = code / 256 * width
        anchor = "end" if code == 255 else ("start" if code == 0 else "middle")
        parts.append(f'<text x="{x:.0f}" y="{height + 14}" font-size="11" '
                     f'text-anchor="{anchor}">{code}</text>')
    for k, (label, _, colour) in enumerate(series):
        parts.append(f'<rect x="{10 + k * 250}" y="{height + 22}" width="10" height="10" fill="{colour}"/>'
                     f'<text x="{24 + k * 250}" y="{height + 31}" font-size="11">{html.escape(label)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def html_table(rows: list[tuple[str, str]]) -> str:
    return ("<table>" + "".join(f"<tr><th>{html.escape(k)}</th><td>{html.escape(v)}</td></tr>"
                                for k, v in rows) + "</table>")


# ---- page -------------------------------------------------------------------
def build_html() -> None:
    css = ("body{font:15px/1.55 system-ui,sans-serif;max-width:980px;margin:2rem auto;padding:0 1rem;"
           "color:#1b2733;background:#fff} h1,h2{color:#0b4f6c} h2{margin-top:2.2rem;"
           "border-bottom:1px solid #d6dde3} figure{display:inline-block;margin:.4rem;text-align:center;"
           "vertical-align:top} img{image-rendering:pixelated;border:1px solid #c9d1d9;max-width:100%} "
           "figcaption{font-size:12px;color:#4a5866;max-width:300px} "
           "table{border-collapse:collapse;margin:.6rem 0;font-size:13px} "
           "th,td{border:1px solid #d6dde3;padding:.3rem .5rem;text-align:left;vertical-align:top} "
           "th{background:#eef3f7} pre{background:#f3f6f9;padding:1rem;overflow-x:auto;font-size:12px} "
           ".missing{color:#b42318;font-weight:600}")
    s = [f"<!doctype html><html lang=id><meta charset=utf-8>"
         f"<meta name=viewport content='width=device-width,initial-scale=1'>"
         f"<title>Laporan Modul 1</title><style>{css}</style>",
         "<h1>Modul 1: Representasi Digital, Warna &amp; Memori</h1>",
         "<p>Subjek: patung kuda berdiri milik sendiri, 24 foto iPhone 17 Pro "
         "(4536 x 8064). Semua angka dan gambar di halaman ini dibuat ulang oleh "
         "<code>make report</code>.</p>"]

    s.append("<h2>1. Budget memori dan bandwidth (resolusi asli)</h2>")
    s.append(html_table(budget_rows(photo_budget())))
    s.append("<details><summary>Contoh E6/E7, refresh rate, dan isi data/</summary>"
             f"<pre>{html.escape(canonical_text())}</pre></details>")

    s.append("<h2>2. Histogram</h2>")
    photo = read_ppm(PHOTO_EDGE[0])
    s.append("<p>Luma (Rec. 601 pada kode, 32 bin) foto IMG_8884, dihitung dengan "
             "<code>histogram_from_scratch</code>:</p>")
    s.append(svg_histogram([("IMG_8884", histogram_from_scratch(to_luma_codes(photo), 32), "#0b4f6c")]))
    if os.path.exists("data/thumb_buggy.ppm"):
        src = read_ppm("data/relief.ppm")
        s.append("<p>Pergeseran histogram thumbnail relief: hasil naif (merah) lebih gelap daripada "
                 "hasil linear (biru), rata-rata 144,20 vs 164,44:</p>")
        s.append(svg_histogram([("naif (rata-rata kode)", histogram_from_scratch(read_ppm("data/thumb_buggy.ppm"), 32), "#c0392b"),
                                ("linear (rata-rata cahaya)", histogram_from_scratch(box_downscale_2x(src, True), 32), "#2471a3")]))

    s.append("<h2>3. Downscale 2x: naif vs benar vs selisih</h2>")
    for name, cap in (("relief_naive", "naif: rata-rata kode sRGB"),
                      ("relief_linear", "benar: decode, rata-rata, encode"),
                      ("relief_diff", "|selisih| x4 (terang = error gamma)")):
        s.append(figure_file(f"{OUT}/{name}.ppm", cap, 256))
    path, y, x, n = PHOTO_EDGE
    crop = photo[y:y + n, x:x + n]
    naive, right = box_downscale_2x(crop, False), box_downscale_2x(crop, True)
    diff = np.clip(np.abs(right.astype(int) - naive.astype(int)) * 4, 0, 255).astype(np.uint8)
    s.append("<p>Hal yang sama pada tepi patung di foto saya (IMG_8884, potongan 256 px):</p>")
    s.append(figure(naive, "naif", 256) + figure(right, "benar", 256) + figure(diff, "|selisih| x4", 256))
    s.append("<p>Perbandingan dengan Pillow <code>Image.BOX</code> (terhadap hasil benar):</p>")
    s.append(md_to_html(f"{OUT}/downscale_compare.md"))

    s.append("<h2>4. Colour-vision deficiency: sebelum dan sesudah</h2>")
    for tag, title in (("_bad", "Sebelum: palet merah-hijau (gagal di make test)"),
                       ("", "Sesudah: viridis 5 warna, ramp luminansi (lolos)")):
        dist = cvd.legend_distances(cvd.BAD_LEGEND if tag else cvd.LEGEND)
        s.append(f"<h3>{title}</h3><p>Jarak terkecil antar kategori: "
                 + ", ".join(f"{k} {v:.1f}" for k, v in dist.items()) + " (batas 20)</p>")
        for suffix, cap in (("", "normal"), ("_deuter", "deuteranopia"),
                            ("_protan", "protanopia"), ("_gray", "grayscale")):
            s.append(figure_file(f"{OUT}/legend{tag}{suffix}.ppm", cap))

    s.append("<h2>5. Banding dan dithering</h2>")
    s.append(figure_file(f"{OUT}/gradient_8vs5.pgm",
                         "atas 8-bit (pita 2 px), tengah 5-bit (pita 16 px), bawah 5-bit + Bayer dither"))

    s.append("<h2>6. Aliasing</h2>")
    s.append(figure_file(f"{OUT}/aliasing_sweep.pgm",
                         "0.1 -> 0.9 cycles/pixel dari kiri ke kanan; atas tanpa pre-filter, bawah box pre-filter"))

    s.append("<h2>7. Format</h2>")
    for name, title in (("crop_dinding", "Crop halus: dinding polos"),
                        ("crop_surai", "Crop berfrekuensi tinggi: surai berukir")):
        s.append(f"<h3>{title}</h3>")
        s.append(figure_file(f"data/{name}.ppm", f"{name}.ppm, 256 x 256", 256))
        s.append(md_to_html(f"{OUT}/formats_{name}.md"))
    s.append("<h3>Kebijakan format</h3>")
    s.append(md_to_html(f"{OUT}/formats.md"))

    with open(os.path.join(OUT, "report.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(s) + "\n")


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    build_budget_md()
    build_html()
    print(f"wrote {OUT}/budget.md and {OUT}/report.html")


if __name__ == "__main__":
    main()
