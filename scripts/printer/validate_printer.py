"""Reimporta o GLB da impressora e confere hierarquia, malhas, materiais, dimensoes e pivos.
Uso: blender -b --factory-startup --python-exit-code 1 --python scripts/printer/validate_printer.py -- <arquivo.glb>
"""
import json
import sys

import bpy
from mathutils import Vector

path = sys.argv[sys.argv.index("--") + 1]
EXPECTED_BBOX = (0.398, 0.404, 0.490)   # Blender X, Y, Z (m)
TOL = 0.001                             # gabinete (Frame_Structure + Feet)
PROTRUSION = 0.012                      # puxador/display podem sair do gabinete
MOVERS = ["Door_Pivot", "Lid_Pivot", "Gantry_Y_Mover", "Toolhead_X_Mover", "Bed_Z_Mover"]
MATERIALS = {"Metal_Dark", "Metal_Rail", "Glass_Smoked", "Gold_Accent", "Plastic_Black",
             "Bed_PEI", "Rubber", "Screen_Emissive"}

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=path)
objs = {o.name: o for o in bpy.context.scene.objects}
meshes = [o for o in objs.values() if o.type == "MESH"]
fail = []

for n in ["Printer_Root", *MOVERS]:
    if n not in objs:
        fail.append(f"falta node {n}")

def bbox(obs):
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in obs:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo, hi = Vector(map(min, lo, w)), Vector(map(max, hi, w))
    return hi - lo


enclosure = bbox([objs[n] for n in ("Frame_Structure", "Feet") if n in objs])
size = bbox(meshes)
for got, total, exp, ax in zip(enclosure, size, EXPECTED_BBOX, "XYZ"):
    if abs(got - exp) > TOL:
        fail.append(f"gabinete {ax}={got:.4f} != {exp}")
    if total - exp > PROTRUSION:
        fail.append(f"total {ax}={total:.4f} excede gabinete em mais de {PROTRUSION}")

mats = {m.name for m in bpy.data.materials}
if not MATERIALS <= mats:
    fail.append(f"materiais faltando: {MATERIALS - mats}")
glass = bpy.data.materials.get("Glass_Smoked")
if glass and glass.node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value < 0.99:
    fail.append("vidro sem transmissao")

# Pivos: extras sobrevivem e o sentido de abertura esta correto.
def world_pt(o, local):
    return o.matrix_world @ Vector(local)

for n in MOVERS:
    if n in objs and "anim" not in objs[n]:
        fail.append(f"{n} sem extras de animacao")
if {"Door_Pivot", "Door_Glass"} <= objs.keys():
    door, glass_ob = objs["Door_Pivot"], objs["Door_Glass"]
    edge = glass_ob.matrix_world @ Vector(glass_ob.bound_box[6])  # canto livre (+x)
    local = door.matrix_world.inverted() @ edge
    door.rotation_mode = "XYZ"
    door.rotation_euler.z += door["range_rad"][0]                  # three Y == Blender Z
    bpy.context.view_layer.update()
    if (door.matrix_world @ local).y >= edge.y:
        fail.append("porta nao abre para fora")
if {"Lid_Pivot", "Lid_Glass"} <= objs.keys():
    lid, lg = objs["Lid_Pivot"], objs["Lid_Glass"]
    front = lg.matrix_world @ Vector(lg.bound_box[0])               # canto frontal (-y)
    local = lid.matrix_world.inverted() @ front
    lid.rotation_mode = "XYZ"
    lid.rotation_euler.x += lid["range_rad"][0]                    # three X == Blender X
    bpy.context.view_layer.update()
    if (lid.matrix_world @ local).z <= front.z:
        fail.append("tampa nao levanta")

report = {
    "file": path, "meshes": len(meshes), "nodes": len(objs),
    "triangles": sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes),
    "enclosure_m": [round(v, 4) for v in enclosure], "bbox_total_m": [round(v, 4) for v in size], "materials": sorted(mats & MATERIALS),
    "movers": {n: objs[n].get("anim") for n in MOVERS if n in objs},
    "fail": fail,
}
print("REPORT " + json.dumps(report))
if fail:
    raise SystemExit(1)
