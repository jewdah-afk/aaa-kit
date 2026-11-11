#!/bin/sh
# Every check in the kit. Exit 0 only if all pass. Run from anywhere.
set -e
cd "$(dirname "$0")/.."
echo "== luau compile";  lune run tools/check_luau.luau . | tail -1
echo "== luau tests"
for f in $(find examples .claude/skills -name '*.test.luau' -o -name 'test.luau' -o -path '*/tests/run.luau' | sort); do
  printf '%s: ' "$f"; lune run "$f" | tail -1
done
echo "== selene";        if command -v selene >/dev/null; then selene examples .claude/skills tools | tail -3; else echo "skipped (selene not installed)"; fi
echo "== links";         python3 tools/check_links.py | tail -1
echo "== skills";        python3 tools/check_skills.py | tail -1
echo "== lexicon";       python3 tools/check_lexicon.py | tail -1
echo "== hook";          python3 tools/hooks/test_amplify.py | tail -1
echo "== web examples";  node tools/check_examples.mjs | tail -1
echo "all checks passed"
