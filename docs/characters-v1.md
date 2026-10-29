# Funcionários de IA: Muse e Produção (v1)

| Personagem | GLB (meshopt) | Bruto | Triângulos | Malhas | Materiais | Juntas |
|---|---|---|---|---|---|---|
| Muse + estação de monitores | `assets/characters/muse_v1.glb` (529204 B) | 1,6 MB | 59 992 | 22 | 28 | 23 |
| Produção + bancada + impressora CC2 | `assets/characters/producao_v1.glb` (476896 B) | 1,4 MB | 48 432 (13 k da CC2) | 44 | 35 | 23 |

Prévias em `docs/previews/characters/`: `*_full.png`, `*_face.png`, `*_station.png` e `*_poses.png`
(Cycles CPU, renderizadas a partir do GLB exportado) e `*_threejs_poses.png` (o GLB **final** renderizado
no three.js r170 com GLTFLoader + MeshoptDecoder, em Chromium headless).

> Nenhuma imagem de referência foi anexada à sessão. Os personagens seguem só a descrição em texto.
> A fidelidade a uma referência visual **não foi avaliada**.

## Técnica
Escolhi modelagem procedural no Blender headless, com o gerador `scripts/lib/chibi.py`:
- **Corpo**: Skin modifier sobre um esqueleto de vértices, depois Subdivision. Gera uma malha orgânica contínua com dedos e pés, sem primitivos aparentes.
- **Cabeça**: esfera esculpida por deformação (mandíbula, bochechas, crânio). Olhos, cílios, sobrancelhas, nariz, boca, lábios e blush são posicionados por raycast na superfície do rosto.
- **Cabelo**: casca solidificada + mechas em curvas que seguem a superfície, com franja e coque.
- **Roupas**: cascas sobre o corpo (blazer aberto, colete refletivo), herdando o rig.
- **Rig único**: 23 ossos, os mesmos nos dois personagens, então os clipes são intercambiáveis. Os pesos são calculados por distância ao osso **normalizada pelo raio do membro**, para o braço não puxar o tronco.
- **Assets-base licenciados**: avaliados e não usados. Mixamo exige login Adobe e restringe redistribuição. Quaternius e Kenney ficam em hosts fora da rede liberada da sessão e não têm o estilo pedido.

## Hierarquia e contrato com o app
```
<Nome> (armature)            juntas: root, hips, spine, chest, neck, head, eye.L/R, brow.L/R, mouth,
│                             upperarm/forearm/hand.L/R, thigh/shin/foot.L/R
├── <Nome>_Body / _Blazer|_Vest / _Belt     malhas com skin
└── anexos rígidos nos ossos: Head, <Nome>_Hair, olhos (eye.*), cílios, sobrancelhas (brow.*),
    boca (mouth), headset/capacete (head), chave inglesa (hand.R), detalhes do colete (chest)
<Nome>_Station                 estação separada (pode ser reposicionada ou omitida)
```
Produção reaproveita o asset `elegoo_cc2_v1` inteiro (`CC2_Root` com os 8 pivôs animáveis) sobre a bancada.

## Animações (24 fps, loops fechados exceto Done)
| Clip | Duração | Muse | Produção |
|---|---|---|---|
| `Idle` | 3 s | respiração, balanço da cabeça, piscar | respiração, peso alternando, piscar |
| `Working` | 2 s | digitando, olhar nos monitores | gira o tronco para a impressora, gira a chave |
| `AwaitingApproval` | 3 s | acena, sobrancelhas erguidas, cabeça inclinada | acena com a mão esquerda, bate o pé |
| `Done` | 2 s | braços para cima, pulo, sorriso e olhos felizes | braço erguido, pulo, sorriso |

Expressões: piscar (escala Z de `eye.*`), sorriso aberto (escala de `mouth`), sobrancelhas (`brow.*`).

## Validação
| Teste | Muse | Produção |
|---|---|---|
| `validate_character.py` (Blender, GLB bruto): 23 ossos, pesos somando 1 em todos os vértices, anexos nos ossos certos, 4 clips sem NaN e com loops fechados | OK | OK |
| `check_runtime.mjs` (GLB final): skins com as mesmas juntas, 4 clips × 69 canais, 0 materiais dupla-face | OK | OK |
| `three_check.mjs` (three.js r170, Chromium): carrega, toca os 4 clips, bbox com skinning | 0,84 × 1,00 × 0,69 m | 1,01 × 1,05 × 0,51 m |
| `gltf-transform validate` | 0 erros, 3 avisos | 0 erros, 3 avisos |

Os avisos são `NODE_SKINNED_MESH_NON_ROOT`: as malhas com skin são filhas do nó do armature (padrão do
exportador do Blender). O three.js ignora o transform do pai nesses casos, e o resultado foi conferido no teste three.js acima.

## Pipeline
```bash
bash scripts/setup.sh --with-gltf-transform && npm install --prefix .tools --ignore-scripts three@0.170.0
B="blender -b --factory-startup --python-exit-code 1 --python"
$B scripts/characters/build_muse.py -- build/muse_v1.glb
$B scripts/characters/validate_character.py -- build/muse_v1.glb Muse
bash scripts/printers/optimize_glb.sh build/muse_v1.glb assets/characters/muse_v1.glb
node scripts/characters/check_runtime.mjs assets/characters/muse_v1.glb Muse
node scripts/characters/three_check.mjs assets/characters/muse_v1.glb build/three.png Working 0.8 _Station
$B scripts/characters/render_character.py -- build/muse_v1.glb out.png --action Done --frame 20 --hide-station
```
(Mesmo fluxo com `build_producao.py` / `Producao`.)

## React Three Fiber
```jsx
const { scene, animations } = useGLTF('/models/muse_v1.glb')        // drei já decodifica meshopt
const { actions } = useAnimations(animations, scene)
useEffect(() => { actions[state]?.reset().fadeIn(0.3).play(); return () => actions[state]?.fadeOut(0.3) }, [state])
// state: 'Idle' | 'Working' | 'AwaitingApproval' | 'Done'  (Done: setLoop(THREE.LoopOnce) + clampWhenFinished)
```
Para posicionar só o personagem, use `scene.getObjectByName('Muse')`. Para a mesa, `'Muse_Station'`.

## Limitações
- O estilo é chibi procedural. É detalhado e expressivo, mas **não chega ao nível de uma escultura feita por artista**: as mãos são simples, a roupa não tem dobras de tecido e não há texturas (só cores PBR).
- O cabelo é de mechas geométricas. É o maior custo da Muse, com cerca de 22 k triângulos.
- O pulso dobra bem, mas em ombros muito erguidos (`Done`) a manga afina, por causa dos pesos automáticos e da falta de ossos corretivos.
- Não há shape keys faciais: as expressões usam ossos (escala e posição), o que basta para piscar, sorrir e erguer as sobrancelhas.
- No `Working`, o técnico gesticula com a chave perto do rosto, e não dentro da impressora (não há IK).
- O sheen foi removido: o exportador do Blender 4.0 grava o tom branco e os tecidos ficavam acinzentados.
- As prévias Cycles têm ruído leve (o Blender do Ubuntu não traz OpenImageDenoise).
