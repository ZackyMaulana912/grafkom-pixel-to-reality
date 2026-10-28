"""Module 3 -- Lab 2 no 4: the far temple with and without a mipmap.

The temple is moved far away (camera pulled back along its view line), where
dozens of texels of the striped relief fall inside one pixel. Three numbers:

  * shimmer: mean |frame A - frame B| over the temple when the camera slides
    sideways by 1% of its distance (the geometry barely moves, so a big
    change is the texture aliasing, i.e. the flicker);
  * high-frequency energy: mean |Laplacian| of the luminance on the temple;
  * error against the truth: an 8x8 supersampled render averaged in linear
    light (what a perfect filter would show), as PSNR on the temple.

Run:  python mip_check.py     -> numbers + out/far_{nomip,mip,truth}.ppm
"""
from __future__ import annotations

import os

import numpy as np

import raster3d
from metrics import psnr
from ppm_io import read_ppm, write_ppm
from scene import load_scene
from srgb import linear_to_srgb, srgb_to_linear

W = H = 160
PULL = 5.0                          # camera distance x 5 -> temple about 1/5 the size
SS = 8                              # supersampling factor for the truth


def camera(sc, slide=0.0):
    c = sc["camera"]
    eye, ctr = np.asarray(c["eye"], float), np.asarray(c["center"], float)
    eye = ctr + (eye - ctr) * PULL
    side = np.cross(ctr - eye, (0, 1, 0))
    side /= np.linalg.norm(side)
    eye = eye + side * slide * np.linalg.norm(ctr - eye)
    return dict(eye=eye, center=ctr, far=c["far"] * PULL)


def render(sc, mip, slide=0.0, w=W, h=H):
    kw = raster3d.scene_kwargs(sc, w, h)
    kw.update(camera(sc, slide))
    col, dep, _ = raster3d.render(raster3d.load_scene_mesh(sc), tex_u8=_tex(sc), mip=mip, **kw)
    return col, np.isfinite(dep)


_cache = {}


def _tex(sc):
    if "t" not in _cache:
        _cache["t"] = read_ppm(sc["model"]["texture"])
    return _cache["t"]


def truth(sc, slide=0.0):
    big, _ = render(sc, mip=False, slide=slide, w=W * SS, h=H * SS)
    lin = srgb_to_linear(big.astype(float) / 255.0)
    lin = lin.reshape(H, SS, W, SS, 3).mean(axis=(1, 3))
    return np.clip(linear_to_srgb(lin) * 255, 0, 255).astype(np.uint8)


def hf_energy(img, mask):
    y = img.astype(float) @ [0.2126, 0.7152, 0.0722]
    lap = np.abs(4 * y[1:-1, 1:-1] - y[:-2, 1:-1] - y[2:, 1:-1] - y[1:-1, :-2] - y[1:-1, 2:])
    return float(lap[mask[1:-1, 1:-1]].mean())


def main():
    sc = load_scene("scenes/temple.json")
    os.makedirs("out", exist_ok=True)
    t0 = truth(sc)
    write_ppm("out/far_truth.ppm", t0)
    print(f"temple pulled back x{PULL:g}, {W}x{H}; truth = {SS}x{SS} supersampled, averaged in linear light")
    rows = []
    for mip in (False, True):
        a, cov = render(sc, mip)
        b, cov_b = render(sc, mip, slide=0.01)
        both = cov & cov_b
        name = "mip" if mip else "nomip"
        write_ppm(f"out/far_{name}.ppm", a)
        write_ppm(f"out/far_{name}_slide.ppm", b)
        shimmer = float(np.abs(a.astype(int) - b.astype(int))[both].mean())
        p = psnr(a[cov], t0[cov])
        rows.append((name, shimmer, hf_energy(a, cov), p))
    t_hf = hf_energy(t0, render(sc, False)[1])
    ys, xs = np.nonzero(render(sc, False)[1])
    y0, y1, x0, x1 = ys.min() - 4, ys.max() + 5, xs.min() - 4, xs.max() + 5
    for name in ("nomip", "nomip_slide", "mip", "mip_slide", "truth"):
        crop = read_ppm(f"out/far_{name}.ppm")[y0:y1, x0:x1]
        write_ppm(f"out/far_{name}_zoom.ppm", crop.repeat(4, 0).repeat(4, 1))     # nearest x4, no smoothing
    print(f"{'':8s} {'shimmer':>10s} {'HF energy':>10s} {'PSNR vs truth':>14s}")
    for name, s, e, p in rows:
        print(f"{name:8s} {s:10.2f} {e:10.2f} {p:11.1f} dB")
    print(f"{'truth':8s} {'':>10s} {t_hf:10.2f}")
    print("wrote out/far_{nomip,mip}{,_slide}.ppm, out/far_truth.ppm and *_zoom.ppm (x4 crops)")


if __name__ == "__main__":
    main()
