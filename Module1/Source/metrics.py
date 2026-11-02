"""Module 1 -- image similarity metrics from scratch (NumPy only).

  psnr(a, b)  : peak signal-to-noise ratio in dB (8-bit, peak 255).
  ssim(a, b)  : a SIMPLE GLOBAL structural-similarity index (single window =
                the whole image). The real SSIM (Wang et al. 2004) slides an
                11x11 Gaussian window; this global version is enough to rank
                "how different" two downscales are and is what the module
                text quotes. Compare against skimage.metrics.ssim in an
                Optional Extension Lab and explain the gap.

  ssim_windowed(a, b) : the windowed SSIM of Wang et al. 2004 (added for the Optional
                Extension Lab above): 11x11 Gaussian window, sigma 1.5, K1 = 0.01,
                K2 = 0.03, only windows that fit inside the image ('valid'), mean of
                the SSIM map; colour images: mean over the channels.

Run:  python metrics.py --selftest
"""
from __future__ import annotations

import sys
import numpy as np


def psnr(a: np.ndarray, b: np.ndarray, peak: float = 255.0) -> float:
    a = a.astype(np.float64)
    b = b.astype(np.float64)
    if a.shape != b.shape:
        raise ValueError(f"psnr: shape mismatch {a.shape} vs {b.shape}")
    mse = np.mean((a - b) ** 2)
    if mse == 0:
        return float("inf")
    return float(10.0 * np.log10(peak * peak / mse))


def ssim(a: np.ndarray, b: np.ndarray, L: float = 255.0) -> float:
    a = a.astype(np.float64)
    b = b.astype(np.float64)
    if a.shape != b.shape:
        raise ValueError(f"ssim: shape mismatch {a.shape} vs {b.shape}")
    c1 = (0.01 * L) ** 2
    c2 = (0.03 * L) ** 2
    mu_a, mu_b = a.mean(), b.mean()
    va, vb = a.var(), b.var()
    cov = ((a - mu_a) * (b - mu_b)).mean()
    return float(((2 * mu_a * mu_b + c1) * (2 * cov + c2)) /
                 ((mu_a ** 2 + mu_b ** 2 + c1) * (va + vb + c2)))


def _gauss1d(size: int, sigma: float) -> np.ndarray:
    x = np.arange(size) - (size - 1) / 2.0
    g = np.exp(-x * x / (2.0 * sigma * sigma))
    return g / g.sum()


def _filter_valid(img: np.ndarray, g: np.ndarray) -> np.ndarray:
    """Weighted window mean at every position where the whole window fits (separable)."""
    k = len(g)
    h, w = img.shape
    rows = sum(g[i] * img[i:h - k + 1 + i, :] for i in range(k))
    return sum(g[j] * rows[:, j:w - k + 1 + j] for j in range(k))


def ssim_map(a: np.ndarray, b: np.ndarray, L: float = 255.0, size: int = 11, sigma: float = 1.5) -> np.ndarray:
    """Local SSIM of two single-channel images, one value per window position."""
    a = a.astype(np.float64)
    b = b.astype(np.float64)
    if a.shape != b.shape or a.ndim != 2:
        raise ValueError(f"ssim_map: need two equal 2-D images, got {a.shape} and {b.shape}")
    if min(a.shape) < size:
        raise ValueError(f"ssim_map: image {a.shape} smaller than the {size}x{size} window")
    g = _gauss1d(size, sigma)
    c1 = (0.01 * L) ** 2
    c2 = (0.03 * L) ** 2
    mu_a, mu_b = _filter_valid(a, g), _filter_valid(b, g)
    va = _filter_valid(a * a, g) - mu_a ** 2
    vb = _filter_valid(b * b, g) - mu_b ** 2
    cov = _filter_valid(a * b, g) - mu_a * mu_b
    return ((2 * mu_a * mu_b + c1) * (2 * cov + c2)) / ((mu_a ** 2 + mu_b ** 2 + c1) * (va + vb + c2))


def ssim_windowed(a: np.ndarray, b: np.ndarray, L: float = 255.0) -> float:
    if a.shape != b.shape:
        raise ValueError(f"ssim_windowed: shape mismatch {a.shape} vs {b.shape}")
    if a.ndim == 2:
        return float(ssim_map(a, b, L).mean())
    return float(np.mean([ssim_map(a[..., c], b[..., c], L).mean() for c in range(a.shape[2])]))


def _selftest() -> None:
    x = (np.arange(64, dtype=np.uint8).reshape(8, 8) * 3)
    assert psnr(x, x) == float("inf")
    assert abs(ssim(x, x) - 1.0) < 1e-9

    # a constant offset of 52 -> known PSNR
    off = np.full((8, 8), 100, np.uint8)
    off2 = np.full((8, 8), 152, np.uint8)
    expect = 10 * np.log10(255 ** 2 / 52 ** 2)
    assert abs(psnr(off, off2) - expect) < 1e-6, f"{psnr(off, off2)} vs {expect}"
    y = ((np.arange(256).reshape(16, 16) * 7) % 256).astype(np.uint8)
    assert abs(ssim_windowed(y, y) - 1.0) < 1e-9
    print(f"metrics self-test OK  (psnr(equal)=inf; ssim(equal)=1; ssim_windowed(equal)=1; "
          f"psnr for a 52-level shift = {expect:.2f} dB)")


if __name__ == "__main__":
    if "--selftest" in sys.argv or len(sys.argv) == 1:
        _selftest()
