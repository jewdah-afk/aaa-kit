#!/usr/bin/env bash
# 1:1 check: rebuild every shipped prop, building and terrain piece in a temp copy and compare its <ID>_rig.json
# (bones, pivots, triangles per piece) with the one shipped in examples/brick/out_<ID>/. Any difference fails.
# Run after ANY change to scripts/ or the brick examples. Needs Blender 4.2+ or the `bpy` pip module. No rendering.
# The .glb bytes are not compared: they change with the Blender version.
set -euo pipefail
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cp -r "$SKILL" "$TMP/sk"; cd "$TMP/sk/examples/brick"
BL="${BLENDER_EXE:-$(command -v blender || true)}"
fail=0; n=0
for d in out_*; do
  id="${d#out_}"; f=props_brick.py
  case "$id" in Shop) f=shop_brick.py;; Watchtower) f=tower_brick.py;; CastleGate) f=gate_brick.py;; Cliff|Waterfall|Wall|WallCorner) f=terrain_brick.py;; esac
  rm -f "$d"/*_rig.json
  if [ -n "$BL" ]; then "$BL" -b --factory-startup --python "$f" -- "$id" >/dev/null 2>&1 || true
  else python3 "$f" -- "$id" >/dev/null 2>&1 || true; fi
  if python3 -c "import json,sys; sys.exit(0 if json.load(open(sys.argv[1]))==json.load(open(sys.argv[2])) else 1)" \
       "$SKILL/examples/brick/$d/${id}_rig.json" "$d/${id}_rig.json" 2>/dev/null; then n=$((n+1))
  else echo "DIFFERS: $id"; fail=1; fi
done
[ "$fail" = 0 ] && echo "REGRESS_OK $n models identical" || { echo "REGRESS_FAIL"; exit 1; }
