"""Previa (Cycles CPU) de personagem GLB, opcionalmente numa pose de animacao.
Uso: blender -b --factory-startup --python-exit-code 1 --python scripts/characters/render_character.py -- \
       <arquivo.glb> <saida.png> [--action Nome --frame N] [--view full|face|station|diorama|pose] [--samples 64]
Tambem importavel: render(parse([...])) renderiza a cena-fonte atual (usado por build_agent.py --preview).
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


def render(a):
    """Renderiza a cena atual (importada ou a cena-fonte do build)."""
    scene = bpy.context.scene
    for o in [o for o in scene.objects if o.name in ("Cam", "Key", "Fill", "Rim", "Room", "RoomFill") or o.name.startswith("Plane")]:
        bpy.data.objects.remove(o)

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


    arm = arms[0] if arms else None
    bpy.context.view_layer.update()
    if arm:                                             # enquadra pelo personagem, onde quer que esteja
        M = arm.matrix_world
        fwd = (M.to_3x3() @ Vector((0, -1, 0))).normalized()
        right = fwd.cross(Vector((0, 0, 1))).normalized()
        head = M @ arm.pose.bones["head"].head + Vector((0, 0, 0.11))
        base = M.translation
    else:
        fwd, right, head, base = Vector((0, -1, 0)), Vector((-1, 0, 0)), Vector((0, 0, 0.8)), Vector()
    views = {   # (camera, alvo, lente)
        "full": (base + fwd * 1.55 - right * 0.45 + Vector((0, 0, 0.95)), base + Vector((0, 0, 0.50)), 50),
        "face": (head + fwd * 0.62 - right * 0.14 + Vector((0, 0, 0.05)), head, 70),
        "station": (base + fwd * 1.75 - right * 0.9 + Vector((0, 0, 1.35)), base + fwd * 0.18 + Vector((0, 0, 0.45)), 40),
        "diorama": (Vector((1.75, -2.15, 1.55)), Vector((0.02, 0.0, 0.40)), 52),
        "pose": (base + Vector((1.75, -2.15, 1.25)).normalized() * 1.9 + Vector((0, 0, 0.1)), base + Vector((0, 0, 0.36)), 55),
    }
    cam_loc, target, lens = views[a.view]
    diorama = any(o.name.endswith("_Diorama") for o in scene.objects)
    if diorama:
        light("Room", (0.0, -0.05, 1.0), 25, 0.9, (0.0, -0.05, 0.0))
        light("RoomFill", (0.5, -0.4, 0.7), 12, 0.5, (0, 0.1, 0.3))
    light("Key", (-1.0, -1.4, 1.8) if a.view != "diorama" else (0.6, -2.0, 2.4), 120, 1.2, target)
    light("Fill", (1.3, -0.9, 0.9) if a.view != "diorama" else (2.2, 0.3, 1.2), 35, 1.5, target)
    light("Rim", (0.4, 1.3, 1.5), 120, 0.8, target)
    if diorama:
        for n in ("Room", "RoomFill", "Key", "Fill", "Rim"):   # sem reflexo das luzes no vidro da vitrine
            bpy.data.objects[n].visible_glossy = False
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


def parse(argv):
    return ap.parse_args(argv)


if __name__ == "__main__":
    args = parse(sys.argv[sys.argv.index("--") + 1:])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=args.glb)
    render(args)
