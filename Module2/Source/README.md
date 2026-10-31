# Module 2 -- Rendering Pipeline & 2D Primitives (reference repo)

Course: *Grafika Komputer / Computer Graphics* (`25MP7716G030`), S1 Informatika
semester 5. Companion to `../../Module2_EN.tex`.

**Rule:** the from-scratch rasteriser (`raster.mjs`) is **plain JavaScript,
run with Node** -- no framework, no `<canvas>`. The framebuffer is a
`Uint8ClampedArray`; the same functions drive a browser `<canvas>` via
`ctx.putImageData`. The **library** side (`web/`) is Three.js, and is the
GitHub Pages deliverable.

**Convention** (stated once in `raster.mjs`, never mixed): `y` is DOWN; a
pixel `(x,y)` is a point sample at `(x+0.5, y+0.5)`; triangle vertices are
passed so the total `edge(A,B,C) > 0`; "inside" = all three edge functions
`>= 0`, and the top-left rule decides the exactly-on-edge case.

## Quick start

```bash
cd Module2/Source            # in this repo the module's code/Module2 lives here
nvm use                      # Node version from .nvmrc (22.23.4)
npm ci                       # exact three + serve from package-lock.json
npm test                     # -> ALL CHECKS PASSED (23 ok, 0 fail)
npm run square               # the Fully Worked Example
npm run bug                  # diagnose-and-fix: shared-edge cracks/doubles
npm run plan                 # MY floor plan (myplan.json), from scratch -> out/plan_scratch.ppm
npm run bench                # forward vs backward on myplan.json
npm run serve                # http://127.0.0.1:4173/web/  (the Three.js viewer)
npm run png                  # out/*.ppm -> ../docs/img/*.png for Module2/README.md
```

The from-scratch side needs no package at all; `npm ci` is for the viewer's
local server (`three` itself is loaded from a CDN in `web/index.html`, pinned
to the same 0.160.0). The server listens on 127.0.0.1 only and fails instead of
switching port if 4173 is taken.

## Unit table

| File | Job | Reproduces |
|---|---|---|
| `raster.mjs` | Framebuffer, `lineDDA`, `lineBresenham` (8 octants), `edge`, `triangle` (+ top-left rule), `barycentric`, `coverage`, PPM r/w | E1-E5, watertightness |
| `metrics.mjs` | `psnr`, global `ssim`, `pixelStats` | Step 4, Case Study diff |
| `plan.mjs` | load `pusaka_plan.json`; the single `worldToScreen` (y-flip); `renderPlan` | Case Study |
| `pusaka_plan.json` | committed Prambanan-style floor plan (metres, y-up) | Case Study input (fallback) |
| `draw_plan.mjs` | render the plan headless -> `out/plan_scratch.ppm` | Case Study step 2 |
| `draw_square.mjs` | Fully Worked Example: 6x6 square, outline / fill / coverage | Steps 1-4 |
| `triangle_gap_bug.mjs` | diagnose-and-fix: shared-edge cracks/doubles, coverage image, proof | Lab 2 |
| `bench.mjs` | forward (rasterise) vs backward (per-pixel) at zoom 1x / 10x | Lab 3 decision |
| `compare.mjs` | diff two rasters (PPM; PNG if `pngjs` installed): identical %, PSNR, SSIM, max\|diff\|, diff image | Step 4, Case Study |
| `tests.mjs` | every from-scratch check; `npm test` entry point | MASTER 11.2 |
| `web/index.html`, `web/viewer.mjs`, `web/cvd.css` | Three.js plan viewer + accessible legend + SVG deuteranopia/protanopia toggles + PPM export | Lab 3 deliverable |

## What `node tests.mjs` asserts

- **E2 / E3** -- `lineDDA` and `lineBresenham` on `(2,1)->(9,5)` both give
  `[(2,1),(3,2),(4,2),(5,3),(6,3),(7,4),(8,4),(9,5)]`; all 8 octants give the
  right length.
- **E4** -- `edge(A,B,C)=28` for `A(1,1) B(6,2) C(3,7)`; edge values at
  `(3,3)` are `(8,12,8)` (inside); `(5,5)` and `(1,4)` are outside.
- **E5** -- `barycentric` sums to 1; interpolating `10/20/40` at
  `(0.5,0.25,0.25)` gives `20`.
- **top-left rule** -- the 6x6 square split on `y=x`: `once=36, twice=0,
  gaps=0` with the rule; `twice=6` without it; `gaps=6` with `">0"`.
- **E1** -- the sample-centre rule lights exactly `(1,1),(2,1),(1,2),(2,2)`
  for a 2x2 rectangle at `(1,1)`.
- **plan** -- `worldToScreen` flips `y` exactly once and is invertible.
- **reference raster** -- `draw_square` fill is byte-identical to
  `ref/square_fill_ref.ppm` (regenerated on first run; commit it).

## Notes on fixes applied while verifying

- `triangle()`: the coverage helper passes a plain `{w,h}` object as the
  "framebuffer"; guarded the draw call with `typeof fb.set === "function"` so
  `coverage()` can run the same rasteriser without a real framebuffer.

## Added in this repo

| File | Job |
|---|---|
| `raster.mjs` (rewritten) | DDA from k (no drift); Bresenham with the E3 decision variable, octant-free; `triangle()` on 1/256-px fixed point so the top-left bias is exact (the starter's -1 bias dropped pixels whose edge value is 0.5), auto-flip winding, `fillRule: "module" \| "gpu"`; `triangleNaive()`; `fillRect()` with centre / corner / corner-inclusive sampling |
| `plan_common.mjs` | legend (viridis, labels, markers) and `makeWorldToScreen()`, shared by Node and the browser viewer |
| `myplan.json` | my own floor plan: the room where my statue stands (sources in `../docs/denah/`) |
| `walkthrough.mjs` | one wall segment through the seven pipeline stages, with real numbers |
| `draw_asterisk.mjs` | 24-spoke octant check |
| `sample_centre.mjs` | Example E1: centre vs corner vs corner-inclusive, plus a quarter-pixel shift |
| `make_tri_ref.mjs` | independent per-pixel integer reference -> `ref/tri_ref.ppm`, `ref/tri_t8_ref.ppm`; `--check` sweeps 1934 triangles |
| `gpu_rule_check.mjs` + `web/gpu_rule.html` | which edge owns on-edge pixels on a real GPU; `ref/gpu_*.ppm` captured from WebGL |
| `winding_demo.mjs` | pitfall fix measured: reversed triangles before/after |
| `diff_pixels.mjs` | lists and classifies every pixel two renders disagree on |
| `cvd_check.mjs` | legend distances under the page's own CVD matrices (read from `web/index.html`) |
| `export_png.mjs` | PPM -> PNG with `node:zlib` only (crop and enlarge options) |
| `prelim_check.mjs`, `figures/make_figures.mjs` | every number and SVG diagram of the Studi Pendahuluan |

Changed starter files: `triangle_gap_bug.mjs` (`--diagnose`: pixel evidence
only), `bench.mjs` (`--plan`, warm-up, interleaved rounds, median), `plan.mjs`
(legend from the plan), `web/viewer.mjs` (my plan, DoubleSide fill, +0.5 line
offset), `web/index.html` (Indonesian, grayscale toggle), `tests.mjs` (12 checks
added, none of the 10 starter checks loosened), `package.json` (exact versions,
safe `serve`).

## Verified (this repo)

| Item | Status | Date | Toolchain |
|---|---|---|---|
| `npm ci` from `package-lock.json` | three 0.160.0, serve 14.2.6 (compression overridden to 1.8.2), `npm audit`: 0 vulnerabilities | 2026-10-28 | macOS 27.0.1 (Apple M5), Node v22.23.4, npm 10.9.9 |
| `npm test` | **ALL CHECKS PASSED (22 ok, 0 fail)**; with the starter `triangle()` swapped in, 4 of the new checks fail | 2026-10-28 | same |
| `npm run serve` | 127.0.0.1:4173 only (checked with `lsof`); `/web/`, `/web/viewer.mjs`, `/myplan.json` all 200 | 2026-10-28 | same |
| Viewer vs from-scratch (`myplan.json`, fill on) | 479929/480000 identical, PSNR 52.7 dB, SSIM 1.000; every mismatch is a line end/joint (25) or diagonal antialiasing (46) | 2026-10-28 | Chrome 156.0.8078.48 headless, ANGLE Metal, Apple M5 |
| Legend under CVD filters | min distance 36.9 (deuteranopia), 46.4 (protanopia), 69.3 (CSS grayscale); browser pixels match the Node model within 1 code | 2026-10-28 | same |
| Legend vs Machado et al. 2009 (31 Oct) | the page's matrices are colorjack.com's "ColorMatrix" values, not Vienot/Brettel; with Machado 2009 (Table 1, severity 1.0, linear light) the legend stays 82.2 / 92.1 apart and the red/green control collapses (4.7 / 10.1), same as Module 1; `npm test` 23 ok | 2026-10-31 | Node 22.23.4, same Mac |
| Fresh clone from GitHub (commit `3f30c76`) | `nvm use` (Node 22.23.4), `npm ci`, `npm test` **23 ok, 0 fail**, `npm run plan` exit 0, `git status` clean. `npm audit` now reports 3 moderate issues: GHSA-g3hv-75wg-m249 (minimatch < 11.0.1, published 2026-10-30 23:09 UTC) through `serve-handler` in the dev dependency `serve`, which only runs the local server on `127.0.0.1`; npm's fix would downgrade `serve` to 6.5.8 (breaking), so it is recorded, not applied | 2026-10-31 | same Mac |
| Clean copy reproduction | see `../docs/laporan/laporan-modul2.md`, section 8 | 2026-10-28 | same |
| GitHub Pages (`https://zackymaulana912.github.io/grafkom-pixel-to-reality/Module2/Source/web/`) | every file 200 with the right type (`.mjs` as `text/javascript`, `cvd.css`, `myplan.json`, three.js from jsDelivr); 0 console errors (only the browser's own `/favicon.ico` 404); 5 legend rows; each of the 4 toggles changes the picture and switching it back restores it exactly; Export PPM byte-identical to the local export (479929/480000 vs from-scratch) | 2026-10-28 | Chrome 156.0.8078.48 headless, ANGLE Metal, Apple M5 |
| Fresh clone from GitHub (commit `cceae00`) | `npm ci` 0 vulnerabilities, `npm test` 22 ok; every regenerated image and reference identical to the 33 committed ones; viewer export from the clone identical to the working copy (479929/480000 vs from-scratch) | 2026-10-28 | same |

Opened by hand: Safari 27.0.1 on the same Mac, GitHub Pages URL, 2026-10-28 -- plan and legend render, all 4 toggles work (visual check only, no export or console check in Safari).

Not yet verified: other GPUs, Windows or Linux.

## Verified (starter, kept for reference)

| Item | Status | Date | Toolchain |
|---|---|---|---|
| `Module2_EN.tex` compiles | **yes** -- Tectonic 0.17.0, no overfull hbox > ~10 pt | 2026-09-04 | Windows 11 |
| `node tests.mjs` | **ALL CHECKS PASSED (10 ok)** | 2026-09-04 | Node v22.19.0 |
| `draw_square` / `triangle_gap_bug` / `draw_plan` / `bench` / `compare` | **run green** -- transcripts in `Module2_EN.tex` are the actual output | 2026-09-04 | Node v22.19.0 |
| `web/` Three.js viewer | **authored, not browser-verified on this host** (no display); loads `three@0.160.0` from jsdelivr, draws the plan + legend, exports PPM for `compare.mjs` | 2026-09-04 | -- |

Before the module fully meets the MASTER Definition of Done, open `web/` in a
browser (`npx serve .` -> `/web/`), confirm the plan and 5-category legend
render, toggle the deuteranopia/protanopia filters (all five stay distinct),
click **Export PPM**, and run
`node compare.mjs out/plan_scratch.ppm plan_three.ppm` -- expect a
high-but-finite PSNR (edge anti-aliasing only). Record the browser + version.
