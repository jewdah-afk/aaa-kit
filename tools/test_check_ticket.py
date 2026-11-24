#!/usr/bin/env python3
"""Tests for check_ticket.py: the shipped example passes, and every rule rejects a ticket that breaks it.
Run: python3 tools/test_check_ticket.py"""
import pathlib
import re
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import check_ticket  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXAMPLE = (ROOT / "docs" / "playbooks" / "templates" / "TASK-TICKET.example.md").read_text(encoding="utf-8")
passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
    else:
        failed += 1
        print("FAIL", name, ("-> " + detail[:200]) if detail else "")


def errors(text, name="ticket.md"):
    with tempfile.TemporaryDirectory() as d:
        f = pathlib.Path(d) / name
        f.write_text(text, encoding="utf-8")
        return check_ticket.check(f, ROOT, template=name == "TASK-TICKET.md")


def rejects(label, text, needle):
    errs = errors(text)
    check(label, any(needle in e for e in errs), "; ".join(errs) or "no errors")


def with_section(text, n, body):
    """The ticket with section n's body replaced (its '## n.' heading kept)."""
    return re.sub(rf"(^## {n}\. [^\n]*\n)(.*?)(?=^## \d+\. )", lambda m: m.group(1) + body, text, count=1, flags=re.S | re.M)


check("the shipped example is valid", errors(EXAMPLE) == [], "; ".join(errors(EXAMPLE)))
tpl = (ROOT / "docs" / "playbooks" / "templates" / "TASK-TICKET.md").read_text(encoding="utf-8")
check("the template's structure is valid", errors(tpl, "TASK-TICKET.md") == [])
check("a ticket with the template's placeholders is rejected", len(errors(tpl)) > 0)

rejects("wrong title", EXAMPLE.replace("# TICKET:", "# Task:", 1), "first line")
rejects("a missing section", EXAMPLE.replace("## 9. Out of scope", "## 9b. Notes"), "sections must be")
rejects("a renamed section", EXAMPLE.replace("## 4. Load", "## 4. Reading"), 'must be named "Load"')
rejects("empty Decisions", with_section(EXAMPLE, 2, "\n| Question | Decision | Why |\n|---|---|---|\n\n"), "Decisions needs")
rejects("a placeholder", EXAMPLE.replace("Budget: at most", "Budget: <number> at most"), "placeholder")
rejects("TBD", EXAMPLE.replace("Commit on", "TBD commit on"), "placeholder")
rejects("an unanswered question", EXAMPLE.replace("Never ask a question.", "Which branch should this use?"), "unanswered question")
rejects("a bad action", EXAMPLE.replace("| 3 | edit |", "| 3 | tweak |"), "action 'tweak'")
rejects("an edit of a file that does not exist", EXAMPLE.replace("`.claude/skills/vfx/SKILL.md` | one row", "`.claude/skills/vfx/NOPE.md` | one row"), "does not exist")
rejects("a path without backticks", EXAMPLE.replace("| 3 | edit | `.claude/skills/vfx/SKILL.md` |", "| 3 | edit | .claude/skills/vfx/SKILL.md |"), "backticks")
rejects("a row without a Check", EXAMPLE.replace("| `python3 tools/check_skills.py` |", "|  |"), "needs a Change and a Check")
rejects("rows out of order", EXAMPLE.replace("| 2 | edit |", "| 7 | edit |"), "is numbered '7'")
rejects("a missing per-file subsection", EXAMPLE.replace("### 3. `.claude/skills/vfx/SKILL.md`", "### Three"), "no '### 3.' subsection")
many = "\n".join(f"| {i} | run | `echo {i}` | step | `true` |" for i in range(5, 15))
rejects("too many rows", EXAMPLE.replace("| 4 | run | `bash tools/check_all.sh` | everything still passes | the last line of its output |",
                                          "| 4 | run | `bash tools/check_all.sh` | everything still passes | the last line of its output |\n" + many), "two tickets")
rejects("a long Load list", EXAMPLE.replace("## 5. Files", "".join(f"- `a{i}.md` - x\n" for i in range(5)) + "\n## 5. Files"), "Load lists")
rejects("two research chapters", EXAMPLE.replace("## 5. Files", "- `docs/research/20-a.md` - x\n- `docs/research/21-b.md` - y\n\n## 5. Files"), "docs/research/")
rejects("no Expect line", EXAMPLE.replace("Expect:", "Result:"), "Expect:")
rejects("no fenced command block", with_section(EXAMPLE, 8, "\nRun the tests.\n\nExpect: they pass.\n\n"), "Acceptance")
rejects("empty Out of scope", with_section(EXAMPLE, 9, "\nNothing.\n\n"), "Out of scope needs")

# a comparison in prose is not a placeholder
check("`<` and `>` as comparisons are fine", errors(EXAMPLE.replace("Budget: at most", "Budget: peak < 0.7 and gap > 3, at most")) == [])

print(f"{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
