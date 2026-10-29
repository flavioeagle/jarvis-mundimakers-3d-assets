# Asset: impressora fechada estilo Elegoo Centauri Carbon 2 (v1)

Asset web **inspirado** na CC2: sem logotipo, sem geometria copiada, layout interno aproximado.

| Item | Valor |
|---|---|
| GLB de runtime | `assets/printers/elegoo_cc2_v1.glb`: 172 276 bytes, SHA-256 `76b5602b…26063140` |
| Fonte | `scripts/printers/build_elegoo_cc2.py` + `scripts/lib/bparts.py` (procedural, reproduzível) |
| Geometria | 24 malhas, 41 primitivas, 33 nós, 13 060 triângulos, 13 materiais PBR |
| Extensões | `EXT_meshopt_compression`, `KHR_mesh_quantization`, `KHR_materials_transmission`, `KHR_materials_clearcoat`, `KHR_materials_emissive_strength` |
| Prévias | `docs/previews/elegoo_cc2_v1_{front34,front,top34}.png` (Cycles CPU, 96 amostras) |

## Fontes e o que é verificado
| Dado | Valor | Fonte | Status |
|---|---|---|---|
| Volume de impressão | 256 × 256 × 256 mm | [ELEGOO US](https://us.elegoo.com/collections/materials/products/centauri-carbon-2), [3dpros](https://3dpros.com/printers/elegoo-centauri-carbon-2) | publicado |
| Placa de impressão | 260 × 260 mm | [Kubii](https://www.kubii.com/en/3d-printers/4972-centauri-carbon-2-combo-3272496325586.html) | revenda |
| Tela | 5" touch colorida | [Micro Center](https://www.microcenter.com/quickview/704705/elegoo-centauri-carbon-2-combo-3d-printer), [3dwithus](https://3dwithus.com/elegoo-centauri-2-combo-overview) | publicado |
| Câmara fechada, câmera, LEDs, filtro de ar, refrigeração auxiliar | presentes | [filament2print](https://filament2print.com/en/filament-fdm/4034-elegoo-centauri-carbon-2-fdm-3d-printer.html), [all3dp (DE)](https://all3dp.com/de/4/neuer-elegoo-centauri-2-guenstiger-multicolor-3d-druck-aber-ohne-gehaeuse/) | publicado (sem posição exata) |
| Gabinete | 398 × 404 × 490 mm | spec oficial da Centauri Carbon 1ª ger.; a CC2 é descrita como mesma estrutura com eletrônica nova ([printer-hub](https://printer-hub.ru/en/posts/elegoo-centauri-carbon-vs-centauri-carbon-2)) | **proxy** |
| Combo 500 × 480 × 743 mm, 19,35 kg | inclui o módulo CANVAS | Micro Center, [Multitronic](https://www.multitronic.fi/en/products/4631262) | não modelado |

A posição de ventoinhas, câmera, LED, filtro, motores, fusos Z e as medidas do cabeçote são
**aproximações de design**. O site da ELEGOO e a análise da Fabbaloo estavam bloqueados pela rede
da sessão, então nada foi conferido por foto oficial.

## Hierarquia (eixos e cursos nos extras glTF, em coordenadas three.js)
```
CC2_Root
├── Frame_Structure  Base_Housing  Base_Details  Feet  Display_Screen  Side_Back_Panels
├── Chamber_Details (filtro, LED Chamber_LED, câmera Lens_Black, motores XY, entrada de filamento)
├── Rails_Y  Z_Axis_Fixed  Fan_Aux_Side_Frame  Fan_Exhaust_Frame
├── Fan_Aux_Side_Rotor_Pivot   spin x  → Fan_Aux_Side_Rotor
├── Fan_Exhaust_Rotor_Pivot    spin z  → Fan_Exhaust_Rotor
├── Door_Pivot   rotate y [-1.9, 0] rad → Door_Frame, Door_Glass, Door_Handle
├── Lid_Pivot    rotate x [-1.4, 0] rad → Lid_Glass, Lid_Handle
├── Gantry_Y_Mover  translate z ±0.128 m → Gantry_X_Beam
│   └── Toolhead_X_Mover  translate x ±0.128 m → Toolhead, Fan_Toolhead_Frame
│       └── Fan_Toolhead_Rotor_Pivot  spin z → Fan_Toolhead_Rotor
└── Bed_Z_Mover  translate y [-0.128, 0.128] m → Bed_Plate, Bed_Carrier
```
Pivôs são nós vazios. `extras` (`anim`, `axis`, `range_m` / `range_rad`, `rpm_hint`) viram
`userData` no three.js. Os cursos são relativos à pose de repouso.

## Pipeline
```bash
bash scripts/setup.sh --with-gltf-transform
B="blender -b --factory-startup --python-exit-code 1 --python"
$B scripts/printers/build_elegoo_cc2.py -- build/elegoo_cc2_v1.glb          # GLB bruto (484 KB, gitignored)
$B scripts/printers/validate_cc2.py     -- build/elegoo_cc2_v1.glb          # Blender: hierarquia, dims, materiais, pivôs
bash scripts/printers/optimize_glb.sh build/elegoo_cc2_v1.glb assets/printers/elegoo_cc2_v1.glb
node scripts/printers/check_runtime.mjs assets/printers/elegoo_cc2_v1.glb   # GLB final decodificado (meshopt)
.tools/node_modules/.bin/gltf-transform validate assets/printers/elegoo_cc2_v1.glb
$B scripts/printer/render_preview.py -- build/elegoo_cc2_v1.glb docs/previews 96 PNG
```
`optimize_glb.sh` faz `dedup → weld → prune(keep-leaves) → meshopt`. Ele **não** usa
`flatten`/`join`/`palette`/`instance`, que quebrariam os pivôs e os nomes de materiais.
O Blender 4.0 não lê meshopt, por isso a reimportação no Blender e a prévia usam o GLB
bruto (mesma geometria antes da quantização) e o GLB final é conferido pelo `check_runtime.mjs`.

## Resultado dos testes
| Teste | Resultado |
|---|---|
| Blender, GLB bruto | gabinete 0.398 × 0.404 × 0.490 m (±1 mm); total 0.401 × 0.423 × 0.494 m (puxadores, entrada de filamento); placa 0.260 m; 13/13 materiais; 8/8 pivôs com extras; porta abre para fora; tampa levanta |
| `check_runtime.mjs`, GLB final | 33 nós, 8 pivôs vazios com `extras.anim`, pais corretos, 0 materiais dupla-face, altura 0.494 m |
| `gltf-transform validate` 4.5.1 | 0 erros, 0 avisos |

## React Three Fiber
```jsx
const { scene, nodes } = useGLTF('/models/elegoo_cc2_v1.glb')   // drei decodifica meshopt por padrão
useFrame((_, dt) => {
  for (const n of ['Fan_Aux_Side_Rotor_Pivot', 'Fan_Exhaust_Rotor_Pivot', 'Fan_Toolhead_Rotor_Pivot'])
    nodes[n].rotation[nodes[n].userData.axis] += dt * (nodes[n].userData.rpm_hint / 60) * Math.PI * 2
})
```
Para porta, tampa, gantry, cabeçote e mesa, use o padrão de `docs/printer-prototype.md`
(interpolar dentro de `userData.range_*`, por ref, sem `setState`). LED e tela: altere
`emissiveIntensity` de `Chamber_LED` / `Screen_Emissive`.
