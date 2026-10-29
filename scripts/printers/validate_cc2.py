"""Valida o GLB bruto da CC2 reimportando no Blender: hierarquia, malhas, materiais, dimensoes, pivos.
Uso: blender -b --factory-startup --python-exit-code 1 --python scripts/printers/validate_cc2.py -- <raw.glb>
"""
import json
import sys

import bpy
from mathutils import Vector

path = sys.argv[sys.argv.index("--") + 1]
ENCLOSURE = (0.398, 0.404, 0.490)       # Blender X, Y, Z (m)
TOL, PROTRUSION = 0.001, 0.020          # puxador (12 mm) + entrada de filamento (7 mm)
MOVERS = ["Door_Pivot", "Lid_Pivot", "Gantry_Y_Mover", "Toolhead_X_Mover", "Bed_Z_Mover",
          "Fan_Aux_Side_Rotor_Pivot", "Fan_Exhaust_Rotor_Pivot", "Fan_Toolhead_Rotor_Pivot"]
MATERIALS = {"Metal_Frame", "Panel_Painted", "Glass_Smoked", "Gold_Accent", "Plastic_Black",
             "Rubber", "Metal_Steel", "Aluminum_Bed", "Bed_PEI", "Brass_Nozzle",
             "Screen_Emissive", "Chamber_LED", "Lens_Black"}
PARENT = {"Door_Glass": "Door_Pivot", "Door_Handle": "Door_Pivot", "Lid_Glass": "Lid_Pivot",
          "Toolhead": "Toolhead_X_Mover", "Toolhead_X_Mover": "Gantry_Y_Mover",
          "Bed_Plate": "Bed_Z_Mover", "Fan_Toolhead_Rotor_Pivot": "Toolhead_X_Mover"}

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=path)
objs = {o.name: o for o in bpy.context.scene.objects}
meshes = [o for o in objs.values() if o.type == "MESH"]
fail = []

for n in ["CC2_Root", *MOVERS]:
    if n not in objs:
        fail.append(f"falta node {n}")
    elif n != "CC2_Root" and "anim" not in objs[n]:
        fail.append(f"{n} sem extras de animacao")
for child, par in PARENT.items():
    if child in objs and (objs[child].parent is None or objs[child].parent.name != par):
        fail.append(f"{child} deveria ser filho de {par}")


def bbox(obs):
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in obs:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo, hi = Vector(map(min, lo, w)), Vector(map(max, hi, w))
    return hi - lo


enclosure = bbox([objs[n] for n in ("Frame_Structure", "Base_Housing", "Feet") if n in objs])
total = bbox(meshes)
for e, t, exp, ax in zip(enclosure, total, ENCLOSURE, "XYZ"):
    if abs(e - exp) > TOL:
        fail.append(f"gabinete {ax}={e:.4f} != {exp}")
    if t - exp > PROTRUSION:
        fail.append(f"total {ax}={t:.4f} excede o gabinete em > {PROTRUSION}")

plate = bbox([objs["Bed_Plate"]]) if "Bed_Plate" in objs else None
if plate and abs(plate.x - 0.260) > TOL:
    fail.append(f"placa X={plate.x:.4f} != 0.260")

mats = {m.name.split(".")[0] for m in bpy.data.materials}
if not MATERIALS <= mats:
    fail.append(f"materiais faltando: {sorted(MATERIALS - mats)}")
g = bpy.data.materials.get("Glass_Smoked")
if g and g.node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value < 0.99:
    fail.append("vidro sem transmissao")


def opens(pivot, mesh, corner, axis_idx, comp, sign):
    """Aplica range_rad[0] e confere se o canto livre se move no sentido esperado."""
    p, m = objs[pivot], objs[mesh]
    before = m.matrix_world @ Vector(m.bound_box[corner])
    local = p.matrix_world.inverted() @ before
    p.rotation_mode = "XYZ"
    p.rotation_euler[axis_idx] += p["range_rad"][0]
    bpy.context.view_layer.update()
    after = p.matrix_world @ local
    p.rotation_euler[axis_idx] -= p["range_rad"][0]
    bpy.context.view_layer.update()
    return (after[comp] - before[comp]) * sign > 0.05


if not opens("Door_Pivot", "Door_Glass", 6, 2, 1, -1):   # three Y == Blender Z; borda livre vai a -Y
    fail.append("porta nao abre para fora")
if not opens("Lid_Pivot", "Lid_Glass", 0, 0, 2, 1):      # frente da tampa sobe em Z
    fail.append("tampa nao levanta")

report = {
    "file": path, "meshes": len(meshes), "nodes": len(objs),
    "triangles": sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes),
    "enclosure_m": [round(v, 4) for v in enclosure], "bbox_total_m": [round(v, 4) for v in total],
    "materials": len(mats & MATERIALS), "movers": len([n for n in MOVERS if n in objs]),
    "fail": fail,
}
print("REPORT " + json.dumps(report))
if fail:
    raise SystemExit(1)
