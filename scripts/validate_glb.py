"""Reimporta o GLB no Blender e confere a geometria.
Uso: blender -b --factory-startup --python scripts/validate_glb.py -- <arquivo.glb> [aresta_m]
"""
import sys
import bpy

args = sys.argv[sys.argv.index("--") + 1:]
path = args[0]
expected = float(args[1]) if len(args) > 1 else 0.1

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=path)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
assert len(meshes) == 1, f"esperado 1 mesh, achou {len(meshes)}"
o = meshes[0]
dims = tuple(round(d, 4) for d in o.dimensions)
assert all(abs(d - expected) < 1e-4 for d in dims), f"dimensoes {dims} != {expected}"
# glTF triangula e separa vertices por face (normais planas): 24 v / 12 tri
assert len(o.data.vertices) in (8, 24) and len(o.data.polygons) in (6, 12), f"topologia inesperada: v={len(o.data.vertices)} f={len(o.data.polygons)}"
print(f"VALID {path} mesh={o.name} dims={dims} verts={len(o.data.vertices)} faces={len(o.data.polygons)}")
