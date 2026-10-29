#!/usr/bin/env bash
# GLB bruto -> GLB de runtime: dedup -> weld -> prune(keep-leaves) -> meshopt.
# Sem flatten/join/palette/instance: preservam pivos animaveis e nomes de materiais.
# Uso: bash scripts/printers/optimize_glb.sh <raw.glb> <saida.glb>
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
T="$ROOT/.tools/node_modules/.bin/gltf-transform"
[ -x "$T" ] || { echo "rode: bash scripts/setup.sh --with-gltf-transform"; exit 1; }
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
"$T" dedup "$1" "$TMP/1.glb" >/dev/null
"$T" weld "$TMP/1.glb" "$TMP/2.glb" >/dev/null
"$T" prune --keep-leaves true "$TMP/2.glb" "$TMP/3.glb" >/dev/null
"$T" meshopt --level medium "$TMP/3.glb" "$2" >/dev/null
echo "OPTIMIZED $1 ($(stat -c %s "$1") B) -> $2 ($(stat -c %s "$2") B)"
