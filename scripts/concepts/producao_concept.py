"""Concept estatico do tecnico de Producao (voxel colecionavel) para aprovacao. Sem rig/animacao.
Uso: blender -b --factory-startup --python-exit-code 1 --python scripts/concepts/producao_concept.py -- <saida.png> [samples]
Proporcoes: docs/visual-guide.md (cabeca+capacete ~45% da altura, corpo compacto, pernas curtas).
"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import chibi as C  # noqa: E402
from bparts import MAT, Part, material  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:]
OUT, SPP = args[0], int(args[1]) if len(args) > 1 else 128

bpy.ops.wm.read_factory_settings(use_empty=True)
MAT.update({
    "skin": material("Skin", (0.55, 0.30, 0.18), rough=0.55),
    "hair": material("Hair", (0.12, 0.05, 0.015), rough=0.6),
    "shirt": material("Shirt_Blue", (0.025, 0.075, 0.25), rough=0.75),
    "vest": material("Overall_Orange", (0.80, 0.17, 0.004), rough=0.6),
    "vest_d": material("Overall_Orange_Dark", (0.45, 0.08, 0.004), rough=0.6),
    "reflect": material("Reflective", (0.80, 0.82, 0.85), metallic=0.5, rough=0.2),
    "pants": material("Pants_Brown", (0.13, 0.065, 0.025), rough=0.75),
    "pants_d": material("Kneepad", (0.06, 0.05, 0.05), rough=0.6),
    "boot": material("Boot", (0.08, 0.045, 0.02), rough=0.45, coat=0.3),
    "toe": material("Boot_Toe", (0.30, 0.18, 0.08), rough=0.4),
    "sole": material("Sole", (0.02, 0.02, 0.02), rough=0.8),
    "glove": material("Glove", (0.05, 0.05, 0.055), rough=0.7),
    "belt": material("Belt", (0.04, 0.03, 0.02), rough=0.5),
    "gold": material("Gold", (0.80, 0.62, 0.33), metallic=1.0, rough=0.3),
    "steel": material("Steel", (0.70, 0.71, 0.73), metallic=1.0, rough=0.25),
    "helmet": material("Helmet_Orange", (0.85, 0.20, 0.004), rough=0.28, coat=0.4),
    "white": material("Eye_White", (0.92, 0.92, 0.90), rough=0.3),
    "iris": material("Iris_Teal", (0.03, 0.32, 0.26), rough=0.3),
    "pupil": material("Pupil", (0.01, 0.01, 0.01), rough=0.3),
    "brow": material("Brow", (0.13, 0.06, 0.02), rough=0.6),
    "mouth": material("Mouth", (0.25, 0.05, 0.04), rough=0.5),
    "tongue": material("Tongue", (0.75, 0.30, 0.28), rough=0.5),
    "blush": material("Blush", (0.85, 0.40, 0.32), rough=0.6),
    "base": material("Base_Graphite", (0.03, 0.032, 0.036), metallic=0.6, rough=0.35),
    "accent": material("Base_Orange_Light", (1.0, 0.5, 0.1), emission=(1.0, 0.45, 0.08), strength=3.0),
})


def P(name, mats, boxes, bevel=0.010, seg=3):
    """Chanfra cada bloco isoladamente (chanfro sobre blocos interpenetrados gera faces invertidas)."""
    obs = []
    for i, b in enumerate(boxes):
        p = Part(f"{name}_{i}", mats)
        p.box(*b)
        obs.append(C.bake(p.build(bevel=min(bevel, min(b[0]) * 0.3), segments=seg)))
    return C.join(name, obs)


Z0 = 0.06                                   # topo da base colecionavel
# --- pernas curtas e botas robustas -----------------------------------------
for sx in (1, -1):
    x = sx * 0.075
    P(f"Leg{sx}", ["pants", "pants_d", "reflect"], [
        ((0.13, 0.14, 0.17), (x, 0, Z0 + 0.075 + 0.085)),
        ((0.11, 0.02, 0.05), (x, -0.072, Z0 + 0.17), "pants_d"),            # joelheira
        ((0.134, 0.144, 0.018), (x, 0, Z0 + 0.115), "reflect"),
    ])
    P(f"Boot{sx}", ["boot", "toe", "sole"], [
        ((0.14, 0.19, 0.075), (x, -0.02, Z0 + 0.045)),
        ((0.13, 0.06, 0.05), (x, -0.095, Z0 + 0.04), "toe"),
        ((0.15, 0.20, 0.022), (x, -0.02, Z0 + 0.011), "sole"),
    ], bevel=0.012)
# --- tronco compacto: camisa + jardineira com detalhes ------------------------
tz0, tz1 = Z0 + 0.245, Z0 + 0.50
tc = (tz0 + tz1) / 2
P("Torso", ["shirt", "vest", "vest_d", "reflect", "gold", "belt", "steel"], [
    ((0.31, 0.19, tz1 - tz0), (0, 0, tc)),
    ((0.24, 0.02, 0.17), (0, -0.098, tc - 0.02), "vest"),                        # peitilho
    ((0.32, 0.20, 0.07), (0, 0, tz0 + 0.035), "vest"),                           # cintura da jardineira
    ((0.045, 0.016, 0.09), (-0.08, -0.096, tz1 - 0.05), "vest"), ((0.045, 0.016, 0.09), (0.08, -0.096, tz1 - 0.05), "vest"),
    ((0.24, 0.022, 0.016), (0, -0.099, tc + 0.02), "reflect"),
    ((0.24, 0.022, 0.016), (0, -0.099, tc - 0.05), "reflect"),
    ((0.08, 0.024, 0.06), (0.05, -0.100, tc + 0.05), "vest_d"),                  # bolso
    ((0.008, 0.026, 0.04), (0.035, -0.102, tc + 0.085), "steel"),                # caneta
    ((0.022, 0.012, 0.022), (-0.08, -0.108, tz1 - 0.035), "gold"), ((0.022, 0.012, 0.022), (0.08, -0.108, tz1 - 0.035), "gold"),
    ((0.33, 0.21, 0.035), (0, 0, tz0 + 0.075), "belt"),
    ((0.05, 0.012, 0.03), (0, -0.112, tz0 + 0.075), "gold"),
    ((0.07, 0.05, 0.08), (0.14, -0.06, tz0 + 0.045), "belt"),                    # bolsa de ferramentas
    ((0.012, 0.012, 0.10), (0.125, -0.07, tz0 + 0.10), "steel"),
    ((0.10, 0.02, 0.03), (0, -0.09, tz1 - 0.005), "shirt"),                       # gola
])
# --- bracos: um acenando ------------------------------------------------------
for sx, wave in ((1, True), (-1, False)):
    x = sx * 0.20
    if not wave:
        P(f"Arm{sx}", ["shirt", "vest", "glove", "reflect"], [
            ((0.095, 0.11, 0.20), (x, 0, tz1 - 0.11)),
            ((0.10, 0.115, 0.05), (x, 0, tz1 - 0.025), "vest"),
            ((0.099, 0.114, 0.014), (x, 0, tz1 - 0.15), "reflect"),
            ((0.10, 0.11, 0.075), (x, -0.005, tz1 - 0.245), "glove"),
        ])
    else:
        P(f"Arm{sx}", ["shirt", "vest", "glove", "reflect"], [
            ((0.10, 0.115, 0.05), (x, 0, tz1 - 0.025), "vest"),
            ((0.15, 0.11, 0.095), (x + 0.05, 0, tz1 - 0.03)),                    # braco aberto
            ((0.092, 0.104, 0.15), (x + 0.10, 0, tz1 + 0.06)),                   # antebraco para cima
            ((0.099, 0.114, 0.014), (x + 0.10, 0, tz1 + 0.05), "reflect"),
            ((0.10, 0.06, 0.10), (x + 0.10, -0.005, tz1 + 0.18), "glove"),        # mao aberta
            ((0.035, 0.05, 0.04), (x + 0.055, -0.005, tz1 + 0.16), "glove"),       # polegar
        ])
# --- cabeca grande, rosto simpatico -------------------------------------------
hz = tz1 + 0.205                                     # centro da cabeca
hw, hd, hh = 0.36, 0.33, 0.33
fy = -hd / 2
P("Head", ["skin", "hair"], [
    ((hw, hd, hh), (0, 0, hz)),
    ((0.024, 0.02, 0.035), (0, fy - 0.008, hz - 0.035)),                          # nariz
    ((0.03, 0.05, 0.07), (hw / 2 + 0.01, 0.02, hz - 0.01)), ((0.03, 0.05, 0.07), (-hw / 2 - 0.01, 0.02, hz - 0.01)),
    ((hw + 0.014, hd * 0.55, hh * 0.62), (0, hd * 0.24, hz + hh * 0.19), "hair"),  # cabelo atras/lados
    ((0.035, hd * 0.5, 0.11), (hw / 2 + 0.006, -0.02, hz + 0.07), "hair"), ((0.035, hd * 0.5, 0.11), (-hw / 2 - 0.006, -0.02, hz + 0.07), "hair"),
    ((hw + 0.006, 0.03, 0.04), (0, fy - 0.004, hz + hh / 2 - 0.02), "hair"),         # faixa de cabelo sob a aba
    ((0.12, 0.03, 0.035), (-0.09, fy - 0.004, hz + hh / 2 - 0.05), "hair"),
    ((0.07, 0.03, 0.028), (0.08, fy - 0.004, hz + hh / 2 - 0.048), "hair"),
], bevel=0.016)
face = Part("Face", ["white", "iris", "pupil", "brow", "mouth", "tongue", "blush"])
for sx in (1, -1):
    ex, ez = sx * 0.075, hz + 0.02
    face.box((0.062, 0.008, 0.056), (ex, fy - 0.004, ez))
    face.box((0.040, 0.010, 0.046), (ex - sx * 0.008, fy - 0.006, ez - 0.004), "iris")
    face.box((0.020, 0.012, 0.024), (ex - sx * 0.008, fy - 0.008, ez - 0.008), "pupil")
    face.box((0.012, 0.014, 0.012), (ex - sx * 0.016, fy - 0.009, ez + 0.010), "white")
    face.box((0.07, 0.012, 0.016), (ex, fy - 0.006, ez + 0.058), "brow")
    face.box((0.045, 0.006, 0.022), (sx * 0.125, fy - 0.003, hz - 0.045), "blush")
for x, z in ((-0.05, -0.068), (-0.035, -0.082), (0.035, -0.082), (0.05, -0.068)):
    face.box((0.018, 0.010, 0.016), (x, fy - 0.005, hz + z), "mouth")
face.box((0.052, 0.010, 0.026), (0, fy - 0.005, hz - 0.090), "mouth")
face.box((0.030, 0.011, 0.010), (0, fy - 0.006, hz - 0.097), "tongue")
face.build(bevel=0.003, segments=2)
# --- capacete laranja marcante -------------------------------------------------
top = hz + hh / 2
P("Helmet", ["helmet", "gold", "white"], [
    ((hw + 0.04, hd + 0.04, 0.10), (0, 0.005, top + 0.03)),
    ((hw - 0.04, hd - 0.03, 0.05), (0, 0.005, top + 0.095)),
    ((0.06, hd + 0.03, 0.05), (0, 0.005, top + 0.10)),                           # nervura central
    ((hw + 0.09, hd + 0.08, 0.026), (0, -0.01, top - 0.005)),                    # aba
    ((0.26, 0.09, 0.024), (0, fy - 0.07, top - 0.004)),                          # pala
    ((0.07, 0.014, 0.06), (0, fy - 0.022, top + 0.045), "gold"),                 # emblema
    ((0.04, 0.016, 0.03), (0, fy - 0.026, top + 0.045), "white"),
], bevel=0.018)
# --- base colecionavel ----------------------------------------------------------
P("Base", ["base", "accent"], [
    ((0.62, 0.50, Z0), (0, 0.0, Z0 / 2)),
    ((0.60, 0.006, 0.010), (0, -0.252, Z0 * 0.55), "accent"),
], bevel=0.012)

# --- estudio -----------------------------------------------------------------------
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device, sc.cycles.samples, sc.cycles.use_denoising = "CPU", SPP, False
sc.cycles.blur_glossy, sc.cycles.sample_clamp_indirect = 1.0, 3.0
sc.render.resolution_x = sc.render.resolution_y = 1000
sc.view_settings.view_transform, sc.view_settings.look = "AgX", "AgX - Medium High Contrast"
w = bpy.data.worlds.new("W")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.75, 0.77, 0.80, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.28
sc.world = w
bpy.ops.mesh.primitive_plane_add(size=10)
fm = bpy.data.materials.new("Floor")
fm.use_nodes = True
fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.75, 0.76, 0.78, 1)
bpy.context.active_object.data.materials.append(fm)
target = Vector((0, 0, 0.55))
for n, loc, e, s in (("Key", (-1.2, -1.6, 2.0), 110, 1.6), ("Fill", (1.6, -1.0, 1.0), 30, 2.0), ("Rim", (0.5, 1.6, 1.8), 120, 1.0)):
    d = bpy.data.lights.new(n, "AREA")
    d.energy, d.size = e, s
    o = bpy.data.objects.new(n, d)
    sc.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (target - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
cd = bpy.data.cameras.new("Cam")
cd.lens = 60
cam = bpy.data.objects.new("Cam", cd)
sc.collection.objects.link(cam)
cam.location = (0.95, -2.3, 1.05)
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
sc.camera = cam
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("RENDERED", OUT)
