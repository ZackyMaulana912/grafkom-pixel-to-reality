"""Turn the photogrammetry scan of my horse statue into the AR model, in metres.

Runs inside Blender (5.x), headless:
  Blender -b -P scan_to_glb.py -- <scan.usdz> <out.glb> <kuda_ukuran.json> <hotspot_text.json> <hotspots_out.json> [texture_px]

Steps, all from the one scan so geometry and hotspots share one coordinate system:
1. Import the USDZ (Object Capture output, arbitrary units, z up in Blender).
2. Level it: the pedestal's side walls must be vertical, so "up" is the direction most
   perpendicular to their normals (smallest eigenvector). The floor is the pedestal's
   underside (downward faces near the bottom, area-weighted median), not the lowest vertex,
   which is a stray bit of geometry about 1 cm lower.
3. Find the pedestal: the lowest 5% of the vertices, boxed along its own main axis (PCA).
   Turn the model so that axis lies along x, with the head (highest vertices) on +x.
4. Scale so the pedestal length equals my measured base length; put the origin at the centre
   of the pedestal's footprint, on the floor. glTF units are metres.
5. Material: the scan's colour and normal maps, resized to texture_px (default 2048) and
   written as JPEG; the 8K roughness map is replaced by one constant value.
6. Hotspots: for every entry of hotspot_text.json, a ray from outside the model towards a
   point given as fractions of the bounding box; where it first hits the mesh is the hotspot
   position, the face normal there its normal. Written in glTF axes (y up, x right, z front).
7. Export one GLB and print the checks (measured vs scanned sizes, triangles, file size).
"""
import json
import math
import os
import sys

import bmesh
import bpy
import mathutils
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT, MEASURE, TEXT, HOTSPOTS_OUT = args[:5]
TEXTURE_PX = int(args[5]) if len(args) > 5 else 2048
ROUGHNESS = 0.45  # polished stone-like surface; the scan's own map is 8K and not worth the bytes


def gltf_from_blender(v):
    """Blender (x, y, z), z up -> glTF (x, z, -y), y up: what the glTF exporter does with +Y up."""
    return [float(v[0]), float(v[2]), float(-v[1])]


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.usd_import(filepath=SRC)
    obj = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
    obj.data.transform(obj.matrix_world)  # bake the USD parent transforms into the vertices
    obj.parent = None
    obj.matrix_world = mathutils.Matrix.Identity(4)
    for o in [o for o in bpy.context.scene.objects if o is not obj]:
        bpy.data.objects.remove(o)

    tilt_deg, z0 = level(obj)
    pts = np.array([v.co[:] for v in obj.data.vertices])
    z1 = pts[:, 2].max()
    base = pts[pts[:, 2] < z0 + 0.05 * (z1 - z0)][:, :2]
    centre = base.mean(axis=0)
    _, vecs = np.linalg.eigh(np.cov((base - centre).T))
    long_axis = vecs[:, -1]
    turn = -math.atan2(long_axis[1], long_axis[0])
    top = pts[pts[:, 2] > z1 - 0.05 * (z1 - z0)][:, :2]
    rot2 = np.array([[math.cos(turn), -math.sin(turn)], [math.sin(turn), math.cos(turn)]])
    if ((top - centre) @ rot2.T)[:, 0].mean() < 0:  # head on -x: turn half a circle more
        turn += math.pi
        rot2 = -rot2
    proj = (base - centre) @ rot2.T
    box_lo, box_hi = proj.min(axis=0), proj.max(axis=0)
    box_mid = (box_lo + box_hi) / 2
    length_units = box_hi[0] - box_lo[0]

    with open(MEASURE) as f:
        measured = json.load(f)
    s = measured["base_length_cm"] / 100.0 / length_units
    m = (mathutils.Matrix.Scale(s, 4)
         @ mathutils.Matrix.Translation((-box_mid[0], -box_mid[1], 0.0))
         @ mathutils.Matrix.Rotation(turn, 4, "Z")
         @ mathutils.Matrix.Translation((-centre[0], -centre[1], -z0)))
    obj.data.transform(m)
    obj.data.update()

    pts = np.array([v.co[:] for v in obj.data.vertices])
    size = pts.max(axis=0) - pts.min(axis=0)
    base_now = pts[pts[:, 2] < 0.05 * size[2]]
    base_w = base_now[:, 1].max() - base_now[:, 1].min()
    top = _faces(obj, lambda c, n: (n[:, 2] > 0.95) & (c[:, 2] > 0.03 * size[2]) & (c[:, 2] < 0.2 * size[2]))
    print(f"LEVEL turned {tilt_deg:.2f} deg so the pedestal walls stand vertical")
    print(f"SCALE {s:.6f} m per scan unit (base length {length_units:.4f} units = {measured['base_length_cm']} cm)")
    print(f"CHECK total height {size[2] * 100:.1f} cm (measured {measured['total_height_cm']}), "
          f"base width {base_w * 100:.1f} cm (measured {measured['base_width_cm']}), "
          f"base height {top * 100:.1f} cm (measured {measured['base_height_cm']}), "
          f"bounding box {size[0] * 100:.1f} x {size[1] * 100:.1f} x {size[2] * 100:.1f} cm")

    # material: keep colour + normal map, resized; constant roughness instead of the 8K map
    mat = obj.data.materials[0]
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
    for n in list(nodes):
        if n.type == "TEX_IMAGE" and "roughness" in n.image.name:
            nodes.remove(n)
        elif n.type == "SEPARATE_COLOR":
            nodes.remove(n)
    bsdf.inputs["Roughness"].default_value = ROUGHNESS
    bsdf.inputs["Metallic"].default_value = 0.0
    for n in nodes:
        if n.type == "TEX_IMAGE":
            n.image.scale(TEXTURE_PX, TEXTURE_PX)
    mat.name = "kuda_scan"
    obj.name = obj.data.name = "kuda"

    hotspots = place_hotspots(obj, pts)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    open_edges = sum(1 for e in bm.edges if len(e.link_faces) == 1)
    tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    print(f"MESH {len(obj.data.vertices)} vertices, {tris} triangles, {open_edges} open edges")

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=True, export_image_format="JPEG", export_jpeg_quality=90,
                              export_texcoords=True, export_normals=True, export_tangents=False,
                              export_materials="EXPORT", export_cameras=False, export_lights=False,
                              export_extras=False, export_animations=False)
    print(f"GLB {OUT} {os.path.getsize(OUT) / 1e6:.2f} MB, textures {TEXTURE_PX} px")
    with open(HOTSPOTS_OUT, "w") as f:
        json.dump({"model": os.path.basename(OUT), "units": "metres, glTF axes (y up)",
                   "measured": measured, "hotspots": hotspots}, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"HOTSPOTS {len(hotspots)} written to {HOTSPOTS_OUT}")


def _face_arrays(obj):
    me = obj.data
    return (np.array([p.center[:] for p in me.polygons]), np.array([p.normal[:] for p in me.polygons]),
            np.array([p.area for p in me.polygons]))


def _faces(obj, rule):
    """Area-weighted median height of the faces selected by rule(centres, normals)."""
    c, n, a = _face_arrays(obj)
    sel = rule(c, n)
    order = np.argsort(c[sel, 2])
    cum = np.cumsum(a[sel][order])
    return float(c[sel, 2][order][np.searchsorted(cum, cum[-1] / 2)])


def level(obj):
    """Rotate so the pedestal walls are vertical; return (angle turned in degrees, floor height)."""
    c, n, a = _face_arrays(obj)
    z0, z1 = c[:, 2].min(), c[:, 2].max()
    walls = (np.abs(n[:, 2]) < 0.3) & (c[:, 2] < z0 + 0.1 * (z1 - z0))
    w = n[walls] * np.sqrt(a[walls])[:, None]
    _, vecs = np.linalg.eigh(w.T @ w)
    up = mathutils.Vector(vecs[:, 0] if vecs[2, 0] > 0 else -vecs[:, 0])
    q = up.rotation_difference(mathutils.Vector((0.0, 0.0, 1.0)))
    obj.data.transform(q.to_matrix().to_4x4())
    obj.data.update()
    c, _, _ = _face_arrays(obj)
    z0, z1 = c[:, 2].min(), c[:, 2].max()
    floor = _faces(obj, lambda c, n: (n[:, 2] < -0.9) & (c[:, 2] < z0 + 0.03 * (z1 - z0)))
    return math.degrees(q.angle), floor


def place_hotspots(obj, pts):
    """Ray-cast every hotspot of the text file onto the mesh (Blender axes), return glTF-axis entries."""
    if not os.path.exists(TEXT):
        return []
    with open(TEXT) as f:
        entries = json.load(f)["hotspots"]
    lo, hi = pts.min(axis=0), pts.max(axis=0)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    out = []
    for e in entries:
        fx, fz = e["aim"]  # fractions of the box: along the length (x) and the height (z)
        target = mathutils.Vector((lo[0] + fx * (hi[0] - lo[0]), 0.0, lo[2] + fz * (hi[2] - lo[2])))
        side = {"front": (0, -1, 0), "back": (0, 1, 0), "head": (1, 0, 0), "tail": (-1, 0, 0)}[e["from"]]
        direction = -mathutils.Vector(side)
        origin = target - direction * 2.0
        hit, loc, normal, *_ = obj.ray_cast(origin, direction, depsgraph=depsgraph)
        if not hit:
            raise SystemExit(f"hotspot {e['id']}: the ray missed the model, change its aim")
        out.append({k: v for k, v in e.items() if k not in ("aim", "from")}
                   | {"position": [round(c, 4) for c in gltf_from_blender(loc)],
                      "normal": [round(c, 4) for c in gltf_from_blender(normal)]})
        print(f"HOTSPOT {e['id']}: {out[-1]['position']} normal {out[-1]['normal']}")
    return out


main()
