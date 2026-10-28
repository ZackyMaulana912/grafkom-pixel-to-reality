"""Module 3 -- mipmaps: Module 1's Nyquist limit, applied to a texture (NumPy only).

A far-away surface squeezes many texels into one pixel; point or bilinear
sampling then picks a few of them and aliases (shimmer, Moire). A mipmap is a
pyramid of pre-filtered half-size copies; the renderer picks the level where
one texel is about one pixel, so it never undersamples.

Each level is a 2x2 box average IN LINEAR LIGHT (Module 1: averaging sRGB codes
darkens). Levels are blended trilinearly by the fractional level of detail.
"""
from __future__ import annotations

import numpy as np


def build_pyramid(tex_lin, levels=4):
    """Level 0 is the texture itself; each next level halves both sides."""
    pyr = [np.asarray(tex_lin, np.float64)]
    for _ in range(levels - 1):
        t = pyr[-1]
        h, w = t.shape[0] // 2 * 2, t.shape[1] // 2 * 2
        t = t[:h, :w]
        pyr.append(0.25 * (t[0::2, 0::2] + t[1::2, 0::2] + t[0::2, 1::2] + t[1::2, 1::2]))
    return pyr


def level_of_detail(u, v, size, axis_y=0, axis_x=1):
    """log2 of the texel footprint of one pixel, from the screen-space
    derivatives of (u, v) over a pixel grid. 0 = one texel per pixel."""
    tu, tv = u * size[1], v * size[0]
    dudx, dvdx = np.gradient(tu, axis=axis_x), np.gradient(tv, axis=axis_x)
    dudy, dvdy = np.gradient(tu, axis=axis_y), np.gradient(tv, axis=axis_y)
    rho = np.maximum(np.hypot(dudx, dvdx), np.hypot(dudy, dvdy))
    return np.log2(np.maximum(rho, 1e-12))


def sample_trilinear(pyr, u, v, lod, sampler):
    """Blend the two nearest levels. `sampler(tex, u, v)` is the bilinear
    sampler of the renderer, so mip and non-mip renders differ only in filtering."""
    lod = np.clip(lod, 0.0, len(pyr) - 1)
    lo = np.floor(lod).astype(int)
    frac = (lod - lo)[..., None]
    out = np.zeros(u.shape + (3,))
    for k in np.unique(lo):
        m = lo == k
        a = sampler(pyr[k], u[m], v[m])
        b = sampler(pyr[min(k + 1, len(pyr) - 1)], u[m], v[m])
        out[m] = a * (1 - frac[m]) + b * frac[m]
    return out
