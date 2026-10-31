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
Added in Fase 3:
  - dither: 8-bit bands 2 px, 5-bit bands 16 px, Bayer dither breaks the bands
  - box_blur_3x3 equals the neighbour mean written out by hand on the E1 patch
  - bilinear: scale 1 is the identity, edges clamp ([0,100] x2 -> [0,25,75,100])
  - luma: every flat grey 0..255 matches Pillow convert("L") within 1 code
Added in Fase 4:
  - cvd: the chart legend stays distinct under deuteranopia, protanopia and
    grayscale, and the guard does fail on a red/green palette
  - aliasing: 0.1..0.9 cycles/px land at |f - fs|; box pre-filter amplitude as predicted
Added on 31 Oct 2026:
  - cvd: the published Machado et al. 2009 matrices (dichromacy) keep white white, keep the
    project legend distinct and collapse the red/green legend, so the legend guard's verdict
    does not depend on the course's ColorJack matrices
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


def t_dither():
    import dither
    dither._selftest()


def t_boxblur_3x3_by_hand():
    from boxblur import box_blur_3x3
    from make_data import running_patch
    P = running_patch()
    b = box_blur_3x3(P)
    # interior pixel (2,3): its 3x3 neighbourhood is P[1:4, 2:5], summed by hand
    assert P[1:4, 2:5].tolist() == [[24, 28, 40], [32, 36, 48], [40, 44, 56]]
    assert b[2, 3] == round((24 + 28 + 40 + 32 + 36 + 48 + 40 + 44 + 56) / 9) == 39


def t_bilinear_edges():
    from resample import resample_bilinear
    flat = np.full((5, 7, 3), 93, dtype=np.uint8)
    assert np.array_equal(resample_bilinear(flat, 2.5), np.full((12, 18, 3), 93, np.uint8))
    img = (np.arange(48, dtype=np.uint8) * 5).reshape(6, 8)
    assert np.array_equal(resample_bilinear(img, 1.0), img), "scale 1 must be the identity"
    up = resample_bilinear(np.array([[0, 100]], dtype=np.uint8), 2.0)
    assert up[0].tolist() == [0, 25, 75, 100], f"edge clamp: {up[0].tolist()}"


def t_luma_vs_pillow_flat():
    from luma import pillow_gap
    flat = np.repeat(np.arange(256, dtype=np.uint8), 3).reshape(1, 256, 3)
    assert pillow_gap(flat).max() <= 1


def t_cvd_legend_guard():
    import cvd
    cvd.assert_legend_safe(cvd.LEGEND)          # the palette our charts use must pass
    try:                                        # and the guard must catch a red/green palette
        cvd.assert_legend_safe(cvd.BAD_LEGEND)
    except AssertionError:
        return
    raise AssertionError("legend guard did not catch the red/green palette")


def t_cvd_machado_agrees():
    import cvd
    import numpy as np
    for kind, m in cvd.MACHADO_2009.items():
        assert np.allclose(m.sum(axis=1), 1.0, atol=2e-6), f"{kind}: white must stay white"
    for kind, d in cvd.compare_models(cvd.LEGEND).items():
        assert d["machado2009"] >= 20.0, f"project legend collapses under Machado {kind}: {d}"
    for kind, d in cvd.compare_models(cvd.BAD_LEGEND).items():
        assert d["machado2009"] < 20.0, f"red/green legend should collapse under Machado {kind}: {d}"


def t_aliasing():
    import aliasing_demo
    aliasing_demo._selftest()


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
        ("dither: bands 2/16 px, Bayer dither breaks them", t_dither),
        ("boxblur: 3x3 = hand neighbour mean", t_boxblur_3x3_by_hand),
        ("bilinear: identity, constant, edge clamp", t_bilinear_edges),
        ("luma: flat greys 0..255 = Pillow 'L' within 1", t_luma_vs_pillow_flat),
        ("cvd: chart legend survives deuter/protan/grayscale", t_cvd_legend_guard),
        ("aliasing: every f lands at its predicted |f - fs|", t_aliasing),
        ("cvd: Machado 2009 gives the same legend verdict", t_cvd_machado_agrees),
    ]
    ok = all(check(n, f) for n, f in checks)
    print("\n" + ("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
