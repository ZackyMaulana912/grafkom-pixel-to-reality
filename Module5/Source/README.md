# Module 5 -- AI Graphics: NeRF, World Models & AR

Course: *Grafika Komputer* (`25MP7716G030`), S1 Informatika UMSurabaya. Student: Zacky Maulana (20241337034).
The PDF and the starter README say `code/Module5/`; in this repo that folder is `Module5/Source/`.
**Integrates Modules 1-4 and is the capstone dry run.**

**Rule:** the pinhole ray generator, the volume-rendering compositing
formula, and a full differentiable-rendering training loop are **NumPy
only** (no PyTorch/JAX/autograd -- the backward pass is hand-derived and
checked against finite differences in `tests.py`). The **AR app**
(`ar_app/`) is a real, deployable static web page (`<model-viewer>` +
vanilla JS) -- open it in a browser and it works; on a phone, "View in your
space" launches a real AR session.

## Quick start

```bash
cd Module5/Source
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt     # numpy 2.4.6, pygltflib 1.16.5, matplotlib 3.11.2 and their pins
python ray_generator.py             # E1: pinhole ray through pixel (400,240)
python volume_render.py             # E2: composite 3 samples -> 1 pixel
python my_ray.py                    # the ray through pixel (1200, 6100) of my own iPhone photo
python capture.py                   # writes data/pusaka_capture/ (8 synthetic views)
python fit_nerf_toy.py              # train PSNR 20.32 dB, novel view (22.5 deg) 14.85 dB
python nerf_bug.py                  # 2 views 9.39 dB vs 8 views 12.05 dB at 190 deg (+2.66 dB)
python nerf_bug.py --sweep          # both grids on the 8 predicted angles
python pitfall_fix.py               # (a) starting density, (b) one third view
python tests.py                     # -> ALL CHECKS PASSED (81 ok)

cd ar_app
python make_temple_glb.py           # the starter's temple + hotspots.json (kept, no longer shown in the app)
python -m http.server 8743 --bind 127.0.0.1   # serve the app (needed for the hotspot fetch)
# open http://127.0.0.1:8743/index.html. On a phone, use the GitHub Pages URL
# (HTTPS, needed for AR) and tap "View in your space (AR)":
# https://zackymaulana912.github.io/grafkom-pixel-to-reality/Module5/Source/ar_app/index.html

# optional, heavier: automated headless-browser verification (see below)
pip install -r ../requirements-verify.txt && python -m playwright install chromium
python verify_ar_app.py http://127.0.0.1:8743   # -> ALL CHECKS PASSED (17 ok)
```

`verify_ar_app.py` rewrites the four PNGs in `ar_app/screenshots/` every run. Three come out identical each
time; `m5_ar_quizmode.png` does not, because the quiz picks its next target at random (`Math.random` in
`app.js`), so `git status` shows that one file as changed after a run.

The two AR models are made from files that are not in Git (the raw scan, 233 MB, and the downloaded car,
235 MB). With the scan on disk, Blender 5.2.2 rebuilds the horse:

```bash
cd ar_app/tools
$BLENDER -b -P scan_to_glb.py -- ../scan/kuda_full.usdz ../assets/kuda.glb ../assets/kuda_ukuran.json kuda_hotspot_text.json ../assets/hotspots_kuda.json 4096
cd .. && python occlusion.py --tune     # picks the hotspot normals (writes them into hotspots_kuda.json)
```

`$BLENDER` is the Blender binary (`/Applications/Blender.app/Contents/MacOS/Blender` on my Mac).
`car_to_glb.py` and `render_views.py` give their command line in their first lines. Checked on 4 Nov: the two
commands above give `kuda.glb` and `hotspots_kuda.json` byte-identical to the committed files.

## Unit table

| File | Job | Reproduces |
|---|---|---|
| `ray_generator.py` | pinhole camera: pixel -> camera-space ray direction, and a batched `generate_rays()` | Running example E1 |
| `volume_render.py` | density -> alpha, front-to-back compositing along a ray | Running example E2 |
| `nerf_toy.py` | the toy differentiable renderer: an analytic ground-truth scene, a look-at camera, a learnable `VoxelGrid` (nearest-voxel lookup, softplus/sigmoid activations), its **hand-derived analytic backward pass**, and a training loop | Case Study's from-scratch "mini-NeRF" |
| `capture.py` | deterministic 8-view ring capture of the toy scene (COLMAP-style `poses.json` + PPM images) | Case Study input |
| `fit_nerf_toy.py` | trains the grid on the capture; reports train/novel-view PSNR; writes comparison PPMs | Case Study evidence |
| `nerf_bug.py` | diagnose-and-fix: 2 clustered views vs 8 spread views, same novel view, PSNR gap | Lab 2 diagnose-and-fix |
| `nerf_bug.py --diagnose` / `--sweep` | training evidence of the 2-view grid only (written before any novel view, K14) / both grids on the 8 predicted angles | Lab 2 no 3 |
| `pitfall_fix.py` | (a) starting `sigma_raw` -5, -2, 0, +2 at lr 5 and 100; (b) one third view added to the 2-view capture at six angles | Lab 2 no 4 |
| `tests.py` | E1-E2 + an analytic-vs-finite-difference gradient check + the view-coverage regression | MASTER Sec 11.2 |
| `my_ray.py` | the ray through my own chosen pixel of my own iPhone photo, from `data/my_camera.json` (focal length estimated from EXIF) | Lab 1 no 4, by-hand ray |
| `document_capture.py` | writes `data/my_capture/` (manifest, checksums, contact sheet) for my 28 photos without committing the photos | Lab 1 no 2, own capture |
| `figures.py` | the only matplotlib user: draws the PNGs in `../docs/` from the from-scratch functions | doc figures |
| `ar_app/make_temple_glb.py` | procedurally builds `pusaka_temple.glb` (6 primitives, flat-shaded, no texture) + `hotspots.json` (5 bilingual educational hotspots) | AR app model + content |
| `ar_app/index.html`, `app.js`, `style.css` | the **Pusaka3D AR Explainer**: `<model-viewer>` + AR button + tap-to-learn hotspots + a quiz mode + EN/ID toggle; a **Model** button switches between my scanned horse (`kuda.glb`, default) and the F1 car (`amr23.glb`), each with its own 5 hotspots | Lab 3 "ship" deliverable |
| `ar_app/tools/photogrammetry.swift` | Apple Object Capture on my 28 photos -> a textured USDZ scan of my horse statue (macOS, Apple silicon; the raw scan stays in the git-ignored `ar_app/scan/`) | Lab 3 no 1, my own model |
| `ar_app/tools/scan_to_glb.py` | inside Blender 5.2: level, turn, scale to my measured 46 cm pedestal, resize textures, ray-cast the hotspots onto the mesh, export `assets/kuda.glb` + `assets/hotspots_kuda.json` | Lab 3 no 1, model in metres |
| `ar_app/tools/car_to_glb.py` | inside Blender: the downloaded Aston Martin AMR23 (Redgrund, Sketchfab, CC BY 4.0) -> `assets/amr23.glb` scaled to the FIA 2023 tyre rule (725 mm, Art. 10.8.1c), + `assets/hotspots_amr23.json` | the second AR model |
| `ar_app/tools/render_views.py` | inside Blender: the nine-view picture `../docs/img/kuda_scan_9sisi.png` | docs |
| `ar_app/occlusion.py` | ground truth for hotspot occlusion: a ray from each hotspot to the camera through the 105,665 triangles of `kuda.glb` (NumPy only) | Lab 3 no 2 |
| `ar_app/verify_ar_app.py` | headless-Chromium (Playwright) end-to-end check of the app, screenshots included | automated AR-app verification |

## What `python tests.py` asserts

- **E1** -- pixel `(400,240)`, `f=100`, principal point `(320,240)` ->
  unnormalised camera-space direction `(0.8, 0, -1)`, normalised
  `(0.625, 0, -0.781)`.
- **E2** -- 3 samples (`alpha=0.5, 0.5, 1.0`; colours red/green/blue) composite
  to weights `(0.5, 0.25, 0.25)` and final pixel colour `(0.5, 0.25, 0.25)`;
  weights + background sum to exactly `1.0`.
- **My own ray** -- iPhone 17 Pro photo, `f = 5591.38` px (24 mm equivalent on the
  diagonal of the 6048 x 8064 sensor frame), principal point `(2268, 4032)`, pixel
  `(1200, 6100)` -> `(-0.19101, -0.36986, -1)`, normalised
  `(-0.17634, -0.34145, -0.92321)`, the by-hand numbers in
  `../docs/catatan/fase2-capture-ray.md`; the principal point gives `(0, 0, -1)`.
- **One pixel convention** -- `generate_rays` shoots through pixel centres of the same
  formula as `pixel_to_camera_dir`, and `nerf_toy` has no copy of its own.
- **Gradient at every touched voxel, also at the extremes** -- hand-derived vs
  central-difference gradient for every voxel a sample touches, density and colour,
  at alpha almost 0, normal, almost 1 and exactly 1 (relative error < 1e-3).
- **Compositing, capture files, imports** -- `nerf_toy._composite_image` equals
  `volume_render.composite` per ray; `poses.json` matches the ring cameras within
  1e-9; `load_ppm` undoes `save_ppm`; the from-scratch files import only NumPy and
  standard modules.
- **Analytic vs finite-difference gradient** -- `backward_grid()`'s hand-derived
  gradient w.r.t. every probed voxel (density and colour) matches a
  central-difference numerical gradient to `< 1e-6` (typically `~1e-11`).
  This is the from-scratch code's *own* "match a reference" check, standing
  in for matching an external autodiff library.
- **View-coverage regression** -- the 8-view grid must beat the 2-view grid by
  `> 1 dB` PSNR on one held-out novel view (190 deg).
- **My horse (`kuda.glb`)** -- pedestal 46 cm long as I measured it, height and depth within 2% of my
  63 cm / 15 cm, standing on the floor, under 10 MB, no metadata but the exporter's name; 5 hotspots in
  both languages, each within 2 mm of the mesh, unit normals, and the normals are the ones
  `occlusion.py --tune` picks.
- **The F1 car (`amr23.glb`)** -- tyres 725 mm (FIA 2023 Art. 10.8.1c), width within 0.3% of 2000 mm
  (Art. 3.4.1), on the floor, under 10 MB; 5 hotspots on the surface; tuned normals.
- **Occlusion and provenance** -- the ray test of `occlusion.py` on three hand-made cases and on the real
  mesh; a provenance line with every field for each AR asset in `assets/LICENSE.md`.
- **Temple (T10)** -- none of the 66 triangles of `pusaka_temple.glb` is wound inwards or has a stored
  normal against its winding.

## Notes on fixes applied while verifying

Moved, word for word, to `../docs/catatan/fase4-view-coverage-pitfall.md` (decision
K14): they explain the outcome of the view-coverage task, which has to be diagnosed
from the evidence first.

## Known deviations from the course plan

1. **No real phone capture / nerfstudio / COLMAP / GPU training on this
   authoring host.** `data/pusaka_capture/` is a **deterministic synthetic
   ring capture** (`capture.py`) of an analytic toy scene
   (`nerf_toy.scene_density_color`), not real photographs, and the model
   that reconstructs it is a **hand-rolled NumPy voxel grid** trained by
   plain gradient descent with an **analytically hand-derived backward
   pass**, not `nerfstudio`'s `nerfacto`/Instant-NGP (which need a CUDA GPU,
   COLMAP, and real multi-view photographs). The real pipeline's commands
   are given and explained in `Module5_EN.tex`'s Software section; the
   toy pipeline here is the actually-run, actually-verified stand-in, in
   the same spirit as Module 1/3's deterministic-generator substitutions.
   A student's own phone capture through the real nerfstudio pipeline is
   the graded, bring-your-own-input version.
2. **Nearest-voxel lookup, not trilinear interpolation.** This keeps the
   backward pass a simple scatter-add (`np.add.at`) into one voxel per
   sample instead of a weighted scatter into 8 -- simple enough to
   hand-derive and unit-test exactly, at the cost of a blockier
   reconstruction than a real NeRF's positional-encoded MLP or a trilinear
   voxel grid would give. Absolute PSNRs here (training views ~20 dB, novel
   views ~10-14 dB) are toy-scale; the point is the *relative* comparison
   in the diagnose-and-fix task, not photorealism.
3. **The AR models.** The starter showed a procedurally generated temple (`make_temple_glb.py`, 6
   flat-coloured primitives). This repo shows **my own horse statue, scanned with Apple Object Capture from
   my 28 photos** (`kuda.glb`, 105,665 triangles, 4.41 MB, scaled to my measured 46 cm pedestal) and a
   second model, the **Aston Martin AMR23 by Redgrund** (Sketchfab, CC BY 4.0, `amr23.glb`, scaled to the
   FIA 2023 tyre rule). The temple files stay in the repo and `make_temple_glb.py` still runs (T10 fixed),
   but the app no longer offers the temple. Source, licence and checksum of every asset are in
   `ar_app/assets/LICENSE.md`.
4. **Real device AR session.** Tested on an **iPhone 17 Pro, iOS 27.2, Safari**: the GitHub Pages URL opens
   Quick Look and the horse stands on the surface at its real size (see Verified). **Android (Scene Viewer /
   WebXR) was not tested**, and the car was not tested on the phone. `verify_ar_app.py` still covers
   everything up to the AR handoff in headless Chromium.
5. **Educational content.** The starter's `hotspots.json` described generic candi cosmology. My hotspots
   (`hotspots_kuda.json`, `hotspots_amr23.json`) explain **how each model was made**: the scale reference,
   the 28 photos, where the colours come from, the side the camera never saw, and for the car the FIA
   rules, the wheelbase check, and the licence.

## Verified

| Item | Status | Date | Toolchain |
|---|---|---|---|
| starter code before any change | `tests.py` 17 ok, all five scripts match the PDF, max gradient error `4.89e-11` | 2026-11-02 | macOS 27.0.1, Apple M5, Python 3.11.8, NumPy 2.4.6 |
| `ar_app/verify_ar_app.py` on the starter app, served on `127.0.0.1:8743` | **ALL CHECKS PASSED (10 ok)** | 2026-11-02 | Playwright 1.64.1, Chrome Headless Shell 156 |
| `python tests.py` after the AR model | **ALL CHECKS PASSED (68 ok)**: `kuda.glb` is 46.0 cm long (my measure), 62.8 cm tall (measured 63), 14.7 cm deep (measured 15), stands on the floor, 4.41 MB; every hotspot within 1.7 mm of the mesh; every asset has a full provenance line | 2026-11-03 | same |
| `ar_app/verify_ar_app.py` on my version | **ALL CHECKS PASSED (12 ok)**: horse by default, 5 hotspots, panel and language, quiz, switch to the temple with its own 5 hotspots, no JS error | 2026-11-03 | Playwright 1.64.1, Chrome Headless Shell 156 |
| F1 car (`amr23.glb`) | tyres 725 mm (scale), width 2.006 m vs 2000 mm (Art. 3.4.1), wheelbase 3.387 m <= 3600 mm (Art. 3.4.2), 161,184 triangles, 7.67 MB; occlusion sweep 2 of 380 off (edge-on), 0 "shown while blocked"; `verify_ar_app.py` 17 ok (the temple is no longer in the model switch) | 2026-11-04 | same, Blender 5.2.2 |
| temple finial (T10) | the 4 sides and the base of the pyramid were wound inwards (6 of 6 triangles; the test fails on the starter's GLB) and the finial looked hollow in the browser; fixed in `make_temple_glb.py`, `tests.py` 75 ok | 2026-11-03 | same |
| language toggle (T11) | `verify_ar_app.py` **16 ok**: an open panel and an open quiz answer now follow the language without a second tap (the new check failed on the starter's `app.js`); the four screenshots in `ar_app/screenshots/` are now from my app | 2026-11-03 | same |
| occlusion fixes | `verify_ar_app.py` **14 ok** (a hidden hotspot can no longer be tapped; the model switch also moves the camera); `--occlusion`: 1 of 380 decisions off (edge-on), 0 "shown while blocked"; `tests.py` 73 ok | 2026-11-03 | same |
| `ar_app/verify_ar_app.py --occlusion` | 76 camera angles x 5 hotspots: 11 of 380 decisions disagree with the geometry, all "shown while blocked" (kaki 255-270 deg, surai 70 deg, plus edge-on cases); <model-viewer> 3.5.0 decides from the normal only, and a dimmed hotspot can still be tapped; two runs identical | 2026-11-03 | same |
| `ar_app/tools/scan_to_glb.py` | same `kuda.glb` and `hotspots_kuda.json`, byte for byte, when rerun on the same scan | 2026-11-03 | Blender 5.2.2 LTS |
| `python tests.py` after Fase 3 | **ALL CHECKS PASSED (57 ok)**: one pixel convention, every touched voxel's gradient vs finite differences also at alpha almost 0, almost 1 and exactly 1, compositing, `poses.json` within 1e-9, `load_ppm`, NumPy-only imports; each new check fails when the code is broken on purpose (`../docs/catatan/fase3-renderer-gradien.md`) | 2026-11-03 | same |
| `python tests.py` with `test_my_ray` | **ALL CHECKS PASSED (27 ok)**; the new check fails if the focal length uses the 36 mm width, if the y flip is dropped, or if the principal point moves half a pixel | 2026-11-03 | same |
| `my_ray.py` vs by-hand ray | equal to 5 decimals | 2026-11-03 | same |
| `document_capture.py` | 28 photos, identical files on a second run | 2026-11-03 | same, Pillow 13.0.0 |
| fresh clone from GitHub (commit `e0e5cce`) + new `.venv` | `pip freeze` = `requirements.txt` + `requirements-verify.txt`; `capture.py`, `make_temple_glb.py`; `tests.py` **81 ok**; `verify_ar_app.py` **17 ok**; `git status` clean afterwards; GitHub Pages serves files identical to the clone | 2026-11-04 | same Mac |
| Real device AR session | **works**: "View in your space (AR)" on the GitHub Pages URL opens Quick Look; the scanned horse stands on the surface, textured, and looks the same size as the real 63 cm statue (judged by eye next to it, not measured in AR); Android not tested | 2026-11-03 | iPhone 17 Pro, iOS 27.2, Safari |
| GitHub Pages (HTTPS) | served files identical to the repo; `verify_ar_app.py` against the live URL **16 ok**, no JS error | 2026-11-03 | Playwright 1.64.1, Chrome Headless Shell 156 |
| audit, clean local clone of `58658ae` | `tests.py` **81 ok**, also under a non-UTF-8 locale; every Quick start command prints the numbers above; `verify_ar_app.py` **17 ok**; README figures rebuild byte-identical. The four `ar_app/screenshots/` were still from 3 Nov (their footer named the temple), so they were taken again; the quiz screenshot changes on every run (random target). `scan_to_glb.py` + `occlusion.py --tune` rerun: `kuda.glb` and `hotspots_kuda.json` byte-identical to the committed ones | 2026-11-04 | same Mac, Blender 5.2.2 |

### Verified by the course author (starter, as shipped)

| Item | Status | Date | Toolchain |
|---|---|---|---|
| `Module5_EN.tex` compiles | **yes** -- Tectonic 0.17.0, no overfull hbox > 2 pt, 27 pp | 2026-09-06 | Windows 11 |
| `python tests.py` | **ALL CHECKS PASSED (17 ok)**, ~10 s | 2026-09-06 | Python 3.11.9, NumPy 2.2.4 |
| `ray_generator.py` / `volume_render.py` / `capture.py` / `fit_nerf_toy.py` / `nerf_bug.py` | **run green**, transcripts in `Module5_EN.tex` are the actual output | 2026-09-06 | same |
| Analytic vs finite-difference gradient | **max err ~3e-11** (well under the `1e-6` test threshold) | 2026-09-06 | same |
| View-coverage diagnose-and-fix | **buggy (2 views) 9.30 dB vs fixed (8 views) 12.02 dB** on the same held-out novel view (`+2.71 dB`) | 2026-09-06 | same |
| `ar_app/make_temple_glb.py` | **run green** -- `pusaka_temple.glb` (9.4 KB, 6 meshes/materials, round-trips through `pygltflib.load_binary`) + `hotspots.json` (5 hotspots) | 2026-09-06 | pygltflib 1.16.5 |
| `ar_app/verify_ar_app.py` | **ALL CHECKS PASSED (10 ok)** in headless Chromium (Playwright): model loads and renders to a real WebGL canvas, 5 hotspots inject, tap opens the info panel, language toggle changes the text, quiz mode picks a target, zero JS errors | 2026-09-06 | Playwright 1.62.0, Chromium (headless shell), `--use-gl=swiftshader` |
| `ar_app/` screenshots | `screenshots/m5_ar_overview.png`, `m5_ar_infopanel_en.png`, `m5_ar_infopanel_id.png`, `m5_ar_quizmode.png` -- real renders from the check above | 2026-09-06 | same |
| `../../figures/make_figures_m5.py` | **run green** -- writes `m5_fig1_pinhole_ray.pdf`, `m5_fig2_volume_compositing.pdf`, `m5_fig3_view_coverage.pdf` (re-runs `nerf_bug.py`, ~10 s) | 2026-09-06 | same |
| Real device AR session (WebXR/Scene Viewer/Quick Look) | **not yet tested on physical hardware** -- see "Known deviations" item 4 | -- | -- |
