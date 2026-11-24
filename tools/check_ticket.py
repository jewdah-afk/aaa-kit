#!/usr/bin/env python3
"""Checks that a task ticket can be executed in one shot, with no questions asked.

  python3 tools/check_ticket.py                 the shipped example ticket, the template's structure and docs/specs/*.md
  python3 tools/check_ticket.py FILE [FILE...]  those tickets
  python3 tools/check_ticket.py --root DIR ...  resolve `edit`/`delete` paths against DIR (default: the git root of the cwd)

A ticket follows docs/playbooks/templates/TASK-TICKET.md. Rules, each one a way a ticket stalls a session that can't ask:
  1. Title is "# TICKET: ...", then sections "## 0." to "## 10." in order, with the template's names.
  2. Decisions is a table (Question | Decision | Why) with at least one row: a vague idea always raises some.
  3. No placeholders (<angle brackets>, TBD, TODO, XXX, ???) and no unanswered question (a sentence-ending "?" in prose; the verbatim idea quote and table cells are exempt).
  4. Files is a table (# | Action | Path | Change | Check): numbered 1..n, Action in create/edit/delete/run, at most 12 rows,
     a backticked path (or command, for run), a Check for every row, and edit/delete paths that exist.
  5. Every create/edit row has a "### n." subsection in Per-file spec; Load lists at most 6 paths and at most one under docs/research/.
  6. Acceptance has a fenced command block and an "Expect:" line. Out of scope has at least one bullet.
"""
import re
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
SECTIONS = ["How to execute", "Goal", "Decisions", "Constraints", "Load", "Files", "Per-file spec", "Phases", "Acceptance", "Out of scope", "Report"]
ACTIONS = {"create", "edit", "delete", "run"}
MAX_FILES, MAX_LOAD = 12, 6
QUESTION = re.compile(r"\?(\s|$)")  # a sentence-ending "?"; a URL query string ("?x=1") is not one
PLACEHOLDER = re.compile(r"<[A-Za-z][^<>\n]{1,78}[A-Za-z0-9.\u2026\")]>|\bTBD\b|\bTODO\b|\bXXX\b|\?\?\?")


def git_root():
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=10)
        if out.returncode == 0 and out.stdout.strip():
            return Path(out.stdout.strip())
    except (OSError, subprocess.TimeoutExpired):
        pass
    return Path.cwd()


def split_sections(lines):
    """-> {number: (title, [lines])} for the '## n. Title' headings, and the order they appeared in."""
    sections, order, cur = {}, [], None
    for ln in lines:
        m = re.match(r"^## (\d+)\. (.+?)\s*$", ln)
        if m:
            cur = int(m.group(1))
            sections[cur] = (m.group(2), [])
            order.append(cur)
        elif cur is not None:
            sections[cur][1].append(ln)
    return sections, order


def prose(lines):
    """Lines outside fenced code blocks."""
    out, fenced = [], False
    for ln in lines:
        if ln.strip().startswith("```"):
            fenced = not fenced
        elif not fenced:
            out.append(ln)
    return out


def table_rows(lines):
    rows = []
    for ln in lines:
        if ln.strip().startswith("|"):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                rows.append(cells)
    return rows[1:]  # drop the header row


def check(path, root, template=False):
    errs = []
    text = Path(path).read_text(encoding="utf-8")
    lines = text.splitlines()

    def bad(msg):
        errs.append(f"{path}: {msg}")

    if not lines or not lines[0].startswith("# TICKET:"):
        bad('the first line must be "# TICKET: <title>"')
    sections, order = split_sections(lines)
    if order != list(range(len(SECTIONS))):
        bad(f"sections must be ## 0. to ## {len(SECTIONS) - 1}. in order (found {order})")
        return errs
    for n, name in enumerate(SECTIONS):
        if not sections[n][0].lower().startswith(name.lower()):
            bad(f'section {n} must be named "{name}" (found "{sections[n][0]}")')
    if template:
        return errs  # the template keeps its placeholders and example rows

    body = {n: sections[n][1] for n in sections}

    if not table_rows(body[2]):
        bad("Decisions needs a table row: every vague idea raises questions, and each one is answered here")
    for n in range(len(SECTIONS)):
        for ln in prose(body[n]):
            if PLACEHOLDER.search(ln):
                bad(f"section {n} has a placeholder: {ln.strip()[:70]}")
            s = ln.strip()
            if QUESTION.search(s) and not s.startswith(("|", ">")) and "Idea as given" not in s:
                bad(f"section {n} has an unanswered question: {s[:70]}")

    rows = table_rows(body[5])
    if not rows:
        bad("Files needs a table of rows")
    if len(rows) > MAX_FILES:
        bad(f"Files has {len(rows)} rows; more than {MAX_FILES} is two tickets")
    wanted = []
    for i, r in enumerate(rows, 1):
        if len(r) < 5:
            bad(f"Files row {i} needs 5 columns (# | Action | Path | Change | Check)")
            continue
        num, action, target, change, chk = r[:5]
        if num != str(i):
            bad(f"Files row {i} is numbered '{num}'")
        if action not in ACTIONS:
            bad(f"Files row {i}: action '{action}' is not one of {sorted(ACTIONS)}")
            continue
        m = re.fullmatch(r"`([^`]+)`", target)
        if not m:
            bad(f"Files row {i}: put the path (or the command, for run) in backticks")
            continue
        if not change or not chk:
            bad(f"Files row {i} needs a Change and a Check")
        if action in ("edit", "delete") and not (root / m.group(1)).exists():
            bad(f"Files row {i}: {action} of `{m.group(1)}` but it does not exist under {root}")
        if action in ("create", "edit"):
            wanted.append(i)
    subs = {int(m.group(1)) for ln in body[6] for m in [re.match(r"^### (\d+)\.", ln)] if m}
    for i in wanted:
        if i not in subs:
            bad(f"Per-file spec has no '### {i}.' subsection for Files row {i}")

    load = [ln for ln in body[4] if re.match(r"^\s*[-*] `", ln)]
    if len(load) > MAX_LOAD:
        bad(f"Load lists {len(load)} paths; the limit is {MAX_LOAD} so the executor reads little")
    if sum("docs/research/" in ln for ln in load) > 1:
        bad("Load names more than one docs/research/ file")

    if "```" not in "\n".join(body[8]) or "Expect:" not in "\n".join(body[8]):
        bad('Acceptance needs a fenced command block and an "Expect:" line')
    if not any(re.match(r"^\s*[-*] \S", ln) for ln in body[9]):
        bad("Out of scope needs at least one bullet")
    return errs


def main(argv):
    root, files, args = git_root(), [], argv[1:]
    while args:
        a = args.pop(0)
        if a == "--root":
            root = Path(args.pop(0)).resolve()
        else:
            files.append(a)
    errs, count = [], 0
    if files:
        for f in files:
            errs += check(f, root, template=Path(f).name == "TASK-TICKET.md")
            count += 1
    else:
        templates = KIT / "docs" / "playbooks" / "templates"
        errs += check(templates / "TASK-TICKET.md", KIT, template=True)
        errs += check(templates / "TASK-TICKET.example.md", KIT)
        count = 2
        for f in sorted((KIT / "docs" / "specs").glob("*.md")) if (KIT / "docs" / "specs").is_dir() else []:
            errs += check(f, KIT)
            count += 1
    for e in errs:
        print("FAIL", e)
    print(f"{count} tickets checked, {len(errs)} errors")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
