"""Sala-vitrine isometrica (diorama) e props reutilizaveis para os agentes.

Convencao: piso interno em z = FLOOR; parede traseira em +Y, parede esquerda em -X;
frente (-Y) e direita (+X) de vidro, teto de vidro. Tudo em metros, Blender Z-up.
Props sao Parts (bparts) para juntar por material e reduzir draw calls.
"""
import math

from mathutils import Euler, Vector

from bparts import MAT, Part, empty, material

W, D, H = 1.20, 1.00, 1.00          # interno
BASE = 0.05                         # espessura da plataforma
FLOOR = BASE


def room_materials(wall, floor_a, floor_b, accent):
    """Materiais da sala; retorna dict de chaves adicionadas ao MAT."""
    glass = material("Vitrine_Glass", (0.55, 0.65, 0.75), rough=0.05)
    glass.blend_method = "BLEND"
    gp = glass.node_tree.nodes["Principled BSDF"]
    gp.inputs["Alpha"].default_value = 0.07
    gp.inputs["Specular IOR Level"].default_value = 0.25
    glass.use_backface_culling = False
    return {
        "v_glass": glass,
        "v_frame": material("Vitrine_Frame", (0.03, 0.032, 0.036), metallic=0.9, rough=0.3),
        "v_base": material("Vitrine_Base", (0.035, 0.036, 0.040), rough=0.4, coat=0.4),
        "v_wall": material("Room_Wall", wall, rough=0.8),
        "v_floor_a": material("Room_Floor_A", floor_a, rough=0.55),
        "v_floor_b": material("Room_Floor_B", floor_b, rough=0.55),
        "v_accent": material("Room_Accent", accent, rough=0.3, emission=accent, strength=3.0),
    }


def build_room(name, planks=True, strip=True):
    root = empty(f"{name}_Diorama", (0, 0, 0), role="diorama")
    hx, hy = W / 2, D / 2
    base = Part(f"{name}_Room_Base", ["v_base", "v_floor_a", "v_floor_b", "v_accent"])
    base.box((W + 0.04, D + 0.04, BASE), (0, 0, BASE / 2))
    n = 10
    for i in range(n):                                       # piso em tabuas / faixas
        y0 = -hy + i * D / n
        base.box((W, D / n - 0.002, 0.004), (0, y0 + D / (2 * n), BASE + 0.002),
                 "v_floor_a" if (i % 2 or not planks) else "v_floor_b")
    if strip:                                                # filete de luz na base
        base.box((W + 0.02, 0.004, 0.006), (0, -hy - 0.021, BASE * 0.55), "v_accent")
    base.build(root, bevel=0.003, segments=2)
    walls = Part(f"{name}_Room_Walls", ["v_wall", "v_frame"])
    walls.box((W, 0.03, H), (0, hy + 0.015, BASE + H / 2))
    walls.box((0.03, D + 0.03, H), (-hx - 0.015, 0.015, BASE + H / 2))
    walls.box((W + 0.03, 0.012, 0.03), (-0.015, hy, BASE + 0.015), "v_frame")          # rodapes
    walls.box((0.012, D, 0.03), (-hx, 0, BASE + 0.015), "v_frame")
    walls.build(root, bevel=0.002, segments=1)
    glass = Part(f"{name}_Vitrine_Glass", ["v_glass"])     # planos simples: 1 camada por lado
    z0, z1 = BASE, BASE + H
    for quad in (((-hx, -hy, z0), (hx, -hy, z0), (hx, -hy, z1), (-hx, -hy, z1)),
                 ((hx, -hy, z0), (hx, hy, z0), (hx, hy, z1), (hx, -hy, z1)),
                 ((-hx, -hy, z1), (hx, -hy, z1), (hx, hy, z1), (-hx, hy, z1))):
        glass.bm.faces.new([glass.bm.verts.new(v) for v in quad])
    glass.build(root)
    fr = Part(f"{name}_Vitrine_Frame", ["v_frame"])
    t = 0.022
    for x, y in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)):
        fr.box((t, t, H), (x, y, BASE + H / 2))
    for y in (-hy, hy):
        fr.box((W + t, t, t), (0, y, BASE + H))
    for x in (-hx, hx):
        fr.box((t, D + t, t), (x, 0, BASE + H))
    fr.box((W + t, t, t), (0, -hy, BASE + t / 2))
    fr.box((t, D + t, t), (hx, 0, BASE + t / 2))
    fr.build(root, bevel=0.003, segments=2, smooth=True)
    return root


# ------------------------------------------------------------------ props
def _rot(loc, yaw):
    R = Euler((0, 0, yaw)).to_matrix()
    return lambda x, y, z: tuple(Vector(loc) + R @ Vector((x, y, z)))


def desk(p, loc, w, d, h, yaw=0.0, top="desk_top", leg="desk_leg"):
    at = _rot(loc, yaw)
    r = (0, 0, yaw)
    p.box((w, d, 0.025), at(0, 0, h - 0.0125), top, r)
    for sx in (-1, 1):
        p.box((0.03, d - 0.04, h - 0.025), at(sx * (w / 2 - 0.03), 0, (h - 0.025) / 2), leg, r)
    p.box((w - 0.06, 0.012, h * 0.5), at(0, d / 2 - 0.02, h * 0.55), leg, r)


def chair(p, loc, yaw=0.0, seat=0.18, mat="chair", metal="desk_leg"):
    at = _rot(loc, yaw)
    r = (0, 0, yaw)
    p.box((0.17, 0.16, 0.035), at(0, 0, seat), mat, r)
    p.box((0.17, 0.03, 0.22), at(0, 0.085, seat + 0.13), mat, (math.radians(-8), 0, yaw))
    p.cyl(0.010, seat - 0.03, at(0, 0, (seat - 0.03) / 2 + 0.02), mat=metal, seg=12)
    for k in range(5):
        a = k * 2 * math.pi / 5 + yaw
        p.box((0.11, 0.016, 0.012), at(0.05 * math.cos(a), 0.05 * math.sin(a), 0.018), metal, (0, 0, a))
        p.sphere(0.009, at(0.10 * math.cos(a), 0.10 * math.sin(a), 0.009), mat=metal, seg=8, rings=4)


def screen_ui(p, at, r, w, h, kind, rnd):
    """Linhas de 'codigo' ou barras de grafico emissivas sobre a tela."""
    if kind == "code":
        rows = 9
        for i in range(rows):
            ind = (rnd(i) % 3) * 0.012
            lw = 0.04 + (rnd(i * 7) % 5) * 0.022
            m = ("ui_a", "ui_b", "ui_c")[rnd(i * 3) % 3]
            p.box((min(lw, w - ind - 0.02), 0.001, 0.006),
                  at(-w / 2 + 0.012 + ind + min(lw, w - ind - 0.02) / 2, -0.0062, h / 2 - 0.016 - i * (h - 0.03) / rows), m, r)
    else:
        for i in range(7):
            bh = (0.25 + (rnd(i * 5) % 7) / 10) * (h - 0.04)
            p.box((w / 10, 0.001, bh), at(-w / 2 + 0.03 + i * w / 8, -0.0062, -h / 2 + 0.02 + bh / 2),
                  ("ui_a", "ui_b")[i % 2], r)
        p.box((w - 0.03, 0.001, 0.004), at(0, -0.0062, h / 2 - 0.02), "ui_c", r)


def monitor(p, loc, yaw, w=0.22, h=0.14, kind="code", seed=1):
    """Monitor olhando para -Y local (gira com yaw)."""
    at = _rot(loc, yaw)
    r = (0, 0, yaw)
    rnd = lambda i: (i * 2654435761 + seed * 97) % 1000  # noqa: E731
    p.box((w + 0.012, 0.012, h + 0.012), at(0, 0, 0), "bezel", r)
    p.box((w, 0.001, h), at(0, -0.0062, 0), "screen", r)
    screen_ui(p, at, r, w, h, kind, rnd)
    p.box((0.016, 0.016, 0.10), at(0, 0.012, -h / 2 - 0.035), "bezel", r)
    p.box((0.08, 0.06, 0.006), at(0, 0.0, -h / 2 - 0.085), "bezel", r)


def laptop(p, loc, yaw, seed=3):
    at = _rot(loc, yaw)
    r = (0, 0, yaw)
    p.box((0.20, 0.14, 0.008), at(0, 0, 0.004), "laptop", r)
    lid = Euler((math.radians(-15), 0, yaw))
    R = lid.to_matrix()
    base = Vector(at(0, 0.07, 0.008))
    p.box((0.20, 0.006, 0.13), tuple(base + R @ Vector((0, 0, 0.065))), "laptop", (math.radians(-15), 0, yaw))
    p.box((0.19, 0.001, 0.12), tuple(base + R @ Vector((0, -0.0035, 0.065))), "screen", (math.radians(-15), 0, yaw))
    rnd = lambda i: (i * 2654435761 + seed * 97) % 1000  # noqa: E731
    for i in range(7):
        lw = 0.04 + (rnd(i) % 5) * 0.022
        p.box((lw, 0.001, 0.005), tuple(base + R @ Vector((-0.085 + lw / 2, -0.0042, 0.115 - i * 0.015))),
              ("ui_a", "ui_b", "ui_c")[i % 3], (math.radians(-15), 0, yaw))
    p.box((0.024, 0.001, 0.024), tuple(base + R @ Vector((0, 0.0035, 0.065))), "ui_c", (math.radians(-15), 0, yaw))


def keyboard(p, loc, yaw, rgb=False):
    at = _rot(loc, yaw)
    r = (0, 0, yaw)
    p.box((0.17, 0.055, 0.008), at(0, 0, 0.004), "bezel", r)
    for row in range(3):
        for c in range(11):
            m = "key" if not rgb else ("ui_a", "ui_b", "ui_c")[(c + row) % 3]
            p.box((0.011, 0.011, 0.004), at(-0.075 + c * 0.015, -0.017 + row * 0.016, 0.010), m, r)


def mug(p, loc, mat="mug"):
    p.cyl(0.016, 0.035, (loc[0], loc[1], loc[2] + 0.0175), mat=mat, seg=20)
    p.cyl(0.0135, 0.002, (loc[0], loc[1], loc[2] + 0.034), mat="coffee", seg=20)
    p.box((0.006, 0.012, 0.018), (loc[0] + 0.018, loc[1], loc[2] + 0.018), mat)


def can(p, loc, mat="can"):
    p.cyl(0.011, 0.04, (loc[0], loc[1], loc[2] + 0.02), mat=mat, seg=16)
    p.cyl(0.0105, 0.003, (loc[0], loc[1], loc[2] + 0.0415), mat="desk_leg", seg=16)


def plant(p, loc, s=1.0):
    p.cyl(0.03 * s, 0.05 * s, (loc[0], loc[1], loc[2] + 0.025 * s), mat="pot", r2=0.024 * s, seg=20)
    for k in range(8):
        a = k * 2 * math.pi / 8
        p.sphere(0.022 * s, (loc[0] + 0.02 * s * math.cos(a), loc[1] + 0.02 * s * math.sin(a), loc[2] + (0.07 + 0.012 * (k % 3)) * s),
                 (0.55, 0.55, 1.35), "leaf", (0.55 * math.sin(a), -0.55 * math.cos(a), 0), seg=10, rings=6)


def shelf(p, loc, w, books=6, yaw=0.0, seed=5):
    at = _rot(loc, yaw)
    r = (0, 0, yaw)
    p.box((w, 0.10, 0.012), at(0, 0, 0), "shelf", r)
    x = -w / 2 + 0.02
    for i in range(books):
        bw = 0.018 + ((i * 7 + seed) % 3) * 0.006
        bh = 0.07 + ((i * 5 + seed) % 4) * 0.012
        m = ("book_a", "book_b", "book_c", "book_d")[(i + seed) % 4]
        tilt = 0.25 if i == books - 1 else 0.0
        p.box((bw, 0.075, bh), at(x + bw / 2, 0, 0.006 + bh / 2), m, (0, tilt, yaw))
        x += bw + 0.002


def sticky_notes(p, wall_x=None, wall_y=None, center=(0, 0), n=6, seed=2, z0=0.6):
    for i in range(n):
        m = ("note_a", "note_b", "note_c")[(i + seed) % 3]
        dx = (i % 3) * 0.055 + ((i * 13 + seed) % 5) * 0.004
        dz = (i // 3) * 0.06 + ((i * 7 + seed) % 3) * 0.006
        rot = math.radians(((i * 17 + seed) % 11) - 5)
        if wall_y is not None:
            p.box((0.045, 0.002, 0.045), (center[0] + dx, wall_y - 0.002, z0 + dz), m, (0, rot, 0))
        else:
            p.box((0.002, 0.045, 0.045), (wall_x + 0.002, center[1] + dx, z0 + dz), m, (rot, 0, 0))


def desk_lamp(p, loc, yaw=0.0):
    at = _rot(loc, yaw)
    p.cyl(0.03, 0.01, at(0, 0, 0.005), mat="desk_leg", seg=20)
    p.box((0.008, 0.008, 0.14), at(0, 0, 0.075), "desk_leg", (0, math.radians(15), yaw))
    p.box((0.008, 0.008, 0.09), at(0.04, 0, 0.16), "desk_leg", (0, math.radians(-55), yaw))
    p.cyl(0.035, 0.04, at(0.08, 0, 0.165), mat="lamp_shade", r2=0.016, seg=20)
    p.sphere(0.014, at(0.08, 0, 0.15), mat="bulb", seg=12, rings=6)


def server_rack(p, loc, h=0.40):
    p.box((0.13, 0.15, h), (loc[0], loc[1], loc[2] + h / 2), "rack")
    for i in range(int(h / 0.04)):
        z = loc[2] + 0.03 + i * 0.04
        p.box((0.11, 0.002, 0.028), (loc[0], loc[1] - 0.076, z), "bezel")
        for k in range(4):
            p.box((0.006, 0.002, 0.006), (loc[0] - 0.04 + k * 0.012, loc[1] - 0.078, z), ("led_a", "led_b")[(i + k) % 2])


def cardboard_box(p, loc, s, yaw=0.0):
    at = _rot(loc, yaw)
    r = (0, 0, yaw)
    p.box(s, at(0, 0, s[2] / 2), "cardboard", r)
    p.box((s[0] + 0.001, 0.035, 0.0015), at(0, 0, s[2] + 0.0007), "tape", r)
    p.box((0.0015, 0.035, s[2] * 0.4), at(-s[0] / 2 - 0.0007, 0, s[2] * 0.8), "tape", r)


def prop_materials():
    return {
        "desk_top": material("Desk_Wood", (0.30, 0.17, 0.08), rough=0.45, coat=0.3),
        "desk_leg": material("Metal_Dark", (0.03, 0.032, 0.036), metallic=0.85, rough=0.35),
        "chair": material("Chair_Fabric", (0.03, 0.03, 0.035), rough=0.7),
        "bezel": material("Device_Black", (0.012, 0.012, 0.014), rough=0.35),
        "screen": material("Screen_Dark", (0.004, 0.006, 0.012), rough=0.15, emission=(0.02, 0.04, 0.10), strength=1.0),
        "ui_a": material("UI_Cyan", (0, 0, 0), emission=(0.20, 0.85, 1.0), strength=2.5),
        "ui_b": material("UI_Gold", (0, 0, 0), emission=(1.0, 0.68, 0.25), strength=2.5),
        "ui_c": material("UI_Magenta", (0, 0, 0), emission=(0.85, 0.30, 0.95), strength=2.5),
        "laptop": material("Laptop_Silver", (0.55, 0.56, 0.58), metallic=1.0, rough=0.3),
        "key": material("Keycap", (0.05, 0.05, 0.06), rough=0.5),
        "mug": material("Mug_White", (0.85, 0.83, 0.78), rough=0.25, coat=0.6),
        "coffee": material("Coffee", (0.05, 0.02, 0.01), rough=0.1),
        "can": material("Can_Red", (0.55, 0.03, 0.03), metallic=0.8, rough=0.25),
        "pot": material("Pot_Terracotta", (0.50, 0.20, 0.10), rough=0.7),
        "leaf": material("Plant_Leaf", (0.06, 0.26, 0.08), rough=0.5),
        "shelf": material("Shelf_Wood", (0.36, 0.21, 0.10), rough=0.5),
        "book_a": material("Book_Teal", (0.04, 0.25, 0.28), rough=0.6),
        "book_b": material("Book_Red", (0.40, 0.06, 0.05), rough=0.6),
        "book_c": material("Book_Cream", (0.70, 0.62, 0.45), rough=0.6),
        "book_d": material("Book_Navy", (0.03, 0.05, 0.15), rough=0.6),
        "note_a": material("Note_Yellow", (0.95, 0.80, 0.20), rough=0.8),
        "note_b": material("Note_Pink", (0.95, 0.40, 0.55), rough=0.8),
        "note_c": material("Note_Green", (0.45, 0.85, 0.40), rough=0.8),
        "lamp_shade": material("Lamp_Shade", (0.02, 0.02, 0.022), metallic=0.6, rough=0.4),
        "bulb": material("Lamp_Bulb", (1, 0.9, 0.7), emission=(1.0, 0.78, 0.45), strength=12.0),
        "rack": material("Rack_Black", (0.02, 0.02, 0.025), metallic=0.6, rough=0.4),
        "led_a": material("LED_Green", (0, 0, 0), emission=(0.2, 1.0, 0.4), strength=6.0),
        "led_b": material("LED_Blue", (0, 0, 0), emission=(0.2, 0.5, 1.0), strength=6.0),
        "cardboard": material("Cardboard", (0.45, 0.28, 0.13), rough=0.85),
        "tape": material("Tape", (0.60, 0.50, 0.35), rough=0.4, coat=0.5),
    }
