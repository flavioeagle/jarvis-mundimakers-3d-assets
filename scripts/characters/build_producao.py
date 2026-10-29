"""Producao: tecnico de IA simpatico, capacete laranja, uniforme industrial e impressora CC2.

Uso: blender -b --factory-startup --python-exit-code 1 --python scripts/characters/build_producao.py -- <raw.glb>
Reutiliza o rig/gerador de scripts/lib/chibi.py e o asset scripts/printers/build_elegoo_cc2.py.
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
sys.path.insert(0, os.path.join(HERE, "..", "printers"))
import build_elegoo_cc2 as CC2  # noqa: E402
import chibi as C  # noqa: E402
from bparts import MAT, Part, empty, material, set_parent  # noqa: E402

OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "build/producao_v1.glb"

CFG = {"build": 1.12, "hip": 1.08, "arm": 1.12, "chest_d": 1.12, "jaw": 0.16, "eye_w": 0.95, "eye_h": 1.12,
       "brow_w": 0.0058, "brow_z": 0.842, "smile": 0.013, "mouth_w": 0.030, "eye_z": 0.782}


def materials():
    return {
        "skin": material("Skin_Producao", (0.46, 0.26, 0.16), rough=0.5),
        "sclera": material("Eye_Sclera", (0.88, 0.88, 0.86), rough=0.15, coat=1.0),
        "iris": material("Eye_Iris_Hazel", (0.14, 0.09, 0.03), rough=0.2, coat=1.0),
        "pupil": material("Eye_Pupil", (0.004, 0.003, 0.003), rough=0.1, coat=1.0),
        "glint": material("Eye_Glint", (1, 1, 1), emission=(1, 1, 1), strength=2.0),
        "lash": material("Lash_Black", (0.010, 0.007, 0.006), rough=0.5),
        "brow": material("Brow_Dark", (0.030, 0.018, 0.010), rough=0.6),
        "lip": material("Mouth_Line", (0.14, 0.04, 0.03), rough=0.4),
        "blush": material("Blush", (0.62, 0.27, 0.20), rough=0.6),
        "hair": material("Hair_Brown", (0.035, 0.020, 0.012), rough=0.4, coat=0.1),
        "coverall": material("Coverall_Navy", (0.016, 0.030, 0.075), rough=0.7),
        "vest": material("HiVis_Orange", (0.85, 0.20, 0.01), rough=0.6),
        "reflect": material("Reflective_Silver", (0.75, 0.76, 0.78), metallic=0.6, rough=0.25),
        "helmet": material("Helmet_Orange", (0.80, 0.16, 0.008), rough=0.30, coat=0.4),
        "glove": material("Glove_Gray", (0.06, 0.06, 0.065), rough=0.7),
        "boot": material("Boot_Leather", (0.11, 0.05, 0.02), rough=0.45, coat=0.3),
        "sole": material("Sole_Black", (0.02, 0.02, 0.02), rough=0.8),
        "steel": material("Tool_Steel", (0.70, 0.71, 0.73), metallic=1.0, rough=0.25),
        "belt": material("Belt_Black", (0.015, 0.015, 0.015), rough=0.5),
        "wood": material("Bench_Wood", (0.38, 0.22, 0.10), rough=0.55),
        "metal": material("Bench_Metal", (0.10, 0.11, 0.12), metallic=0.9, rough=0.4),
        "red": material("Toolbox_Red", (0.55, 0.03, 0.02), rough=0.35, coat=0.6),
    }


def region(bone):
    if bone.startswith("hand"):
        return "glove"
    if bone.startswith("foot"):
        return "boot"
    if bone in ("neck", "head"):
        return "skin"
    return "coverall"


def extra(c, bone):
    if c.z < 0.012:
        return "sole"
    if bone.startswith("shin") and c.z < 0.115:
        return "boot"
    if bone == "chest" and c.z > 0.635:
        return "skin"
    if bone.startswith("forearm") and c.z < 0.372:
        return "glove"
    return None


def build_character():
    body = C.build_body("Producao_Body", CFG)
    C.assign_regions(body, region, ["skin", "coverall", "glove", "boot", "sole"], extra)
    segs = C.bone_segments()
    vest = C.shell(
        body, "Producao_Vest",
        keep=lambda c: C.dominant_bone(c, segs) in ("hips", "spine", "chest") and 0.445 < c.z < 0.635,
        cut=lambda c: abs(c.x) < 0.012 and c.y < 0,
        offset=0.006, thickness=0.006, mat="vest")
    bsurf = C.Surface([vest])
    bands = []
    for z in (0.505, 0.560):                                  # faixas refletivas
        bands.append(C.tube(f"band{z}", C.ring(bsurf, z, 0.0015), 0.0055, 0.0055, "reflect", res=3, bevel_res=1))
    for sx in (1, -1):                                        # alcas verticais do colete
        pts = []
        for z in (0.46, 0.52, 0.58, 0.62):
            try:
                pts.append(bsurf.front(sx * 0.045, z, 0.0015)[0])
            except RuntimeError:
                pass
        bands.append(C.tube(f"strap{sx}", pts, 0.0055, 0.0055, "reflect", res=3, bevel_res=1))
    pocket = Part("pocket", ["vest", "reflect"])
    p, n = bsurf.front(-0.045, 0.585, 0.002)
    pocket.box((0.034, 0.008, 0.030), (0, 0, 0))
    pocket.box((0.036, 0.009, 0.006), (0, 0, 0.012), "reflect")
    bands.append(C.place(pocket.build(bevel=0.002, segments=2, smooth=True), p, n))
    vest_detail = C.join("Producao_Vest_Details", bands)

    surf = C.Surface([body])
    belt_parts = [C.tube("belt", C.ring(surf, 0.44, 0.004), 0.009, 0.009, "belt", res=3)]
    pouch = Part("Belt_Pouches", ["belt", "steel"])
    for sx in (1, -1):
        pouch.box((0.040, 0.030, 0.045), (sx * 0.085, -0.035, 0.425))
    pouch.box((0.022, 0.012, 0.016), (0, -0.078, 0.440), "steel")       # fivela
    belt_parts.append(pouch.build(bevel=0.004, segments=2, smooth=True))
    belt = C.join("Producao_Belt", belt_parts)

    head = C.build_head(CFG)
    face, _ = C.build_face(CFG, head)
    hsurf = C.Surface([head])
    stache = C.arc(hsurf, -0.028, 0.028, lambda t, x: 0.731 + 0.006 * (abs(x) / 0.028) - 0.004 * math.sin(math.pi * t), n=7, push=0.003)
    mustache = C.tube("Mustache", stache, 0.0035, 0.0035, "hair", res=5, swell=0.004)
    cap = C.build_hair_cap(CFG, opening=0.30)
    side = []
    for sx in (1, -1):                                       # costeletas
        pts = [hsurf.front(sx * x, z, 0.004)[0] for x, z in ((0.128, 0.815), (0.132, 0.785), (0.130, 0.758))]
        side.append(C.tube(f"burn{sx}", pts, 0.006, 0.004, "hair", res=4))
    hair = C.join("Producao_Hair", [cap, mustache, *side])

    hb = C.bmesh.new()                                      # capacete: cupula + aba + nervura
    C.bmesh.ops.create_uvsphere(hb, u_segments=40, v_segments=20, radius=C.HEAD_R * 1.20)
    kill = [f for f in hb.faces if f.calc_center_median().z < 0.02]
    C.bmesh.ops.delete(hb, geom=kill, context="FACES")
    for v in hb.verts:
        v.co.y *= 1.02
        v.co += C.HEAD_C + C.Vector((0, 0.008, 0.040))
    helmet = C.mesh_from_bm("Helmet_Dome", hb, ["helmet"])
    sol = helmet.modifiers.new("Solid", "SOLIDIFY")
    sol.thickness, sol.offset = 0.008, 1.0
    helmet = C.bake(helmet, "Helmet_Dome")
    helmet = C.smooth(helmet, subsurf=1)
    brim = Part("Helmet_Brim", ["helmet", "reflect"])
    brim.cyl(C.HEAD_R * 1.27, 0.008, tuple(C.HEAD_C + C.Vector((0, -0.012, 0.045))), seg=48)
    brim.box((0.10, 0.06, 0.008), tuple(C.HEAD_C + C.Vector((0, -0.18, 0.041))))           # pala
    brim_ob = brim.build(bevel=0.003, segments=2, smooth=True)
    ridge = [C.HEAD_C + C.Vector((0, 0.008 + 0.19 * math.sin(a), 0.040 + 0.195 * math.cos(a)))
             for a in [math.radians(v) for v in range(-80, 81, 10)]]
    rid = C.tube("Helmet_Ridge", ridge, 0.011, 0.011, "helmet", res=4)
    badge = Part("Helmet_Badge", ["gold"])
    badge.cyl(0.022, 0.004, tuple(C.HEAD_C + C.Vector((0, -0.176, 0.120))), axis="Y", seg=32,
              rot=(-0.55, 0, 0))
    helmet_ob = C.join("Producao_Helmet", [helmet, brim_ob, rid, badge.build(smooth=True)])

    wrench = Part("Producao_Wrench", ["steel", "red"])
    hand = C.Vector((-0.157, -0.022, 0.305))                 # punho na palma direita
    wrench.box((0.020, 0.022, 0.070), tuple(hand), "red")
    wrench.box((0.014, 0.010, 0.110), tuple(hand + C.Vector((0, 0, -0.085))), "steel")
    wrench.cyl(0.028, 0.012, tuple(hand + C.Vector((0, 0, -0.150))), axis="X", seg=32)
    wrench.box((0.014, 0.024, 0.026), tuple(hand + C.Vector((0, -0.018, -0.165))), "steel")
    wrench_ob = wrench.build(bevel=0.0015, segments=2, smooth=True)

    arm = C.build_armature("Producao")
    for o in (body, vest, belt):
        C.skin_to(o, arm)
    C.attach(vest_detail, arm, "chest")
    for o in (head, hair, helmet_ob, face["nose"], face["blush"], face["ears"]):
        C.attach(o, arm, "head")
    for s in ("L", "R"):
        C.attach(face[f"eye.{s}"], arm, f"eye.{s}")
        C.attach(face[f"brow.{s}"], arm, f"brow.{s}")
    C.attach(face["lash"][0], arm, "eye.L")
    C.attach(face["lash"][1], arm, "eye.R")
    for m in face["mouth"]:
        C.attach(m, arm, "mouth")
    C.attach(wrench_ob, arm, "hand.R")
    return arm


def build_station(printer_root):
    root = empty("Producao_Station", (0, 0, 0), role="workstation", owner="Producao")
    bx, by, top = 0.50, -0.05, 0.40
    b = Part("Station_Workbench", ["wood", "metal"])
    b.box((0.62, 0.50, 0.030), (bx, by, top - 0.015))
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.box((0.035, 0.035, top - 0.03), (bx + sx * 0.27, by + sy * 0.21, (top - 0.03) / 2), "metal")
    b.box((0.58, 0.46, 0.012), (bx, by, 0.09), "metal")
    b.build(root, bevel=0.003, segments=2, smooth=True)
    tb = Part("Station_Toolbox", ["red", "metal", "steel"])
    tb.box((0.22, 0.12, 0.10), (bx - 0.02, by + 0.02, 0.09 + 0.006 + 0.05))
    tb.box((0.10, 0.012, 0.014), (bx - 0.02, by + 0.02, 0.21), "steel")
    tb.box((0.222, 0.122, 0.006), (bx - 0.02, by + 0.02, 0.17), "metal")
    tb.build(root, bevel=0.004, segments=2, smooth=True)
    printer_root.location = (bx + 0.05, by + 0.02, top)
    bpy.context.view_layer.update()
    set_parent(printer_root, root)
    return root


def animations(arm):
    blink = [(1, (0, 0, 0), None, (1, 1, 1)), (52, (0, 0, 0), None, (1, 1, 1)),
             (55, (0, 0, 0), None, (1, 1, 0.08)), (58, (0, 0, 0), None, (1, 1, 1))]
    C.make_action(arm, "Idle", 72, {
        "hips": [(1, (0, 0, -1.5)), (36, (0, 0, 1.5)), (72, (0, 0, -1.5))],
        "chest": [(1, (0, 0, 0)), (36, (2.5, 0, 0)), (72, (0, 0, 0))],
        "head": [(1, (0, 2, 0)), (36, (1, -3, -1)), (72, (0, 2, 0))],
        "upperarm.L": [(1, (0, 0, -7)), (72, (0, 0, -7))],
        "upperarm.R": [(1, (-8, 0, 7)), (72, (-8, 0, 7))],
        "forearm.R": [(1, (-25, 0, 0)), (72, (-25, 0, 0))],
        "eye.L": blink, "eye.R": blink,
    })
    turn = [(f, (-70 + 22 * math.sin(f / 48 * 4 * math.pi), 0, -10)) for f in range(1, 49, 4)]
    C.make_action(arm, "Working", 48, {
        "spine": [(1, (5, 22, 0)), (48, (5, 22, 0))],
        "head": [(1, (10, 18, 0)), (24, (12, 22, 0)), (48, (10, 18, 0))],
        "upperarm.L": [(1, (-55, 0, -20)), (48, (-55, 0, -20))],
        "forearm.L": [(1, (-35, 0, 0)), (24, (-40, 0, 0)), (48, (-35, 0, 0))],
        "upperarm.R": [(1, (-45, 0, 0)), (48, (-45, 0, 0))],
        "forearm.R": turn,
        "eye.L": blink[:1] + [(30, (0, 0, 0), None, (1, 1, 1)), (33, (0, 0, 0), None, (1, 1, 0.08)), (36, (0, 0, 0), None, (1, 1, 1))],
        "eye.R": blink[:1] + [(30, (0, 0, 0), None, (1, 1, 1)), (33, (0, 0, 0), None, (1, 1, 0.08)), (36, (0, 0, 0), None, (1, 1, 1))],
    })
    wave = [(f, (-15 + 12 * math.sin(f / 72 * 4 * math.pi), 0, -95)) for f in range(1, 73, 6)]
    tap = [(f, (10 if (f // 12) % 2 else 0, 0, 0)) for f in range(1, 73, 12)]
    C.make_action(arm, "AwaitingApproval", 72, {
        "head": [(1, (-4, 0, -7)), (36, (-4, 0, -10)), (72, (-4, 0, -7))],
        "upperarm.L": [(1, (-25, 0, -55)), (72, (-25, 0, -55))],
        "forearm.L": wave,
        "upperarm.R": [(1, (-8, 0, 8)), (72, (-8, 0, 8))],
        "forearm.R": [(1, (-30, 0, 0)), (72, (-30, 0, 0))],
        "foot.R": tap,
        "brow.L": [(1, (0, 0, 0), (0, 0, 0.006)), (72, (0, 0, 0), (0, 0, 0.006))],
        "brow.R": [(1, (0, 0, 0), (0, 0, 0.006)), (72, (0, 0, 0), (0, 0, 0.006))],
    })
    C.make_action(arm, "Done", 48, {
        "root": [(1, (0, 0, 0), (0, 0, 0)), (12, (0, 0, 0), (0, 0.04, 0)), (24, (0, 0, 0), (0, 0, 0)), (48, (0, 0, 0), (0, 0, 0))],
        "upperarm.R": [(1, (0, 0, 15)), (12, (0, 0, 150)), (40, (0, 0, 150)), (48, (0, 0, 15))],
        "forearm.R": [(1, (0, 0, 0)), (12, (0, 0, 25)), (48, (0, 0, 0))],
        "upperarm.L": [(1, (0, 0, -8)), (12, (-60, 0, -10)), (40, (-60, 0, -10)), (48, (0, 0, -8))],
        "forearm.L": [(1, (0, 0, 0)), (12, (-70, 0, 0)), (40, (-70, 0, 0)), (48, (0, 0, 0))],
        "head": [(1, (0, 0, 0)), (12, (-8, 0, 0)), (40, (-8, 0, 0)), (48, (0, 0, 0))],
        "mouth": [(1, (0, 0, 0), None, (1, 1, 1)), (12, (0, 0, 0), None, (1.3, 1, 2.2)), (40, (0, 0, 0), None, (1.3, 1, 2.2)), (48, (0, 0, 0), None, (1, 1, 1))],
        "eye.L": [(1, (0, 0, 0), None, (1, 1, 1)), (12, (0, 0, 0), None, (1.05, 1, 0.55)), (40, (0, 0, 0), None, (1.05, 1, 0.55)), (48, (0, 0, 0), None, (1, 1, 1))],
        "eye.R": [(1, (0, 0, 0), None, (1, 1, 1)), (12, (0, 0, 0), None, (1.05, 1, 0.55)), (40, (0, 0, 0), None, (1.05, 1, 0.55)), (48, (0, 0, 0), None, (1, 1, 1))],
    })


if __name__ == "__main__":
    printer = CC2.build()                     # reseta a cena e cria CC2_Root (pivos proprios)
    keep = dict(MAT)
    MAT.update(materials())
    MAT["gold"] = keep["gold"]                # reaproveita Gold_Accent da impressora
    bpy.context.scene.render.fps = 24
    arm = build_character()
    arm["role"], arm["animations"] = "ai_employee_producao", ["Idle", "Working", "AwaitingApproval", "Done"]
    station = build_station(printer)
    animations(arm)
    os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
    C.export_glb(OUT, [arm, station])
    print(f"EXPORTED {OUT}")
