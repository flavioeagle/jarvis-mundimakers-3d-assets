# Protótipo: impressora 3D fechada (v001)

Inspirada na Elegoo Centauri Carbon 2. **Não é réplica.** É um protótipo visual com
proporções coerentes, sem logotipos e sem geometria copiada.

- GLB: `assets/printer/printer_proto_v001.glb` (164 404 bytes)
- Fonte: `scripts/printer/build_printer.py` (100% procedural, reproduzível)
- Prévias: `docs/previews/printer_proto_v001_{front34,front,top34}.jpg`

## Referências de medida
| Medida | Valor | Fonte | Uso no modelo |
|---|---|---|---|
| Volume de impressão CC2 | 256 × 256 × 256 mm | [ELEGOO US store](https://us.elegoo.com/collections/materials/products/centauri-carbon-2), [3dpros](https://3dpros.com/printers/elegoo-centauri-carbon-2) | Mesa 266 mm (256 + margem) e curso X/Y/Z de 256 mm |
| Gabinete Centauri Carbon (1ª geração) | 398 × 404 × 490 mm | Especificação oficial da CC1 | **Proporção** do gabinete (L × P × A) |
| Gabinete CC2 | não confirmado | Só há listagens de revenda (ex.: 500 × 480 × 743 mm no Combo, que inclui o módulo de filamentos) | Não usado |

Perfis, cabeçote, trilhos, base e display são **aproximações de design**. Ajuste as
constantes no topo de `build_printer.py` quando houver medidas oficiais da CC2.

## Hierarquia (contrato de nomes com o viewer)
```
Printer_Root                       extras: ref_build_volume_mm, ref_enclosure_mm_proxy_cc1
├── Frame_Structure                Metal_Dark (base, montantes, aro superior, painel traseiro)
├── Feet                           Rubber
├── Trim_Gold                      Gold_Accent (frisos discretos)
├── Display_Screen                 Plastic_Black + Screen_Emissive
├── Glass_Side_Panels              Glass_Smoked
├── Rails_Y                        Metal_Rail + Metal_Dark (fixos)
├── Z_Lead_Screws                  Metal_Rail (fixos)
├── Door_Pivot      ⟲ rotate y  [-1.9, 0] rad  (dobradiça esquerda, abre para fora)
│   ├── Door_Glass
│   └── Door_Handle                Gold_Accent
├── Lid_Pivot       ⟲ rotate x  [-1.4, 0] rad  (dobradiça traseira, levanta a frente)
│   └── Lid_Glass
├── Gantry_Y_Mover  ↔ translate z  [-0.128, 0.128] m
│   ├── Gantry_X_Beam
│   └── Toolhead_X_Mover  ↔ translate x  [-0.128, 0.128] m
│       └── Toolhead               Plastic_Black + Gold_Accent (bico latão) + Metal_Dark
└── Bed_Z_Mover     ↕ translate y  [-0.133, 0.123] m  (0.123 = mesa no bico)
    ├── Bed_Plate                  Bed_PEI
    └── Bed_Carrier                Metal_Dark + Gold_Accent (porcas)
```
Eixos e cursos estão nos **extras glTF** de cada Empty (`anim`, `axis`, `range_m`/`range_rad`)
em coordenadas three.js (Y para cima, metros), relativos à pose de repouso. Em R3F eles
viram `object.userData`.

14 malhas, 20 nós, 2 868 triângulos, 8 materiais PBR.
Extensões: `KHR_materials_transmission` (vidro) e `KHR_materials_emissive_strength` (display).

## Validação
| Teste | Resultado |
|---|---|
| Reimportação no Blender (`validate_printer.py`) | OK: 14 malhas, nós e materiais esperados, extras presentes |
| Dimensões do gabinete | 0.398 × 0.404 × 0.490 m (tolerância 1 mm) |
| Total com protrusões | 0.398 × 0.412 × 0.490 m (puxador e display saem 8 mm da frente) |
| Sentido dos pivôs | Porta abre para fora e tampa levanta (testado aplicando `range_rad[0]`) |
| `gltf-transform validate` 4.5.1 | 0 erros, 0 avisos, 0 infos, 0 hints |

## Boas práticas aplicadas (revisão dos SKILL.md, sem executar scripts)
De [czlonkowski/blender-web-3d-skill](https://github.com/czlonkowski/blender-web-3d-skill):
- Pipeline headless reproduzível: o modelo é um script, não um .blend editado à mão.
- Nomes de materiais e pivôs são o contrato entre o modelo e o viewer.
- Exportação limitada à hierarquia do root, sem câmeras e luzes, com `export_apply` e `export_extras`.
- Peças móveis são Empties `*_Mover` / `*_Pivot`, porque drivers não exportam.
- Partes estáticas agrupadas por mesh (menos draw calls); as móveis ficam separadas.
- Vidro com Transmission + IOR → `KHR_materials_transmission`.
- Conferir renderizando: a prévia é renderizada a partir do GLB exportado.
- Ainda **não** otimizado (meshopt/Draco): risco de `flatten`/`palette` quebrarem pivôs e nomes. Se otimizar, nunca use `flatten` nem `palette`.

De [emalorenzo/three-agent-skills](https://github.com/emalorenzo/three-agent-skills) (r3f-best-practices):
- `useGLTF` + `useGLTF.preload`, dentro de `<Suspense>`.
- Animar por ref no `useFrame` usando `delta`, nunca com `setState`.
- `frameloop="demand"` + `invalidate()` quando a impressora estiver parada.
- `<Environment>` do drei para os reflexos do metal e do vidro.

## Integração React Three Fiber
Copie o GLB para `public/models/printer_proto_v001.glb`.

```jsx
import { useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import { useGLTF } from '@react-three/drei'

const URL = '/models/printer_proto_v001.glb'

export function Printer({ doorOpen = 0, lidOpen = 0, printing = true }) {
  const { scene, nodes } = useGLTF(URL)
  const t = useRef(0)
  useFrame((_, delta) => {
    t.current += delta
    const lerp = (r, k) => r[0] + (r[1] - r[0]) * k   // k em 0..1
    const door = nodes.Door_Pivot, lid = nodes.Lid_Pivot
    door.rotation.y = lerp(door.userData.range_rad, 1 - doorOpen)
    lid.rotation.x = lerp(lid.userData.range_rad, 1 - lidOpen)
    if (printing) {
      const s = Math.sin(t.current * 2) * 0.5 + 0.5
      nodes.Toolhead_X_Mover.position.x = lerp(nodes.Toolhead_X_Mover.userData.range_m, s)
      nodes.Gantry_Y_Mover.position.z = lerp(nodes.Gantry_Y_Mover.userData.range_m, Math.cos(t.current) * 0.5 + 0.5)
    }
  })
  return <primitive object={scene} />
}
useGLTF.preload(URL)
```
`position` dos movers é absoluta: some o valor do curso à posição de repouso
(`rest = node.position.clone()` no primeiro frame) se quiser manter o offset original.
A pose de repouso tem Toolhead e Gantry em 0, então o snippet acima já funciona para os dois.
Para a mesa use `rest.y + offset`. Use `MeshPhysicalMaterial` (padrão do GLTFLoader com transmissão) e
um `<Environment preset="studio" />`.

## Limitações visuais
- Geometria simples (caixas e cilindros chanfrados). Sem cabos, correias, ventoinhas detalhadas, parafusos ou logotipo.
- Sem texturas: a PEI é cor sólida, sem normal map e sem UVs dedicados.
- O vidro depende de `transmission`, que é caro em mobile. Alternativa: `transparent` + `opacity 0.3`.
- A prévia tem ruído: o Blender do Ubuntu não traz OpenImageDenoise e o render é feito em CPU (Cycles, 96 amostras, cerca de 1 min por vista).
- O GLB não está comprimido. Com 164 KB isso ainda não é necessário.
