"""Impressora 3D fechada inspirada na Elegoo Centauri Carbon 2 (asset v1, sem logotipo).

Uso: blender -b --factory-startup --python-exit-code 1 --python scripts/printers/build_elegoo_cc2.py -- <raw.glb>

Medidas (metros, Blender Z-up; exportador converte para glTF Y-up). Fontes em docs/elegoo-cc2-v1.md:
- Volume de impressao 256^3 mm e placa 260 x 260 mm: especificacoes publicadas da CC2.
- Tela de toque 5" (16:9 -> ~111 x 62 mm): especificacao publicada da CC2.
- Gabinete 398 x 404 x 490 mm: medida oficial da Centauri Carbon (1a ger.), usada como
  proporcao; a CC2 e descrita como mesma estrutura com eletronica nova. Os 500 x 480 x 743 mm
  listados para o Combo incluem o modulo CANVAS e nao sao usados.
- Layout interno (perfis, cabecote, ventoinhas, fusos, camera) = aproximacao de design.
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Euler, Vector

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import bparts  # noqa: E402
from bparts import MAT, Part, empty, material  # noqa: E402

OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "build/elegoo_cc2_v1_raw.glb"

W, D, H = 0.398, 0.404, 0.490
HX, HY = W / 2, D / 2
BUILD, PLATE = 0.256, 0.260
POST, FOOT_H, BASE_TOP, TOP = 0.024, 0.010, 0.095, 0.022
CH_Z0, CH_Z1 = BASE_TOP, H - TOP
CH_H = CH_Z1 - CH_Z0
GANTRY_Z = 0.445
NOZZLE_TIP = GANTRY_Z - 0.067
BED_REST = 0.250
RAIL_X = 0.170
SCREW_X, SCREW_Y = 0.150, HY - 0.035
ROD_X = 0.172

# three.js (Y-up) a partir de eixo Blender
THREE_AXIS = {"X": "x", "Y": "z", "Z": "y"}


def make_materials():
    return {
        "frame": material("Metal_Frame", (0.030, 0.032, 0.036), metallic=0.9, rough=0.34),
        "panel": material("Panel_Painted", (0.012, 0.013, 0.015), rough=0.42, coat=0.3),
        "glass": material("Glass_Smoked", (0.40, 0.43, 0.46), rough=0.02, transmission=1.0),
        "gold": material("Gold_Accent", (0.80, 0.62, 0.33), metallic=1.0, rough=0.30),
        "plastic": material("Plastic_Black", (0.016, 0.016, 0.018), rough=0.55),
        "rubber": material("Rubber", (0.010, 0.010, 0.010), rough=0.9),
        "steel": material("Metal_Steel", (0.62, 0.63, 0.65), metallic=1.0, rough=0.20),
        "alu": material("Aluminum_Bed", (0.30, 0.31, 0.33), metallic=1.0, rough=0.42),
        "pei": material("Bed_PEI", (0.11, 0.105, 0.10), metallic=0.2, rough=0.72),
        "brass": material("Brass_Nozzle", (0.85, 0.66, 0.36), metallic=1.0, rough=0.25),
        "screen": material("Screen_Emissive", (0.02, 0.02, 0.03), rough=0.15,
                           emission=(0.10, 0.22, 0.50), strength=0.8),
        "led": material("Chamber_LED", (0.9, 0.9, 0.9), rough=0.4,
                        emission=(1.0, 0.92, 0.80), strength=4.0),
        "lens": material("Lens_Black", (0.005, 0.005, 0.008), metallic=0.0, rough=0.05, coat=1.0),
    }


def fan(name, center, axis, size, parent, outward):
    """Ventoinha: moldura + grade fixas e rotor animavel (spin) num pivo proprio."""
    c = Vector(center)
    ax = Vector({"X": (1, 0, 0), "Y": (0, 1, 0), "Z": (0, 0, 1)}[axis]) * outward
    to_axis = {"X": Euler((0, math.pi / 2, 0)), "Y": Euler((-math.pi / 2, 0, 0)), "Z": Euler()}[axis]
    m = to_axis.to_matrix()

    def at(x, y, z):                       # coords locais (eixo = Z) -> mundo
        return tuple(c + m @ Vector((x, y, z * outward)))

    def sz(x, y, z):                        # tamanho de caixa local -> mundo (eixos alinhados)
        v = m @ Vector((x, y, z))
        return (abs(v.x), abs(v.y), abs(v.z))

    s, t = size, size * 0.09
    frame = Part(f"Fan_{name}_Frame", ["plastic", "frame"])
    for sx, sy, w, h in ((0, 1, s, t), (0, -1, s, t), (1, 0, t, s), (-1, 0, t, s)):
        frame.box(sz(w, h, 0.012), at(sx * (s - t) / 2, sy * (s - t) / 2, -0.004))
    for i in range(5):                      # grade externa
        y = -s / 2 + t + (i + 0.5) * (s - 2 * t) / 5
        frame.box(sz(s - t, 0.0025, 0.002), at(0, y, 0.004), "frame")
    frame.cyl(s * 0.17, 0.004, at(0, 0, -0.010), axis=axis, mat="plastic")   # mancal
    frame.build(parent, bevel=0.0008)

    pivot = empty(f"Fan_{name}_Rotor_Pivot", at(0, 0, -0.004), parent,
                  anim="spin", axis=THREE_AXIS[axis], rpm_hint=2400)
    rotor = Part(f"Fan_{name}_Rotor", ["plastic"])
    rotor.cyl(s * 0.15, 0.008, at(0, 0, -0.004), axis=axis)
    for k in range(7):
        a = k * 2 * math.pi / 7
        r = s * 0.29
        blade = Euler((0.45, 0, a)).to_matrix()                 # passo 0.45 rad
        verts = bmesh.ops.create_cube(rotor.bm, size=1.0)["verts"]
        for v in verts:
            local = Vector((v.co.x * s * 0.26, v.co.y * s * 0.13, v.co.z * 0.0016))
            v.co = m @ (blade @ local + Vector((r * math.cos(a), r * math.sin(a), 0))) + Vector(at(0, 0, -0.004))
    rotor.build(pivot, origin=pivot.matrix_world.translation)
    return pivot


def panel_with_hole(part, plane, fixed, span_a, span_b, hole_c, hole_s, thick, mat=None):
    """Painel retangular com abertura quadrada. plane='YZ' (lateral) ou 'XZ' (traseiro)."""
    (a0, a1), (b0, b1) = span_a, span_b
    ha0, ha1 = hole_c[0] - hole_s / 2, hole_c[0] + hole_s / 2
    hb0, hb1 = hole_c[1] - hole_s / 2, hole_c[1] + hole_s / 2
    rects = [(a0, a1, b0, hb0), (a0, a1, hb1, b1), (a0, ha0, hb0, hb1), (ha1, a1, hb0, hb1)]
    for r0, r1, s0, s1 in rects:
        ca, cb, la, lb = (r0 + r1) / 2, (s0 + s1) / 2, r1 - r0, s1 - s0
        if plane == "YZ":
            part.box((thick, la, lb), (fixed, ca, cb), mat)
        else:
            part.box((la, thick, lb), (ca, fixed, cb), mat)


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    MAT.update(make_materials())
    bpy.context.scene.unit_settings.system = "METRIC"

    root = empty("CC2_Root", (0, 0, 0), asset="elegoo_cc2_v1", units="meters", up_axis="Y",
                 ref_build_volume_mm=[256, 256, 256], ref_plate_mm=[260, 260],
                 ref_enclosure_mm_proxy_cc1=[398, 404, 490], ref_screen_in=5.0)

    # --- Estrutura: base, montantes arredondados, aro superior -----------------
    fr = Part("Frame_Structure", ["frame"])
    for sx in (-1, 1):
        for sy in (-1, 1):
            fr.box((POST, POST, CH_H), (sx * (HX - POST / 2), sy * (HY - POST / 2), CH_Z0 + CH_H / 2))
    zt = H - TOP / 2
    fr.box((W, 0.025, TOP), (0, -HY + 0.0125, zt))
    fr.box((W, 0.025, TOP), (0, HY - 0.0125, zt))
    fr.box((0.025, D - 0.05, TOP), (-HX + 0.0125, 0, zt))
    fr.box((0.025, D - 0.05, TOP), (HX - 0.0125, 0, zt))
    fr.build(root, bevel=0.004, segments=3, smooth=True)

    base = Part("Base_Housing", ["panel"])
    base.box((W, D, BASE_TOP - FOOT_H), (0, 0, (BASE_TOP + FOOT_H) / 2))
    base.build(root, bevel=0.005, segments=3, smooth=True)

    det = Part("Base_Details", ["plastic", "gold"])
    for sx in (-1, 1):                                      # fendas de ventilacao da base
        for i in range(9):
            det.box((0.0012, 0.090, 0.0035), (sx * (HX + 0.0003), 0.05, 0.030 + i * 0.0065))
    det.box((0.200, 0.0012, 0.0025), (-0.065, -HY - 0.0004, BASE_TOP - 0.016), "gold")  # friso
    for sx in (-1, 1):
        det.box((0.0025, 0.0012, CH_H - 0.05), (sx * (HX - POST / 2), -HY - 0.0004, CH_Z0 + CH_H / 2), "gold")
    det.build(root)

    feet = Part("Feet", ["rubber"])
    for sx in (-1, 1):
        for sy in (-1, 1):
            feet.cyl(0.016, FOOT_H, (sx * (HX - 0.045), sy * (HY - 0.045), FOOT_H / 2))
    feet.build(root, bevel=0.002, segments=2, smooth=True)

    # Tela 5" (16:9): area ativa ~111 x 62 mm
    scr = Part("Display_Screen", ["plastic", "screen"])
    scr.box((0.122, 0.006, 0.072), (HX - 0.085, -HY - 0.003, (FOOT_H + BASE_TOP) / 2))
    scr.box((0.111, 0.001, 0.062), (HX - 0.085, -HY - 0.0062, (FOOT_H + BASE_TOP) / 2), "screen")
    scr.build(root, bevel=0.002, segments=2)

    # --- Paineis: laterais e traseiro opacos com aberturas de ventilacao --------
    side_fan_c, fan_s = (-0.030, 0.300), 0.092
    exh_c = (0.0, 0.400)
    pn = Part("Side_Back_Panels", ["panel"])
    ys, zs = (-HY + POST, HY - POST), (CH_Z0, CH_Z1)
    panel_with_hole(pn, "YZ", -HX + 0.003, ys, zs, side_fan_c, fan_s, 0.004)        # esquerda
    pn.box((0.004, ys[1] - ys[0], CH_H), (HX - 0.003, 0, CH_Z0 + CH_H / 2))          # direita
    panel_with_hole(pn, "XZ", HY - 0.003, (-HX + POST, HX - POST), zs, exh_c, 0.080, 0.004)
    pn.build(root)

    fan("Aux_Side", (-HX + 0.003, *side_fan_c), "X", fan_s, root, outward=-1)
    fan("Exhaust", (exh_c[0], HY - 0.003, exh_c[1]), "Y", 0.080, root, outward=1)

    inner = Part("Chamber_Details", ["plastic", "led", "lens", "frame"])
    inner.box((0.120, 0.030, 0.090), (0, HY - 0.041, exh_c[1]))                      # filtro de carvao
    inner.box((0.300, 0.008, 0.003), (0, -HY + 0.030, CH_Z1 - 0.002), "led")         # LED da camara
    inner.box((0.034, 0.022, 0.024), (-HX + POST + 0.025, -HY + 0.030, CH_Z1 - 0.016))  # camera
    inner.cyl(0.006, 0.004, (-HX + POST + 0.025, -HY + 0.042, CH_Z1 - 0.016), axis="Y", mat="lens")
    for sx in (-1, 1):                                                              # motores XY
        inner.box((0.042, 0.042, 0.040), (sx * 0.135, HY - 0.027, GANTRY_Z + 0.002), "frame")
    inner.cyl(0.006, 0.020, (0.09, HY - 0.003, CH_Z1 - 0.03), axis="Y")              # entrada filamento
    inner.build(root, bevel=0.0015, segments=2)

    # --- Porta frontal (dobradica esquerda, abre para fora) --------------------
    door = empty("Door_Pivot", (-HX + POST, -HY, CH_Z0 + CH_H / 2), root,
                 anim="rotate", axis="y", range_rad=[-1.9, 0.0], hinge="left")
    dw, dz0, dz1 = W - 2 * POST - 0.002, CH_Z0 + 0.004, CH_Z1 - 0.002
    dx0 = -HX + POST + 0.001
    dcx, dcz, dh = dx0 + dw / 2, (dz0 + dz1) / 2, dz1 - dz0
    org = door.matrix_world.translation
    df = Part("Door_Frame", ["frame"])
    bw = 0.010
    df.box((dw, 0.008, bw), (dcx, -HY + 0.004, dz0 + bw / 2))
    df.box((dw, 0.008, bw), (dcx, -HY + 0.004, dz1 - bw / 2))
    df.box((bw, 0.008, dh - 2 * bw), (dx0 + bw / 2, -HY + 0.004, dcz))
    df.box((bw, 0.008, dh - 2 * bw), (dx0 + dw - bw / 2, -HY + 0.004, dcz))
    df.build(door, origin=org, bevel=0.0015, segments=2, smooth=True)
    dg = Part("Door_Glass", ["glass"])
    dg.box((dw - 2 * bw + 0.004, 0.004, dh - 2 * bw + 0.004), (dcx, -HY + 0.004, dcz))
    dg.build(door, origin=org)
    hd = Part("Door_Handle", ["gold"])
    hx_ = dx0 + dw - 0.028
    hd.box((0.010, 0.008, 0.180), (hx_, -HY - 0.008, dcz))
    for sz in (-1, 1):
        hd.box((0.008, 0.008, 0.010), (hx_, -HY - 0.002, dcz + sz * 0.080))
    hd.build(door, origin=org, bevel=0.002, segments=3, smooth=True)

    # --- Tampa de vidro (dobradica traseira, levanta a frente) -----------------
    lid = empty("Lid_Pivot", (0, HY - 0.025, H), root,
                anim="rotate", axis="x", range_rad=[-1.4, 0.0], hinge="back")
    lw, ld = W - 0.052, D - 0.052
    lg = Part("Lid_Glass", ["glass"])
    lg.box((lw, ld, 0.005), (0, 0, H - 0.0025))
    lg.build(lid, origin=lid.matrix_world.translation)
    lh = Part("Lid_Handle", ["gold"])
    lh.box((0.070, 0.010, 0.004), (0, -ld / 2 + 0.012, H + 0.002))
    lh.build(lid, origin=lid.matrix_world.translation, bevel=0.0015, segments=2, smooth=True)

    # --- Movimento CoreXY: trilhos e correias fixos ---------------------------
    rl = D - 2 * POST - 0.010
    rails = Part("Rails_Y", ["steel", "frame", "rubber"])
    for sx in (-1, 1):
        rails.cyl(0.005, rl, (sx * RAIL_X, 0, GANTRY_Z), axis="Y")
        for sy in (-1, 1):
            rails.box((0.024, 0.016, 0.028), (sx * RAIL_X, sy * (rl / 2 - 0.008), GANTRY_Z), "frame")
        rails.box((0.002, rl - 0.04, 0.006), (sx * (RAIL_X - 0.016), 0, GANTRY_Z + 0.012), "rubber")
    rails.build(root, bevel=0.001, segments=2)

    zs_ = Part("Z_Axis_Fixed", ["steel"])
    for sx in (-1, 1):
        top = GANTRY_Z - 0.030
        zs_.cyl(0.004, top - CH_Z0, (sx * SCREW_X, SCREW_Y, (top + CH_Z0) / 2), seg=16)
        zs_.cyl(0.004, top - CH_Z0, (sx * ROD_X, SCREW_Y, (top + CH_Z0) / 2), seg=16)
    zs_.build(root)

    travel = BUILD / 2
    gantry = empty("Gantry_Y_Mover", (0, 0, GANTRY_Z), root,
                   anim="translate", axis="z", range_m=[-travel, travel])
    gb = Part("Gantry_X_Beam", ["frame", "steel"])
    gb.box((2 * RAIL_X - 0.02, 0.020, 0.016), (0, 0, GANTRY_Z + 0.006))
    gb.box((2 * RAIL_X - 0.04, 0.012, 0.006), (0, -0.010, GANTRY_Z + 0.006), "steel")  # trilho linear
    for sx in (-1, 1):
        gb.box((0.032, 0.046, 0.032), (sx * RAIL_X, 0, GANTRY_Z))
    gb.build(gantry, origin=gantry.matrix_world.translation, bevel=0.0015, segments=2, smooth=True)

    tool = empty("Toolhead_X_Mover", (0, 0, GANTRY_Z), gantry,
                 anim="translate", axis="x", range_m=[-travel, travel])
    to = tool.matrix_world.translation
    th = Part("Toolhead", ["plastic", "gold", "frame", "steel", "brass"])
    th.box((0.064, 0.052, 0.078), (0, -0.016, GANTRY_Z - 0.018))                    # corpo
    th.box((0.064, 0.010, 0.020), (0, -0.032, GANTRY_Z - 0.062), "plastic")          # duto
    th.cyl(0.023, 0.002, (0, -0.0425, GANTRY_Z - 0.012), axis="Y", mat="gold")       # aro dourado
    th.cyl(0.020, 0.003, (0, -0.0430, GANTRY_Z - 0.012), axis="Y", mat="frame")      # recesso
    th.box((0.018, 0.016, 0.010), (0, -0.016, GANTRY_Z - 0.060), "steel")            # bloco aquecedor
    th.cyl(0.004, 0.010, (0, -0.016, GANTRY_Z - 0.0705), mat="brass", r2=0.0012, seg=16)
    th.build(tool, origin=to, bevel=0.003, segments=3, smooth=True)
    fan("Toolhead", (0, -0.0445, GANTRY_Z - 0.012), "Y", 0.036, tool, outward=-1)

    # --- Mesa (move em Z Blender = Y three) ----------------------------------
    bed = empty("Bed_Z_Mover", (0, 0, BED_REST), root, anim="translate", axis="y",
                range_m=[round(NOZZLE_TIP - BUILD - BED_REST, 4), round(NOZZLE_TIP - BED_REST, 4)])
    bo = bed.matrix_world.translation
    bp = Part("Bed_Plate", ["pei"])
    bp.box((PLATE, PLATE, 0.003), (0, 0, BED_REST - 0.0015))
    bp.box((0.040, 0.014, 0.003), (0, -PLATE / 2 - 0.007, BED_REST - 0.0015))       # aba frontal
    bp.build(bed, origin=bo, bevel=0.0012, segments=2)
    bc = Part("Bed_Carrier", ["alu", "frame", "gold"])
    bc.box((PLATE + 0.002, PLATE + 0.002, 0.008), (0, 0, BED_REST - 0.007))
    for sx in (-1, 1):
        y0, y1 = PLATE / 2 - 0.02, SCREW_Y + 0.012
        bc.box((0.070, y1 - y0, 0.012), (sx * 0.145, (y0 + y1) / 2, BED_REST - 0.017), "frame")
        bc.cyl(0.009, 0.016, (sx * SCREW_X, SCREW_Y, BED_REST - 0.017), mat="gold")  # porca
        bc.cyl(0.008, 0.022, (sx * ROD_X, SCREW_Y, BED_REST - 0.017), mat="frame")   # bucha
    bc.build(bed, origin=bo, bevel=0.0015, segments=2, smooth=True)

    return root


if __name__ == "__main__":
    os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
    root = build()
    bparts.export_hierarchy(root, OUT)
    meshes = [o for o in root.children_recursive if o.type == "MESH"]
    print(f"EXPORTED {OUT} meshes={len(meshes)}")
