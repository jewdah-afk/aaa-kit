#!/usr/bin/env bash
# Runs bench.luau RUNS times in each VM mode and writes results/RESULTS.md (fastest run per row).
# Usage: LUAU=/path/to/luau bash tools/vfxbench/run.sh [RUNS]
set -eo pipefail
cd "$(dirname "$0")"
LUAU="${LUAU:-luau}"
RUNS="${1:-3}"
rm -rf results/raw && mkdir -p results/raw
for i in $(seq 1 "$RUNS"); do
  "$LUAU" -O2 bench.luau -a full "interpreter -O2" > "results/raw/interp-O2-$i.md"
  "$LUAU" -O2 --codegen bench.luau -a full "native codegen -O2" > "results/raw/native-O2-$i.md"
  "$LUAU" -O1 bench.luau -a full "interpreter -O1" > "results/raw/interp-O1-$i.md"
  for f in results/raw/*-"$i".md; do
    tail -n 1 "$f" | grep -q '^@@DONE 0$' || { echo "output mismatch in $f"; exit 1; }
  done
done
python3 merge.py results/raw > results/RESULTS.md
echo "wrote tools/vfxbench/results/RESULTS.md"
