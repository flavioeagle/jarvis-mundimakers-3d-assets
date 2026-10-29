#!/usr/bin/env bash
# Prepara Blender headless + dependencias numa sessao Ubuntu nova.
# Verifica antes de instalar; nao altera configuracoes globais alem de pacotes apt.
# Uso: bash scripts/setup.sh [--with-gltf-transform]
set -euo pipefail

BLENDER_MIN="4.0"
GLTF_TRANSFORM_VERSION="4.5.1"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS="$ROOT/.tools"   # gitignored; npm local, nunca global

SUDO=""
if [ "$(id -u)" -ne 0 ]; then
  command -v sudo >/dev/null || { echo "ERRO: precisa de root ou sudo para apt"; exit 1; }
  SUDO="sudo"
fi

ver_ge() { [ "$(printf '%s\n%s\n' "$2" "$1" | sort -V | head -1)" = "$2" ]; }

apt_install() {
  echo "Instalando: $*"
  $SUDO apt-get update -qq
  DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y -qq --no-install-recommends "$@"
}

# Blender
if command -v blender >/dev/null; then
  BV="$(blender -b --version 2>/dev/null | awk '/^Blender/{print $2; exit}')"
  echo "Blender encontrado: $BV"
  ver_ge "$BV" "$BLENDER_MIN" || { echo "ERRO: Blender $BV < $BLENDER_MIN"; exit 1; }
else
  apt_install blender
fi

# numpy (exigido pelo exportador glTF do Blender)
if blender -b --factory-startup --python-exit-code 1 --python-expr "import numpy" >/dev/null 2>&1; then
  echo "numpy OK no Python do Blender"
else
  apt_install python3-numpy
fi

# gltf-transform (opcional, local)
if [ "${1:-}" = "--with-gltf-transform" ]; then
  command -v node >/dev/null || { echo "ERRO: Node.js ausente"; exit 1; }
  if [ -x "$TOOLS/node_modules/.bin/gltf-transform" ] \
     && [ "$("$TOOLS/node_modules/.bin/gltf-transform" --version 2>/dev/null | tail -1)" = "$GLTF_TRANSFORM_VERSION" ]; then
    echo "gltf-transform $GLTF_TRANSFORM_VERSION OK"
  else
    mkdir -p "$TOOLS"
    [ -f "$TOOLS/package.json" ] || echo '{"private":true}' > "$TOOLS/package.json"
    npm install --prefix "$TOOLS" --no-fund --no-audit --ignore-scripts \
      "@gltf-transform/cli@$GLTF_TRANSFORM_VERSION"
  fi
fi

echo "--- versoes ---"
blender -b --version 2>/dev/null | head -1
blender -b --factory-startup --python-expr "import numpy; print('numpy', numpy.__version__)" 2>/dev/null | grep '^numpy'
[ -x "$TOOLS/node_modules/.bin/gltf-transform" ] && echo "gltf-transform $("$TOOLS/node_modules/.bin/gltf-transform" --version | tail -1)"
echo "setup OK"
