"""Module 1 -- histogram-shift plot for the gamma diagnosis (Lab 2 no 2).

Uses gamma_diagnosis.py for every number, so the plot and the printed
diagnosis can never disagree. Writes ../docs/prediksi/img/diagnosis_histogram.png.

Run (from Module1/Source):  figures/.venv/bin/python figures/diagnosis_plot.py
"""
from __future__ import annotations

import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)
sys.path.insert(0, SRC)
from gamma_diagnosis import diagnose  # noqa: E402
from ppm_io import read_ppm  # noqa: E402

OUT = os.path.join(SRC, "..", "docs", "prediksi", "img")


def main() -> None:
    thumb = read_ppm(os.path.join(SRC, "data", "thumb_buggy.ppm"))
    d = diagnose(read_ppm(os.path.join(SRC, "data", "relief.ppm")), thumb)
    ht, hl = d["hist_thumb"], d["hist_light"]
    edges = np.arange(32) * 8
    mt, ml = float(thumb.mean()), float(d["h2"].mean())   # exact means, not bin centres

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 3.8), gridspec_kw={"width_ratios": [3, 2]})
    a1.bar(edges, ht, width=8, align="edge", color="tab:red", alpha=0.6,
           label=f"thumbnail yang gelap (rata-rata {mt:.2f})")
    a1.bar(edges, hl, width=8, align="edge", color="tab:blue", alpha=0.45,
           label=f"kalau cahaya dijaga (rata-rata {ml:.2f})")
    for m, c in ((mt, "tab:red"), (ml, "tab:blue")):
        a1.axvline(m, color=c, ls="--", lw=1.2)
    a1.annotate("", xy=(ml, a1.get_ylim()[1] * 0.92), xytext=(mt, a1.get_ylim()[1] * 0.92),
                arrowprops=dict(arrowstyle="<-", lw=1.3))
    a1.set_xlabel("kode sRGB (bin 8 kode)")
    a1.set_ylabel("jumlah nilai channel")
    a1.set_title("Histogram bergeser ke kiri: thumbnail lebih gelap")
    a1.legend(fontsize=8, loc="upper left")

    ct, db = d["contrast"], d["darker_by"]
    groups = [(32, 96), (96, 160), (160, 256)]
    means = [db[(ct >= lo) & (ct < hi)].mean() for lo, hi in groups]
    a2.bar([f"{lo}-{hi - 1}" for lo, hi in groups], means, color="0.45")
    for i, m in enumerate(means):
        a2.text(i, m + 0.4, f"{m:.1f}", ha="center", fontsize=9)
    a2.set_xlabel("kontras di dalam blok 2x2 (max - min, kode)")
    a2.set_ylabel("lebih gelap rata-rata (kode)")
    a2.set_title("Makin kontras bloknya, makin gelap hasilnya")
    fig.tight_layout()
    os.makedirs(OUT, exist_ok=True)
    path = os.path.normpath(os.path.join(OUT, "diagnosis_histogram.png"))
    fig.savefig(path, dpi=200, facecolor="white")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
