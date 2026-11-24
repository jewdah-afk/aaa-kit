#!/usr/bin/env bash
# Generate one answer per trap with the Claude Code CLI, for tools/evals/score.py. Run it on a PC with `claude` installed.
#   bash tools/evals/run_claude.sh OUT_DIR            run from the kit repo: its CLAUDE.md, hooks and tools are in play
#   (cd /some/empty/dir && bash /path/to/aaa-kit/tools/evals/run_claude.sh OUT_DIR)   baseline: no harness
# Then:  python3 tools/evals/score.py OUT_DIR
# Compare the two scores to see what the harness is worth. No keys are read or written here; `claude` uses your own login.
set -euo pipefail
out="${1:?usage: run_claude.sh OUT_DIR}"
here="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$out"
python3 - "$here/roblox_traps/cases.json" "$out" <<'PY'
import json, subprocess, sys
from pathlib import Path
cases = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["cases"]
out = Path(sys.argv[2])
for c in cases:
    prompt = c["prompt"] + " Answer with one Luau code block and nothing else."
    r = subprocess.run(["claude", "-p", prompt], capture_output=True, text=True, timeout=300)
    (out / f"{c['id']}.md").write_text(r.stdout, encoding="utf-8")
    print(c["id"], "ok" if r.returncode == 0 else f"exit {r.returncode}")
PY
