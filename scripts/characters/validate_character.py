"""Valida GLB bruto de personagem reimportando no Blender: rig, pesos, anexos, materiais, animacoes.
Uso: blender -b --factory-startup --python-exit-code 1 --python scripts/characters/validate_character.py -- <raw.glb> <Nome> [clay|voxel]
"""
import json
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from chibi import BONES  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:]
path, name = args[:2]
kind = args[2] if len(args) > 2 else "clay"
ANIMS = ["Idle", "Working", "AwaitingApproval", "Done"]
if kind == "voxel":
    RIGID = {"head": [f"{name}_Head"], "eye.L": ["Eye.L"], "eye.R": ["Eye.R"], "mouth": ["Mouth"],
             "brow.L": ["Brow.L"], "brow.R": ["Brow.R"], "chest": [f"{name}_Torso"],
             "upperarm.L": [f"{name}_UpperArm.L"], "hand.R": [f"{name}_Hand.R"], "foot.L": [f"{name}_Boot.L"]}
else:
    RIGID = {"head": [f"{name}_Hair", "Head", "Nose"], "eye.L": ["Eye.L", "Lash.L"], "eye.R": ["Eye.R", "Lash.R"],
             "mouth": ["Mouth"], "brow.L": ["Brow.L"], "brow.R": ["Brow.R"]}

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=path)
objs = {o.name: o for o in bpy.data.objects}
fail = []
arms = [o for o in objs.values() if o.type == "ARMATURE"]
if len(arms) != 1:
    fail.append(f"esperado 1 armature, achou {len(arms)}")
arm = arms[0]
bones = {b.name for b in arm.data.bones}
missing = {b[0] for b in BONES} - bones
if missing:
    fail.append(f"ossos faltando: {sorted(missing)}")

skinned = [o for o in objs.values() if o.type == "MESH" and any(m.type == "ARMATURE" for m in o.modifiers)]
if kind == "clay" and len(skinned) < 3:
    fail.append(f"poucas malhas com skin: {len(skinned)}")
unweighted = 0
for o in skinned:
    for v in o.data.vertices:
        s = sum(g.weight for g in v.groups)
        if s < 0.99 or s > 1.01:
            unweighted += 1
if unweighted:
    fail.append(f"{unweighted} vertices com peso != 1")

for bone, names in RIGID.items():
    for n in names:
        o = objs.get(n)
        if o is None:
            fail.append(f"falta {n}")
        elif o.parent_type != "BONE" or o.parent_bone != bone:
            fail.append(f"{n} deveria seguir o osso {bone} (esta em {o.parent_type}/{o.parent_bone})")

acts = {a.name.split("_")[0]: a for a in bpy.data.actions}
for an in ANIMS:
    a = acts.get(an)
    if a is None:
        fail.append(f"falta animacao {an}")
        continue
    if len(a.fcurves) < 6:
        fail.append(f"{an}: poucos canais ({len(a.fcurves)})")
    for fc in a.fcurves:
        ys = [k.co.y for k in fc.keyframe_points]
        if any(math.isnan(y) for y in ys):
            fail.append(f"{an}: NaN em {fc.data_path}")
            break
        if an != "Done" and ys and abs(ys[0] - ys[-1]) > 1e-3:
            fail.append(f"{an}: loop aberto em {fc.data_path}[{fc.array_index}]")
            break

meshes = [o for o in objs.values() if o.type == "MESH"]
dio = objs.get(f"{name}_Diorama")
if dio is None:
    fail.append("sem no _Diorama")
elif arm.parent != dio:
    fail.append("armature fora do diorama")
glass = bpy.data.materials.get("Vitrine_Glass")
if glass is None or glass.blend_method != "BLEND":
    fail.append("vidro da vitrine sem alpha blend")
mats = sorted({m.name for o in meshes for m in o.data.materials if m})
report = {
    "file": path, "bones": len(bones), "skinned_meshes": len(skinned), "meshes": len(meshes),
    "triangles": sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes),
    "materials": len(mats), "animations": {an: round(acts[an].frame_range[1] - acts[an].frame_range[0] + 1) for an in ANIMS if an in acts},
    "kind": kind, "fail": fail,
}
print("REPORT " + json.dumps(report))
if fail:
    raise SystemExit(1)
