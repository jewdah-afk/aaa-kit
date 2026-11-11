#!/usr/bin/env python3
"""Tests for the UserPromptSubmit hook. Run: python3 tools/hooks/test_amplify.py"""
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOOK = ROOT / "tools" / "hooks" / "amplify.py"


def run(prompt):
    out = subprocess.run([sys.executable, str(HOOK)], input=json.dumps({"prompt": prompt}), text=True,
                         capture_output=True, env={**os.environ, "CLAUDE_PROJECT_DIR": str(ROOT)}, timeout=10)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)["hookSpecificOutput"]["additionalContext"] if out.stdout.strip() else None


CASES = [
    ("make the shop better", True, "shop card"),
    ("fix the ui", True, "UI"),
    ("add juice to hits", True, "hit-stop"),
    ("make it cool", True, "loudness tier"),            # nothing specific: starter pack, hierarchy first
    ("What does Economy.buy return?", False, None),     # a question, not a build request
    ("/review", False, None),                           # slash command
    ("just do it, make it better", False, None),        # user opted out
    ("In src/client/Hud.luau line 40 the coin TextLabel should use Format.short and tween over 180 ms on phone", False, None),
]

failed = 0
for prompt, want_weak, want_term in CASES:
    ctx = run(prompt)
    ok = (ctx is not None) == want_weak and (want_term is None or (ctx and want_term in ctx))
    if not ok:
        failed += 1
        print("FAIL", repr(prompt), "->", (ctx or "")[:120])
bad = subprocess.run([sys.executable, str(HOOK)], input="not json", text=True, capture_output=True)
if bad.returncode != 0 or bad.stdout:
    failed += 1
    print("FAIL bad input should exit 0 silently")
print(f"{len(CASES) + 1 - failed} passed, {failed} failed")
sys.exit(1 if failed else 0)
