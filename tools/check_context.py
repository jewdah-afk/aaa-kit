#!/usr/bin/env python3
"""Keeps the context a session loads small, so a cheaper model can run a long task without drowning.

Always loaded: CLAUDE.md and every skill's frontmatter description. Loaded on a match: a skill's SKILL.md. Everything else
(patterns, examples, playbooks, research) loads only when something names it, which these checks protect:

  1. CLAUDE.md is at most 150 lines.
  2. CLAUDE.md links no research chapter directly (only the docs/research/README.md index), and states the context rules.
  3. Every SKILL.md is at most 130 lines (lihfolk-stud-voxel, a large vendored pack, at most 170).
  4. CLAUDE.md plus all skill descriptions stay under 16,000 characters (about 4,000 tokens at 4 characters per token: an
     estimate, not a tokenizer count).

Run: python3 tools/check_context.py
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CHECK_CONTEXT_ROOT") or Path(__file__).resolve().parents[1])  # the env var is for the test
CLAUDE_MAX_LINES = 150
SKILL_MAX_LINES = 130
SKILL_EXCEPTIONS = {"lihfolk-stud-voxel": 170}
ALWAYS_LOADED_MAX_CHARS = 16000


def description(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    d = re.search(r"^description:\s*(.*)$", m.group(1), re.M) if m else None
    return d.group(1).strip() if d else ""


def main():
    errs = []
    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    n = len(claude.splitlines())
    if n > CLAUDE_MAX_LINES:
        errs.append(f"CLAUDE.md is {n} lines; the cap is {CLAUDE_MAX_LINES}")
    if re.search(r"docs/research/\d", claude):
        errs.append("CLAUDE.md links a research chapter directly; link only the docs/research/README.md index")
    if "## Context rules" not in claude:
        errs.append('CLAUDE.md needs its "Context rules" section')

    chars, longest = len(claude), (0, "")
    for f in sorted((ROOT / ".claude" / "skills").glob("*/SKILL.md")):
        text = f.read_text(encoding="utf-8")
        name = f.parent.name
        lines = len(text.splitlines())
        cap = SKILL_EXCEPTIONS.get(name, SKILL_MAX_LINES)
        if lines > cap:
            errs.append(f"{name}/SKILL.md is {lines} lines; the cap is {cap}")
        chars += len(description(text))
        longest = max(longest, (lines, name))
    if chars > ALWAYS_LOADED_MAX_CHARS:
        errs.append(f"always-loaded text is {chars} characters; the budget is {ALWAYS_LOADED_MAX_CHARS}")

    for e in errs:
        print("FAIL", e)
    print(f"CLAUDE.md {n} lines (cap {CLAUDE_MAX_LINES}); longest skill {longest[1]} {longest[0]} lines; "
          f"always-loaded ~{chars // 4} tokens (budget ~{ALWAYS_LOADED_MAX_CHARS // 4}); {len(errs)} errors")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
