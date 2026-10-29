"""Muse: funcionaria de IA criativa/tecnologica, com estacao de monitores.

Uso: blender -b --factory-startup --python-exit-code 1 --python scripts/characters/build_muse.py -- <raw.glb>
"""
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import chibi as C  # noqa: E402
from bparts import MAT, Part, empty, material  # noqa: E402

OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "build/muse_v1.glb"

CFG = {"build": 0.92, "hip": 1.0, "arm": 0.9, "chest_d": 1.05, "jaw": 0.26, "eye_h": 1.3,
       "lash_flick": True, "brow_w": 0.0036, "lips": True, "smile": 0.008, "mouth_w": 0.022}


def materials():
    return {
        "skin": material("Skin_Muse", (0.60, 0.36, 0.26), rough=0.5),
        "sclera": material("Eye_Sclera", (0.88, 0.88, 0.86), rough=0.15, coat=1.0),
        "iris": material("Eye_Iris_Brown", (0.10, 0.045, 0.02), rough=0.2, coat=1.0),
        "pupil": material("Eye_Pupil", (0.004, 0.003, 0.003), rough=0.1, coat=1.0),
        "glint": material("Eye_Glint", (1, 1, 1), emission=(1, 1, 1), strength=2.0),
        "lash": material("Lash_Black", (0.008, 0.006, 0.006), rough=0.5),
        "brow": material("Brow_Dark", (0.025, 0.014, 0.010), rough=0.6),
        "lip": material("Mouth_Line", (0.18, 0.05, 0.05), rough=0.4),
        "lipcolor": material("Lip_Rose", (0.50, 0.18, 0.18), rough=0.35, coat=0.4),
        "blush": material("Blush", (0.80, 0.38, 0.33), rough=0.6),
        "hair": material("Hair_Dark", (0.012, 0.008, 0.007), rough=0.32, coat=0.15),
        "top": material("Top_Lilac", (0.30, 0.17, 0.52), rough=0.6),
        "blazer": material("Blazer_Charcoal", (0.018, 0.019, 0.026), rough=0.55),
        "pants": material("Pants_Navy", (0.012, 0.016, 0.040), rough=0.65),
        "shoe": material("Sneaker_White", (0.80, 0.80, 0.78), rough=0.45),
        "sole": material("Sole_Gray", (0.20, 0.20, 0.21), rough=0.7),
        "gold": material("Gold_Accent", (0.80, 0.62, 0.33), metallic=1.0, rough=0.30),
        "white": material("Headset_White", (0.82, 0.82, 0.84), rough=0.3, coat=0.5),
        "dark": material("Desk_Dark", (0.030, 0.032, 0.036), metallic=0.8, rough=0.35),
        "desk": material("Desk_Top_White", (0.75, 0.74, 0.72), rough=0.3, coat=0.6),
        "screen": material("Screen_UI", (0.01, 0.02, 0.05), rough=0.2,
                           emission=(0.06, 0.12, 0.30), strength=1.0),
        "ui_cyan": material("UI_Cyan", (0, 0, 0), emission=(0.20, 0.85, 1.0), strength=2.0),
        "ui_gold": material("UI_Gold", (0, 0, 0), emission=(1.0, 0.70, 0.30), strength=2.0),
        "ui_pink": material("UI_Magenta", (0, 0, 0), emission=(0.90, 0.30, 0.80), strength=2.0),
        "key": material("Keycap", (0.06, 0.06, 0.07), rough=0.5),
        "ceramic": material("Mug_Ceramic", (0.85, 0.83, 0.78), rough=0.25, coat=0.6),
        "leaf": material("Plant_Leaf", (0.08, 0.30, 0.10), rough=0.5),
        "pot": material("Pot_Terracotta", (0.55, 0.22, 0.12), rough=0.7),
    }


def region(bone):
    if bone.startswith(("thigh", "shin", "hips")):
        return "pants"
    if bone.startswith("foot"):
        return "shoe"
    if bone in ("neck", "head") or bone.startswith("hand"):
        return "skin"
    return "top"


def extra(c, bone):
    if c.z < 0.012:
        return "sole"
    if bone.startswith("shin") and c.z < 0.085:
        return "shoe"
    if bone.startswith("forearm") and c.z < 0.375:
        return "skin"
    if bone == "chest" and c.z > 0.635:
        return "skin"
    return None


def build_character():
    body = C.build_body("Muse_Body", CFG)
    C.assign_regions(body, region, ["skin", "top", "pants", "shoe", "sole"], extra)

    torso = ("hips", "spine", "chest", "upperarm", "forearm")
    segs = C.bone_segments()
    jacket = C.shell(
        body, "Muse_Blazer",
        keep=lambda c: C.dominant_bone(c, segs).startswith(torso) and 0.43 < c.z < 0.645
        and not (C.dominant_bone(c, segs).startswith("forearm") and c.z < 0.385),
        cut=lambda c: abs(c.x) < 0.028 and c.y < 0 and c.z > 0.41,
        offset=0.005, thickness=0.006, mat="blazer")

    head = C.build_head(CFG)
    face, surf = C.build_face(CFG, head)
    cap = C.build_hair_cap(CFG, opening=0.40)

    bun_c = C.HEAD_C + C.Vector((0, 0.150, 0.095))
    starts = [(math.radians(56 + 10 * abs(math.sin(p))), p)
              for p in [math.radians(a) for a in range(-115, 116, 7)]]
    strands = C.hair_strands(cap, lambda p0: (math.radians(52), math.pi if p0 >= 0 else -math.pi), starts)
    bun = Part("Hair_Bun", ["hair", "gold"])
    bun.sphere(0.064, tuple(bun_c), (1.0, 0.85, 0.95), seg=24, rings=12)
    bun.cyl(0.040, 0.010, tuple(bun_c + C.Vector((0, -0.045, -0.006))), axis="Y", mat="gold", seg=32)
    bun_ob = bun.build(smooth=True)
    swirl = []
    for k in range(5):                                         # mechas em espiral no coque
        pts = []
        for i in range(10):
            a = i * 0.62 + k * 1.25
            r = 0.060 - i * 0.0045
            pts.append(bun_c + C.Vector((r * math.cos(a), 0.035 + 0.006 * i * 0.3 + 0.012, r * 0.92 * math.sin(a))))
        swirl.append(C.tube(f"swirl{k}", pts, 0.003, 0.002, "hair", res=3, bevel_res=2, swell=0.007))
    # franja lateral e mechas que emolduram o rosto
    head_surf = C.Surface([cap, head])
    fringe = []
    for k in range(7):                                         # franja lateral varrida
        t0, p0 = 0.30 + 0.03 * k, -0.62 + 0.05 * k
        t1, p1 = 1.10 - 0.015 * k, 0.80 + 0.06 * k
        pts = [head_surf.radial(t0 + (t1 - t0) * u, p0 + (p1 - p0) * u, 0.004 + 0.004 * math.sin(math.pi * u))[0]
               for u in [i / 8 for i in range(9)]]
        fringe.append(C.tube(f"fringe{k}", pts, 0.002, 0.0015, "hair", res=4, bevel_res=2, swell=0.0065))
    for sx in (1, -1):
        p = [C.HEAD_C + C.Vector(v) for v in ((sx * 0.120, -0.085, 0.075), (sx * 0.140, -0.088, 0.015),
                                             (sx * 0.135, -0.082, -0.045), (sx * 0.118, -0.090, -0.085))]
        fringe.append(C.tube(f"frame{sx}", p, 0.003, 0.0015, "hair", res=5, swell=0.005))
    hair = C.join("Muse_Hair", [cap, strands, bun_ob, *swirl, *fringe])
    hair.data.polygons.foreach_set("use_smooth", [True] * len(hair.data.polygons))

    # headset
    band = [C.HEAD_C + C.Vector((0.172 * math.sin(a), 0.01, 0.197 * math.cos(a)))
            for a in [math.radians(v) for v in range(-90, 91, 15)]]
    hs = [C.tube("Headset_Band", band, 0.0065, 0.0065, "white", res=6)]
    cups = Part("Headset_Cups", ["white", "gold", "dark"])
    for sx in (1, -1):
        cups.cyl(0.034, 0.024, (sx * 0.170, 0.012, C.HEAD_C.z), axis="X", seg=32)
        cups.cyl(0.036, 0.004, (sx * 0.183, 0.012, C.HEAD_C.z), axis="X", mat="gold", seg=32)
        cups.cyl(0.022, 0.003, (sx * 0.186, 0.012, C.HEAD_C.z), axis="X", mat="white", seg=32)
    hs.append(cups.build(smooth=True))
    mic = [C.HEAD_C + C.Vector(v) for v in ((0.175, -0.01, -0.02), (0.165, -0.08, -0.07), (0.11, -0.14, -0.095), (0.055, -0.155, -0.10))]
    hs.append(C.tube("Mic_Boom", mic, 0.0035, 0.0030, "dark"))
    tip = Part("Mic_Tip", ["dark"])
    tip.sphere(0.009, tuple(mic[-1]), seg=16, rings=8)
    hs.append(tip.build(smooth=True))
    headset = C.join("Muse_Headset", hs)

    belt_c = C.Vector((0, 0, 0.452))
    bsurf = C.Surface([body])
    ring = [bsurf.radial(math.pi / 2, math.radians(a), 0.002, center=belt_c)[0] for a in range(0, 361, 20)]
    belt = C.tube("Muse_Belt", ring, 0.006, 0.006, "dark", res=4)
    pin = Part("Muse_Pin", ["gold"])
    pin.sphere(0.008, (0.045, -0.066, 0.585), (1, 0.4, 1), seg=16, rings=8)
    pin_ob = pin.build(smooth=True)

    arm = C.build_armature("Muse")
    for o in (body, jacket, belt):
        C.skin_to(o, arm)
    C.attach(head, arm, "head")
    C.attach(hair, arm, "head")
    C.attach(headset, arm, "head")
    C.attach(face["nose"], arm, "head")
    C.attach(face["blush"], arm, "head")
    C.attach(face["ears"], arm, "head")
    C.attach(pin_ob, arm, "chest")
    for s in ("L", "R"):
        C.attach(face[f"eye.{s}"], arm, f"eye.{s}")
        C.attach(face[f"brow.{s}"], arm, f"brow.{s}")
    C.attach(face["lash"][0], arm, "eye.L")
    C.attach(face["lash"][1], arm, "eye.R")
    for m in face["mouth"]:
        C.attach(m, arm, "mouth")
    return arm


def build_station():
    root = empty("Muse_Station", (0, 0, 0), role="workstation", owner="Muse")
    d = Part("Station_Desk", ["desk", "dark", "gold"])
    top_z, y0, y1, w = 0.40, -0.17, -0.47, 0.84
    d.box((w, y0 - y1, 0.022), (0, (y0 + y1) / 2, top_z - 0.011))
    d.box((w, 0.004, 0.006), (0, y0 - 0.002 + 0.001, top_z - 0.012), "gold")
    for sx in (-1, 1):
        d.box((0.03, 0.26, 0.012), (sx * 0.36, (y0 + y1) / 2, 0.006), "dark")
        d.box((0.035, 0.035, top_z - 0.034), (sx * 0.36, (y0 + y1) / 2, (top_z - 0.022) / 2 + 0.006), "dark")
    d.build(root, bevel=0.004, segments=3, smooth=True)

    mon = Part("Station_Monitors", ["dark", "screen", "ui_cyan", "ui_gold", "ui_pink"])
    mon_y, mon_z = -0.40, top_z + 0.13
    for i, ang in enumerate((-0.55, 0.0, 0.55)):
        cx = math.sin(ang) * 0.30
        cy = mon_y + (1 - math.cos(ang)) * 0.30
        rot = (0, 0, -ang)
        R = C.Euler(rot).to_matrix()

        def at(x, y, z):
            v = R @ C.Vector((x, y, z))
            return (cx + v.x, cy + v.y, mon_z + v.z)
        mon.box((0.27, 0.014, 0.17), at(0, 0, 0), "dark", rot)
        mon.box((0.255, 0.002, 0.155), at(0, 0.0075, 0), "screen", rot)
        for j, (ux, uz, uw, uh, m) in enumerate([(-0.07, 0.05, 0.09, 0.012, "ui_cyan"), (-0.07, 0.03, 0.06, 0.006, "ui_gold"),
                                                 (0.05, 0.02, 0.10, 0.07, "ui_pink" if i == 1 else "ui_cyan"),
                                                 (-0.07, -0.02, 0.09, 0.04, "ui_gold" if i != 1 else "ui_cyan"),
                                                 (0.0, -0.06, 0.22, 0.006, "ui_cyan")]):
            mon.box((uw, 0.001, uh), at(ux, 0.0090, uz), m, rot)
        mon.box((0.02, 0.02, 0.11), at(0, -0.02, -0.11), "dark", rot)
        mon.box((0.10, 0.07, 0.008), at(0, -0.02, -0.126), "dark", rot)
    mon.build(root, bevel=0.002, segments=2)

    kb = Part("Station_Keyboard", ["dark", "key", "gold"])
    kb.box((0.26, 0.085, 0.012), (0, -0.235, top_z + 0.006))
    for r in range(4):
        for c in range(14):
            kb.box((0.0145, 0.0145, 0.006), (-0.117 + c * 0.018, -0.208 - r * 0.018, top_z + 0.014), "key")
    kb.box((0.26, 0.002, 0.003), (0, -0.193, top_z + 0.0135), "gold")
    kb.sphere(0.018, (0.20, -0.235, top_z + 0.006), (0.7, 1.0, 0.45), "dark", seg=20, rings=10)
    kb.build(root, bevel=0.0015, segments=2, smooth=True)

    props = Part("Station_Props", ["ceramic", "gold", "pot", "leaf"])
    props.cyl(0.024, 0.07, (-0.30, -0.24, top_z + 0.035), seg=28)
    props.cyl(0.0245, 0.006, (-0.30, -0.24, top_z + 0.055), mat="gold", seg=28)
    props.cyl(0.032, 0.05, (0.31, -0.27, top_z + 0.025), mat="pot", r2=0.025, seg=24)
    for k in range(7):
        a = k * 2 * math.pi / 7
        props.sphere(0.018, (0.31 + 0.017 * math.cos(a), -0.27 + 0.017 * math.sin(a), top_z + 0.065 + 0.008 * (k % 2)),
                     (0.6, 0.6, 1.4), "leaf", rot=(0.5 * math.sin(a), -0.5 * math.cos(a), 0), seg=12, rings=8)
    props.build(root, bevel=0.002, segments=2, smooth=True)
    return root


def animations(arm):
    blink = [(1, (0, 0, 0), None, (1, 1, 1)), (40, (0, 0, 0), None, (1, 1, 1)),
             (43, (0, 0, 0), None, (1, 1, 0.08)), (46, (0, 0, 0), None, (1, 1, 1))]
    C.make_action(arm, "Idle", 72, {
        "chest": [(1, (0, 0, 0)), (36, (2.5, 0, 0)), (72, (0, 0, 0))],
        "head": [(1, (0, -3, 0)), (36, (2, 3, 1.5)), (72, (0, -3, 0))],
        "upperarm.L": [(1, (0, 0, -6)), (36, (0, 0, -8)), (72, (0, 0, -6))],
        "upperarm.R": [(1, (0, 0, 6)), (36, (0, 0, 8)), (72, (0, 0, 6))],
        "eye.L": blink, "eye.R": blink,
    })
    type_l = [(f, (-62 + (7 if (f // 6) % 2 else 0), 0, 6)) for f in range(1, 49, 6)]
    type_r = [(f, (-62 + (0 if (f // 6) % 2 else 7), 0, -6)) for f in range(1, 49, 6)]
    C.make_action(arm, "Working", 48, {
        "spine": [(1, (6, 0, 0)), (48, (6, 0, 0))],
        "head": [(1, (14, 0, 0)), (24, (12, 6, 0)), (48, (14, 0, 0))],
        "upperarm.L": [(1, (-48, 0, 8)), (48, (-48, 0, 8))],
        "upperarm.R": [(1, (-48, 0, -8)), (48, (-48, 0, -8))],
        "forearm.L": type_l, "forearm.R": type_r,
        "eye.L": [(1, (0, 0, 0), None, (1, 1, 1)), (20, (0, 0, 0), None, (1, 1, 1)), (23, (0, 0, 0), None, (1, 1, 0.08)), (26, (0, 0, 0), None, (1, 1, 1))],
        "eye.R": [(1, (0, 0, 0), None, (1, 1, 1)), (20, (0, 0, 0), None, (1, 1, 1)), (23, (0, 0, 0), None, (1, 1, 0.08)), (26, (0, 0, 0), None, (1, 1, 1))],
    })
    wave = [(f, (-15 + 12 * math.sin(f / 72 * 4 * math.pi), 0, 95)) for f in range(1, 73, 6)]
    C.make_action(arm, "AwaitingApproval", 72, {
        "spine": [(1, (0, 0, 3)), (72, (0, 0, 3))],
        "head": [(1, (-4, 0, 8)), (36, (-4, 0, 11)), (72, (-4, 0, 8))],
        "upperarm.R": [(1, (-25, 0, 55)), (72, (-25, 0, 55))],
        "forearm.R": wave,
        "upperarm.L": [(1, (-10, 0, -8)), (72, (-10, 0, -8))],
        "forearm.L": [(1, (-60, 0, 0)), (72, (-60, 0, 0))],
        "brow.L": [(1, (0, 0, 0), (0, 0, 0.006)), (72, (0, 0, 0), (0, 0, 0.006))],
        "brow.R": [(1, (0, 0, 0), (0, 0, 0.006)), (72, (0, 0, 0), (0, 0, 0.006))],
    })
    C.make_action(arm, "Done", 48, {
        "root": [(1, (0, 0, 0), (0, 0, 0)), (12, (0, 0, 0), (0, 0.045, 0)), (24, (0, 0, 0), (0, 0, 0)), (48, (0, 0, 0), (0, 0, 0))],
        "upperarm.L": [(1, (0, 0, -20)), (12, (0, 0, -150)), (40, (0, 0, -150)), (48, (0, 0, -20))],
        "upperarm.R": [(1, (0, 0, 20)), (12, (0, 0, 150)), (40, (0, 0, 150)), (48, (0, 0, 20))],
        "forearm.L": [(1, (0, 0, 0)), (12, (0, 0, -20)), (48, (0, 0, 0))],
        "forearm.R": [(1, (0, 0, 0)), (12, (0, 0, 20)), (48, (0, 0, 0))],
        "head": [(1, (0, 0, 0)), (12, (-10, 0, 0)), (40, (-10, 0, 0)), (48, (0, 0, 0))],
        "mouth": [(1, (0, 0, 0), None, (1, 1, 1)), (12, (0, 0, 0), None, (1.35, 1, 2.2)), (40, (0, 0, 0), None, (1.35, 1, 2.2)), (48, (0, 0, 0), None, (1, 1, 1))],
        "eye.L": [(1, (0, 0, 0), None, (1, 1, 1)), (12, (0, 0, 0), None, (1.05, 1, 0.55)), (40, (0, 0, 0), None, (1.05, 1, 0.55)), (48, (0, 0, 0), None, (1, 1, 1))],
        "eye.R": [(1, (0, 0, 0), None, (1, 1, 1)), (12, (0, 0, 0), None, (1.05, 1, 0.55)), (40, (0, 0, 0), None, (1.05, 1, 0.55)), (48, (0, 0, 0), None, (1, 1, 1))],
    })


if __name__ == "__main__":
    bpy.ops.wm.read_factory_settings(use_empty=True)
    MAT.update(materials())
    bpy.context.scene.render.fps = 24
    arm = build_character()
    arm["role"], arm["animations"] = "ai_employee_muse", ["Idle", "Working", "AwaitingApproval", "Done"]
    station = build_station()
    animations(arm)
    os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
    C.export_glb(OUT, [arm, station])
    print(f"EXPORTED {OUT}")
