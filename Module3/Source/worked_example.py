"""Module 3 -- Fully Worked Example, Step 1: a point through every coordinate space.

Without options it prints the module's running point (2,3,4) with
M = Ry(90) @ T(1,0,-1), exactly as the PDF. With --scene it traces vertex
--vertex of that scene's model with the scene's own M, V, P and frame size,
and prints the columns of M and V (Lab 1 no 3 and 4).

Run:  python worked_example.py
      python worked_example.py --scene scenes/mymodel.json --vertex 120
"""
from __future__ import annotations

import argparse

import numpy as np

from transforms import (translate, rot_y, look_at, perspective, viewport,
                        perspective_divide_2d)

np.set_printoptions(precision=3, suppress=True)       # the PDF's transcript


def running_point():
    p = np.array([2.0, 3.0, 4.0])
    print(f"object p        = {np.r_[p, 1.0]}")

    M = rot_y(90) @ translate((1, 0, -1))
    world = (M @ np.r_[p, 1.0])
    print(f"model  M = Ry(90) . T(1,0,-1)        ; world  = M p       = {world}")

    V = look_at(eye=(0, 0, 8), center=(0, 0, 0))
    eye = V @ world
    print(f"view   V = lookAt(eye=[0,0,8], ctr=0); eye    = V world   = {eye}   "
          f"(z={eye[2]:.0f}: {'in front' if eye[2] < 0 else 'BEHIND'}, dist {abs(eye[2]):.0f})")

    P = perspective(60, 1.0, 1.0, 50.0)
    clip = P @ eye
    print(f"proj   P = perspective(60deg, 1, 1, 50)")
    print(f"clip            = P eye              = {clip}")
    ndc = clip[:3] / clip[3]
    print(f"ndc  = clip/clip.w                   = {ndc}")

    W, H = 800, 600
    scr = viewport(ndc[None, :], W, H)[0]
    print(f"screen ({W}x{H}) = [{scr[0]:.0f} {scr[1]:.0f}]  depth {(ndc[2] + 1) * 0.5:.3f}")

    print()
    print("--- Example E1 cross-check (bare similar-triangles projection) ---")
    print(f"world point (pre-view) = {world[:3]}   -> after Ry(90) of (3,3,3): (3,3,-3)")
    proj2d = perspective_divide_2d(world[:3], d=2)
    print(f"perspective divide d=2 of (3,3,-3)   = {proj2d}   (expected [2. 2.])")


def columns(name, A, labels=("+x", "+y", "+z", "origin")):
    for k, lab in enumerate(labels):
        print(f"  {name} column {k + 1}: {lab:>12} -> {A[:3, k]}")


def trace_scene(path, vi):
    from objio import load_obj
    from scene import load_scene, model_matrix, view_matrix, projection_matrix

    sc = load_scene(path)
    mesh = load_obj(sc["model"]["obj"])
    W, H = sc["frame"]["w"], sc["frame"]["h"]
    M, V, P = model_matrix(sc), view_matrix(sc), projection_matrix(sc)
    p = np.r_[mesh.positions[vi], 1.0]
    m, c = sc["model"], sc["camera"]

    print(f"scene {path}: {mesh.n_tris} triangles, frame {W}x{H}")
    print(f"vertex {vi} of {m['obj']}")
    print(f"object p        = {p}")
    world = M @ p
    print(f"model  M = T{tuple(m['translate'])} . Ry({m['rot_y_deg']}) . S{tuple(m['scale'])}")
    print(f"world  = M p     = {world}")
    eye = V @ world
    print(f"view   V = lookAt(eye={c['eye']}, ctr={c['center']})")
    print(f"eye    = V world = {eye}   (z={eye[2]:.4f}: "
          f"{'in front' if eye[2] < 0 else 'BEHIND'}, dist {-eye[2]:.4f})")
    clip = P @ eye
    print(f"proj   P = perspective({c['fovy_deg']}deg, {W}/{H}, {c['near']}, {c['far']})")
    print(f"clip   = P eye   = {clip}   (w = -z_eye = {clip[3]:.4f})")
    inside = bool(np.all(np.abs(clip[:3]) <= clip[3]))
    print(f"inside the frustum (-w <= x,y,z <= w): {inside}")
    ndc = clip[:3] / clip[3]
    print(f"ndc    = clip/w  = {ndc}")
    scr = viewport(ndc[None, :], W, H)[0]
    print(f"screen ({W}x{H}) = [{scr[0]:.4f} {scr[1]:.4f}]  -> pixel "
          f"({int(np.floor(scr[0]))}, {int(np.floor(scr[1]))})  depth01 {(ndc[2] + 1) * 0.5:.4f}")
    print()
    print("M =\n" + np.array2string(M))
    columns("M", M)
    print("V =\n" + np.array2string(V))
    columns("V", V, ("world +x", "world +y", "world +z", "world origin"))
    print("  (columns of V: where the world axes and origin land, seen from the camera)")
    for k, lab in enumerate(("right", "up", "back (-view direction)")):
        print(f"  V row {k + 1}: camera {lab} in world = {V[k, :3]}")
    print(f"  V^-1 column 4 (the camera position) = {np.linalg.inv(V)[:3, 3]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene")
    ap.add_argument("--vertex", type=int, default=0)
    args = ap.parse_args()
    if args.scene:
        with np.printoptions(precision=4, suppress=True):   # A1 asks for >= 3 decimals
            trace_scene(args.scene, args.vertex)
    else:
        running_point()


if __name__ == "__main__":
    main()
