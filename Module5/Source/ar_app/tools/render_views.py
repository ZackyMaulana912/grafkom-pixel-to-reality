"""Render the AR model from eight sides plus the top, into one PNG for the docs.

Runs inside Blender (5.x), headless:
  Blender -b -P render_views.py -- <model.glb> <out.png> [distance]
Workbench renderer with the model's own texture, so the picture shows the scan itself.
"""
import math
import os
import sys
import tempfile

import bpy
import mathutils
import numpy as np

ARGS = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = ARGS[:2]
DISTANCE = float(ARGS[2]) if len(ARGS) > 2 else 1.25  # camera distance in model diagonals; a long car needs more
CELL = 360
VIEWS = [(az, 12) for az in (0, 45, 90, 135, 180, 225, 270, 315)] + [(0, 89)]


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=SRC)
    obj = next(o for o in bpy.context.scene.objects if o.type == "MESH")
    pts = np.array([obj.matrix_world @ v.co for v in obj.data.vertices])
    centre = mathutils.Vector((pts.max(axis=0) + pts.min(axis=0)) / 2)
    radius = float(np.linalg.norm(pts.max(axis=0) - pts.min(axis=0)))
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "TEXTURE"
    scene.render.resolution_x = scene.render.resolution_y = CELL
    scene.render.film_transparent = False
    scene.world = bpy.data.worlds.new("light grey")
    scene.world.color = (0.8, 0.8, 0.8)
    target = bpy.data.objects.new("target", None)
    scene.collection.objects.link(target)
    target.location = centre
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    scene.collection.objects.link(cam)
    scene.camera = cam
    track = cam.constraints.new("TRACK_TO")
    track.target, track.track_axis, track.up_axis = target, "TRACK_NEGATIVE_Z", "UP_Y"
    cells = []
    with tempfile.TemporaryDirectory() as tmp:
        for az, el in VIEWS:
            # azimuth 0 = the glTF front (+z), which is Blender -y after import
            a, e = math.radians(az - 90), math.radians(el)
            cam.location = centre + mathutils.Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e),
                                                      math.sin(e))) * radius * DISTANCE
            scene.render.filepath = os.path.join(tmp, f"{az}_{el}.png")
            bpy.ops.render.render(write_still=True)
            img = bpy.data.images.load(scene.render.filepath)
            cells.append(np.array(img.pixels[:]).reshape(CELL, CELL, 4))
            bpy.data.images.remove(img)
    rows = [np.concatenate(cells[i:i + 3], axis=1) for i in (0, 3, 6)]
    sheet = np.concatenate(rows[::-1], axis=0)  # Blender images are stored bottom row first
    out = bpy.data.images.new("sheet", width=3 * CELL, height=3 * CELL)
    out.pixels = sheet.ravel()
    out.filepath_raw = OUT
    out.file_format = "PNG"
    out.save()
    print(f"wrote {OUT}")


main()
