"""Gerador de personagens estilizados (proporcao ~3 cabecas) com rig e animacoes para glTF.

Tecnica: corpo organico por Skin modifier + Subdivision sobre um esqueleto de vertices,
cabeca esculpida por deformacao de esfera, rosto posicionado por raycast na superficie,
cabelo em casca solidificada + mechas em curvas, roupas como cascas sobre o corpo.
Rig unico (mesmos nomes de ossos em todos os personagens) -> clipes reutilizaveis.

Eixos Blender: Z para cima, personagem olha para -Y, lado esquerdo = +X.
"""
import math

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector
from mathutils.bvhtree import BVHTree

from bparts import MAT, Part

HEAD_C = Vector((0, 0, 0.80))
HEAD_R = 0.155

# (nome, cabeca, cauda, pai, deform)
BONES = [
    ("root", (0, 0, 0), (0, 0, 0.10), None, False),
    ("hips", (0, 0, 0.40), (0, 0, 0.48), "root", True),
    ("spine", (0, 0, 0.48), (0, 0, 0.56), "hips", True),
    ("chest", (0, 0, 0.56), (0, 0, 0.63), "spine", True),
    ("neck", (0, 0, 0.63), (0, 0, 0.68), "chest", True),
    ("head", (0, 0, 0.68), (0, 0, 0.98), "neck", True),
    ("mouth", (0, -0.16, 0.715), (0, -0.19, 0.715), "head", False),
    ("brow.L", (0.058, -0.15, 0.845), (0.058, -0.18, 0.845), "head", False),
    ("brow.R", (-0.058, -0.15, 0.845), (-0.058, -0.18, 0.845), "head", False),
    ("eye.L", (0.058, -0.13, 0.79), (0.058, -0.16, 0.79), "head", False),
    ("eye.R", (-0.058, -0.13, 0.79), (-0.058, -0.16, 0.79), "head", False),
]
for s, sx in (("L", 1), ("R", -1)):
    BONES += [
        (f"upperarm.{s}", (sx * 0.095, 0, 0.615), (sx * 0.135, 0, 0.47), "chest", True),
        (f"forearm.{s}", (sx * 0.135, 0, 0.47), (sx * 0.15, -0.01, 0.355), f"upperarm.{s}", True),
        (f"hand.{s}", (sx * 0.15, -0.01, 0.355), (sx * 0.155, -0.014, 0.29), f"forearm.{s}", True),
        (f"thigh.{s}", (sx * 0.058, 0, 0.40), (sx * 0.062, 0, 0.22), "hips", True),
        (f"shin.{s}", (sx * 0.062, 0, 0.22), (sx * 0.063, 0, 0.065), f"thigh.{s}", True),
        (f"foot.{s}", (sx * 0.063, 0, 0.065), (sx * 0.063, -0.085, 0.025), f"shin.{s}", True),
    ]


# ---------------------------------------------------------------- utilidades
def link(ob):
    bpy.context.scene.collection.objects.link(ob)
    return ob


def bake(ob, name=None):
    """Aplica modificadores via depsgraph (sem operadores) e devolve novo objeto."""
    orig = ob.name
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    new = link(bpy.data.objects.new(name or ob.name, me))
    new.matrix_world = ob.matrix_world.copy()
    old = ob.data
    bpy.data.objects.remove(ob)
    if isinstance(old, bpy.types.Mesh) and old.users == 0:
        bpy.data.meshes.remove(old)
    elif isinstance(old, bpy.types.Curve) and old.users == 0:
        bpy.data.curves.remove(old)
    new.name = name or orig
    return new


def smooth(ob, subsurf=0):
    ob.data.polygons.foreach_set("use_smooth", [True] * len(ob.data.polygons))
    if subsurf:
        m = ob.modifiers.new("Sub", "SUBSURF")
        m.levels = m.render_levels = subsurf
        ob = bake(ob)
        ob.data.polygons.foreach_set("use_smooth", [True] * len(ob.data.polygons))
    return ob


def mesh_from_bm(name, bm, mats):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for k in mats:
        me.materials.append(MAT[k])
    return link(bpy.data.objects.new(name, me))


def tube(name, pts, r0, r1, mat, res=6, bevel_res=3, swell=0.0, flat=1.0):
    """Curva bezier suave com raio de r0 a r1 (+ swell no meio); flat<1 achata a secao."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth, cu.bevel_resolution, cu.resolution_u = 1.0, bevel_res, res
    cu.use_fill_caps = True
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(pts) - 1)
    n = len(pts) - 1
    for i, (bp, p) in enumerate(zip(sp.bezier_points, pts)):
        bp.co = Vector(p)
        bp.handle_left_type = bp.handle_right_type = "AUTO"
        u = i / n if n else 0
        bp.radius = r0 + (r1 - r0) * u + swell * math.sin(math.pi * u)
    if flat != 1.0:
        cu.bevel_mode = "PROFILE"
        cu.bevel_profile.preset = "SUPPORTS"     # perfil semi-plano (mecha achatada)
    ob = link(bpy.data.objects.new(name, cu))
    ob = bake(ob, name)
    ob.data.materials.append(MAT[mat])
    ob.data.polygons.foreach_set("use_smooth", [True] * len(ob.data.polygons))
    return ob


def join(name, obs):
    """Junta objetos (mesmos materiais podem repetir; viram slots)."""
    bm = bmesh.new()
    mats = []
    for o in obs:
        me = o.data.copy()
        me.transform(o.matrix_world)
        offset = len(mats)
        for m in me.materials:
            mats.append(m)
        tmp = bmesh.new()
        tmp.from_mesh(me)
        for f in tmp.faces:
            f.material_index += offset
        tmp.to_mesh(me)
        tmp.free()
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    for o in obs:
        bpy.data.objects.remove(o)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    uniq = []
    for m in mats:
        if m not in uniq:
            uniq.append(m)
    remap = [uniq.index(m) for m in mats]
    for m in uniq:
        me.materials.append(m)
    idx = [0] * len(me.polygons)
    me.polygons.foreach_get("material_index", idx)
    me.polygons.foreach_set("material_index", [remap[i] for i in idx])
    return link(bpy.data.objects.new(name, me))


class Surface:
    """Raycast contra uma malha para colar detalhes na superficie."""

    def __init__(self, obs):
        dg = bpy.context.evaluated_depsgraph_get()
        self.trees = [BVHTree.FromObject(o, dg) for o in obs]

    def hit(self, origin, direction):
        best = None
        for t in self.trees:
            r = t.ray_cast(Vector(origin), Vector(direction).normalized())
            if r[0] is not None and (best is None or r[3] < best[3]):
                best = r
        return best

    def front(self, x, z, push=0.0):
        """Ponto da face (olhando -Y) em (x, z) e normal."""
        h = self.hit((x, -1.0, z), (0, 1, 0))
        if h is None:
            raise RuntimeError(f"raycast falhou em x={x} z={z}")
        return h[0] + h[1] * push, h[1]

    def radial(self, theta, phi, push=0.0, center=HEAD_C):
        d = Vector((math.sin(theta) * math.sin(phi), -math.sin(theta) * math.cos(phi), math.cos(theta)))
        h = self.hit(center + d * 0.6, -d)
        if h is None:
            raise RuntimeError(f"radial falhou theta={theta} phi={phi}")
        return h[0] + h[1] * push, h[1]


def ring(surf, z, push=0.0, step=15):
    """Anel horizontal colado na superficie (pula angulos sem acerto)."""
    pts = []
    for a in range(0, 361, step):
        try:
            pts.append(surf.radial(math.pi / 2, math.radians(a), push, center=Vector((0, 0, z)))[0])
        except RuntimeError:
            pass
    return pts


# ---------------------------------------------------------------- corpo
def body_skeleton(cfg):
    """Vertices (pos, raio x/y) e arestas para o Skin modifier."""
    b = cfg.get("build", 1.0)            # largura do tronco
    hip = cfg.get("hip", 1.0)
    J = {
        "pelvis": ((0, 0, 0.40), (0.085 * hip, 0.068)),
        "waist": ((0, 0, 0.49), (0.068 * b, 0.055)),
        "chest": ((0, 0.003, 0.57), (0.084 * b, 0.062 * cfg.get("chest_d", 1.0))),
        "shoulders": ((0, 0.004, 0.615), (0.072 * b, 0.05)),
        "neck": ((0, 0.006, 0.70), (0.030, 0.030)),
    }
    E = [("pelvis", "waist"), ("waist", "chest"), ("chest", "shoulders"), ("shoulders", "neck")]
    for s, sx in (("L", 1), ("R", -1)):
        a = cfg.get("arm", 1.0)
        J.update({
            f"sh.{s}": ((sx * 0.098 * b, 0.004, 0.612), (0.033 * a, 0.033 * a)),
            f"el.{s}": ((sx * 0.135, 0, 0.47), (0.026 * a, 0.026 * a)),
            f"wr.{s}": ((sx * 0.150, -0.010, 0.358), (0.020, 0.019)),
            f"palm.{s}": ((sx * 0.153, -0.013, 0.330), (0.012, 0.024)),
            f"th.{s}": ((sx * 0.145, -0.036, 0.318), (0.0075, 0.0075)),
            f"hip.{s}": ((sx * 0.056, 0, 0.385), (0.046, 0.046)),
            f"kn.{s}": ((sx * 0.061, -0.003, 0.22), (0.036, 0.036)),
            f"an.{s}": ((sx * 0.063, 0.004, 0.072), (0.028, 0.028)),
            f"ball.{s}": ((sx * 0.063, -0.055, 0.034), (0.034, 0.030)),
            f"toe.{s}": ((sx * 0.063, -0.088, 0.030), (0.028, 0.024)),
        })
        E += [("shoulders", f"sh.{s}"), (f"sh.{s}", f"el.{s}"), (f"el.{s}", f"wr.{s}"),
              (f"wr.{s}", f"palm.{s}"), (f"palm.{s}", f"th.{s}"),
              ("pelvis", f"hip.{s}"), (f"hip.{s}", f"kn.{s}"), (f"kn.{s}", f"an.{s}"),
              (f"an.{s}", f"ball.{s}"), (f"ball.{s}", f"toe.{s}")]
        for i, y in enumerate((-0.030, -0.016, -0.002, 0.011)):        # dedos
            tip = f"f{i}.{s}"
            J[tip] = ((sx * 0.156, y - 0.012, 0.290 + (0.006 if i in (0, 3) else 0)), (0.0068, 0.0068))
            E.append((f"palm.{s}", tip))
    return J, E


def build_body(name, cfg):
    J, E = body_skeleton(cfg)
    bm = bmesh.new()
    lay = bm.verts.layers.skin.verify()
    idx = {}
    for k, (co, r) in J.items():
        v = bm.verts.new(co)
        v[lay].radius = r
        v[lay].use_root = k == "pelvis"
        idx[k] = v
    for a, b in E:
        bm.edges.new((idx[a], idx[b]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = link(bpy.data.objects.new(name, me))
    sk = ob.modifiers.new("Skin", "SKIN")
    sk.branch_smoothing, sk.use_smooth_shade = 0.6, True
    sub = ob.modifiers.new("Sub", "SUBSURF")
    sub.levels = sub.render_levels = 2
    ob = bake(ob, name)
    return smooth(ob)


def bone_segments():
    return {n: (Vector(h), Vector(t)) for n, h, t, _, d in BONES if d}


def seg_dist(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
    return (p - (a + ab * t)).length


def dominant_bone(p, segs):
    """Osso dominante por distancia normalizada pelo raio (ver BONE_R)."""
    return min(segs, key=lambda n: seg_dist(p, *segs[n]) / BONE_R[n.split(".")[0]])


def assign_regions(ob, region_of_bone, mats, extra=None):
    """Material por face segundo o osso dominante; extra(face_center, bone) pode sobrescrever."""
    for k in mats:
        ob.data.materials.append(MAT[k])
    segs = bone_segments()
    for f in ob.data.polygons:
        c = ob.matrix_world @ f.center
        bone = dominant_bone(c, segs)
        reg = region_of_bone(bone)
        if extra:
            reg = extra(c, bone) or reg
        f.material_index = mats.index(reg)


def shell(src, name, keep, offset, thickness, mat, cut=None):
    """Casca de roupa: copia as faces que satisfazem keep(center), afasta pela normal e solidifica."""
    me = src.data.copy()
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.normal_update()
    kill = [f for f in bm.faces if not keep(f.calc_center_median()) or (cut and cut(f.calc_center_median()))]
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    for v in bm.verts:
        v.co += v.normal * offset
    bm.to_mesh(me)
    bm.free()
    me.materials.clear()
    me.materials.append(MAT[mat])
    ob = link(bpy.data.objects.new(name, me))
    sol = ob.modifiers.new("Solid", "SOLIDIFY")
    sol.thickness, sol.offset, sol.use_even_offset = thickness, 1.0, True
    ob = bake(ob, name)                        # corpo ja vem subdividido; casca sem nova subdivisao
    return smooth(ob)


# ---------------------------------------------------------------- cabeca e rosto
def build_head(cfg):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=24, radius=HEAD_R)
    jaw = cfg.get("jaw", 0.22)
    for v in bm.verts:
        x, y, z = v.co
        y *= 0.93
        if z < 0:
            t = -z / HEAD_R
            x *= 1 - jaw * t ** 1.5
            y *= 1 - 0.10 * t
        if y > 0:
            y *= 1.06
        if y < 0 and abs(z) < 0.5 * HEAD_R:          # bochechas
            x *= 1 + 0.03 * (1 - abs(z) / (0.5 * HEAD_R))
        v.co = Vector((x, y, z)) + HEAD_C
    ob = mesh_from_bm("Head", bm, ["skin"])
    ob = smooth(ob, subsurf=1)
    return ob


def place(ob, loc, normal, tilt=0.0):
    """Orienta um objeto modelado olhando -Y para a normal da superficie."""
    yaw = math.atan2(normal.x, -normal.y)
    pitch = math.atan2(normal.z, math.hypot(normal.x, normal.y))
    ob.matrix_world = Matrix.Translation(loc) @ Euler((pitch, 0, yaw + tilt)).to_matrix().to_4x4()
    return ob


def build_eye(name, cfg, surf, x, z):
    loc, n = surf.front(x, z, push=-0.010)
    e = Part(name, ["sclera", "iris", "pupil", "glint"])
    w, h = cfg.get("eye_w", 1.0), cfg.get("eye_h", 1.25)
    e.sphere(0.026, (0, 0, 0), (w, 0.55, h), "sclera", seg=24, rings=16)
    e.sphere(0.0175, (0, -0.0105, -0.001), (w, 0.32, h * 0.95), "iris", seg=24, rings=12)
    e.sphere(0.0085, (0, -0.0142, -0.001), (w, 0.25, h * 0.95), "pupil", seg=16, rings=8)
    e.sphere(0.0052, (0.006 * (1 if x > 0 else -1) * -1 + 0.004, -0.0165, 0.008), (1, 0.4, 1), "glint", seg=12, rings=6)
    e.sphere(0.0024, (-0.005, -0.0165, -0.007), (1, 0.4, 1), "glint", seg=8, rings=4)
    ob = e.build(smooth=True)
    return place(ob, loc, n)


def arc(surf, x0, x1, zf, n=7, push=0.002):
    pts = []
    for i in range(n):
        t = i / (n - 1)
        x = x0 + (x1 - x0) * t
        p, _ = surf.front(x, zf(t, x), push)
        pts.append(p)
    return pts


def build_face(cfg, head):
    surf = Surface([head])
    parts = {}
    ex, ez = cfg.get("eye_x", 0.058), cfg.get("eye_z", 0.785)
    parts["eye.L"] = build_eye("Eye.L", cfg, surf, ex, ez)
    parts["eye.R"] = build_eye("Eye.R", cfg, surf, -ex, ez)
    lash = []
    for sx in (1, -1):                                   # palpebra superior / cilios
        pts = arc(surf, sx * (ex - 0.026), sx * (ex + 0.028),
                  lambda t, x: ez + 0.013 + 0.012 * math.sin(math.pi * t) - (0.004 * t if cfg.get("lash_flick") else 0),
                  n=6, push=0.004)
        if cfg.get("lash_flick"):
            p = pts[-1]
            pts.append(p + Vector((sx * 0.008, 0.002, 0.006)))
        lash.append(tube(f"Lash.{'L' if sx > 0 else 'R'}", pts, 0.0030, 0.0045 if cfg.get("lash_flick") else 0.0032, "lash", swell=0.0012))
    parts["lash"] = lash
    bz = cfg.get("brow_z", 0.845)
    for sx, s in ((1, "L"), (-1, "R")):
        pts = arc(surf, sx * 0.028, sx * 0.090, lambda t, x: bz + 0.010 * math.sin(math.pi * (0.25 + 0.7 * t)) - 0.006 * t, n=6)
        parts[f"brow.{s}"] = tube(f"Brow.{s}", pts, cfg.get("brow_w", 0.0042), 0.0022, "brow")
    mw, mz, sm = cfg.get("mouth_w", 0.026), cfg.get("mouth_z", 0.712), cfg.get("smile", 0.010)
    pts = arc(surf, -mw, mw, lambda t, x: mz + sm * (abs(x) / mw) ** 2 - sm * 0.2, n=9, push=0.001)
    mouth = [tube("Mouth", pts, 0.0026, 0.0026, "lip")]
    if cfg.get("lips"):
        lp = arc(surf, -mw * 0.55, mw * 0.55, lambda t, x: mz - 0.007 - 0.002 * math.sin(math.pi * t), n=7, push=0.0)
        mouth.append(tube("LowerLip", lp, 0.0038, 0.0038, "lipcolor"))
    parts["mouth"] = mouth
    nose_p, nose_n = surf.front(0, cfg.get("nose_z", 0.748), push=-0.004)
    nose = Part("Nose", ["skin"])
    nose.sphere(0.0115, (0, 0, 0), (1.0, 0.8, 0.85), seg=16, rings=8)
    parts["nose"] = place(nose.build(smooth=True), nose_p, nose_n)
    blush = Part("Blush", ["blush"])
    for sx in (1, -1):
        p, n = surf.front(sx * 0.082, 0.742, push=-0.0035)
        b = Part("tmp", ["blush"])
        b.sphere(0.017, (0, 0, 0), (1.1, 0.25, 0.65), seg=16, rings=8)
        o = place(b.build(smooth=True), p, n)
        blush.bm.from_mesh(_world_mesh(o))
        bpy.data.objects.remove(o)
    parts["blush"] = blush.build(smooth=True)
    ears = Part("Ears", ["skin"])
    for sx in (1, -1):
        ears.sphere(0.024, (sx * 0.146, 0.012, 0.785), (0.42, 0.75, 1.0), seg=16, rings=10,
                    rot=(0, 0, -sx * 0.25))
    parts["ears"] = ears.build(smooth=True)
    return parts, surf


def _world_mesh(o):
    me = o.data.copy()
    me.transform(o.matrix_world)
    return me


# ---------------------------------------------------------------- cabelo
def build_hair_cap(cfg, opening=0.42, ear_gap=True):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=24, radius=HEAD_R * 1.07)
    for v in bm.verts:
        x, y, z = v.co
        y *= 0.95
        if z < 0:
            t = -z / (HEAD_R * 1.07)
            x *= 1 - 0.18 * t ** 1.5
        if y > 0:
            y *= 1.08
        z = z * 1.03 if z > 0 else z
        v.co = Vector((x, y, z))
    R = HEAD_R
    kill = []
    for f in bm.faces:
        c = f.calc_center_median()
        face_open = c.y < -0.18 * R and c.z < opening * R
        ear = ear_gap and abs(c.x) > 0.70 * R and -0.45 * R < c.z < 0.15 * R and c.y < 0.30 * R
        low = c.z < -0.50 * R or (c.z < -0.25 * R and c.y < 0.2 * R)
        if face_open or ear or low:
            kill.append(f)
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    for v in bm.verts:
        v.co += HEAD_C
    ob = mesh_from_bm("Hair_Cap", bm, ["hair"])
    sol = ob.modifiers.new("Solid", "SOLIDIFY")
    sol.thickness, sol.offset = 0.010, 1.0
    sub = ob.modifiers.new("Sub", "SUBSURF")
    sub.levels = sub.render_levels = 1
    ob = bake(ob, "Hair_Cap")
    return smooth(ob)


def hair_strands(cap, targets, starts, push=0.0015, r0=0.002, r1=0.002, name="Hair_Strands", mat="hair", swell=0.0045):
    """Mechas que seguem a superficie da casca de cada inicio (theta, phi) ate um alvo."""
    surf = Surface([cap])
    obs = []
    for i, (t0, p0) in enumerate(starts):
        t1, p1 = targets(p0)
        pts = []
        n = 9
        for k in range(n):
            u = k / (n - 1)
            th = t0 + (t1 - t0) * u - 0.35 * math.sin(math.pi * u) * (1 - abs(math.sin(p0)) * 0.6)
            ph = p0 + (p1 - p0) * u
            try:
                pts.append(surf.radial(max(0.05, th), ph, push)[0])
            except RuntimeError:                       # sobre uma abertura da casca
                continue
        if len(pts) < 4:
            continue
        obs.append(tube(f"strand{i}", pts, r0, r1, mat, res=3, bevel_res=1, swell=swell))
    return join(name, obs)


# ---------------------------------------------------------------- rig
def build_armature(name):
    data = bpy.data.armatures.new(name + "_Rig")
    arm = link(bpy.data.objects.new(name, data))
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    for n, h, t, p, d in BONES:
        eb = data.edit_bones.new(n)
        eb.head, eb.tail, eb.roll = h, t, 0.0
        eb.use_deform = d
        if p:
            eb.parent = data.edit_bones[p]
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm


# raio aproximado da malha em volta de cada osso: a distancia e normalizada por ele, assim a
# lateral do tronco nao e capturada pelo braco (que esta mais perto em metros, mas e mais fino).
BONE_R = {"hips": 0.080, "spine": 0.065, "chest": 0.080, "neck": 0.032, "head": 0.032,
          "upperarm": 0.031, "forearm": 0.023, "hand": 0.020, "thigh": 0.043, "shin": 0.033, "foot": 0.030}


def skin_to(ob, arm, k=6.0, top=3):
    segs = bone_segments()
    rad = {n: BONE_R[n.split(".")[0]] for n in segs}
    groups = {n: ob.vertex_groups.new(name=n) for n in segs}
    for v in ob.data.vertices:
        p = ob.matrix_world @ v.co
        ws = sorted(((1.0 / max(seg_dist(p, *segs[n]) / rad[n], 0.05) ** k, n) for n in segs), reverse=True)[:top]
        tot = sum(w for w, _ in ws)
        for w, n in ws:
            if w / tot > 0.03:
                groups[n].add([v.index], w / tot, "REPLACE")
    ob.parent = arm
    mod = ob.modifiers.new("Armature", "ARMATURE")
    mod.object = arm


def attach(ob, arm, bone):
    """Objeto rigido seguindo um osso (vira filho do joint no glTF)."""
    bpy.context.view_layer.update()
    mw = ob.matrix_world.copy()
    ob.parent = arm
    ob.parent_type = "BONE"
    ob.parent_bone = bone
    bpy.context.view_layer.update()
    ob.matrix_world = mw


# ---------------------------------------------------------------- animacao
def make_action(arm, name, frames, keys, loop=True):
    """keys: {osso: [(frame, (rx, ry, rz) graus) | (frame, rot, loc) | (frame, rot, loc, scale)]}."""
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    arm.animation_data_create()
    arm.animation_data.action = act
    for pb in arm.pose.bones:
        pb.rotation_mode = "XYZ"
    for bone, ks in keys.items():
        pb = arm.pose.bones[bone]
        for k in ks:
            f, rot = k[0], k[1]
            pb.rotation_euler = [math.radians(a) for a in rot]
            pb.keyframe_insert("rotation_euler", frame=f)
            if len(k) > 2 and k[2] is not None:
                pb.location = k[2]
                pb.keyframe_insert("location", frame=f)
            if len(k) > 3:
                pb.scale = k[3]
                pb.keyframe_insert("scale", frame=f)
    act.frame_range = (1, frames)
    if loop:                                         # garante ciclo fechado
        for fc in act.fcurves:
            kp = fc.keyframe_points
            if kp and kp[0].co.x == 1 and kp[-1].co.x != frames:
                kp.insert(frames, kp[0].co.y)
    for pb in arm.pose.bones:
        pb.rotation_euler, pb.location, pb.scale = (0, 0, 0), (0, 0, 0), (1, 1, 1)
    track = arm.animation_data.nla_tracks.new()
    track.name = name
    track.strips.new(name, 1, act)
    arm.animation_data.action = None
    return act


def export_glb(path, roots):
    bpy.ops.object.select_all(action="DESELECT")
    for r in roots:
        for ob in [r, *r.children_recursive]:
            ob.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=path, export_format="GLB", use_selection=True,
        export_apply=False, export_extras=True, export_skins=True,
        export_animations=True, export_animation_mode="ACTIONS",
        export_force_sampling=True, export_optimize_animation_size=True,
        export_def_bones=False, export_cameras=False, export_lights=False,
        export_draco_mesh_compression_enable=False)
