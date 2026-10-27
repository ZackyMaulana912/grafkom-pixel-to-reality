"""Module 1 -- aliasing demo (Lab 2 no 5), NumPy only.

Job: sweep a pattern from 0.1 to 0.9 cycles per OUTPUT pixel, bring it down to
one sample per output pixel with and without a pre-filter, predict where every
frequency should land, and measure where it actually landed.

Set-up: the pattern is first rendered with K samples per output pixel (a stand
-in for the continuous scene), then reduced K -> 1 in two ways:
  no pre-filter : keep one of the K samples (decimation, like resample_nearest)
  box pre-filter: average all K samples (like a sensor pixel collecting light)

Prediction (fs = 1 sample per output pixel):
  frequency  : f if f <= 0.5, otherwise it folds back to |f - fs| = |f - 1|
  amplitude  : 1 without a pre-filter; with the K-sample box it is the box's
               frequency response |sin(pi f) / (K sin(pi f / K))|, about |sinc f|

Measurement: the strongest peak of the FFT of each 1000-sample output.

Run:
  python aliasing_demo.py --selftest
  python aliasing_demo.py --out report/      # table + chirp images
"""
from __future__ import annotations

import argparse
import os

import numpy as np

from ppm_io import write_ppm

N = 1000        # output samples: every tested f and |f - 1| is a whole FFT bin
K = 16          # fine samples per output pixel
FREQS = [round(0.1 * i, 1) for i in range(1, 10)]


def fine_positions(n_out: int, k: int = K) -> np.ndarray:
    """Centres of the k fine samples inside each output pixel, in output-pixel units."""
    return (np.arange(n_out * k) + 0.5) / k


def reduce(fine: np.ndarray, k: int, prefilter: bool) -> np.ndarray:
    blocks = fine.reshape(-1, k)
    return blocks.mean(axis=1) if prefilter else blocks[:, k // 2]


def predicted_frequency(f: float, fs: float = 1.0) -> float:
    return f if f <= fs / 2 else abs(f - fs)


def box_response(f: float, k: int = K) -> float:
    return abs(np.sin(np.pi * f) / (k * np.sin(np.pi * f / k)))


def strongest(signal: np.ndarray) -> tuple[float, float]:
    """(frequency in cycles/pixel, amplitude) of the largest FFT peak, DC removed."""
    n = len(signal)
    spec = np.fft.rfft(signal - signal.mean())
    b = int(np.argmax(np.abs(spec)))
    scale = 1 if 2 * b == n else 2          # the Nyquist bin has no mirror twin
    return b / n, scale * np.abs(spec[b]) / n


def sweep() -> list[dict]:
    x = fine_positions(N)
    rows = []
    for f in FREQS:
        fine = np.cos(2 * np.pi * f * x)
        f_raw, a_raw = strongest(reduce(fine, K, prefilter=False))
        f_box, a_box = strongest(reduce(fine, K, prefilter=True))
        rows.append({"f": f, "pred": predicted_frequency(f), "f_raw": f_raw, "a_raw": a_raw,
                     "f_box": f_box, "a_box": a_box, "a_box_pred": box_response(f)})
    return rows


def chirp(width: int = 1024, height: int = 48, f0: float = 0.1, f1: float = 0.9,
          k: int = 8) -> tuple[np.ndarray, np.ndarray]:
    """Vertical stripes whose frequency rises linearly from f0 to f1 across the width.
    Returns (no pre-filter, box pre-filter) as uint8 images."""
    x = fine_positions(width, k)
    phase = 2 * np.pi * (f0 * x + (f1 - f0) * x * x / (2 * width))
    fine = 0.5 + 0.5 * np.cos(phase)
    out = []
    for pf in (False, True):
        row = np.round(reduce(fine, k, pf) * 255).astype(np.uint8)
        out.append(np.tile(row, (height, 1)))
    return out[0], out[1]


def _selftest() -> None:
    for r in sweep():
        if r["f"] == 0.5:
            continue    # exactly at Nyquist the result depends on phase, see the table
        assert abs(r["f_raw"] - r["pred"]) < 1e-9, f"f={r['f']}: measured {r['f_raw']} vs {r['pred']}"
        assert abs(r["f_box"] - r["pred"]) < 1e-9
        assert abs(r["a_raw"] - 1.0) < 1e-6
        assert abs(r["a_box"] - r["a_box_pred"]) < 1e-6, f"f={r['f']}: box amplitude"
    print("aliasing self-test OK  (every f measured at its predicted |f - fs|; "
          "box pre-filter amplitude = predicted response)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest or not args.out:
        _selftest()
        return

    print(f"{'f':>4} | {'predicted':>9} | {'no pre-filter':^22} | {'box pre-filter':^34}")
    print(f"{'':>4} | {'|f - fs|':>9} | {'measured f':>10} {'amplitude':>10} | "
          f"{'measured f':>10} {'amplitude':>10} {'predicted':>10}")
    for r in sweep():
        nyq = r["f"] == 0.5
        tag = "  <- alias" if r["f"] > 0.5 else ("  <- Nyquist: depends on sample phase" if nyq else "")
        pred = f"{'n/a':>10}" if nyq else f"{r['a_box_pred']:10.3f}"
        print(f"{r['f']:4.1f} | {r['pred']:9.1f} | {r['f_raw']:10.3f} {r['a_raw']:10.3f} | "
              f"{r['f_box']:10.3f} {r['a_box']:10.3f} {pred}{tag}")
    phase = 2 * np.pi * 0.5 * fine_positions(1)[K // 2]
    print(f"     at f = 0.5 the kept sample sits at phase {phase:.3f} rad, so its amplitude is "
          f"|cos(phase)| = {abs(np.cos(phase)):.3f}; the box average is centred where cos = 0")

    raw, box = chirp()
    gap = np.full((8, raw.shape[1]), 255, dtype=np.uint8)
    os.makedirs(args.out, exist_ok=True)
    write_ppm(os.path.join(args.out, "aliasing_sweep.pgm"), np.vstack([raw, gap, box]))
    print(f"wrote {args.out}/aliasing_sweep.pgm (top: no pre-filter, bottom: box pre-filter; "
          f"0.1 -> 0.9 cycles/pixel left to right, 0.5 at x = 512)")


if __name__ == "__main__":
    main()
