"""Personagem voxel premium (blocos chanfrados) sobre o mesmo rig de chibi.BONES.

Cada membro e um bloco rigido preso ao seu osso: anima com os mesmos clipes dos agentes clay.
Cores e pecas vem de cfg; tudo em metros, Blender Z-up, olhando -Y.
"""
import chibi as C
from bparts import Part

BEV = 0.006


def _part(name, mats, boxes, bevel=BEV):
    p = Part(name, mats)
    for size, loc, *m in boxes:
        p.box(size, loc, m[0] if m else None)
    return p.build(bevel=bevel, segments=2, smooth=True)


def build_voxel(name, cfg):
    """cfg: chaves de material: skin, shirt, vest, pants, boot, sole, hair, helmet, eye, iris, pupil,
    brow, mouth, blush, gold, belt."""
    arm = C.build_armature(name)
    fy = -0.135                                               # plano frontal da cabeca
    pieces = {
        "head": _part(f"{name}_Head", ["skin", "hair", "helmet", "gold"], [
            ((0.27, 0.26, 0.26), (0, 0, 0.80)),
            ((0.012, 0.014, 0.030), (0, fy - 0.004, 0.775)),                      # nariz
            ((0.03, 0.03, 0.05), (0.142, 0.01, 0.79)), ((0.03, 0.03, 0.05), (-0.142, 0.01, 0.79)),  # orelhas
            ((0.282, 0.27, 0.07), (0, 0.006, 0.915), "hair"),                      # cabelo
            ((0.282, 0.06, 0.18), (0, 0.112, 0.84), "hair"),
            ((0.03, 0.22, 0.12), (0.135, 0.03, 0.87), "hair"), ((0.03, 0.22, 0.12), (-0.135, 0.03, 0.87), "hair"),
            ((0.06, 0.02, 0.03), (-0.08, fy - 0.002, 0.885), "hair"), ((0.05, 0.02, 0.022), (0.02, fy - 0.002, 0.89), "hair"),
            ((0.30, 0.30, 0.115), (0, 0.012, 0.995), "helmet"),                     # capacete
            ((0.05, 0.31, 0.03), (0, 0.012, 1.05), "helmet"),                     # nervura
            ((0.33, 0.34, 0.024), (0, -0.012, 0.944), "helmet"),                  # aba
            ((0.20, 0.07, 0.022), (0, -0.19, 0.947), "helmet"),                   # pala
            ((0.05, 0.012, 0.05), (0, -0.155, 0.995), "gold"),                    # emblema
        ]),
        "chest": _part(f"{name}_Torso", ["vest", "shirt", "gold", "belt"], [
            ((0.19, 0.12, 0.235), (0, 0, 0.517)),
            ((0.10, 0.01, 0.04), (0, -0.062, 0.615), "shirt"),                   # gola
            ((0.07, 0.012, 0.05), (-0.045, -0.062, 0.545)), ((0.07, 0.012, 0.05), (0.045, -0.062, 0.545)),  # bolsos
            ((0.016, 0.006, 0.016), (-0.045, -0.071, 0.568), "gold"), ((0.016, 0.006, 0.016), (0.045, -0.071, 0.568), "gold"),
            ((0.20, 0.13, 0.03), (0, 0, 0.413), "belt"),
            ((0.04, 0.008, 0.026), (0, -0.068, 0.413), "gold"),
        ]),
        "neck": _part(f"{name}_Neck", ["skin"], [((0.07, 0.07, 0.05), (0, 0, 0.655))]),
    }
    for s, sx in (("L", 1), ("R", -1)):
        pieces[f"upperarm.{s}"] = _part(f"{name}_UpperArm.{s}", ["shirt", "vest"], [
            ((0.072, 0.075, 0.17), (sx * 0.131, 0, 0.545)),
            ((0.076, 0.079, 0.04), (sx * 0.131, 0, 0.61), "vest"),               # ombreira do colete
        ])
        pieces[f"forearm.{s}"] = _part(f"{name}_Forearm.{s}", ["shirt"], [((0.068, 0.07, 0.11), (sx * 0.131, 0, 0.405))])
        pieces[f"hand.{s}"] = _part(f"{name}_Hand.{s}", ["skin"], [((0.066, 0.066, 0.062), (sx * 0.131, -0.004, 0.318))])
        pieces[f"thigh.{s}"] = _part(f"{name}_Thigh.{s}", ["pants"], [((0.088, 0.10, 0.20), (sx * 0.048, 0, 0.30))])
        pieces[f"shin.{s}"] = _part(f"{name}_Shin.{s}", ["pants", "boot"], [
            ((0.086, 0.098, 0.12), (sx * 0.048, 0, 0.14)),
            ((0.09, 0.102, 0.03), (sx * 0.048, 0, 0.085), "boot"),
        ])
        pieces[f"foot.{s}"] = _part(f"{name}_Boot.{s}", ["boot", "sole"], [
            ((0.09, 0.13, 0.07), (sx * 0.048, -0.016, 0.045)),
            ((0.094, 0.136, 0.014), (sx * 0.048, -0.016, 0.007), "sole"),
        ])
    for bone, ob in pieces.items():
        C.attach(ob, arm, bone)

    for s, sx in (("L", 1), ("R", -1)):                      # olhos pixelados
        e = Part(f"Eye.{s}", ["eye", "iris", "pupil", "eye"])
        x = sx * 0.058
        e.box((0.054, 0.006, 0.044), (x, fy - 0.003, 0.80))
        e.box((0.030, 0.007, 0.036), (x - sx * 0.006, fy - 0.0045, 0.798), "iris")
        e.box((0.016, 0.008, 0.020), (x - sx * 0.006, fy - 0.0055, 0.794), "pupil")
        e.box((0.009, 0.009, 0.009), (x - sx * 0.012, fy - 0.0065, 0.807), "eye")
        C.attach(e.build(bevel=0.0015, segments=1), arm, f"eye.{s}")
        b = Part(f"Brow.{s}", ["brow"])
        b.box((0.056, 0.008, 0.012), (x, fy - 0.004, 0.845))
        C.attach(b.build(bevel=0.002, segments=1), arm, f"brow.{s}")
        bl = Part(f"Blush.{s}", ["blush"])
        bl.box((0.03, 0.004, 0.016), (sx * 0.09, fy - 0.002, 0.757))
        C.attach(bl.build(), arm, "head")
    m = Part("Mouth", ["mouth"])
    for x, z in ((-0.036, 0.738), (-0.022, 0.728), (-0.007, 0.724), (0.007, 0.724), (0.022, 0.728), (0.036, 0.738)):
        m.box((0.016, 0.007, 0.012), (x, fy - 0.0035, z))
    C.attach(m.build(bevel=0.002, segments=1), arm, "mouth")
    return arm
