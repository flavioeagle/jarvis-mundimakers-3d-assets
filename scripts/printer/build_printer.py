"""Prototipo visual de impressora 3D fechada (inspirada na Elegoo Centauri Carbon 2).

Uso: blender -b --factory-startup --python scripts/printer/build_printer.py -- <saida.glb>

Medidas (metros, Blender Z-up; o exportador converte para glTF Y-up):
- Volume de impressao 256 x 256 x 256 mm: especificacao publicada da CC2 (loja ELEGOO).
- Gabinete 398 x 404 x 490 mm: medida oficial da Centauri Carbon (1a geracao),
  usada apenas como PROPORCAO. Nao ha medida externa oficial da CC2 confirmada.
- Demais medidas (perfis, cabecote, trilhos) sao aproximacoes de design, nao copias.

Contrato de nomes para o React Three Fiber (ver docs/printer-prototype.md):
  *_Mover / *_Pivot = Empties animaveis; extras glTF descrevem eixo e curso em
  coordenadas three.js (Y-up).
"""
import math
import sys

import bmesh
import bpy
from mathutils import Euler, Vector

OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "assets/printer/printer_proto_v001.glb"

# --- dimensoes ------------------------------------------------------------
W, D, H = 0.398, 0.404, 0.490          # gabinete (proporcao CC1)
BUILD = 0.256                           # volume de impressao (CC2)
POST = 0.022                            # perfil dos montantes
FOOT_H = 0.008
BASE_TOP = 0.075                        # topo da base (eletronica, display)
TOP_RING = 0.020                        # aro superior
CH_Z0, CH_Z1 = BASE_TOP, H - TOP_RING   # camara interna
GANTRY_Z = 0.440
NOZZLE_TIP = GANTRY_Z - 0.067           # ponta do bico (ver Toolhead)
BED_REST = 0.250                        # altura de repouso do topo da mesa
RAIL_X = 0.170                          # trilhos Y em x = +-RAIL_X


# --- materiais PBR --------------------------------------------------------
def material(name, base, metallic=0.0, rough=0.5, transmission=0.0, ior=1.5,
             emission=None, strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*base, 1.0)
    p.inputs["Metallic"].default_value = metallic
    p.inputs["Roughness"].default_value = rough
    p.inputs["Transmission Weight"].default_value = transmission
    p.inputs["IOR"].default_value = ior
    if emission:
        p.inputs["Emission Color"].default_value = (*emission, 1.0)
        p.inputs["Emission Strength"].default_value = strength
    return m


MAT = {}


def make_materials():
    return {
    "dark": material("Metal_Dark", (0.035, 0.037, 0.040), metallic=0.85, rough=0.38),
    "rail": material("Metal_Rail", (0.62, 0.63, 0.65), metallic=1.0, rough=0.22),
    "glass": material("Glass_Smoked", (0.42, 0.45, 0.48), rough=0.03, transmission=1.0, ior=1.5),
    "gold": material("Gold_Accent", (0.78, 0.60, 0.32), metallic=1.0, rough=0.32),
    "plastic": material("Plastic_Black", (0.018, 0.018, 0.020), rough=0.55),
    "bed": material("Bed_PEI", (0.10, 0.10, 0.11), metallic=0.3, rough=0.62),
    "rubber": material("Rubber", (0.01, 0.01, 0.01), rough=0.9),
    "screen": material("Screen_Emissive", (0.02, 0.02, 0.03), rough=0.2,
                       emission=(0.35, 0.55, 0.9), strength=1.5),
}


# --- construcao por bmesh (sem operadores de viewport) ---------------------
class Part:
    """Acumula primitivas num unico mesh (menos draw calls)."""

    def __init__(self, name, mats):
        self.name, self.mats, self.bm = name, [MAT[k] for k in mats], bmesh.new()
        self.keys = list(mats)

    def _tag(self, verts, mat):
        idx = self.keys.index(mat)
        for f in {f for v in verts for f in v.link_faces}:
            f.material_index = idx

    def box(self, size, loc, mat=None):
        mat = mat or self.keys[0]
        r = bmesh.ops.create_cube(self.bm, size=1.0)
        for v in r["verts"]:
            v.co = (v.co.x * size[0] + loc[0], v.co.y * size[1] + loc[1], v.co.z * size[2] + loc[2])
        self._tag(r["verts"], mat)

    def cyl(self, r, depth, loc, axis="Z", mat=None, r2=None, seg=24):
        mat = mat or self.keys[0]
        res = bmesh.ops.create_cone(self.bm, cap_ends=True, segments=seg,
                                    radius1=r, radius2=r if r2 is None else r2, depth=depth)
        rot = {"Z": None, "X": (0, math.pi / 2, 0), "Y": (math.pi / 2, 0, 0)}[axis]
        m = Euler(rot).to_matrix() if rot else None
        for v in res["verts"]:
            v.co = (m @ v.co if m else v.co) + Vector(loc)
        self._tag(res["verts"], mat)

    def build(self, parent=None, origin=(0, 0, 0), bevel=0.0015):
        """Cria o objeto. Coordenadas das primitivas sao de mundo; origin vira o pivo."""
        for v in self.bm.verts:
            v.co -= Vector(origin)
        me = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(m)
        ob = bpy.data.objects.new(self.name, me)
        bpy.context.scene.collection.objects.link(ob)
        ob.location = origin
        if parent:
            set_parent(ob, parent)
        if bevel:
            b = ob.modifiers.new("Bevel", "BEVEL")
            b.width, b.segments, b.limit_method = bevel, 1, "ANGLE"
        return ob


def empty(name, loc, parent=None, **extras):
    ob = bpy.data.objects.new(name, None)
    ob.empty_display_type, ob.empty_display_size = "ARROWS", 0.05
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    if parent:
        set_parent(ob, parent)
    for k, v in extras.items():
        ob[k] = v
    return ob


def set_parent(child, parent):
    """Parenteia mantendo a posicao de mundo (origens em coords de mundo)."""
    world = child.location.copy()
    child.parent = parent
    child.location = world - parent.matrix_world.translation
    bpy.context.view_layer.update()


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    MAT.update(make_materials())
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"

    root = empty("Printer_Root", (0, 0, 0),
                 ref_build_volume_mm=[256, 256, 256],
                 ref_enclosure_mm_proxy_cc1=[398, 404, 490],
                 units="meters", up_axis="Y")
    bpy.context.view_layer.update()

    hx, hy = W / 2, D / 2
    ch_h = CH_Z1 - CH_Z0

    # Estrutura fixa (metal escuro)
    f = Part("Frame_Structure", ["dark"])
    f.box((W, D, BASE_TOP - FOOT_H), (0, 0, (BASE_TOP + FOOT_H) / 2))           # base
    for sx in (-1, 1):
        for sy in (-1, 1):
            f.box((POST, POST, ch_h), (sx * (hx - POST / 2), sy * (hy - POST / 2), CH_Z0 + ch_h / 2))
    zt = H - TOP_RING / 2
    f.box((W, 0.025, TOP_RING), (0, -hy + 0.0125, zt))
    f.box((W, 0.025, TOP_RING), (0, hy - 0.0125, zt))
    f.box((0.025, D, TOP_RING), (-hx + 0.0125, 0, zt))
    f.box((0.025, D, TOP_RING), (hx - 0.0125, 0, zt))
    f.box((W - 2 * POST, 0.006, ch_h), (0, hy - 0.003, CH_Z0 + ch_h / 2))           # painel traseiro
    f.box((W - 2 * POST, 0.012, 0.010), (0, -hy + 0.006, CH_Z0 + 0.005))              # soleira da porta
    f.build(root)

    feet = Part("Feet", ["rubber"])
    for sx in (-1, 1):
        for sy in (-1, 1):
            feet.cyl(0.014, FOOT_H, (sx * (hx - 0.04), sy * (hy - 0.04), FOOT_H / 2))
    feet.build(root, bevel=0)

    # Detalhes dourados discretos
    g = Part("Trim_Gold", ["gold"])
    g.box((W - 0.08, 0.0015, 0.003), (0, -hy - 0.00075, BASE_TOP - 0.012))           # friso frontal
    for sx in (-1, 1):
        g.box((0.0025, 0.0015, ch_h - 0.04), (sx * (hx - POST / 2), -hy - 0.00075, CH_Z0 + ch_h / 2))
    g.build(root, bevel=0)

    # Display frontal
    s = Part("Display_Screen", ["plastic", "screen"])
    s.box((0.090, 0.004, 0.042), (hx - 0.085, -hy - 0.002, 0.040))
    s.box((0.080, 0.001, 0.034), (hx - 0.085, -hy - 0.0045, 0.040), "screen")
    s.build(root, bevel=0.0008)

    # Paineis de vidro laterais (fixos)
    gl = Part("Glass_Side_Panels", ["glass"])
    for sx in (-1, 1):
        gl.box((0.004, D - 2 * POST, ch_h), (sx * (hx - 0.006), 0, CH_Z0 + ch_h / 2))
    gl.build(root, bevel=0)

    # Porta frontal: dobradica na aresta esquerda; abre para fora (+Z three).
    door = empty("Door_Pivot", (-hx + POST, -hy, CH_Z0 + ch_h / 2), root,
                 anim="rotate", axis="y", range_rad=[-1.9, 0.0], hinge="left")
    dg = Part("Door_Glass", ["glass"])
    dw, dz0, dz1 = W - 2 * POST - 0.002, CH_Z0 + 0.011, CH_Z1 - 0.002   # entre montantes, acima da soleira
    dg.box((dw, 0.005, dz1 - dz0), (-hx + POST + 0.001 + dw / 2, -hy + 0.0025, (dz0 + dz1) / 2))
    dg.build(door, origin=door.matrix_world.translation, bevel=0)
    dh = Part("Door_Handle", ["gold"])
    dh.box((0.010, 0.008, 0.160), (hx - POST - 0.015, -hy - 0.004, CH_Z0 + ch_h / 2))
    dh.build(door, origin=door.matrix_world.translation, bevel=0.002)

    # Tampa de vidro: dobradica na traseira; abre levantando a frente.
    lid = empty("Lid_Pivot", (0, hy - 0.025, H), root,
                anim="rotate", axis="x", range_rad=[-1.4, 0.0], hinge="back")
    lg = Part("Lid_Glass", ["glass"])
    lg.box((W - 0.05, D - 0.05, 0.005), (0, 0, H - 0.0025))
    lg.build(lid, origin=lid.matrix_world.translation, bevel=0)

    # Trilhos Y fixos + fusos Z
    r = Part("Rails_Y", ["rail", "dark"])
    rl = D - 2 * POST - 0.01
    for sx in (-1, 1):
        r.cyl(0.005, rl, (sx * RAIL_X, 0, GANTRY_Z), axis="Y")
        for sy in (-1, 1):
            r.box((0.022, 0.016, 0.026), (sx * RAIL_X, sy * (rl / 2 - 0.008), GANTRY_Z), "dark")
    r.build(root, bevel=0.001)

    z = Part("Z_Lead_Screws", ["rail"])
    for sx in (-1, 1):
        z.cyl(0.004, GANTRY_Z - 0.02 - CH_Z0, (sx * 0.150, hy - 0.035, (GANTRY_Z - 0.02 + CH_Z0) / 2), seg=16)
    z.build(root, bevel=0)

    # Gantry (move em Y) -> cabecote (move em X)
    travel = BUILD / 2
    gantry = empty("Gantry_Y_Mover", (0, 0, GANTRY_Z), root,
                   anim="translate", axis="z", range_m=[-travel, travel])
    gb = Part("Gantry_X_Beam", ["rail", "dark"])
    gb.box((2 * RAIL_X - 0.02, 0.018, 0.012), (0, 0, GANTRY_Z + 0.004))
    for sx in (-1, 1):
        gb.box((0.030, 0.040, 0.030), (sx * RAIL_X, 0, GANTRY_Z), "dark")
    gb.build(gantry, origin=gantry.matrix_world.translation, bevel=0.001)

    tool = empty("Toolhead_X_Mover", (0, 0, GANTRY_Z), gantry,
                 anim="translate", axis="x", range_m=[-travel, travel])
    t = Part("Toolhead", ["plastic", "gold", "dark"])
    t.box((0.060, 0.050, 0.070), (0, -0.012, GANTRY_Z - 0.020))                       # corpo
    t.box((0.050, 0.0015, 0.003), (0, -0.0378, GANTRY_Z - 0.048), "gold")              # friso
    t.cyl(0.016, 0.004, (0, -0.0385, GANTRY_Z - 0.015), axis="Y", mat="dark")          # ventoinha
    t.cyl(0.004, 0.012, (0, -0.012, GANTRY_Z - 0.061), mat="gold", r2=0.0012, seg=16)  # bico latao
    t.build(tool, origin=tool.matrix_world.translation, bevel=0.002)

    # Mesa (move em Z Blender = Y three)
    bed = empty("Bed_Z_Mover", (0, 0, BED_REST), root,
                anim="translate", axis="y",
                range_m=[round(NOZZLE_TIP - BUILD - BED_REST, 4), round(NOZZLE_TIP - BED_REST, 4)])
    bp = Part("Bed_Plate", ["bed"])
    bp.box((BUILD + 0.010, BUILD + 0.010, 0.004), (0, 0, BED_REST - 0.002))
    bp.build(bed, origin=bed.matrix_world.translation, bevel=0.001)
    bc = Part("Bed_Carrier", ["dark", "gold"])
    bc.box((BUILD, BUILD, 0.010), (0, 0, BED_REST - 0.009))
    bc.box((0.32, 0.030, 0.010), (0, hy - 0.035, BED_REST - 0.014))                    # bracos ate os fusos
    for sx in (-1, 1):
        bc.box((0.040, hy - 0.035 - BUILD / 2 + 0.02, 0.010),
               (sx * 0.110, (hy - 0.035 + BUILD / 2 - 0.02) / 2, BED_REST - 0.014))
        bc.cyl(0.009, 0.014, (sx * 0.150, hy - 0.035, BED_REST - 0.014), mat="gold")   # porcas
    bc.build(bed, origin=bed.matrix_world.translation)

    return root


def export(root, path):
    bpy.ops.object.select_all(action="DESELECT")
    for ob in [root, *root.children_recursive]:
        ob.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=path, export_format="GLB", use_selection=True,
        export_apply=True, export_extras=True,
        export_cameras=False, export_lights=False, export_animations=False,
        export_draco_mesh_compression_enable=False)


if __name__ == "__main__":
    root = build()
    export(root, OUT)
    meshes = [o for o in root.children_recursive if o.type == "MESH"]
    print(f"EXPORTED {OUT} meshes={len(meshes)}")
