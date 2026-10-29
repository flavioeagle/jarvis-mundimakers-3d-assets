"""Gera um cubo de 10 cm e exporta para GLB.
Uso: blender -b --factory-startup --python scripts/make_test_cube.py -- <saida.glb>
"""
import sys
import bpy

out = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "assets/test/cube_10cm.glb"

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0

# size = aresta em metros (glTF usa metros): 0.1 m = 10 cm
bpy.ops.mesh.primitive_cube_add(size=0.1, location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "TestCube_10cm"

bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=False)
print(f"EXPORTED {out} dims={tuple(round(d, 4) for d in cube.dimensions)}")
