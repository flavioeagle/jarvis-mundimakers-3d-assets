// Carrega o GLB final no three.js r170 (GLTFLoader + MeshoptDecoder) num Chromium headless:
// confere clips, skinning (bbox com ossos aplicados) e salva um screenshot.
// Uso: node scripts/characters/three_check.mjs <glb> <saida.png> [anim] [t] [hideSufixo]
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const { chromium } = createRequire(import.meta.url)('playwright');
const [glb, out, anim = '', t = '0', hide = ''] = process.argv.slice(2);
const types = { '.html': 'text/html', '.js': 'text/javascript', '.glb': 'model/gltf-binary' };
const server = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(new URL(req.url, 'http://x').pathname));
  if (!p.startsWith(ROOT) || !fs.existsSync(p)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'content-type': types[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
}).listen(0, '127.0.0.1');
await new Promise((r) => server.once('listening', r));
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const page = await browser.newPage({ viewport: { width: 700, height: 700 } });
const qs = new URLSearchParams({ glb: '/' + glb, anim, t, hide });
await page.goto(`http://127.0.0.1:${server.address().port}/scripts/characters/three_check.html?${qs}`);
await page.waitForFunction(() => window.__result, null, { timeout: 120000 });
const result = await page.evaluate(() => window.__result);
if (out) await page.locator('canvas').screenshot({ path: out });
console.log('THREE ' + JSON.stringify({ glb, anim, ...result }));
await browser.close();
server.close();
if (!result.ok) process.exit(1);
