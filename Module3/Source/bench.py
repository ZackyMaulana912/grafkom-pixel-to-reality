"""Module 3 -- Lab 3 no 3: frame time of raster3d.py vs raytrace.py, measured.

The prediction was written and committed before this file existed
(docs/prediksi/prediksi-raster-vs-raytrace.md). Every case renders the same
scene at the same size; one untimed warm-up, then the median of --runs.
Loading the mesh and texture is outside the timer (both renderers share it).

Run:  python bench.py [--runs 5]      -> table + out/bench.txt
"""
from __future__ import annotations

import argparse
import platform
import statistics
import time

import numpy as np

import raster3d
import raytrace
from ppm_io import read_ppm
from scene import load_scene


def timed(fn, runs):
    fn()                                                  # warm-up: caches, first allocation
    times = []
    for _ in range(runs):
        t0 = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t0)
    return statistics.median(times), min(times), max(times)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=5)
    args = ap.parse_args()
    lines = [f"python {platform.python_version()}, numpy {np.__version__}, {platform.machine()}, "
             f"median of {args.runs} runs after 1 warm-up"]
    print(lines[0])
    cases = [("mymodel", 512, False), ("mymodel", 256, False), ("mymodel", 512, True),
             ("temple", 512, False), ("temple", 256, False)]
    header = f"{'scene':8s} {'size':>5s} {'shadow':>6s} {'raster s':>9s} {'ray s':>9s} {'ratio':>6s}"
    print(header)
    lines.append(header)
    for name, size, shadow in cases:
        sc = load_scene(f"scenes/{name}.json")
        mesh, tex = raster3d.load_scene_mesh(sc), read_ppm(sc["model"]["texture"])
        r = timed(lambda: raster3d.render_scene(sc, size, size, mesh=mesh, tex=tex, shadow=shadow), args.runs)
        t = timed(lambda: raytrace.render_scene(sc, size, size, mesh=mesh, tex=tex, shadow=shadow), args.runs)
        row = (f"{name:8s} {size:5d} {'yes' if shadow else 'no':>6s} {r[0]:9.3f} {t[0]:9.3f} {t[0] / r[0]:6.1f}"
               f"   (raster {r[1]:.3f}-{r[2]:.3f}, ray {t[1]:.3f}-{t[2]:.3f})")
        print(row)
        lines.append(row)
    with open("out/bench.txt", "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("wrote out/bench.txt")


if __name__ == "__main__":
    main()
