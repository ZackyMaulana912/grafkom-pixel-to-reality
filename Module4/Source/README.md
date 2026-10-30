# Module 4 -- Animation, Kinematics & Game Engine

Course: *Grafika Komputer* (`25MP7716G030`), S1 Informatika UMSurabaya. Student: Zacky Maulana (20241337034).
The PDF and the starter README say `code/Module4/`; in this repo that folder is `Module4/Source/`.

**Rule:** forward kinematics, inverse kinematics, the Catmull-Rom sampler, quaternions / Euler angles and the
foot-slide study are **Python standard library only** (`tests.py` checks the imports with `ast`). matplotlib is
used only by `figures.py` to draw the README PNGs. `godot_project/` rebuilds the same primitives inside
Godot 4.7.2 and prints its numbers, which `godot_check.py` compares with the Python ones.

**Conventions** (pinned once at the top of `fk.py` and `quaternion.py`): a chain is a list of
`Bone(length, local_angle_deg)`, each angle relative to the parent bone, counter-clockwise positive, degrees in
every public function; quaternions are `(w, x, y, z)` with norm 1; matrices act on column vectors and an Euler
order is the matrix product left to right, so `"ZYX"` is `M = Rz(roll) @ Ry(yaw) @ Rx(pitch)` (extrinsic X, Y, Z
= intrinsic Z, Y', X''; locks at yaw = 90). Godot's `Node3D` default is intrinsic YXZ = `Ry @ Rx @ Rz` (locks at
pitch = 90); comparisons with Godot always name the order.

## Quick start

```bash
cd Module4/Source
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # matplotlib 3.11.2 and its pinned dependencies
python tests.py                          # ALL CHECKS PASSED (134 ok)
```

There is no Makefile; every task is one command:

```bash
python fk.py                             # E1: elbow (2.598, 1.500), hand (2.598, 3.500)
python ik.py                             # E2: -13.18 / 70.53 deg, FK error 4.44e-16, two unreachable targets
python spline.py                         # E3 + camera_path.json + my_path.json (all 51 samples, spacing)
python quaternion.py                     # E4 + gimbal lock + the locked axis of ZYX, XZY and Godot's YXZ
python my_chain.py                       # my arm (data/my_chain.json): FK, angles re-derived from the photo
python foot_slide_bug.py --diagnose      # evidence only: root vs animation distance and the gap
python foot_slide_bug.py                 # the fix (gap exactly 0.0) and pitfall (c), baked root-motion curve
python figures.py --set studi            # ../docs/studi-pendahuluan/img/*.png
python figures.py --set readme           # ../docs/img/*.png
```

Godot (`$GODOT` = the Godot 4.7.2 binary; on my Mac `/Applications/Godot.app/Contents/MacOS/Godot`):

```bash
$GODOT --headless --path godot_project --quit-after 60 | python godot_check.py               # scene numbers vs Python
$GODOT --headless --path godot_project --script res://tools/cek_basis.gd | python godot_check.py      # T4
$GODOT --headless --path godot_project --script res://tools/cek_walker.gd | python godot_check.py     # T11
$GODOT --headless --path godot_project --script res://tools/cek_knight.gd | python godot_check.py     # Knight
$GODOT --headless --path godot_project --script res://tools/cek_euler_rig.gd | python godot_check.py  # prediction
$GODOT --path godot_project --resolution 1280x720 --script res://tools/foto_scene.gd -- ../docs/img    # screenshots
$GODOT --headless --path godot_project --export-release "Web" ../../build/web/index.html             # Web build
python -m http.server 8000 --bind 127.0.0.1 -d ../build/web                                         # test it locally
```

The Web export needs the Godot 4.7.2 export templates (`web_nothreads_release.zip`); the build is single-threaded,
so it needs no cross-origin isolation headers.

## Unit table

| File | Job |
|---|---|
| `fk.py` | planar FK as a product of local 3 x 3 homogeneous matrices `R(theta) T(l, 0)`, root to leaf |
| `ik.py` | analytic 2-bone IK (law of cosines), `UnreachableTarget` outside `|l1 - l2| <= d <= l1 + l2`, `fk_error()` |
| `spline.py` | Catmull-Rom as basis weights, clamped-end sampler, `sample_spacing()`, both path loaders |
| `quaternion.py` | product, conjugate, norm, rotate, slerp, axis-angle, matrices, `euler_to_matrix(..., order)`, `lock_rule(order)` |
| `foot_slide_bug.py` | the foot-slide case study: `--diagnose`, the fix `matched_speed()`, pitfall (c) `walk()` / `root_motion()` |
| `my_chain.py` | my measured arm: FK of the 2-bone and 3-bone chains, local angles recomputed from the photo's pixels |
| `godot_check.py` | parses the lines Godot prints (`ARM_*`, `BASIS`, `GIMBAL`, `CURVE`, `MYARM`, `WALKER`, `KNIGHT_WALK`, `RIG_*`) and checks them against the Python code |
| `figures.py` | every PNG in `../docs/` (the only matplotlib user) |
| `tests.py` | E1-E4, my chain, IK limits and 20 000 random targets, matrices vs angle sums, my path, file copies, Euler orders, quaternion algebra, foot-slide fix and pitfall (c), the Godot checker, stdlib-only imports |
| `data/my_chain.json`, `data/my_path.json` | my arm (29 / 24 / 20 cm, photo IMG_9035) and my 6-point camera path around the horse statue |
| `godot_project/` | my room from Module 3, the spline camera on my path, my arm as a `Skeleton3D`, the CC0 KayKit Knight walking by root motion, and the course demos (FK/IK arm, foot-slide walker, gimbal lock); `tools/` holds the headless measuring scripts |

## Findings

| | Finding | Proof |
|---|---|---|
| T1 | the starter runs clean; on this Mac `ik.py` prints error `4.44e-16` (as the PDF), a Linux run printed `0.00e+00` | Fase 0 transcript |
| T2 | the gimbal-lock matrices are equal to rounding, not bit-identical | `1.11e-16`, `1.06e-17`; `==` is False |
| T3 | the docstring said intrinsic X -> Y -> Z, but the code computes `Rz Ry Rx` (extrinsic X, Y, Z) | `max|RzRyRx - RxRyRz| = 0.360` at (20, 30, 40) |
| T4 | the starter's Godot gimbal cube was **not locked**: it pinned yaw = 90, but Godot's YXZ locks at pitch = 90 | Godot `Basis`: 0.0865 / 0.174 at yaw 90, 4.4e-8 at pitch 90; fixed (pitch 90, cube moves 1.2e-7 while yaw goes 12 -> 30 deg) |
| T5 | `arm_kinematics.gd` clamped unreachable targets and printed nothing | now prints, warns in red; matches `ik.py` to 3e-13 |
| T6 | `foot_slide_bug.py` printed its own fix; the tests used typed 1.5 / 1.0 | `--diagnose` + tests computed from the constants |
| T7 | the "elbow up" solution puts the elbow **below** the shoulder-target line for (4, 1) | elbow (2.921, -0.684), line at 14.04 deg |
| T8 | equal t steps are not equal distances (0.373-0.719 m on `camera_path.json`); `Curve3D` points have no handles | `sample_spacing()`; `my_path.png` |
| T9 | renderer `mobile` cannot export to the Web | switched to `gl_compatibility` |
| T10 | `requirements.txt` used `>=` for a script that is not in the zip | pinned with `==` |
| T11 | the Godot walker slid **31.5 cm per step** at the "fixed" speed `stride x rate = 1.0` (its legs cover 1.60 m per cycle), its planted foot rose 9.2 cm, and the footfall markers sat 45 cm behind the real foot | `tools/cek_walker.gd`; fixed by root motion from the planted foot: 2.4e-7 m |
| T12 | the inner reach limit was untested; no quaternion product / normalise | tests added; `quat_mul`, `quat_normalize` |
| T13 | the two `camera_path.json` copies agreed only by hand | test; `my_path.json` and `my_chain.json` copies tested too |
| T14 | at 1.5 m/s the walker slides 7-10 cm already in the first step (< 0.75 s), not "within two seconds" | `tools/cek_walker.gd` |
| T15 | the starter names no AI tool; one em dash in the starter README | this README has none |
| new | law of cosines at the shoulder too gave IK errors up to 1.4e-7 near full reach | 20 000 targets; the atan2 form gives 1.4e-12 |
| new | a constant "correct" speed still slides 4.75 cm inside every step when the baked foot speed varies; sampling every 0.5 s hides it | `walk()` at 60 fps |
| new | `Quaternion.get_angle()` returns 240 deg for a 120 deg rotation (no shortest-arc) | `tools/cek_euler_rig.gd` |
| new | `Vector2` / `Vector3` / `Basis` are 32-bit in Godot; the arm agrees with Python to 6e-6 deg only until it is computed with plain (64-bit) floats | 6.3e-6 -> 3e-13 |

## Known deviations from the course plan

1. **Path and Godot version.** The PDF says `code/Module4/` and "Godot 4.2+". The project uses `.uid` files
   (Godot 4.4+) and `config/features "4.7"`; it was verified with **Godot 4.7.2 stable** only.
2. **Renderer.** `gl_compatibility` instead of `mobile`, because the Web export needs WebGL 2.0.
3. **`foot_slide_bug.py --diagnose`.** Added so the diagnosis could be written from numbers before the fix
   (committed first, `docs/prediksi/diagnosis-foot-slide.md`).
4. **The scene.** The temple blockout is replaced by my Module 3 room (`temple_blockout.gd` is kept as a
   fallback, unused). The course demos moved to a `Lab` node 7 m to the side; my path is open (300 deg), so the
   camera goes there and back (`ping_pong`) instead of jumping from the last point to the first.
5. **Gimbal demo.** Pinned at pitch = 90 (Godot's middle axis) instead of yaw = 90.
6. **Walker.** Root motion from the planted foot by default; `F` switches back to the starter behaviour.
7. **Asset.** KayKit (CC0) instead of Kenney: Kenney's download needs a browser button. Source, commit, size,
   SHA-256 and the licence text are in `godot_project/assets/`.

## Verified

| Item | Status | Date | Toolchain |
|---|---|---|---|
| starter code before any change | `tests.py` 40 ok, all five scripts match the PDF | 2026-10-30 | macOS 27.0.1, Apple M5, Python 3.11.8 |
| `python tests.py` | **ALL CHECKS PASSED (134 ok)** | 2026-10-30 | same, matplotlib 3.11.2 |
| new code vs the starter, 2000 random inputs per function | max difference 1.2e-13 (IK, deg), 0 (Euler matrices) | 2026-10-30 | same |
| `godot_project/` headless, editor import and run | exit 0, no error or warning, no starter file rewritten | 2026-10-30 | Godot 4.7.2 stable (macOS) |
| Godot numbers vs Python (`godot_check.py`) | 13 scene lines + 16 `Basis` + 4 walker + 1 Knight + 8 prediction lines, all within tolerance | 2026-10-30 | same |
| windowed run, Compatibility renderer | `OpenGL API 4.1 Metal ... Compatibility`, screenshots correct | 2026-10-30 | same, Apple M5 |
| Web build (`Module4/build/web/`, 40 MB) | re-export with the same `.godot/` import cache byte-identical; local server `127.0.0.1:8000`: no console error, 13 lines from the browser console match Python | 2026-10-30 | Chrome 156 headless, WebGL 2.0, ANGLE Metal, Apple M5 |
| Web build opened by hand | loads and runs | 2026-10-30 | Safari 27.0.1, same Mac |
| fresh clone from GitHub (commit `418d846`) + new `.venv` | `pip freeze` = `requirements.txt`; `tests.py` 134 ok; editor import and 300-frame run exit 0 with no error or missing script; `godot_check.py` 13 lines ok; `git status` clean | 2026-10-30 | same Mac, Godot 4.7.2 |
| GitHub Pages URL | the 4 main files 200 with the right MIME type and identical to the repo; no console error; 13 lines from the browser console match Python | 2026-10-30 | Chrome 156 headless, Apple M5 |
| export after a fresh import | `index.wasm` / `index.js` identical, but the imported `Knight.glb` and `Main.scn` differ by 89 / 56 bytes between two fresh imports (likely random sub-resource ids); same behaviour | 2026-10-30 | same |
| other GPUs, Windows, Linux | **not tested** | | |
