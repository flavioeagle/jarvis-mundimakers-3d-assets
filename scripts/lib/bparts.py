"""Helpers de modelagem procedural para Blender headless (sem operadores de viewport).

Part acumula primitivas num unico mesh (menos draw calls); coordenadas sao de mundo
e `origin` vira o pivo do objeto. Materiais vem do dict MAT, preenchido pelo script.
"""
import bmesh
import bpy
from mathutils import Euler, Vector

MAT = {}


def material(name, base, metallic=0.0, rough=0.5, transmission=0.0, ior=1.5,
             emission=None, strength=0.0, coat=0.0, sheen=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.use_backface_culling = True          # glTF doubleSided=false (malhas fechadas)
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*base, 1.0)
    p.inputs["Metallic"].default_value = metallic
    p.inputs["Roughness"].default_value = rough
    p.inputs["Transmission Weight"].default_value = transmission
    p.inputs["IOR"].default_value = ior
    p.inputs["Coat Weight"].default_value = coat
    p.inputs["Sheen Weight"].default_value = sheen        # tecidos -> KHR_materials_sheen
    if emission:
        p.inputs["Emission Color"].default_value = (*emission, 1.0)
        p.inputs["Emission Strength"].default_value = strength
    return m


class Part:
    def __init__(self, name, mats):
        self.name, self.keys, self.bm = name, list(mats), bmesh.new()

    def _place(self, verts, loc, rot, mat):
        m = Euler(rot).to_matrix() if rot else None
        for v in verts:
            v.co = (m @ v.co if m else v.co) + Vector(loc)
        idx = self.keys.index(mat or self.keys[0])
        for f in {f for v in verts for f in v.link_faces}:
            f.material_index = idx

    def box(self, size, loc, mat=None, rot=None):
        r = bmesh.ops.create_cube(self.bm, size=1.0)
        for v in r["verts"]:
            v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
        self._place(r["verts"], loc, rot, mat)

    def cyl(self, r, depth, loc, axis="Z", mat=None, r2=None, seg=24, rot=None):
        res = bmesh.ops.create_cone(self.bm, cap_ends=True, segments=seg, radius1=r,
                                    radius2=r if r2 is None else r2, depth=depth)
        base = {"Z": (0, 0, 0), "X": (0, 1.5707963, 0), "Y": (1.5707963, 0, 0)}[axis]
        m = Euler(base).to_matrix()
        for v in res["verts"]:
            v.co = m @ v.co
        self._place(res["verts"], loc, rot, mat)

    def sphere(self, r, loc, scale=(1, 1, 1), mat=None, rot=None, seg=24, rings=12):
        res = bmesh.ops.create_uvsphere(self.bm, u_segments=seg, v_segments=rings, radius=r)
        for v in res["verts"]:
            v.co = Vector((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2]))
        self._place(res["verts"], loc, rot, mat)

    def empty(self):
        return len(self.bm.verts) == 0

    def build(self, parent=None, origin=(0, 0, 0), bevel=0.0, segments=1, smooth=False):
        for v in self.bm.verts:
            v.co -= Vector(origin)
        me = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(me)
        self.bm.free()
        for k in self.keys:
            me.materials.append(MAT[k])
        ob = bpy.data.objects.new(self.name, me)
        bpy.context.scene.collection.objects.link(ob)
        ob.location = origin
        if parent:
            set_parent(ob, parent)
        if bevel:
            b = ob.modifiers.new("Bevel", "BEVEL")
            b.width, b.segments, b.limit_method = bevel, segments, "ANGLE"
            if smooth:
                me.use_auto_smooth = True          # Blender 4.0; 4.1+ usa Smooth by Angle
                b.harden_normals = True
        if smooth:
            me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
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
    """Parenteia mantendo a posicao de mundo (hierarquia so com translacoes)."""
    world = child.location.copy()
    child.parent = parent
    child.location = world - parent.matrix_world.translation
    bpy.context.view_layer.update()


def export_hierarchy(root, path):
    bpy.ops.object.select_all(action="DESELECT")
    for ob in [root, *root.children_recursive]:
        ob.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=path, export_format="GLB", use_selection=True,
        export_apply=True, export_extras=True,
        export_cameras=False, export_lights=False, export_animations=False,
        export_draco_mesh_compression_enable=False)
