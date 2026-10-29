"""Previa do GLB com Cycles em CPU (sem GPU). Renderiza o arquivo exportado, nao a cena-fonte.
Uso: blender -b --factory-startup --python scripts/printer/render_preview.py -- <arquivo.glb> <saida_dir> [samples]
"""
import math
import os
import sys

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
glb, out_dir = args[0], args[1]
samples = int(args[2]) if len(args) > 2 else 96

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = samples
scene.cycles.use_denoising = False  # build Ubuntu sem OpenImageDenoise
# menos ruido sem denoiser: sem causticas, glossy borrado, indireto limitado
scene.cycles.caustics_reflective = scene.cycles.caustics_refractive = False
scene.cycles.blur_glossy = 1.0
scene.cycles.sample_clamp_indirect = 3.0
scene.render.resolution_x = scene.render.resolution_y = 900
scene.render.image_settings.file_format = "JPEG"
scene.render.image_settings.quality = 88
scene.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in
    scene.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"

world = bpy.data.worlds.new("Studio")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.18, 0.19, 0.21, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
scene.world = world

# piso neutro
bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, 0))
floor = bpy.context.active_object
fm = bpy.data.materials.new("Floor")
fm.use_nodes = True
fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.5, 0.5, 0.52, 1)
fm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.8
floor.data.materials.append(fm)


def area(name, loc, energy, size):
    d = bpy.data.lights.new(name, "AREA")
    d.energy, d.size = energy, size
    o = bpy.data.objects.new(name, d)
    scene.collection.objects.link(o)
    o.location = loc
    o.visible_camera = False
    o.rotation_euler = (Vector((0, 0, 0.25)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


area("Key", (-0.8, -1.0, 1.2), 120, 0.8)
area("Fill", (1.0, -0.6, 0.6), 40, 1.0)
area("Rim", (0.3, 1.0, 1.0), 60, 0.6)
area("Inner", (0, 0, 0.45), 4.0, 0.2)   # luz da camara (ilustra o interior pelo vidro)

cam_d = bpy.data.cameras.new("Cam")
cam_d.lens = 50
cam = bpy.data.objects.new("Cam", cam_d)
scene.collection.objects.link(cam)
scene.camera = cam

views = {"front34": (0.95, -1.25, 0.75), "front": (0.0, -1.45, 0.32), "top34": (-0.75, -0.9, 1.25)}
os.makedirs(out_dir, exist_ok=True)
for name, loc in views.items():
    cam.location = loc
    cam.rotation_euler = (Vector((0, 0, 0.24)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = os.path.join(out_dir, f"{os.path.splitext(os.path.basename(glb))[0]}_{name}.jpg")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", scene.render.filepath)
