"""Module 1 -- recompute every number used in the Studi Pendahuluan (Q1-Q3).

Each value printed here is the one written in
../docs/studi-pendahuluan/studi-pendahuluan.md. Every value is also asserted,
so the script exits non-zero if the write-up and the arithmetic ever disagree.

Run:  .venv/bin/python prelim_check.py
"""
from __future__ import annotations

import colorsys

import numpy as np

from budget import GB, GiB, MB, MiB, bytes_per_frame, frame_ms, mip_chain_bytes
from srgb import linear_to_srgb, srgb_to_linear


def close(a, b, tol=1e-9):
    assert abs(a - b) <= tol, f"{a} != {b}"


def q1() -> None:
    print("== Q1(b): 0.7 cycles/px sampled at 1 sample/px ==")
    n = np.arange(512)
    a = np.cos(2 * np.pi * 0.7 * n)
    b = np.cos(2 * np.pi * 0.3 * n)
    # identical at every integer sample, so the grid cannot tell them apart
    err = np.max(np.abs(a - b))
    print(f"  max |cos(2pi*0.7n) - cos(2pi*0.3n)| over 512 samples = {err:.1e}")
    assert err < 1e-9

    print("\n== Q1(c): 512 px black-to-white gradient ==")
    x = np.arange(512)
    for bits, want_band in ((8, 2), (5, 16)):
        levels = 2 ** bits
        q = 1 / (levels - 1)
        # equal-width bins: each code owns 512/L input pixels
        codes = np.floor(x * levels / 512).astype(int)
        widths = np.bincount(codes)
        assert len(np.unique(codes)) == levels and set(widths) == {want_band}
        # module formula code = round(v * (L-1)) with v = x/511: end bands are half width
        rcodes = np.round(x / 511 * (levels - 1)).astype(int)
        rwidths = np.bincount(rcodes)
        print(f"  {bits}-bit: L = {levels}, q = 1/{levels - 1} = {q:.4f} "
              f"(= {255 * q:.2f} codes on an 8-bit scale), band = {want_band} px")
        print(f"         with round(v*(L-1)): first/last band = {rwidths[0]}/{rwidths[-1]} px, "
              f"inner bands = {sorted(set(rwidths[1:-1].tolist()))} px")
    close(1 / 255, 0.00392156862745098)
    close(1 / 31, 0.03225806451612903)


def q2() -> None:
    print("\n== Q2(b): RGB (200,100,50) -> HSV by hand ==")
    r, g, b = 200 / 255, 100 / 255, 50 / 255
    mx, mn = max(r, g, b), min(r, g, b)
    c = mx - mn
    h = 60 * (((g - b) / c) % 6)   # max is R
    s = c / mx
    v = mx
    print(f"  R,G,B = {r:.4f}, {g:.4f}, {b:.4f}")
    print(f"  max = {mx:.4f}, min = {mn:.4f}, chroma = {c:.4f}")
    print(f"  H = 60 * ((G-B)/C mod 6) = {h:.2f} deg, S = C/max = {s:.4f}, V = max = {v:.4f}")
    close(h, 20.0)
    close(s, 0.75)
    ref = colorsys.rgb_to_hsv(r, g, b)
    close(ref[0] * 360, h, 1e-9)
    close(ref[1], s)
    close(ref[2], v)
    print("  matches colorsys.rgb_to_hsv")

    print("\n== Q2(c): where does code 0.5 land in linear light ==")
    lin_half = float(srgb_to_linear(0.5))
    enc_half = float(linear_to_srgb(0.5))
    print(f"  srgb_to_linear(0.5) = {lin_half:.4f}  (gamma-2 approx: 0.25)")
    print(f"  linear_to_srgb(0.5) = {enc_half:.4f} -> code {enc_half * 255:.1f}")
    close(round(lin_half, 3), 0.214)
    close(round(enc_half * 255, 1), 187.5)

    print("\n== Q2(d): three operations done on codes instead of light ==")
    # (i) average of black and white
    naive = (0 + 255) / 2
    right = float(linear_to_srgb((srgb_to_linear(0.0) + srgb_to_linear(1.0)) / 2)) * 255
    print(f"  (i)  average 0 and 255 : naive {naive:.1f}, correct {right:.1f} -> naive too dark")
    # (ii) 50% white over black, plus 50/50 red over green
    rg_naive = np.array([127.5, 127.5, 0.0])
    rg_right = linear_to_srgb((srgb_to_linear(np.array([1.0, 0, 0]))
                               + srgb_to_linear(np.array([0, 1.0, 0]))) / 2) * 255
    print(f"  (ii) 50% red over green: naive {np.round(rg_naive).astype(int)}, "
          f"correct {np.round(rg_right).astype(int)} -> naive dark muddy olive")
    # (iii) halve the brightness by halving the code
    half_code_light = float(srgb_to_linear(0.5))
    print(f"  (iii) code x0.5 gives {half_code_light:.3f} of the light, not 0.5 -> too dark")
    # doubling a code: 64 -> 128
    l64, l128 = float(srgb_to_linear(64 / 255)), float(srgb_to_linear(128 / 255))
    print(f"        code 64 -> 128 changes light {l64:.4f} -> {l128:.4f} = x{l128 / l64:.2f}, "
          f"not x2 -> too bright")
    assert naive < right and half_code_light < 0.5 and rg_naive[0] < rg_right[0]
    assert l128 / l64 > 2


def q3() -> None:
    print("\n== Q3(a): 1920x1080 RGB888 ==")
    bpf = bytes_per_frame(1920, 1080, 24)
    clip = bpf * 30 * 10
    bw = bpf * 30
    print(f"  frame : {bpf:,} B = {bpf / MB:.4f} MB = {bpf / MiB:.4f} MiB")
    print(f"  clip  : {clip:,} B = {clip / GB:.5f} GB = {clip / GiB:.4f} GiB")
    print(f"  bw    : {bw:,} B/s = {bw / MB:.3f} MB/s = {bw / MiB:.2f} MiB/s")
    print(f"          {bw * 8:,} bit/s = {bw * 8 / GB:.3f} Gbit/s")
    assert bpf == 6_220_800 and clip == 1_866_240_000 and bw == 186_624_000

    print("\n== Q3(b): 4096x4096 RGBA8 atlas ==")
    base = bytes_per_frame(4096, 4096, 32)
    mip = mip_chain_bytes(base)
    exact = sum(bytes_per_frame(4096 >> k, 4096 >> k, 32) for k in range(13))
    fit = 8 * GiB / mip
    print(f"  no mips    : {base:,} B = {base / MiB:.0f} MiB")
    print(f"  x4/3 mips  : {mip:,.0f} B = {mip / MiB:.2f} MiB "
          f"(exact chain down to 1x1: {exact:,} B)")
    print(f"  in 8 GiB   : 8192 MiB / {mip / MiB:.2f} MiB = {fit:.2f} atlases")
    print(f"  200 atlases: {200 * mip / MiB:,.1f} MiB = {200 * mip / GiB:.2f} GiB "
          f"= {200 * mip / (8 * GiB):.2f}x the card")
    bc7 = 200 * mip_chain_bytes(4096 * 4096 * 1)   # BC7: 16 B per 4x4 block = 1 B/px
    print(f"  200 atlases as BC7 (1 B/px) with mips: {bc7 / GiB:.2f} GiB")
    assert base == 64 * MiB
    close(mip / MiB, 256 / 3, 1e-9)
    close(fit, 96.0, 1e-9)

    print("\n== Q3(c): refresh rate -> time per frame ==")
    for hz in (24, 60, 120, 144):
        print(f"  {hz:3d} Hz : 1000/{hz} = {frame_ms(hz):.2f} ms")
    print("\n== Q3(d): 2- and 3-blade shutter ==")
    for blades in (2, 3):
        print(f"  24 fps x {blades} flashes = {24 * blades} Hz")


def main() -> None:
    q1()
    q2()
    q3()
    print("\nALL STUDI PENDAHULUAN NUMBERS CHECKED")


if __name__ == "__main__":
    main()
