"""Module 1 -- run every from-scratch unit's self-test + its reference match.

This is what `make test` runs. Exit code 0 iff every check passes.

Covers (MASTER plan section 11.2):
  - ppm_io round-trip (P5 / P6)
  - srgb round-trip identity + Example E4 numbers
  - Example E1: running patch mean = 54; 2x2 box blur 4x4 result; nearest == a_ij
  - 1-D bilinear identity 25 / 50 / 75
  - histogram: max err vs numpy.histogram = 0
  - Example E5: luma of (200,100,50) -- correct ~126, naive-weights ~118, avg 117
  - luma of a flat grey maps to itself (+/-1)
  - metrics: psnr(equal)=inf, ssim(equal)=1, 52-level shift -> known dB
  - cvd: red/green collapses under deuteranopia, blue/orange survives
  - Example E6/E7 budget numbers exact to the byte
"""
from __future__ import annotations

import sys
import traceback

import numpy as np


def check(name, fn):
    try:
        fn()
        print(f"OK   {name}")
        return True
    except Exception:
        print(f"FAIL {name}")
        traceback.print_exc()
        return False


def t_ppm_io():
    import ppm_io
    ppm_io._selftest()


def t_srgb():
    import srgb
    srgb._demo()


def t_boxblur_patch():
    import boxblur
    boxblur._selftest()


def t_resample():
    import resample
    resample._selftest()


def t_histogram():
    import histogram
    histogram._selftest()


def t_luma():
    import luma
    luma._selftest()


def t_metrics():
    import metrics
    metrics._selftest()


def t_cvd():
    import cvd
    cvd._selftest()


def t_budget_exact():
    import budget as B
    assert B.bytes_per_frame(1920, 1080, 24) == 6_220_800          # E6
    assert B.bytes_per_frame(1920, 1080, 24) * 30 * 10 == 1_866_240_000
    assert B.bytes_per_frame(4096, 4096, 32) == 67_108_864          # E7 = 64 MiB
    assert abs(B.bytes_per_frame(4096, 4096, 32) / 2**20 - 64.0) < 1e-9
    assert abs(B.mip_chain_bytes(67_108_864) / 2**20 - 85.333) < 0.01
    assert abs(B.frame_ms(60) - 16.667) < 0.01
    assert abs(B.frame_ms(144) - 6.944) < 0.01


def t_make_data_patch():
    from make_data import running_patch
    P = running_patch()
    assert P.shape == (8, 8) and P.dtype == np.uint8
    assert int(round(P.mean())) == 54
    assert P[0, 0] == 0 and P[7, 7] == 108 and P[1, 1] == 12


def main() -> int:
    checks = [
        ("ppm_io round-trip", t_ppm_io),
        ("srgb round-trip + E4", t_srgb),
        ("make_data running patch (mean 54)", t_make_data_patch),
        ("boxblur: E1 2x2 result + mean 54", t_boxblur_patch),
        ("resample: nearest==a_ij, bilinear 25/50/75, checker split", t_resample),
        ("histogram: max err vs numpy = 0", t_histogram),
        ("luma: E5 numbers + flat-grey identity", t_luma),
        ("metrics: psnr/ssim sanity", t_metrics),
        ("cvd: red/green collapse under deuteranopia", t_cvd),
        ("budget: E6/E7 exact to the byte", t_budget_exact),
    ]
    ok = all(check(n, f) for n, f in checks)
    print("\n" + ("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
