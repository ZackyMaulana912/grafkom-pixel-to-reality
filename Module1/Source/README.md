# Module 1 -- Digital Representation, Colour & Memory (reference repo)

Course: *Grafika Komputer / Computer Graphics* (`25MP7716G030`), S1 Informatika
semester 5. Companion to `../../Module1_EN.tex`.

**Rule:** every from-scratch unit is **NumPy only**. Pillow appears solely as
(a) the single reference call each primitive is matched against and (b) the
JPG/PNG/WebP/AVIF encoder in `format_compare.py`. No imaging library touches
the from-scratch code paths.

All inputs are **deterministic** -- `make_data.py` synthesises them with no
RNG, so the whole study reproduces with no camera and no binary assets in Git.
Your **graded** input is your own heritage building's photos (Lab 1); this set
is the documented fallback.

## Quick start

```bash
cd Module1/Source            # in this repo the module's code/Module1 lives here
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
make data      # synthetic set + my photos + the two Lab 3 crops -> data/
make test      # -> "ALL CHECKS PASSED"
make report    # -> report/budget.md + report/report.html
make png       # -> ../docs/img/*.png for Module1/README.md
# then open report/report.html
```

Windows without `make`: use Git Bash / WSL, or run the `python ...` lines from
the `Makefile` directly.

## Unit table

| File | Job | Reproduces | From scratch? |
|---|---|---|---|
| `ppm_io.py` | P5/P6 PGM/PPM read+write | infrastructure | yes (no imaging lib) |
| `srgb.py` | sRGB <-> linear (real curve + gamma-2 approx) | E4, E5 decode steps | yes |
| `make_data.py` | deterministic heritage image set + `manifest.csv` | E1 patch; Case Study inputs | yes |
| `histogram.py` | histogram from raw codes | Worked Example Step 2 (`max err = 0`) | yes; matched to `numpy.histogram` |
| `boxblur.py` | 2x2 downscale + 3x3 blur | E1 (`[[6,22,38,54],...]`, mean 54) | yes |
| `resample.py` | nearest / bilinear / gamma-correct box | E1 nearest==a_ij; bilinear 25/50/75; Step 3 | yes; caveats vs Pillow noted |
| `luma.py` | RGB->grey: decode, Rec.709, encode | E5 (~126 vs ~118 vs 117) | yes; cross-checked vs Pillow `"L"` |
| `cvd.py` | deuteranopia/protanopia 3x3 sim + tests | section "Colour-Vision Deficiency" | yes |
| `metrics.py` | PSNR + simple global SSIM | Step 3 numbers | yes (global SSIM only) |
| `budget.py` | bytes/frame, clip, bandwidth, mip chain, ms/frame | E6, E7, refresh table | yes |
| `gamma_resize_bug.py` | the washed-out downscale: diagnose / fix / prove | Step 3/4 | uses `resample.py` |
| `format_compare.py` | JPG/PNG/WebP/AVIF size + PSNR | E8, Step 5 | Pillow = codec under test |
| `report.py` | writes `report/budget.md` + `report/report.html` | MASTER 5.13 ship step | -- |
| `tests.py` | aggregates every self-test; `make test` entry point | MASTER 11.2 | -- |

## What `make test` asserts (hand-checkable invariants)

- `ppm_io` P5 and P6 round-trip exactly.
- sRGB decode/encode round-trip within 1e-9; `linear_to_srgb(0.5)*255` in
  [187,188]; gamma-2 version ~= 180.3.
- **Example E1:** running patch mean = 54; `box_blur_2x2_downscale(P)` equals
  `[[6,22,38,54],[22,38,54,70],[38,54,70,86],[54,70,86,102]]`;
  `resample_nearest(P,2)` equals `a_ij = 16*(i+j)`.
- 1-D bilinear of `[0,100]` at t = 0.25/0.5/0.75 gives 25/50/75.
- `histogram_from_scratch` vs `numpy.histogram`: **max err = 0** for bins
  2..32.
- **Example E5:** grey of `(200,100,50)` -- correct (gamma-2) in [124,128],
  naive Rec.709 weights in [116,120], plain average = 117; grey of a flat 128
  maps to 128 +/-1.
- `psnr(x,x)=inf`, `ssim(x,x)=1`, a constant 52-level shift gives
  `10*log10(255^2/52^2)` dB.
- **CVD:** a pure red / pure green pair collapses under the deuteranopia
  matrix; a blue / orange pair survives deuteranopia and protanopia.
- **Examples E6/E7 exact to the byte:** `1920x1080 RGB888 = 6_220_800`;
  `x30x10 = 1_866_240_000`; `4096x4096 RGBA8 = 67_108_864 = 64 MiB`;
  `*4/3 ~= 85.33 MiB`; `1000/60 = 16.67 ms`, `1000/144 = 6.94 ms`.

## Notes on fixes applied while verifying

- `ppm_io._selftest`: NumPy 2.x rejects `uint8_array % 256` (Python int out of
  `uint8` range) with `OverflowError`; changed to build the test array in
  default int and `.astype(np.uint8)`.
- Tuned `make_data.relief()` to near-square-wave chisel ridges
  (`fx = 0.37`, `tanh` shaping) so the gamma-space downscale error is large
  and obvious (mean 20 codes / PSNR 21.5 dB) rather than marginal.
- `make_figures_m1.py`: write the PDFs next to the script (`_out()`), not the
  caller's CWD.
- `cvd._legend_demo` / `report.py`: the "good" hue-diverse palette actually
  fails the grayscale test; added a viridis luminance-ramp palette as the
  one that passes CVD **and** grayscale (this is the real lesson).
- `Module1_EN.tex` Case Study transcripts (Steps 2/3/5, the evidence caption,
  Expected State) updated to the values this run prints.

## Added in this repo

| File | Job |
|---|---|
| `prepare_photos.py` | full-resolution iPhone photos (Display P3) -> `photos/small/`: P3 -> sRGB, 5x box downscale in linear light, GPS and all metadata stripped |
| `import_photos.py` | `photos/small/` -> `data/*.ppm`, the two Lab 3 crops, and photo rows in `data/manifest.csv` (original camera W, H, bytes) |
| `dither.py` | 8-bit / 5-bit gradient, band widths, ordered (Bayer 4x4) dithering |
| `gamma_diagnosis.py` | the washed-out thumbnail diagnosed from pixel values only (written before the fix) |
| `gamma_fix_check.py` | checks the four predictions of the diagnosis against the one-line fix |
| `aliasing_demo.py` | 0.1..0.9 cycles/px sweep, predicted vs measured alias, with and without box pre-filter |
| `downscale_compare.py` | linear-correct vs naive vs Pillow `Image.BOX`, PSNR/SSIM |
| `export_png.py` | report images -> PNG for the GitHub README |
| `prelim_check.py` | recomputes every number in the Studi Pendahuluan |
| `figures/` | diagrams (own venv with matplotlib, not needed for make data/test/report) |

## Verified (this repo)

| Item | Status | Date | Toolchain |
|---|---|---|---|
| Clean copy, fresh `.venv`, `pip install -r requirements.txt` | numpy 2.4.6, pillow 13.0.0 installed exactly | 2026-10-27 | macOS 27.0.1 (arm64), Python 3.11.8, GNU Make 3.81 |
| `make data` | 21 synthetic images + 24 photos + 2 crops, `manifest.csv` 47 rows | 2026-10-27 | same |
| `make test` | **ALL CHECKS PASSED** (16/16) | 2026-10-27 | same |
| `make report` | `budget.md` + `report.html` (7 sections, 18 inline images, no external file) | 2026-10-27 | same, Pillow has WebP + AVIF |
| Reproducible | every `report/` file, `data/manifest.csv` and all 47 `data/` images byte-identical to the working copy | 2026-10-27 | same |

Not yet verified: a clone pulled from GitHub (needs the commits pushed first), and Windows or Linux.

## Verified (starter, kept for reference)

| Item | Status | Date | Toolchain |
|---|---|---|---|
| `Module1_EN.tex` compiles | **yes** -- Tectonic 0.17.0, 39 pp, no overfull hbox > 7 pt | 2026-09-04 | Windows 11 |
| `python tests.py` | **ALL CHECKS PASSED** (10/10) | 2026-09-04 | Windows 11, Python 3.12.9, NumPy 2.4.6, Pillow 12.3.0 (webp+avif) |
| `make data` -> 21 images + `manifest.csv` | **yes** | 2026-09-04 | same |
| `gamma_resize_bug.py --fix` | **yes** -- mean 20.2, max 42, PSNR 21.5 dB, SSIM 0.962 | 2026-09-04 | same |
| `format_compare.py` (hifreq + smooth) | **yes** -- table in `Module1_EN.tex` Step 5 | 2026-09-04 | same |
| `report.py` -> `report/budget.md` + `report/report.html` | **yes** (325 KB, images inline) | 2026-09-04 | same |
| `figures/make_figures_m1.py` -> 3 PDFs | **yes** | 2026-09-04 | Matplotlib (Agg) |
| `luma.py --cross-check` vs Pillow `"L"` | **yes** -- mean \|diff\| 0.16 on the desaturated relief; the ~8-code gap is on saturated colour (Example E5) | 2026-09-04 | same |

End-to-end run: `python make_data.py --out data && python tests.py &&
python gamma_resize_bug.py --fix --out report/ &&
python resample.py --image data/relief.ppm --factor 2 --methods naive-box,linear-box --out report/ &&
python format_compare.py --image data/crop_hifreq.ppm --out report/ &&
python format_compare.py --image data/crop_smooth.ppm --out report/ &&
python report.py` -- all green.
