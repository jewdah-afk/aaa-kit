#!/usr/bin/env bash
# Every check in the kit. Exit 0 only if all pass. Run from anywhere.
set -eo pipefail
cd "$(dirname "$0")/.."
echo "== luau compile";  lune run tools/check_luau.luau . | tail -1
echo "== luau tests"
for f in $(find examples .claude/skills -name '*.test.luau' -o -name 'test.luau' -o -path '*/tests/run.luau' | sort); do
  printf '%s: ' "$f"; lune run "$f" | tail -1
done
echo "== lib/frontier"
for f in lib/frontier/qa/test_*.luau; do
  done_line=$(cd lib/frontier/qa && lune run "$(basename "$f")" | grep -a '^@@DONE')
  printf '%s: %s\n' "$f" "$done_line"
  [ "$done_line" = "@@DONE 0" ] || { echo "frontier check failed: $f"; exit 1; }
done
echo "== lib/surfacebake"
done_line=$(cd lib/surfacebake/qa && lune run test_surfacebake.luau | grep -a '^@@DONE')
echo "test_surfacebake.luau: $done_line"; [ "$done_line" = "@@DONE 0" ] || { echo "surfacebake check failed"; exit 1; }
done_line=$(cd lib/surfacebake/qa && lune run test_motion.luau | grep -a '^@@DONE')
echo "test_motion.luau: $done_line"; [ "$done_line" = "@@DONE 0" ] || { echo "surfacebake motion check failed"; exit 1; }
done_line=$(cd lib/surfacebake/qa && lune run test_react.luau | grep -a '^@@DONE')
echo "test_react.luau: $done_line"; [ "$done_line" = "@@DONE 0" ] || { echo "surfacebake react check failed"; exit 1; }
echo "== lib/pixelfx";   (cd lib/pixelfx/qa && lune run run.luau > /dev/null && echo "run.luau ok")
echo "== doctor";        python3 tools/doctor.py --brief | head -1
echo "== selene"
if ! command -v selene >/dev/null; then
  echo "skipped (selene not installed)"
elif out=$(selene examples .claude/skills tools lib 2>&1); then
  echo "$out" | tail -3
elif echo "$out" | grep -q "Could not collect standard library"; then
  echo "skipped: selene needs network once to download the Roblox std (std = \"roblox\")"
else
  echo "$out" | tail -20; exit 1
fi
echo "== links";         python3 tools/check_links.py | tail -1
echo "== skills";        python3 tools/check_skills.py | tail -1
echo "== lexicon";       python3 tools/check_lexicon.py | tail -1
echo "== hook";          python3 tools/hooks/test_amplify.py | tail -1
echo "== hierarchy";     python3 tools/hierarchy/test_hierarchy.py 2>&1 | tail -1
for g in media/gifs/*.gif media/gifs/*/*.gif; do python3 tools/hierarchy/hierarchy.py flash "$g" > /dev/null || { echo "flash check failed: $g"; exit 1; }; done
echo "flash: $(ls media/gifs/*.gif media/gifs/*/*.gif | wc -l) GIFs pass WCAG 2.3.1"
echo "== web examples";  node tools/check_examples.mjs | tail -1
echo "all checks passed"
