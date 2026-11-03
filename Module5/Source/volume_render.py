"""Volume rendering: compositing the samples along one ray into one colour (NumPy only).

Module 3's z-buffer kept only the nearest surface. Here every sample counts:
    alpha_i = 1 - exp(-sigma_i * delta_i)           opacity of the step at sample i
    T_i     = (1 - alpha_1) ... (1 - alpha_(i-1))   light that reaches sample i, T_1 = 1
    w_i     = T_i * alpha_i                         what sample i adds to the pixel
    C       = sum_i w_i c_i + T_(N+1) c_bg
T_(N+1), the product over ALL N samples, is what is left for the background (the
module writes it T_N). The weights plus T_(N+1) always add up to 1. A hard surface
is no special case: it is alpha = 1, the limit of sigma -> infinity.
"""
from __future__ import annotations

import numpy as np


def alpha_from_density(sigma, delta):
    """Opacity of a step of length delta through density sigma."""
    return 1.0 - np.exp(-sigma * delta)


def composite(alphas, colors):
    """Front-to-back compositing of N samples.

    alphas: (N,), colors: (N, 3). Returns (colour without background, weights (N,),
    transmittance before each sample (N,), background weight T_(N+1)).
    """
    alphas = np.asarray(alphas, dtype=float)
    colors = np.asarray(colors, dtype=float)
    trans = np.cumprod(np.concatenate([[1.0], 1.0 - alphas]))  # T_1 .. T_(N+1)
    weights = trans[:-1] * alphas
    return weights @ colors, weights, trans[:-1], trans[-1]


def alphas_of(sigmas, deltas, is_opaque=None):
    """Per-sample opacity; a sample flagged opaque (a hard surface hit) is alpha = 1."""
    is_opaque = is_opaque or [False] * len(sigmas)
    return [1.0 if hard else float(alpha_from_density(s, d)) for s, d, hard in zip(sigmas, deltas, is_opaque)]


def render_ray(sigmas, deltas, colors, is_opaque=None):
    """sigmas and deltas -> alphas -> composite."""
    return composite(alphas_of(sigmas, deltas, is_opaque), colors)


# E2: two half-opaque steps of fog (sigma = 1 over delta = ln 2), then a hard blue surface
E2_SIGMAS = [1.0, 1.0, None]
E2_DELTAS = [float(np.log(2.0)), float(np.log(2.0)), None]
E2_COLORS = [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)]
E2_OPAQUE = [False, False, True]


def running_example():
    """E2: three samples composited into one pixel."""
    return render_ray(E2_SIGMAS, E2_DELTAS, E2_COLORS, E2_OPAQUE)


if __name__ == "__main__":
    final_color, weights, transmittance, bg_weight = running_example()
    alphas = alphas_of(E2_SIGMAS, E2_DELTAS, E2_OPAQUE)
    print("sample   T (before)   alpha    weight   colour")
    for lab, t, a, w in zip(["1 (red)  ", "2 (green)", "3 (blue) "], transmittance, alphas, weights):
        print(f"  {lab}   {t:.3f}         {a:.3f}    {w:.3f}")
    print(f"background weight (unblocked) = {bg_weight:.3f}")
    print(f"sum of weights + background   = {weights.sum() + bg_weight:.3f}  (must be 1.0)")
    print(f"final pixel colour (R,G,B)    = ({final_color[0]:.3f}, {final_color[1]:.3f}, {final_color[2]:.3f})")
