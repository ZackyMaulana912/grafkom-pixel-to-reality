"""Turn the downloaded Aston Martin F1 AMR23 model (Redgrund, Sketchfab, CC BY 4.0) into the
third AR model, in metres.

Runs inside Blender (5.x), headless:
  Blender -b <AMR23 .blend> -P car_to_glb.py -- <out.glb> <hotspot_text.json> <hotspots_out.json> [subdiv] [texture_px]

The source has no trustworthy size (it is about 3.7 units long), so it is scaled with a rule
from the 2023 F1 Technical Regulations (FIA, Issue 7): Article 10.8.1c, a dry tyre may not be
more than 725 mm in diameter. The tyres are found as the outermost geometry of the car, and
two other rules become checks: Article 3.4.1 (no bodywork outboard of Y = 1000 mm, so the car
is at most 2000 mm wide, tyres excepted) and Article 3.4.2 (wheelbase at most 3600 mm).
"""
import json
import math
import os
import sys

import bpy
import mathutils
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scan_to_glb import place_hotspots  # noqa: E402  (same ray-cast placement as the horse)

TYRE_DIAMETER_M = 0.725   # FIA 2023 Technical Regulations, Article 10.8.1c (dry-weather tyres)
WHEELBASE_MAX_M = 3.600   # Article 3.4.2
HALF_WIDTH_M = 1.000      # Article 3.4.1, Y = 1000


def measure_tyres(pts):
    """Find the two axles among the outermost vertices; return [(centre_y, diameter), ...] front to back."""
    xmax = np.abs(pts[:, 0]).max()
    outer = pts[np.abs(pts[:, 0]) > 0.8 * xmax]
    ys = np.sort(outer[:, 1])
    gap = int(np.argmax(np.diff(ys)))      # the empty stretch between the two wheel pairs
    out = []
    for c in (outer[outer[:, 1] <= ys[gap]], outer[outer[:, 1] > ys[gap]]):
        z_lo, z_hi = c[:, 2].min(), c[:, 2].max()
        top = c[c[:, 2] > z_lo + 0.9 * (z_hi - z_lo)]
        out.append(((top[:, 1].min() + top[:, 1].max()) / 2, z_hi - z_lo))
    return out


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    out_glb, text_path, hotspots_out = args[:3]
    subdiv = int(args[3]) if len(args) > 3 else 1
    texture_px = int(args[4]) if len(args) > 4 else 2048

    for o in [o for o in bpy.data.objects if o.type != "MESH"]:  # the two blueprint images
        bpy.data.objects.remove(o)
    obj = bpy.data.objects["Body_Baked"]
    for m in list(obj.modifiers):
        if m.type == "SUBSURF" and subdiv == 0:
            obj.modifiers.remove(m)  # level 0 means the plain cage; Blender refuses to apply a level-0 modifier
        elif m.type == "SUBSURF":
            m.levels = m.render_levels = subdiv
    bpy.context.view_layer.objects.active = obj
    for m in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)
    obj.data.transform(obj.matrix_world)
    obj.matrix_world = mathutils.Matrix.Identity(4)

    pts = np.array([v.co[:] for v in obj.data.vertices])
    (y_a, d_a), (y_b, d_b) = measure_tyres(pts)
    s = TYRE_DIAMETER_M / ((d_a + d_b) / 2)
    mid_y = (y_a + y_b) / 2
    # wheelbase centre to the origin, floor at z = 0, length turned from y onto x
    m = (mathutils.Matrix.Rotation(-math.pi / 2, 4, "Z") @ mathutils.Matrix.Scale(s, 4)
         @ mathutils.Matrix.Translation((0.0, -mid_y, -pts[:, 2].min())))
    obj.data.transform(m)
    obj.data.update()
    pts = np.array([v.co[:] for v in obj.data.vertices])
    size = pts.max(axis=0) - pts.min(axis=0)
    wheelbase = abs(y_a - y_b) * s
    print(f"SCALE {s:.6f} m per unit (tyre diameters {d_a:.4f} and {d_b:.4f} units = {TYRE_DIAMETER_M * 1000:.0f} mm)")
    print(f"CHECK width {size[1]:.3f} m (FIA limit {2 * HALF_WIDTH_M:.3f}), wheelbase {wheelbase:.3f} m "
          f"(FIA limit {WHEELBASE_MAX_M:.3f}), length {size[0]:.3f} m, height {size[2]:.3f} m")

    mat = obj.data.materials[0]
    for n in mat.node_tree.nodes:
        if n.type == "TEX_IMAGE" and n.image and n.image.size[0] > texture_px:
            n.image.scale(texture_px, texture_px)
    mat.name = "amr23"
    obj.name = obj.data.name = "amr23"

    hotspots = place_hotspots(obj, pts, text_path)
    tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    print(f"MESH {len(obj.data.vertices)} vertices, {tris} triangles (subdivision level {subdiv})")
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=out_glb, export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=True, export_image_format="JPEG", export_jpeg_quality=90,
                              export_texcoords=True, export_normals=True, export_tangents=False,
                              export_materials="EXPORT", export_cameras=False, export_lights=False,
                              export_extras=False, export_animations=False)
    print(f"GLB {out_glb} {os.path.getsize(out_glb) / 1e6:.2f} MB, textures at most {texture_px} px")
    with open(hotspots_out, "w") as f:
        json.dump({"model": os.path.basename(out_glb), "units": "metres, glTF axes (y up)",
                   "scale_rule": "tyre diameter 725 mm, FIA 2023 F1 Technical Regulations Art. 10.8.1c",
                   "hotspots": hotspots}, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"HOTSPOTS {len(hotspots)} written to {hotspots_out}")


main()
