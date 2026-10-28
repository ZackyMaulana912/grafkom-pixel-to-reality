# Module 3 -- 3D Transforms, Projection, Texture & Real-Time Rendering

Course: *Grafika Komputer* (`25MP7716G030`), S1 Informatika UMSurabaya. Student: Zacky Maulana (20241337034).
The PDF and the starter README say `code/Module3/`; in this repo that folder is `Module3/Source/`.

**Rule:** the transform stack, the z-buffer rasteriser, the ray tracer, the OBJ loader and the mipmap are
**NumPy only**. Pillow decodes my JPG photos once (`import_texture.py`) and writes README PNGs
(`export_png.py`). The real-time renderer (`web/`) is Three.js 0.160.0 and is the GitHub Pages deliverable.

**Conventions** (pinned once at the top of `transforms.py`): column vectors, `p' = M @ p`, chains read right to
left; right-handed world and view space, camera looks down `-z`, `w_clip = -z`; NDC `[-1,1]^3` with near at
`-1`; viewport flips `y`, pixel centres at `+0.5`; front faces CCW from outside (the loader can enforce it);
OBJ `v` flipped once on load; angles end in `_deg`.

## Quick start

```bash
cd Module3/Source
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # numpy==2.4.6, pillow==13.0.0
python make_model.py                     # the starter's temple: data/pusaka_model.obj + data/relief.ppm
python tests.py                          # ALL CHECKS PASSED (17 ok, 0 fail)
python -m http.server 8000 --bind 127.0.0.1   # open http://127.0.0.1:8000/web/
```

Serve `Source/`, not `web/`: the viewer loads `../scenes`, `../data` (finding T8). `--bind 127.0.0.1` keeps the
server off the network. There is no Makefile; every task is one command:

```bash
python worked_example.py                                   # the PDF's running point (2,3,4)
python worked_example.py --scene scenes/mymodel.json --vertex 134   # my model, every space + columns of M, V
python raster3d.py --scene scenes/mymodel.json             # out/mymodel_raster.ppm + out/mymodel_depth.ppm
python raytrace.py --scene scenes/mymodel.json             # out/mymodel_rt.ppm   (--shadow for shadow rays)
python compare.py out/mymodel_raster.ppm out/mymodel_rt.ppm --diff out/diff_rt.ppm
python diff_regions.py --scene scenes/mymodel.json out/mymodel_raster.ppm web/mymodel_three.ppm
python persp_check.py                                      # E4 + the swimming floor
python mip_check.py                                        # far temple with / without mipmap
python diagnose_scene.py                                   # evidence only (written before any fix)
python broken_scene.py --all                               # the three fixes + depth formats / reverse-Z
python bench.py                                            # frame time, raster vs ray tracer
python export_png.py --src out --out ../docs/img           # PNG copies for the README
```

The starter's forms still work: `python raster3d.py --model data/pusaka_model.obj --w 512 --h 512` and
`python raytrace.py --model data/pusaka_model.obj --w 256 --h 256` (render both at the same size before
`compare.py`; the starter's quick start did not, finding T6).

## My model

`data/mymodel.obj` (394 triangles) and `data/mymodel_tex.ppm` (512 x 512 atlas of my own photos) are committed.
They are generated from one hand-written file, `data/mymodel_ukuran.json`, by `make_mymodel.py` and
`import_texture.py`; see `../docs/model/README.md` for where every number and pixel comes from.

## Unit table

| File | Job |
|---|---|
| `transforms.py` | T / S / R, `perspective`, `reverse_z_depth`, `look_at`, `project`, `viewport`, `perspective_divide_2d` |
| `objio.py` | OBJ loader (fan triangulation, `v` flip, `signed_volume`, optional CCW enforcement) |
| `scene.py`, `scenes/*.json` | one file per model: camera, model matrix, light, texture, frame size; read by all three renderers |
| `raster3d.py` | MVP -> near clip -> w divide -> viewport -> barycentric z-buffer -> perspective-correct bilinear texture -> Lambert; options: naive UV, mipmap, culling, shadow map, reverse-Z, depth formats |
| `raytrace.py` | pinhole rays + Moller-Trumbore, nearest hit, same sampler and Lambert; optional shadow rays |
| `mipmap.py` | 4-level pyramid (2x2 average in linear light), level of detail, trilinear |
| `make_mymodel.py`, `import_texture.py` | my model and texture atlas |
| `worked_example.py` | a point through object, world, view, clip, NDC, screen |
| `persp_check.py`, `mip_check.py` | Lab 2 no 3 and 4 |
| `diagnose_scene.py`, `broken_scene.py` | Lab 2 no 2 and 5 |
| `bench.py` | Lab 3 no 3 |
| `compare.py`, `metrics.py`, `diff_regions.py` | PSNR, global SSIM, amplified difference; edge vs interior split |
| `web/index.html`, `web/viewer.js` | Three.js viewer reading `scenes/mymodel.json`, OrbitControls, Export PPM |
| `make_model.py`, `ppm_io.py`, `srgb.py` | from the starter, unchanged |
| `figures/make_figures.py` | diagrams for the Studi Pendahuluan |

## What `python tests.py` asserts (17 checks)

- **E1-E3** as in the PDF: `(2,3,4)` -> `(3,3,-3)` -> `(2,2)`, the other order `(5,3,-3)`; the duality; `z=-n -> -1`, `z=-f -> +1`, `z=-3 -> 0.5`.
- **E4, E5 through the rasteriser's own functions** (`perspective_correct` 0.1 vs `bary_mix` 0.5; depth 0.625).
- the starter's shape check, one-triangle render, and **byte-identical** match with `ref/temple_ref.ppm`,
  both as stored and through `scenes/temple.json` with the CCW-enforcing loader.
- my model (>= 200 triangles, no zero area, UV on every corner and inside the atlas, consistent winding on 564
  shared edges), the 512 x 512 texture, handedness (`det M > 0`, signed volumes), the near clip, the mipmap,
  reverse-Z, order-free z-buffer, and raster vs ray tracer on my model > 60 dB.

## Findings about the starter (details in `../docs/catatan/`)

| | Finding | Proof |
|---|---|---|
| T13 | the temple's 180 faces are wound inward (signed volume -2.976), so `broken_scene.py --bug inside-out` labels the correct render as broken and the inside-out one as fixed | culling + stored winding is farther than the truth at 19029 of 19029 pixels |
| T14 | raster vs ray tracer differs on a few temple pixels where `u` is exactly 1: `np.mod` wraps 1.0 to 0.0 but 0.9999999999999999 stays; machine-dependent | 1 pixel at 256^2 on my Mac (68.1 dB) vs 76.9 dB in the PDF |
| T15 | the rasteriser truncates to uint8, a GPU rounds: +0.49 codes in the interior vs WebGL | `quantize="round"` brings it to -0.002 |
| T7 | starter viewer 3.12x darker in linear light (three.js r155+ physical lights: Lambert / pi), nearest filtering, different texel centres | three.js r160 source; 11.4 -> 40.4 dB |
| T4 | `--demo-overlap` printed fixed text; the back triangle alone covers 648 px, but only 136 are visible outside the overlap | now counted |
| T5 | `--out` without "raster" wrote the depth image over the colour image | fixed in `depth_path()` |
| T9 | swapping the uniform scale and the rotation changes nothing; the stretch is an extra `diag(2.2, 0.5, 1)` | column lengths 3.08 / 0.70 / 1.40 |

## Verified

| Item | Status | Date | Toolchain |
|---|---|---|---|
| `python tests.py` | **ALL CHECKS PASSED (17 ok, 0 fail)** | 2026-10-29 | macOS 27.0.1, Apple M5, Python 3.11.8, NumPy 2.4.6, Pillow 13.0.0 |
| starter code before any change | `tests.py` 8 OK; `ref/temple_ref.ppm` generated by it and committed separately | 2026-10-28 | same |
| my rasteriser vs the starter's | byte-identical frames (temple 160, 256, 512; demo triangle) | 2026-10-29 | same |
| raster vs ray tracer, my model 512^2 | **PSNR inf (byte-identical)** | 2026-10-29 | same |
| raster vs ray tracer, temple | 78.6 dB at 256^2 (2 px), 69.1 dB at 512^2 (3 px), all on the `u = 1` seam (T14) | 2026-10-29 | same |
| `web/` viewer, local server `127.0.0.1:8000` | loads my model and the temple, 0 console / page / network errors, orbit + reset work, Export PPM 512 x 512 | 2026-10-29 | Chrome 156.0.8078.48 headless, ANGLE Metal, Apple M5 |
| raster vs WebGL, my model | **40.4 dB, SSIM 0.998**; 92.2% of the squared error on triangle edges (MSAA) | 2026-10-29 | same |
| raster vs WebGL, temple | 35.3 dB, SSIM 0.998 | 2026-10-29 | same |
| fresh copy of the repo files + new `.venv` | `pip install -r requirements.txt`, `make_model.py`, `tests.py` green | 2026-10-29 | same Mac |
| opened by hand in a normal browser | **not yet** | | |
| GitHub Pages URL | **not yet** (after push) | | |
| other GPUs, Windows, Linux | **not tested** | | |
