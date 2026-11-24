#!/usr/bin/env python3
"""Tests for check_context.py: the real repo is within budget, and each budget rejects an oversized input.
Run: python3 tools/test_check_context.py"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "check_context.py"
passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
    else:
        failed += 1
        print("FAIL", name, ("-> " + detail[:200]) if detail else "")


def run(root):
    p = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True, env={**os.environ, "CHECK_CONTEXT_ROOT": str(root)})
    return p.returncode, p.stdout


def make(root, claude_lines=30, skill_lines=20, desc="Use when testing.", extra_claude=""):
    root = Path(root)
    (root / ".claude" / "skills" / "demo").mkdir(parents=True)
    (root / "CLAUDE.md").write_text("# CLAUDE.md\n\n## Context rules\n" + "line\n" * claude_lines + extra_claude, encoding="utf-8")
    (root / ".claude" / "skills" / "demo" / "SKILL.md").write_text(f"---\nname: demo\ndescription: {desc}\n---\n" + "x\n" * skill_lines, encoding="utf-8")


rc, out = run(Path(__file__).resolve().parents[1])
check("the real repo is within budget", rc == 0, out)

with tempfile.TemporaryDirectory() as d:
    make(d)
    rc, out = run(d)
    check("a small repo passes", rc == 0, out)
with tempfile.TemporaryDirectory() as d:
    make(d, claude_lines=200)
    rc, out = run(d)
    check("a CLAUDE.md over 150 lines fails", rc == 1 and "CLAUDE.md is" in out, out)
with tempfile.TemporaryDirectory() as d:
    make(d, skill_lines=200)
    rc, out = run(d)
    check("a SKILL.md over 130 lines fails", rc == 1 and "demo/SKILL.md" in out, out)
with tempfile.TemporaryDirectory() as d:
    make(d, desc="Use " + "w" * 17000)
    rc, out = run(d)
    check("always-loaded text over budget fails", rc == 1 and "budget" in out, out)
with tempfile.TemporaryDirectory() as d:
    make(d, extra_claude="[a chapter](docs/research/20-roblox-editableimage-api.md)\n")
    rc, out = run(d)
    check("a direct research link in CLAUDE.md fails", rc == 1 and "research chapter" in out, out)
with tempfile.TemporaryDirectory() as d:
    make(d)
    (Path(d) / "CLAUDE.md").write_text("# CLAUDE.md\n", encoding="utf-8")
    rc, out = run(d)
    check("a CLAUDE.md without the context rules fails", rc == 1 and "Context rules" in out, out)

print(f"{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
