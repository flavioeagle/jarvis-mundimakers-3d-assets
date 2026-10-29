"""Previa (Cycles CPU) de personagem GLB, opcionalmente numa pose de animacao.
Uso: blender -b --factory-startup --python-exit-code 1 --python scripts/characters/render_character.py -- \
       <arquivo.glb> <saida.png> [--action Nome --frame N] [--view full|face|station] [--samples 64]
"""
import argparse
import sys

import bpy
from mathutils import Vector

ap = argparse.ArgumentParser()
ap.add_argument("glb")
ap.add_argument("out")
ap.add_argument("--action")
ap.add_argument("--frame", type=int, default=1)
ap.add_argument("--view", default="full")
ap.add_argument("--samples", type=int, default=64)
ap.add_argument("--res", type=int, default=900)
ap.add_argument("--hide-station", action="store_true")
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:])

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a.glb)
scene = bpy.context.scene
arms = [o for o in scene.objects if o.type == "ARMATURE"]
act = None
if a.action:
    act = bpy.data.actions.get(a.action) or next(x for x in bpy.data.actions if x.name.startswith(a.action))
for arm in arms:                                    # sem NLA: so a acao pedida (ou pose de repouso)
    arm.animation_data_create()
    for t in list(arm.animation_data.nla_tracks):
        arm.animation_data.nla_tracks.remove(t)
    arm.animation_data.action = act
    for pb in arm.pose.bones:                       # o importador deixa a ultima pose aplicada
        pb.rotation_quaternion, pb.rotation_euler = (1, 0, 0, 0), (0, 0, 0)
        pb.location, pb.scale = (0, 0, 0), (1, 1, 1)
scene.frame_set(a.frame)
if a.hide_station:
    for root in [o for o in scene.objects if o.name.endswith("_Station")]:
        for o in [root, *root.children_recursive]:
            o.hide_render = True

scene.render.engine = "CYCLES"
c = scene.cycles
c.device, c.samples, c.use_denoising = "CPU", a.samples, False
c.caustics_reflective = c.caustics_refractive = False
c.blur_glossy, c.sample_clamp_indirect = 1.0, 3.0
scene.render.resolution_x = scene.render.resolution_y = a.res
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.compression = 90
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"

world = bpy.data.worlds.new("Studio")
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value, bg.inputs["Strength"].default_value = (0.45, 0.48, 0.54, 1), 0.35
scene.world = world
bpy.ops.mesh.primitive_plane_add(size=8)
fm = bpy.data.materials.new("Floor")
fm.use_nodes = True
fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.42, 0.43, 0.46, 1)
bpy.context.active_object.data.materials.append(fm)


def light(name, loc, energy, size, target):
    d = bpy.data.lights.new(name, "AREA")
    d.energy, d.size = energy, size
    o = bpy.data.objects.new(name, d)
    scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    o.visible_camera = False


views = {   # (camera, alvo, lente)
    "full": ((0.55, -1.55, 0.95), (0.0, 0.0, 0.50), 50),
    "face": ((0.18, -0.75, 0.86), (0.0, 0.0, 0.79), 70),
    "station": ((0.95, -1.75, 1.35), (0.0, -0.18, 0.45), 40),
}
cam_loc, target, lens = views[a.view]
light("Key", (-1.0, -1.4, 1.8), 120, 1.2, target)
light("Fill", (1.3, -0.9, 0.9), 35, 1.5, target)
light("Rim", (0.4, 1.3, 1.5), 120, 0.8, target)
cd = bpy.data.cameras.new("Cam")
cd.lens = lens
cam = bpy.data.objects.new("Cam", cd)
scene.collection.objects.link(cam)
cam.location = cam_loc
cam.rotation_euler = (Vector(target) - Vector(cam_loc)).to_track_quat("-Z", "Y").to_euler()
scene.camera = cam
scene.render.filepath = a.out
bpy.ops.render.render(write_still=True)
print("RENDERED", a.out)
