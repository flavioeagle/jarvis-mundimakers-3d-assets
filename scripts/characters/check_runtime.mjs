// Confere o GLB final (meshopt): skins, juntas, animacoes e materiais. Bbox com ossos: three_check.mjs.
// Uso: node scripts/characters/check_runtime.mjs <arquivo.glb> <NomeDoArmature>
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const here = path.dirname(fileURLToPath(import.meta.url));
const req = createRequire(path.join(here, '../../.tools/package.json'));
const { NodeIO } = req('@gltf-transform/core');
const { ALL_EXTENSIONS } = req('@gltf-transform/extensions');
const { MeshoptDecoder } = req('meshoptimizer');

await MeshoptDecoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.decoder': MeshoptDecoder });
const [file, rigName] = process.argv.slice(2);
const doc = await io.read(file);
const root = doc.getRoot();
const fail = [];
const names = new Set(root.listNodes().map((n) => n.getName()));

const skins = root.listSkins();                     // o exportador cria 1 skin por malha, mesmas juntas
if (!skins.length) fail.push('sem skin');
const key = (s) => s.listJoints().map((j) => j.getName()).join();
if (skins.some((s) => key(s) !== key(skins[0]))) fail.push('skins com juntas diferentes');
const joints = skins[0]?.listJoints().map((j) => j.getName()) ?? [];
for (const j of ['hips', 'head', 'hand.L', 'hand.R', 'foot.L', 'eye.L', 'mouth']) if (!joints.includes(j)) fail.push(`junta ${j} ausente`);
if (!names.has(rigName)) fail.push(`no ${rigName} ausente`);

const want = ['Idle', 'Working', 'AwaitingApproval', 'Done'];
const anims = Object.fromEntries(root.listAnimations().map((a) => [a.getName(), a]));
const animInfo = {};
for (const w of want) {
  const a = anims[w];
  if (!a) { fail.push(`animacao ${w} ausente`); continue; }
  const ch = a.listChannels();
  let dur = 0;
  for (const s of a.listSamplers()) { const t = s.getInput().getArray(); dur = Math.max(dur, t[t.length - 1]); }
  for (const s of a.listSamplers()) if ([...s.getOutput().getArray()].some((v) => !Number.isFinite(v))) fail.push(`${w}: valor invalido`);
  animInfo[w] = { channels: ch.length, seconds: +dur.toFixed(2) };
  if (!ch.length) fail.push(`${w} sem canais`);
}
const report = {
  file, nodes: root.listNodes().length, meshes: root.listMeshes().length, joints: joints.length,
  materials: root.listMaterials().length, doubleSided: root.listMaterials().filter((m) => m.getDoubleSided()).length,
  animations: animInfo, extensions: root.listExtensionsUsed().map((e) => e.extensionName), skins: skins.length, fail,
};
console.log('RUNTIME ' + JSON.stringify(report));
if (fail.length) process.exit(1);
