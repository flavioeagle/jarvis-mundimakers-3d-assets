// Confere o GLB de runtime (meshopt) como o three.js vai le-lo: nos, pais, extras, materiais, bbox.
// Uso: node scripts/printers/check_runtime.mjs assets/printers/elegoo_cc2_v1.glb
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const here = path.dirname(fileURLToPath(import.meta.url));
const req = createRequire(path.join(here, '../../.tools/package.json'));
const { NodeIO } = req('@gltf-transform/core');
const { ALL_EXTENSIONS } = req('@gltf-transform/extensions');
const { getBounds } = req('@gltf-transform/core');
const { MeshoptDecoder } = req('meshoptimizer');

await MeshoptDecoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.decoder': MeshoptDecoder });
const file = process.argv[2];
const doc = await io.read(file);
const root = doc.getRoot();
const nodes = Object.fromEntries(root.listNodes().map((n) => [n.getName(), n]));
const parentOf = (n) => root.listNodes().find((p) => p.listChildren().includes(n))?.getName();
const fail = [];

const movers = {
  Door_Pivot: 'rotate', Lid_Pivot: 'rotate', Gantry_Y_Mover: 'translate', Toolhead_X_Mover: 'translate',
  Bed_Z_Mover: 'translate', Fan_Aux_Side_Rotor_Pivot: 'spin', Fan_Exhaust_Rotor_Pivot: 'spin',
  Fan_Toolhead_Rotor_Pivot: 'spin',
};
for (const [name, anim] of Object.entries(movers)) {
  const n = nodes[name];
  if (!n) { fail.push(`falta ${name}`); continue; }
  if (n.getExtras().anim !== anim) fail.push(`${name}.extras.anim != ${anim}`);
  if (n.getMesh()) fail.push(`${name} deveria ser vazio (pivo)`);
}
const parents = { Door_Glass: 'Door_Pivot', Toolhead: 'Toolhead_X_Mover', Toolhead_X_Mover: 'Gantry_Y_Mover',
  Bed_Plate: 'Bed_Z_Mover', Lid_Glass: 'Lid_Pivot', Fan_Toolhead_Rotor: 'Fan_Toolhead_Rotor_Pivot' };
for (const [c, p] of Object.entries(parents)) if (parentOf(nodes[c]) !== p) fail.push(`${c} deveria ser filho de ${p}`);

const scene = root.listScenes()[0];
const { min, max } = getBounds(scene);
const size = max.map((v, i) => +(v - min[i]).toFixed(4));          // three: x, y(altura), z(profundidade)
if (Math.abs(size[1] - 0.494) > 0.002) fail.push(`altura ${size[1]} != 0.494 (490 + puxador da tampa)`);

const mats = root.listMaterials().map((m) => m.getName());
const report = {
  file, nodes: root.listNodes().length, meshes: root.listMeshes().length,
  primitives: root.listMeshes().reduce((a, m) => a + m.listPrimitives().length, 0),
  materials: mats.length, doubleSided: root.listMaterials().filter((m) => m.getDoubleSided()).length,
  extensions: root.listExtensionsUsed().map((e) => e.extensionName), bbox_three_m: size, fail,
};
console.log('RUNTIME ' + JSON.stringify(report));
if (fail.length) process.exit(1);
