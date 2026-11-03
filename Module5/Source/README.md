# Module 5 -- AI Graphics: NeRF, World Models & AR (reference repo)

Course: *Grafika Komputer / Computer Graphics* (`25MP7716G030`), S1 Informatika
semester 5. Companion to `../../Module5_EN.tex`. **Integrates Modules 1-4 and
is the capstone dry run.**

**Rule:** the pinhole ray generator, the volume-rendering compositing
formula, and a full differentiable-rendering training loop are **NumPy
only** (no PyTorch/JAX/autograd -- the backward pass is hand-derived and
checked against finite differences in `tests.py`). The **AR app**
(`ar_app/`) is a real, deployable static web page (`<model-viewer>` +
vanilla JS) -- open it in a browser and it works; on a phone, "View in your
space" launches a real AR session.

## Quick start

```bash
cd code/Module5
python -m pip install -r requirements.txt
python ray_generator.py             # E1: pinhole ray through pixel (400,240)
python volume_render.py             # E2: composite 3 samples -> 1 pixel
python capture.py                   # writes data/pusaka_capture/ (8 synthetic views)
python fit_nerf_toy.py              # trains a voxel grid on the capture; novel-view PSNR
python nerf_bug.py                  # diagnose-and-fix: 2 clustered views vs 8 spread views
python tests.py                     # -> ALL CHECKS PASSED (17 ok), ~10 s

cd ar_app
python make_temple_glb.py           # writes assets/pusaka_temple.glb + hotspots.json
python -m http.server 8743          # serve the app (needed for the hotspots.json fetch)
# open http://localhost:8743/index.html in a browser -- or on a phone on the
# same network, open http://<your-computer-ip>:8743/index.html and tap
# "View in your space" for real AR.

# optional, heavier: automated headless-browser verification (see below)
pip install playwright && python -m playwright install chromium
python verify_ar_app.py             # -> ALL CHECKS PASSED (10 ok)
```

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
| `ar_app/index.html`, `app.js`, `style.css` | the **Pusaka3D AR Explainer**: `<model-viewer>` + AR button + tap-to-learn hotspots + a quiz mode + EN/ID toggle | Lab 3 "ship" deliverable |
| `ar_app/tools/photogrammetry.swift` | Apple Object Capture on my 28 photos -> a textured USDZ scan of my horse statue (macOS, Apple silicon; the raw scan stays in the git-ignored `ar_app/scan/`) | Lab 3 no 1, my own model |
| `ar_app/tools/scan_to_glb.py` | inside Blender 5.2: level, turn, scale to my measured 46 cm pedestal, resize textures, ray-cast the hotspots onto the mesh, export `assets/kuda.glb` + `assets/hotspots_kuda.json` | Lab 3 no 1, model in metres |
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
3. **The AR app's 3D model is procedurally generated** (`make_temple_glb.py`,
   6 flat-coloured primitives), not downloaded from a marketplace or scanned
   from a real building -- avoids any asset-licence ambiguity and keeps the
   whole pipeline reproducible from source with no binary asset committed
   beyond the small (~9 KB) generated `.glb`. A student's own free/CC0
   asset or their own Module 3/4 model is a straightforward drop-in
   (swap `assets/pusaka_temple.glb` and regenerate `hotspots.json` for the
   new geometry).
4. **The AR session itself (WebXR / Android Scene Viewer / iOS Quick Look)
   was not tested on physical hardware** in this authoring session --
   `verify_ar_app.py` (headless Chromium via Playwright) verifies everything
   up to that handoff: the page loads, `<model-viewer>` parses and renders
   the `.glb` in a real WebGL canvas, all 5 hotspots inject and respond to
   taps with the correct bilingual text, and the "View in your space" button
   is present. Before this module fully meets the MASTER Definition of Done,
   open the hosted app on an actual Android phone (Chrome, triggers Scene
   Viewer) and an iPhone (Safari, triggers Quick Look via a generated
   `.usdz` -- see the note in `Module5_EN.tex`) and confirm the model
   anchors to a real surface at a plausible scale. Record the device +
   browser here.
5. **Educational content is generic, not site-specific.** `hotspots.json`'s
   text describes widely-documented Hindu-Buddhist candi cosmology (the
   three-tier Bhurloka/Bhuvarloka/Svarloka structure; the finial as Mount
   Meru) rather than claiming to describe any single named real temple --
   deliberate, so the app cannot misrepresent a specific heritage site it
   has never actually captured.

## Verified

| Item | Status | Date | Toolchain |
|---|---|---|---|
| starter code before any change | `tests.py` 17 ok, all five scripts match the PDF, max gradient error `4.89e-11` | 2026-11-02 | macOS 27.0.1, Apple M5, Python 3.11.8, NumPy 2.4.6 |
| `ar_app/verify_ar_app.py` on the starter app, served on `127.0.0.1:8743` | **ALL CHECKS PASSED (10 ok)** | 2026-11-02 | Playwright 1.64.1, Chrome Headless Shell 156 |
| `python tests.py` after the AR model | **ALL CHECKS PASSED (68 ok)**: `kuda.glb` is 46.0 cm long (my measure), 62.8 cm tall (measured 63), 14.7 cm deep (measured 15), stands on the floor, 4.41 MB; every hotspot within 1.7 mm of the mesh; every asset has a full provenance line | 2026-11-03 | same |
| `ar_app/verify_ar_app.py` on my version | **ALL CHECKS PASSED (12 ok)**: horse by default, 5 hotspots, panel and language, quiz, switch to the temple with its own 5 hotspots, no JS error | 2026-11-03 | Playwright 1.64.1, Chrome Headless Shell 156 |
| occlusion fixes | `verify_ar_app.py` **14 ok** (a hidden hotspot can no longer be tapped; the model switch also moves the camera); `--occlusion`: 1 of 380 decisions off (edge-on), 0 "shown while blocked"; `tests.py` 73 ok | 2026-11-03 | same |
| `ar_app/verify_ar_app.py --occlusion` | 76 camera angles x 5 hotspots: 11 of 380 decisions disagree with the geometry, all "shown while blocked" (kaki 255-270 deg, surai 70 deg, plus edge-on cases); <model-viewer> 3.5.0 decides from the normal only, and a dimmed hotspot can still be tapped; two runs identical | 2026-11-03 | same |
| `ar_app/tools/scan_to_glb.py` | same `kuda.glb` and `hotspots_kuda.json`, byte for byte, when rerun on the same scan | 2026-11-03 | Blender 5.2.2 LTS |
| `python tests.py` after Fase 3 | **ALL CHECKS PASSED (57 ok)**: one pixel convention, every touched voxel's gradient vs finite differences also at alpha almost 0, almost 1 and exactly 1, compositing, `poses.json` within 1e-9, `load_ppm`, NumPy-only imports; each new check fails when the code is broken on purpose (`../docs/catatan/fase3-renderer-gradien.md`) | 2026-11-03 | same |
| `python tests.py` with `test_my_ray` | **ALL CHECKS PASSED (27 ok)**; the new check fails if the focal length uses the 36 mm width, if the y flip is dropped, or if the principal point moves half a pixel | 2026-11-03 | same |
| `my_ray.py` vs by-hand ray | equal to 5 decimals | 2026-11-03 | same |
| `document_capture.py` | 28 photos, identical files on a second run | 2026-11-03 | same, Pillow 13.0.0 |
| Real device AR session | not yet tested (Fase 5) | -- | -- |

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
