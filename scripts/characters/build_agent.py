"""Agentes de IA do Jarvis Mundimakers em sala-vitrine (diorama) com rig e 4 clipes de estado.

Uso: blender -b --factory-startup --python-exit-code 1 --python scripts/characters/build_agent.py -- <agente> <saida.glb>
agente: muse | pesquisa | logistica | producao
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
sys.path.insert(0, HERE)
import chibi as C  # noqa: E402
import clips  # noqa: E402
import diorama as R  # noqa: E402
import voxel  # noqa: E402
from bparts import MAT, Part, empty, material, set_parent  # noqa: E402
from mathutils import Euler, Matrix, Vector  # noqa: E402

F = R.FLOOR
S = 0.78          # escala dos personagens dentro da vitrine (moveis relativos ao corpo acompanham)


def face_mats(skin, iris, hair, lip=(0.18, 0.05, 0.05), blush=(0.80, 0.38, 0.33)):
    return {
        "skin": material("Skin", skin, rough=0.5),
        "sclera": material("Eye_Sclera", (0.88, 0.88, 0.86), rough=0.15, coat=1.0),
        "iris": material("Eye_Iris", iris, rough=0.2, coat=1.0),
        "pupil": material("Eye_Pupil", (0.004, 0.003, 0.003), rough=0.1, coat=1.0),
        "glint": material("Eye_Glint", (1, 1, 1), emission=(1, 1, 1), strength=2.0),
        "lash": material("Lash", (0.008, 0.006, 0.006), rough=0.5),
        "brow": material("Brow", tuple(c * 0.9 for c in hair), rough=0.6),
        "lip": material("Mouth_Line", lip, rough=0.4),
        "lipcolor": material("Lip_Rose", (0.50, 0.18, 0.18), rough=0.35, coat=0.4),
        "blush": material("Blush", blush, rough=0.6),
        "hair": material("Hair", hair, rough=0.35, coat=0.15),
    }


def outfit_regions(top, bottom, shoe, glove=None):
    def region(bone):
        if bone.startswith(("thigh", "shin", "hips")):
            return bottom
        if bone.startswith("foot"):
            return shoe
        if bone in ("neck", "head"):
            return "skin"
        if bone.startswith("hand"):
            return glove or "skin"
        return top

    def extra(c, bone):
        if c.z < 0.012:
            return "sole"
        if bone.startswith("shin") and c.z < 0.085:
            return shoe
        if bone.startswith("forearm") and c.z < 0.372:
            return glove or "skin"
        if bone == "chest" and c.z > 0.635:
            return "skin"
        return None
    return region, extra, [k for k in dict.fromkeys(["skin", top, bottom, shoe, "sole", glove]) if k]


def rig_clay(name, body, shells, head, hair, face, more_head=(), more=()):
    arm = C.build_armature(name)
    for o in (body, *shells):
        C.skin_to(o, arm)
    for o in (head, hair, face["nose"], face["blush"], face["ears"], *more_head):
        C.attach(o, arm, "head")
    for s in ("L", "R"):
        C.attach(face[f"eye.{s}"], arm, f"eye.{s}")
        C.attach(face[f"brow.{s}"], arm, f"brow.{s}")
    C.attach(face["lash"][0], arm, "eye.L")
    C.attach(face["lash"][1], arm, "eye.R")
    for m in face["mouth"]:
        C.attach(m, arm, "mouth")
    for o, bone in more:
        C.attach(o, arm, bone)
    return arm


def ring_tube(name, surf, z, push, r, mat):
    return C.tube(name, C.ring(surf, z, push), r, r, mat, res=3, bevel_res=2)


def circle_on_face(surf, x, z, radius, push, n=20):
    p, nrm = surf.front(x, z, push)
    yaw = math.atan2(nrm.x, -nrm.y)
    M = Matrix.Translation(p) @ Euler((0, 0, yaw)).to_matrix().to_4x4()
    return [M @ Vector((radius * math.cos(a), 0, radius * 0.85 * math.sin(a)))
            for a in [2 * math.pi * i / n for i in range(n + 1)]]


def place_character(arm, root, x, y, yaw):
    arm.location = (x, y, F)
    arm.rotation_euler = (0, 0, yaw)
    arm.scale = (S, S, S)
    bpy.context.view_layer.update()
    arm.parent = root


def at(x, y, yaw, fx, fy, z=0.0):
    """Ponto (fx lateral, fy a frente) no referencial do personagem em (x, y) olhando yaw."""
    v = Euler((0, 0, yaw)).to_matrix() @ Vector((fx * S, -fy * S, 0))
    return (x + v.x, y + v.y, F + z)


# ======================================================================= MUSE
def build_muse():
    MAT.update(R.prop_materials())
    MAT.update(R.room_materials((0.045, 0.035, 0.030), (0.24, 0.13, 0.06), (0.20, 0.11, 0.05), (1.0, 0.70, 0.35)))
    MAT.update(face_mats((0.62, 0.38, 0.27), (0.12, 0.17, 0.22), (0.012, 0.009, 0.008)))
    MAT.update({
        "sweater": material("Sweater_Gray", (0.16, 0.16, 0.165), rough=0.92),
        "pants": material("Pants_Charcoal", (0.022, 0.022, 0.028), rough=0.7),
        "shoe": material("Slipper_Cream", (0.62, 0.58, 0.50), rough=0.8),
        "sole": material("Sole_Gray", (0.20, 0.20, 0.21), rough=0.7),
        "tie": material("Hair_Tie", (0.55, 0.10, 0.12), rough=0.4),
    })
    cfg = {"build": 0.92, "arm": 0.92, "chest_d": 1.05, "jaw": 0.27, "eye_h": 1.40, "eye_w": 1.05, "lash_flick": True,
           "brow_w": 0.0034, "lips": True, "smile": 0.008, "mouth_w": 0.020}
    region, extra, mats = outfit_regions("sweater", "pants", "shoe")
    body = C.build_body("Muse_Body", cfg)
    C.assign_regions(body, region, mats, extra)
    segs = C.bone_segments()
    sweater = C.shell(body, "Muse_Sweater",
                      keep=lambda c: C.dominant_bone(c, segs).startswith(("hips", "spine", "chest", "upperarm", "forearm"))
                      and 0.425 < c.z < 0.64 and not (C.dominant_bone(c, segs).startswith("forearm") and c.z < 0.38),
                      offset=0.006, thickness=0.007, mat="sweater")
    ssurf = C.Surface([sweater])
    knit = [ring_tube("hem", ssurf, 0.432, 0.0, 0.007, "sweater"), ring_tube("collar", ssurf, 0.630, 0.002, 0.010, "sweater")]
    knit = C.join("Muse_Sweater_Rib", knit)

    head = C.build_head(cfg)
    face, _ = C.build_face(cfg, head)
    cap = C.build_hair_cap(cfg, opening=0.40)
    bun_c = C.HEAD_C + Vector((0, 0.035, 0.200))
    starts = [(math.radians(56 + 10 * abs(math.sin(p))), p) for p in [math.radians(a) for a in range(-115, 116, 8)]]
    starts += [(math.radians(108), math.radians(a)) for a in range(125, 240, 10)]
    strands = C.hair_strands(cap, lambda p0: (math.radians(18), math.pi), starts)
    bun = Part("Hair_Bun", ["hair", "tie"])
    bun.sphere(0.072, tuple(bun_c), (1.0, 0.95, 0.85), seg=24, rings=12)
    bun.cyl(0.050, 0.016, tuple(bun_c - Vector((0, 0, 0.055))), seg=24, mat="tie")
    swirl = []
    for k in range(6):
        pts = [bun_c + Vector(((0.070 - i * 0.005) * math.cos(i * 0.6 + k * 1.05), (0.066 - i * 0.005) * math.sin(i * 0.6 + k * 1.05),
                               0.010 + i * 0.006)) for i in range(10)]
        swirl.append(C.tube(f"swirl{k}", pts, 0.003, 0.002, "hair", res=3, bevel_res=2, swell=0.008))
    hs = C.Surface([cap, head])
    fringe = []
    for k in range(6):
        t0, p0, t1, p1 = 0.32 + 0.03 * k, -0.55 + 0.05 * k, 1.08 - 0.015 * k, 0.80 + 0.06 * k
        pts = [hs.radial(t0 + (t1 - t0) * u, p0 + (p1 - p0) * u, 0.004 + 0.004 * math.sin(math.pi * u))[0] for u in [i / 8 for i in range(9)]]
        fringe.append(C.tube(f"fringe{k}", pts, 0.002, 0.0015, "hair", res=4, bevel_res=2, swell=0.0065))
    for sx in (1, -1):
        p = [C.HEAD_C + Vector(v) for v in ((sx * 0.120, -0.085, 0.075), (sx * 0.142, -0.088, 0.010),
                                           (sx * 0.138, -0.080, -0.055), (sx * 0.122, -0.088, -0.100))]
        fringe.append(C.tube(f"frame{sx}", p, 0.003, 0.0015, "hair", res=4, swell=0.0055))
    hair = C.join("Muse_Hair", [cap, strands, bun.build(smooth=True), *swirl, *fringe])
    hair.data.polygons.foreach_set("use_smooth", [True] * len(hair.data.polygons))
    arm = rig_clay("Muse", body, [sweater, knit], head, hair, face)

    root = R.build_room("Muse")
    cx, cy, yaw = 0.10, 0.12, math.radians(32)
    place_character(arm, root, cx, cy, yaw)
    st = Part("Muse_Station", ["desk_top", "desk_leg", "chair", "bezel", "screen", "ui_a", "ui_b", "ui_c", "laptop", "key",
                               "mug", "coffee", "can", "pot", "leaf", "lamp_shade", "bulb", "shelf", "book_a", "book_b",
                               "book_c", "book_d", "rack", "led_a", "led_b", "note_a", "note_b", "note_c"])
    dz = 0.30 * S
    d = at(cx, cy, yaw, 0, 0.30)
    R.desk(st, d, 0.56, 0.30 * S, dz, yaw)
    R.chair(st, (cx, cy, F), yaw, seat=0.17 * S)
    R.laptop(st, at(cx, cy, yaw, 0, 0.22, dz), yaw + math.pi)
    R.mug(st, at(cx, cy, yaw, -0.20, 0.30, dz))
    R.can(st, at(cx, cy, yaw, 0.21, 0.34, dz))
    R.can(st, at(cx, cy, yaw, 0.25, 0.30, dz))
    R.desk_lamp(st, at(cx, cy, yaw, 0.24, 0.40, dz), yaw + math.pi * 0.75)
    side = (-0.42, 0.05, F)                                   # mesa lateral junto a parede esquerda
    R.desk(st, side, 0.55, 0.26, dz, math.radians(90))
    for i, yy in enumerate((-0.12, 0.13)):
        R.monitor(st, (-0.48, 0.05 + yy, F + dz + 0.13), math.radians(90), kind="code" if i == 0 else "chart", seed=i + 3)
    R.keyboard(st, (-0.36, 0.05, F + dz), math.radians(90))
    R.plant(st, (-0.45, -0.20, F + dz), 0.9)
    R.server_rack(st, (-0.50, 0.40, F), h=0.46)
    for z, books in ((0.62, 7), (0.80, 5)):
        R.shelf(st, (0.10, 0.44, F + z), 0.42, books=books, seed=int(z * 10))
    R.plant(st, (0.27, 0.44, F + 0.806), 0.8)
    R.sticky_notes(st, wall_y=0.50, center=(-0.25, 0), n=6, z0=F + 0.50)
    st.build(root, bevel=0.002, segments=1, smooth=True)
    clips.make_clips(arm, posture="sit", work="type", wave="R", look_yaw=-10)
    return root, arm


# ======================================================================= PESQUISA
def build_pesquisa():
    MAT.update(R.prop_materials())
    MAT.update(R.room_materials((0.020, 0.024, 0.050), (0.06, 0.06, 0.08), (0.05, 0.05, 0.07), (0.55, 0.25, 1.0)))
    MAT.update(face_mats((0.62, 0.40, 0.29), (0.10, 0.06, 0.03), (0.075, 0.042, 0.020)))
    MAT.update({
        "hoodie": material("Hoodie_Charcoal", (0.030, 0.031, 0.038), rough=0.85),
        "jeans": material("Jeans_Blue", (0.040, 0.065, 0.13), rough=0.75),
        "shoe": material("Sneaker_White", (0.78, 0.78, 0.76), rough=0.45),
        "sole": material("Sole_Red", (0.45, 0.05, 0.04), rough=0.6),
        "string": material("Drawstring_White", (0.8, 0.8, 0.8), rough=0.6),
        "frame": material("Glasses_Frame", (0.015, 0.012, 0.010), rough=0.3, coat=0.6),
        "phones": material("Headphones_Black", (0.02, 0.02, 0.022), rough=0.35),
        "white": material("Whiteboard", (0.85, 0.86, 0.86), rough=0.3, coat=0.4),
        "foam": material("Acoustic_Foam", (0.03, 0.03, 0.04), rough=0.95),
    })
    cfg = {"build": 1.05, "arm": 1.05, "jaw": 0.20, "eye_h": 1.15, "brow_w": 0.0052, "smile": 0.010, "mouth_w": 0.024}
    region, extra, mats = outfit_regions("hoodie", "jeans", "shoe")
    body = C.build_body("Pesquisa_Body", cfg)
    C.assign_regions(body, region, mats, extra)
    segs = C.bone_segments()
    hoodie = C.shell(body, "Pesquisa_Hoodie",
                     keep=lambda c: C.dominant_bone(c, segs).startswith(("hips", "spine", "chest", "upperarm", "forearm"))
                     and 0.42 < c.z < 0.64 and not (C.dominant_bone(c, segs).startswith("forearm") and c.z < 0.38),
                     offset=0.006, thickness=0.008, mat="hoodie")
    hood = [C.Vector((0.078 * math.sin(a), 0.012 + 0.060 * math.cos(a), 0.640 + 0.012 * math.cos(a)))
            for a in [math.radians(v) for v in range(-100, 101, 20)]]
    extras = [C.tube("hood", hood, 0.020, 0.020, "hoodie", res=4, swell=0.010)]
    for sx in (1, -1):
        extras.append(C.tube(f"str{sx}", [Vector((sx * 0.024, -0.064, 0.625)), Vector((sx * 0.026, -0.074, 0.585)),
                                          Vector((sx * 0.027, -0.076, 0.545))], 0.0022, 0.0022, "string", res=3))
    band = [Vector((0.090 * math.sin(a), 0.012 + 0.075 * math.cos(a), 0.672)) for a in [math.radians(v) for v in range(-90, 91, 15)]]
    phones = Part("phones_cups", ["phones", "ui_c"])
    for sx in (1, -1):
        phones.cyl(0.032, 0.022, (sx * 0.090, -0.010, 0.660), axis="X", seg=24, rot=(0, 0, sx * 0.4))
        phones.cyl(0.020, 0.003, (sx * 0.102, -0.016, 0.660), axis="X", mat="ui_c", seg=24, rot=(0, 0, sx * 0.4))
    extras += [C.tube("band", band, 0.007, 0.007, "phones", res=4), phones.build(smooth=True)]
    hoodie_extra = C.join("Pesquisa_Hoodie_Details", extras)

    head = C.build_head(cfg)
    face, fsurf = C.build_face(cfg, head)
    cap = C.build_hair_cap(cfg, opening=0.36)
    hs = C.Surface([cap])
    tufts = []
    for k in range(22):
        th, ph = math.radians(12 + (k * 37) % 55), math.radians(-150 + (k * 71) % 300)
        p0, n0 = hs.radial(th, ph, -0.004)
        fwd = Vector((0, -1, 0.3)).normalized()
        dirv = (n0 * 0.7 + fwd * 0.5).normalized()
        pts = [p0, p0 + dirv * 0.022, p0 + dirv * 0.040 + Vector((0, 0, -0.010)), p0 + dirv * 0.050 + Vector((0, -0.006, -0.022))]
        tufts.append(C.tube(f"tuft{k}", pts, 0.012, 0.002, "hair", res=4, bevel_res=2))
    hair = C.join("Pesquisa_Hair", [cap, *tufts])
    glasses = []
    ex, ez = 0.058, 0.785
    for sx in (1, -1):
        glasses.append(C.tube(f"lens{sx}", circle_on_face(fsurf, sx * ex, ez, 0.036, 0.014), 0.0028, 0.0028, "frame", res=3))
        glasses.append(C.tube(f"temple{sx}", [fsurf.front(sx * (ex + 0.036), ez + 0.004, 0.012)[0],
                                              Vector((sx * 0.150, -0.06, ez + 0.006)), Vector((sx * 0.152, 0.010, ez - 0.004))],
                              0.0024, 0.0024, "frame", res=3))
    glasses.append(C.tube("bridge", [fsurf.front(-0.022, ez + 0.010, 0.016)[0], fsurf.front(0, ez + 0.014, 0.018)[0],
                                     fsurf.front(0.022, ez + 0.010, 0.016)[0]], 0.0026, 0.0026, "frame", res=3))
    glasses = C.join("Pesquisa_Glasses", glasses)
    arm = rig_clay("Pesquisa", body, [hoodie], head, hair, face, more_head=[glasses], more=[(hoodie_extra, "chest")])

    root = R.build_room("Pesquisa", planks=False)
    cx, cy, yaw = -0.05, 0.05, math.radians(-90 + 25)
    place_character(arm, root, cx, cy, yaw)
    st = Part("Pesquisa_Station", ["desk_top", "desk_leg", "chair", "bezel", "screen", "ui_a", "ui_b", "ui_c", "key", "mug",
                                   "coffee", "can", "pot", "leaf", "lamp_shade", "bulb", "shelf", "book_a", "book_b", "book_c",
                                   "book_d", "note_a", "note_b", "note_c", "white", "foam", "v_accent"])
    dz = 0.30 * S
    R.desk(st, at(cx, cy, yaw, 0, 0.30), 0.66, 0.30 * S, dz, yaw)
    R.chair(st, (cx, cy, F), yaw, seat=0.17 * S)
    for i, (fx, ang) in enumerate(((-0.24, 0.45), (0, 0), (0.24, -0.45))):
        R.monitor(st, at(cx, cy, yaw, fx, 0.38 - abs(fx) * 0.3, dz + 0.13), yaw + math.pi + ang,
                  kind="chart" if i == 2 else "code", seed=i + 7)
    R.keyboard(st, at(cx, cy, yaw, 0, 0.22, dz), yaw + math.pi, rgb=True)
    R.mug(st, at(cx, cy, yaw, -0.26, 0.24, dz))
    for k in range(3):
        R.can(st, at(cx, cy, yaw, 0.22 + 0.03 * k, 0.22 + 0.02 * (k % 2), dz))
    R.desk_lamp(st, at(cx, cy, yaw, -0.30, 0.36, dz), yaw)
    st.box((0.46, 0.012, 0.30), (0.12, 0.49, F + 0.62), "white")                     # quadro branco
    for i in range(7):
        st.box((0.05 + (i * 37 % 5) * 0.04, 0.002, 0.004), (0.0 + (i % 2) * 0.12, 0.483, F + 0.73 - i * 0.03),
               ("ui_a", "book_b", "book_d")[i % 3])
    for i in range(3):
        st.box((0.05, 0.002, 0.035), (0.25, 0.483, F + 0.70 - i * 0.06), ("book_b", "book_d", "ui_a")[i])
    for r_ in range(2):                                                               # espuma acustica
        for c in range(3):
            st.box((0.025, 0.11, 0.11), (-0.585, -0.25 + c * 0.13, F + 0.55 + r_ * 0.13), "foam")
    R.shelf(st, (-0.30, 0.44, F + 0.75), 0.36, books=6, seed=3)
    R.plant(st, (-0.18, 0.44, F + 0.756), 0.7)
    R.sticky_notes(st, wall_y=0.50, center=(-0.45, 0), n=3, z0=F + 0.50)
    st.box((R.W, 0.01, 0.012), (0, 0.48, F + R.H - 0.04), "v_accent")                 # LED roxo
    st.box((0.01, R.D, 0.012), (-0.58, 0, F + R.H - 0.04), "v_accent")
    st.build(root, bevel=0.002, segments=1, smooth=True)
    clips.make_clips(arm, posture="sit", work="type", wave="R", look_yaw=-50)
    return root, arm


# ======================================================================= LOGISTICA
def build_logistica():
    MAT.update(R.prop_materials())
    MAT.update(R.room_materials((0.05, 0.05, 0.22), (0.12, 0.12, 0.18), (0.10, 0.10, 0.16), (0.55, 0.40, 1.0)))
    MAT.update(face_mats((0.55, 0.33, 0.22), (0.07, 0.04, 0.02), (0.010, 0.010, 0.014)))
    MAT.update({
        "shirt": material("Shirt_Lavender", (0.62, 0.62, 0.76), rough=0.75),
        "vest": material("Vest_Purple", (0.20, 0.07, 0.62), rough=0.45, coat=0.3),
        "quilt": material("Vest_Quilt", (0.14, 0.04, 0.45), rough=0.4, coat=0.3),
        "pants": material("Pants_Graphite", (0.03, 0.03, 0.04), rough=0.7),
        "shoe": material("Sneaker_White", (0.78, 0.78, 0.76), rough=0.45),
        "sole": material("Sole_Gray", (0.25, 0.25, 0.27), rough=0.7),
        "silver": material("Zipper_Silver", (0.7, 0.7, 0.72), metallic=1.0, rough=0.3),
        "scanner": material("Scanner_Graphite", (0.04, 0.04, 0.045), rough=0.4),
        "laser": material("Scanner_Laser", (0, 0, 0), emission=(1.0, 0.1, 0.1), strength=6.0),
        "table": material("Table_Gray", (0.30, 0.31, 0.36), rough=0.4, coat=0.3),
        "tray": material("Tray_Purple", (0.18, 0.08, 0.55), rough=0.4),
        "rack_blue": material("Rack_Blue", (0.10, 0.12, 0.40), metallic=0.5, rough=0.4),
        "paper": material("Clipboard_Paper", (0.85, 0.85, 0.82), rough=0.8),
    })
    cfg = {"build": 1.12, "arm": 1.1, "chest_d": 1.1, "jaw": 0.18, "eye_h": 1.12, "brow_w": 0.0058, "smile": 0.013, "mouth_w": 0.028}
    region, extra, mats = outfit_regions("shirt", "pants", "shoe")
    body = C.build_body("Logistica_Body", cfg)
    C.assign_regions(body, region, mats, extra)
    segs = C.bone_segments()
    vest = C.shell(body, "Logistica_Vest",
                   keep=lambda c: C.dominant_bone(c, segs) in ("hips", "spine", "chest") and 0.43 < c.z < 0.64,
                   offset=0.012, thickness=0.010, mat="vest")
    vs = C.Surface([vest])
    quilt = [ring_tube(f"q{z}", vs, z, -0.002, 0.009, "vest") for z in (0.455, 0.495, 0.535, 0.575, 0.612)]
    quilt.append(ring_tube("collar", vs, 0.636, 0.0, 0.013, "vest"))
    zp = []
    for z in (0.44, 0.50, 0.56, 0.62):
        try:
            zp.append(vs.front(0.0, z, 0.002)[0])
        except RuntimeError:
            pass
    quilt.append(C.tube("zip", zp, 0.003, 0.003, "silver", res=3))
    vest_d = C.join("Logistica_Vest_Quilt", quilt)
    head = C.build_head(cfg)
    face, _ = C.build_face(cfg, head)
    cap = C.build_hair_cap(cfg, opening=0.42)
    starts = [(math.radians(58 + 8 * abs(math.sin(p))), p) for p in [math.radians(a) for a in range(-110, 111, 10)]]
    strands = C.hair_strands(cap, lambda p0: (math.radians(80), math.pi if p0 >= 0 else -math.pi), starts, swell=0.006)
    hs = C.Surface([cap])
    quiff = []
    for k in range(5):                                         # topete
        p0, n0 = hs.radial(math.radians(48), math.radians(-30 + 15 * k), -0.003)
        pts = [p0, p0 + n0 * 0.025 + Vector((0, -0.010, 0.010)), p0 + n0 * 0.030 + Vector((0.012, 0.010, 0.020))]
        quiff.append(C.tube(f"quiff{k}", pts, 0.013, 0.004, "hair", res=4))
    hair = C.join("Logistica_Hair", [cap, strands, *quiff])
    sc = Part("Logistica_Scanner", ["scanner", "laser"])
    hp = Vector((-0.157, -0.025, 0.300))
    sc.box((0.026, 0.030, 0.065), tuple(hp))
    sc.box((0.034, 0.070, 0.030), tuple(hp + Vector((0, -0.030, 0.035))))
    sc.box((0.026, 0.004, 0.016), tuple(hp + Vector((0, -0.066, 0.035))), "laser")
    scanner = sc.build(bevel=0.004, segments=2, smooth=True)
    arm = rig_clay("Logistica", body, [vest], head, hair, face, more=[(vest_d, "chest"), (scanner, "hand.R")])

    root = R.build_room("Logistica", planks=False)
    cx, cy, yaw = 0.05, 0.10, math.radians(15)
    place_character(arm, root, cx, cy, yaw)
    st = Part("Logistica_Station", ["table", "desk_leg", "tray", "cardboard", "tape", "paper", "rack_blue", "ui_a", "v_accent"])
    tz = 0.36 * S
    tc = at(cx, cy, yaw, 0, 0.26)
    R.desk(st, tc, 0.66, 0.30 * S, tz, yaw, top="table", leg="desk_leg")
    T = lambda fx, fy: at(cx, cy, yaw, fx, fy, tz)  # noqa: E731
    tr = T(-0.05, 0.25)
    for size, off in (((0.24, 0.16, 0.010), (0, 0, 0.005)), ((0.24, 0.012, 0.035), (0, -0.074, 0.017)),
                      ((0.24, 0.012, 0.035), (0, 0.074, 0.017)), ((0.012, 0.16, 0.035), (-0.114, 0, 0.017)),
                      ((0.012, 0.16, 0.035), (0.114, 0, 0.017)), ((0.012, 0.15, 0.03), (0.02, 0, 0.015))):
        R_ = Euler((0, 0, yaw)).to_matrix()
        st.box(size, tuple(Vector(tr) + R_ @ Vector(off)), "tray", (0, 0, yaw))
    st.box((0.07, 0.10, 0.02), tuple(Vector(tr) + Euler((0, 0, yaw)).to_matrix() @ Vector((-0.05, 0, 0.02))), "paper", (0, 0, yaw))
    R.cardboard_box(st, T(0.20, 0.26), (0.13, 0.11, 0.10), yaw + 0.1)
    R.cardboard_box(st, T(-0.27, 0.30), (0.12, 0.12, 0.09), yaw - 0.2)
    st.box((0.07, 0.10, 0.004), T(0.27, 0.18), "paper", (0, 0, yaw - 0.3))         # prancheta
    for i, (x, y, s) in enumerate(((0.38, -0.30, (0.16, 0.14, 0.13)), (0.40, -0.30, (0.12, 0.11, 0.10)),
                                   (-0.40, -0.25, (0.15, 0.15, 0.14)), (0.38, -0.12, (0.13, 0.12, 0.12)))):
        z = 0.13 if i == 1 else 0
        R.cardboard_box(st, (x, y, F + z), s, 0.2 * i)
    for lvl in range(3):                                                             # estante de armazem
        z = F + 0.20 + lvl * 0.26
        st.box((0.80, 0.18, 0.015), (-0.05, 0.40, z), "rack_blue")
        for k in range(4):
            if (k + lvl) % 3 != 2:
                R.cardboard_box(st, (-0.36 + k * 0.20, 0.40, z + 0.008), (0.14, 0.13, 0.11 + 0.02 * (k % 2)), 0.05 * k)
    for sx in (-1, 1):
        st.box((0.025, 0.18, 0.80), (-0.05 + sx * 0.40, 0.40, F + 0.40), "rack_blue")
    st.box((R.W, 0.01, 0.012), (0, 0.48, F + R.H - 0.04), "v_accent")
    st.build(root, bevel=0.002, segments=1, smooth=True)
    clips.make_clips(arm, posture="stand", work="scan", wave="L", look_yaw=-10)
    return root, arm


# ======================================================================= PRODUCAO (voxel)
def build_producao():
    MAT.update(R.prop_materials())
    MAT.update(R.room_materials((0.50, 0.52, 0.56), (0.80, 0.81, 0.83), (0.70, 0.71, 0.74), (1.0, 0.55, 0.10)))
    MAT.update({
        "skin": material("Voxel_Skin", (0.60, 0.36, 0.22), rough=0.55),
        "shirt": material("Voxel_Shirt_Blue", (0.10, 0.22, 0.45), rough=0.7),
        "vest": material("Voxel_Overall_Orange", (0.85, 0.30, 0.02), rough=0.55),
        "pants": material("Voxel_Pants_Brown", (0.18, 0.10, 0.05), rough=0.7),
        "boot": material("Voxel_Boot", (0.07, 0.04, 0.02), rough=0.5),
        "sole": material("Voxel_Sole", (0.02, 0.02, 0.02), rough=0.8),
        "hair": material("Voxel_Hair_Brown", (0.16, 0.07, 0.025), rough=0.6),
        "helmet": material("Voxel_Helmet_Orange", (0.90, 0.40, 0.02), rough=0.35, coat=0.5),
        "gold": material("Gold_Accent", (0.80, 0.62, 0.33), metallic=1.0, rough=0.30),
        "eye": material("Voxel_Eye_White", (0.88, 0.88, 0.86), rough=0.3),
        "iris": material("Voxel_Iris_Teal", (0.02, 0.30, 0.25), rough=0.3),
        "pupil": material("Voxel_Pupil", (0.01, 0.01, 0.01), rough=0.3),
        "brow": material("Voxel_Brow", (0.10, 0.045, 0.015), rough=0.6),
        "mouth": material("Voxel_Mouth", (0.12, 0.03, 0.02), rough=0.5),
        "blush": material("Voxel_Blush", (0.80, 0.35, 0.28), rough=0.6),
        "belt": material("Voxel_Belt", (0.05, 0.03, 0.02), rough=0.5),
        "m_gray": material("Machine_Gray", (0.20, 0.21, 0.23), metallic=0.6, rough=0.45),
        "m_dark": material("Machine_Dark", (0.05, 0.055, 0.06), metallic=0.7, rough=0.4),
        "m_light": material("Machine_Light", (0.45, 0.46, 0.48), metallic=0.6, rough=0.4),
        "m_orange": material("Machine_Orange", (0.90, 0.40, 0.02), rough=0.4, coat=0.4),
        "tile": material("Platform_Tile", (0.85, 0.86, 0.88), rough=0.35),
    })
    arm = voxel.build_voxel("Producao", {})
    root = R.build_room("Producao", planks=True)
    cx, cy, yaw = -0.24, -0.08, math.radians(22)
    place_character(arm, root, cx, cy, yaw)
    mx, my = 0.22, 0.12                                        # maquina voxel sobre plataforma
    plat = Part("Producao_Platform", ["m_dark", "tile", "v_accent"])
    plat.box((0.62, 0.62, 0.06), (mx, my, F + 0.03))
    for i in range(4):
        for j in range(4):
            plat.box((0.145, 0.145, 0.008), (mx - 0.225 + i * 0.15, my - 0.225 + j * 0.15, F + 0.064), "tile")
    for k in range(3):
        plat.box((0.06, 0.006, 0.02), (mx - 0.18 + k * 0.18, my - 0.312, F + 0.03), "v_accent")
    plat.build(root, bevel=0.004, segments=2)
    pz = F + 0.068
    mac = Part("Producao_Machine", ["m_gray", "m_dark", "m_light", "m_orange", "ui_a", "ui_b"])
    mac.box((0.42, 0.40, 0.10), (mx, my, pz + 0.05))
    for sx in (-1, 1):
        for sy in (-1, 1):
            mac.box((0.06, 0.06, 0.50), (mx + sx * 0.18, my + sy * 0.17, pz + 0.10 + 0.25), "m_dark")
    mac.box((0.44, 0.42, 0.08), (mx, my, pz + 0.64))
    mac.box((0.44, 0.08, 0.05), (mx, my - 0.17, pz + 0.575), "m_orange")
    for i in range(5):
        mac.box((0.06, 0.012, 0.04), (mx - 0.14 + i * 0.07, my - 0.212, pz + 0.05), ("m_orange", "m_light")[i % 2])
    mac.box((0.10, 0.012, 0.07), (mx + 0.12, my - 0.211, pz + 0.64), "m_dark")
    for i in range(3):
        for j in range(2):
            mac.box((0.018, 0.004, 0.014), (mx + 0.09 + i * 0.03, my - 0.219, pz + 0.65 - j * 0.025), ("ui_a", "ui_b")[(i + j) % 2])
    mac.box((0.10, 0.14, 0.14), (mx + 0.27, my + 0.08, pz + 0.37), "m_gray")         # caixa do carretel
    mac.cyl(0.055, 0.035, (mx + 0.335, my + 0.08, pz + 0.37), axis="X", mat="m_orange", seg=8)
    mac.box((0.38, 0.30, 0.018), (mx, my, pz + 0.10 + 0.012), "m_light")             # base fixa
    mac.build(root, bevel=0.006, segments=2)
    bed = empty("Machine_Bed_Z_Mover", (mx, my, pz + 0.20), root, anim="translate", axis="y", range_m=[-0.08, 0.15])
    b = Part("Machine_Bed", ["m_light", "m_orange"])
    b.box((0.30, 0.28, 0.02), (mx, my, pz + 0.20))
    for k in range(4):
        b.box((0.06 - k * 0.01, 0.06 - k * 0.01, 0.025), (mx, my, pz + 0.222 + k * 0.025), "m_orange")
    b.build(bed, origin=bed.matrix_world.translation, bevel=0.004, segments=2)
    head_ = empty("Machine_Toolhead_X_Mover", (mx, my, pz + 0.52), root, anim="translate", axis="x", range_m=[-0.12, 0.12])
    g = Part("Machine_Gantry", ["m_dark"])
    g.box((0.36, 0.03, 0.03), (mx, my, pz + 0.55))
    g.build(root, bevel=0.004, segments=2)
    th = Part("Machine_Toolhead", ["m_orange", "m_dark", "m_light"])
    th.box((0.07, 0.07, 0.08), (mx, my - 0.01, pz + 0.52))
    th.box((0.03, 0.03, 0.03), (mx, my - 0.01, pz + 0.465), "m_light")
    th.box((0.04, 0.012, 0.04), (mx, my - 0.05, pz + 0.53), "m_dark")
    th.build(head_, origin=head_.matrix_world.translation, bevel=0.005, segments=2)
    tool = Part("Producao_Wrench", ["m_light", "m_orange"])
    hp = Vector((-0.131, -0.02, 0.30))
    tool.box((0.020, 0.024, 0.06), tuple(hp), "m_orange")
    tool.box((0.016, 0.014, 0.10), tuple(hp + Vector((0, 0, -0.07))))
    tool.box((0.05, 0.016, 0.03), tuple(hp + Vector((0, 0, -0.13))))
    w = tool.build(bevel=0.003, segments=2)
    C.attach(w, arm, "hand.R")
    clips.make_clips(arm, posture="stand", work="inspect", wave="L", look_yaw=-15)
    return root, arm


AGENTS = {"muse": build_muse, "pesquisa": build_pesquisa, "logistica": build_logistica, "producao": build_producao}

if __name__ == "__main__":
    agent, out = sys.argv[sys.argv.index("--") + 1:][:2]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = 24
    root, arm = AGENTS[agent]()
    arm["role"] = f"ai_agent_{agent}"
    arm["animations"] = ["Idle", "Working", "AwaitingApproval", "Done"]
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    C.export_glb(out, [root])
    print(f"EXPORTED {out}")
    argv = sys.argv[sys.argv.index("--") + 1:]
    if "--preview" in argv:                     # previa Cycles da cena-fonte (o importador glTF do Blender
        import render_character as RC          # desloca anexos de ossos sob armature escalada)
        d = argv[argv.index("--preview") + 1]
        os.makedirs(d, exist_ok=True)
        jobs = [("diorama", "Idle", 1, 1000, 128, "diorama"), ("face", "Idle", 1, 700, 96, "face")]
        jobs += [("pose", an, fr, 450, 64, f"pose_{an}") for an, fr in
                 (("Idle", 1), ("Working", 20), ("AwaitingApproval", 30), ("Done", 20))]
        for view, action, frame, res, spp, tag in jobs:
            RC.render(RC.parse([out, os.path.join(d, f"{agent}_{tag}.png"), "--view", view, "--action", action,
                                "--frame", str(frame), "--res", str(res), "--samples", str(spp)]))
