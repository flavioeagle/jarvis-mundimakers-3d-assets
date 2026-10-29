# Setup log — Blender headless (2026-10-29)

Ambiente: container cloud Ubuntu 24.04.5 LTS, usuário root (sem sudo), Node v22.22.0.

## Instalação
```bash
apt-get update
apt-get install -y --no-install-recommends blender        # 4.0.2+dfsg-1ubuntu8
apt-get install -y --no-install-recommends python3-numpy  # 1:1.26.4+ds-6ubuntu1
```
`python3-numpy` é obrigatório: o exportador glTF do Blender falha com
`ModuleNotFoundError: No module named 'numpy'` sem ele (vem só como "recommends").

## gltf-transform (isolado, não global)
```bash
mkdir -p <scratch>/gt && cd <scratch>/gt && npm init -y
npm install --ignore-scripts @gltf-transform/cli@4.5.1
npx gltf-transform validate <arquivo.glb>
npx gltf-transform inspect  <arquivo.glb>
```
Usado só para validação pela spec Khronos (glTF-Validator). Nenhuma otimização aplicada.

## Ocorrências
1. Exportação falhou sem numpy → resolvido com `python3-numpy`.
2. Validação inicial esperava 8 vértices / 6 faces. glTF triangula e duplica
   vértices por face (normais planas): o correto é 24 vértices / 12 triângulos.
