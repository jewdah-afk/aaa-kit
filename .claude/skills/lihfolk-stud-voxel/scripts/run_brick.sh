#!/usr/bin/env bash
# Build + render a BRICK-pipeline model on Linux/macOS, then outline/glow post and a contact sheet.
# Usage: bash run_brick.sh <path/to/model.py> [view names...] [res=600] [norig]      (no views = all views)
# Uses $BLENDER_EXE, else `blender` on PATH, else the `bpy` pip module (pip install bpy; needs libegl1 for EEVEE).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
MODEL="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"; shift
OUT="$(dirname "$MODEL")/out_$(basename "$MODEL" .py)"
FILTER='VOX_OK|PALETTE|CONN_OK|LINT_|BL_OK|RIG_|SHEET_OK|Traceback|Error|line [0-9]+'
BL="${BLENDER_EXE:-$(command -v blender || true)}"
if [ -n "$BL" ]; then
  "$BL" -b --factory-startup --python "$MODEL" -- render "$@" 2>&1 | grep -E "$FILTER" || true
else
  python3 "$MODEL" -- render "$@" 2>&1 | grep -E "$FILTER" || true
fi
if grep -q '^# GLOW: strong' "$MODEL"; then export GLOW_STRONG=1; else unset GLOW_STRONG || true; fi
python3 "$HERE/post_glow.py" "$OUT/render"
python3 "$HERE/brick_sheet.py" "$OUT/render" "$OUT/sheet.png"
