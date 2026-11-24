#!/usr/bin/env python3
"""Edit-time checks for Claude Code hooks, so a session can't finish a turn on code that doesn't compile or pass.

  edit_checks.py post     PostToolUse (Edit|Write|MultiEdit): check the one file just written.
  edit_checks.py stop     Stop: re-check every file this session changed that hasn't passed at its current mtime.
                          Files come from the post hook's record AND `git status`, so edits made through Bash count too.
  edit_checks.py check F  Manual: check the given files and print the result (exit 1 on a failure).

What runs per file (each takes 30 to 150 ms):
  .luau / .lua   lune compile check (tools/check_luau.luau); the sibling Name.test.luau (or the file itself when it is a test,
                 or lib/*/qa/test_*.luau expecting "@@DONE 0"); selene on the file.
  .md            the Luau blocks in it compile (the same checker); skills also run check_skills.py; links run check_links.py.
  .py            it parses; its test (test_<name>.py next to it, or itself when it is a test or a tools/check_*.py).

A failure exits 2 with the output on stderr: Claude Code feeds that back to Claude, and on Stop it keeps the turn going.
If Stop already blocked once this turn (stop_hook_active), it lets the turn end and shows the user a warning instead of looping.
Missing tools never fail a check, but they are reported: no lune, no selene, or selene without its Roblox std (it downloads the
std from raw.githubusercontent.com with its own TLS roots, which a proxy that re-signs HTTPS breaks; generate roblox.yml once on a
PC with `selene generate-roblox-std` and commit it to lint in the cloud).

Escape hatches: EDIT_CHECKS=0 turns everything off; EDIT_CHECKS_SELENE=0 skips selene.
"""
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]  # the kit: where tools/check_luau.luau lives
LUAU_EXT = {".luau", ".lua"}
EXTS = LUAU_EXT | {".py", ".md"}
MAX_FILES = 40  # one Stop pass checks at most this many files
TAIL_LINES = 30  # lines of failure output shown per file
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def project_dir():
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()).resolve()


def run(cmd, cwd, timeout=60):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, ANSI.sub("", (p.stdout or "") + (p.stderr or ""))
    except subprocess.TimeoutExpired:
        return 124, f"timed out after {timeout}s: {' '.join(map(str, cmd))}"
    except FileNotFoundError:
        return 127, f"not installed: {cmd[0]}"


STACK = re.compile(r"\[Stack Begin\].*?\[Stack End\]\n?", re.S)


def tail(text, n=TAIL_LINES):
    text = STACK.sub("", text)  # lune's stack frames name its own scripts, not the edited file
    lines = [ln for ln in text.strip().splitlines() if ln.strip()]
    return "\n".join(lines[-n:])


# ---------------------------------------------------------------- per-file checks
def find_luau_test(path):
    """(test file, directory to run it in, needs '@@DONE 0') or None."""
    name = path.name
    if name.endswith(".test.luau") or name == "test.luau":
        return path, KIT, False
    if path.parent.name == "qa" and name.startswith("test_") and name.endswith(".luau"):
        return path, path.parent, True
    sibling = path.with_name(path.stem + ".test.luau")
    if path.suffix == ".luau" and sibling.exists():
        return sibling, KIT, False
    return None


def check_luau(path, proj):
    fails, notes = [], []
    if not shutil.which("lune"):
        return fails, ["lune is not installed, so .luau checks were skipped (python3 tools/hooks/session_setup.py --force)"]
    rc, out = run(["lune", "run", str(KIT / "tools" / "check_luau.luau"), str(path)], proj)
    if rc != 0:
        fails.append("compile:\n" + tail(out))
        return fails, notes  # a file that doesn't compile can't be tested or linted
    test = find_luau_test(path)
    if test:
        tfile, cwd, done_line = test
        rc, out = run(["lune", "run", str(tfile)], cwd, timeout=90)
        if rc != 0 or (done_line and "@@DONE 0" not in out):
            fails.append(f"test {tfile.name}:\n" + tail(out))
    if os.environ.get("EDIT_CHECKS_SELENE") != "0":
        if not shutil.which("selene"):
            notes.append("selene is not installed, so lint was skipped")
        else:
            rc, out = run(["selene", "--display-style=quiet", str(path)], proj)
            if "Could not collect standard library" in out or "error when getting API dump" in out:
                notes.append("selene could not build its Roblox std (needs roblox.yml or a direct connection), so lint was skipped")
            elif rc != 0:
                fails.append("selene:\n" + tail(out))
    return fails, notes


def check_md(path, proj):
    fails, notes = [], []
    if shutil.which("lune"):
        rc, out = run(["lune", "run", str(KIT / "tools" / "check_luau.luau"), str(path)], proj)
        if rc != 0:
            fails.append("Luau blocks:\n" + tail(out))
    else:
        notes.append("lune is not installed, so Markdown Luau blocks were not compiled")
    try:
        rel = path.resolve().relative_to(KIT).as_posix()
    except ValueError:
        return fails, notes
    if rel.startswith(".claude/skills/") and (KIT / "tools" / "check_skills.py").exists():
        rc, out = run([sys.executable, str(KIT / "tools" / "check_skills.py")], KIT)
        if rc != 0:
            fails.append("skills:\n" + tail(out))
    if (KIT / "tools" / "check_links.py").exists():
        rc, out = run([sys.executable, str(KIT / "tools" / "check_links.py")], KIT)
        mine = [ln for ln in out.splitlines() if rel in ln]
        if rc != 0 and mine:  # failures elsewhere are not this edit's
            fails.append("links:\n" + "\n".join(mine[:TAIL_LINES]))
    return fails, notes


def check_py(path, proj):
    fails, notes = [], []
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as e:
        return [f"syntax: {e}"], notes
    test = None
    if path.name.startswith("test_") or (path.parent.name == "tools" and path.name.startswith("check_")):
        test = path
    elif (path.parent / f"test_{path.name}").exists():
        test = path.parent / f"test_{path.name}"
    elif path.parent.name == "hierarchy" and (path.parent / "test_hierarchy.py").exists():
        test = path.parent / "test_hierarchy.py"
    if test:
        rc, out = run([sys.executable, str(test)], KIT, timeout=90)
        if rc != 0:
            fails.append(f"test {test.name}:\n" + tail(out))
    return fails, notes


def check_file(path, proj):
    """-> (failures, notes) for one file."""
    if path.suffix in LUAU_EXT:
        return check_luau(path, proj)
    if path.suffix == ".md":
        return check_md(path, proj)
    if path.suffix == ".py":
        return check_py(path, proj)
    return [], []


# ---------------------------------------------------------------- session state
def state_path(session_id):
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id or "nosession")[:80]
    return Path(tempfile.gettempdir()) / "aaa-kit-edit-checks" / f"{safe}.json"


def load_state(session_id):
    try:
        return json.loads(state_path(session_id).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"files": {}, "notes": []}


def save_state(session_id, state):
    p = state_path(session_id)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(state), encoding="utf-8")
    except OSError:
        pass  # state is an optimisation: losing it only means a re-check


def mtime(path):
    try:
        return path.stat().st_mtime
    except OSError:
        return None


def run_and_record(path, proj, state):
    fails, notes = check_file(path, proj)
    state["files"][str(path)] = {"mtime": mtime(path), "ok": not fails}
    for n in notes:
        if n not in state["notes"]:
            state["notes"].append(n)
    return fails


def git_changed(proj):
    rc, out = run(["git", "status", "--porcelain", "-uall"], proj, timeout=20)
    if rc != 0:
        return []
    found = []
    for line in out.splitlines():
        name = line[3:].split(" -> ")[-1].strip().strip('"')
        p = (proj / name)
        if p.suffix in EXTS and p.is_file():
            found.append(p.resolve())
    return found


def report(failed):
    parts = []
    for path, fails in failed.items():
        parts.append(f"edit-checks: {path} FAILED\n" + "\n".join(fails))
    return "\n\n".join(parts) + "\n\nFix these before finishing. Re-run `python3 tools/hooks/edit_checks.py check <file>` to confirm."


# ---------------------------------------------------------------- hook entry points
def hook_post(payload):
    ti = payload.get("tool_input") or {}
    raw = ti.get("file_path") or ti.get("notebook_path")
    if not raw:
        return 0
    path = Path(raw)
    if path.suffix not in EXTS or not path.is_file():
        return 0
    sid = payload.get("session_id", "")
    state = load_state(sid)
    fails = run_and_record(path.resolve(), project_dir(), state)
    save_state(sid, state)
    if fails:
        print(report({str(path): fails}), file=sys.stderr)
        return 2
    return 0


def hook_stop(payload):
    proj = project_dir()
    sid = payload.get("session_id", "")
    state = load_state(sid)
    todo = {}
    for p in [Path(k) for k in state["files"]] + git_changed(proj):
        if p.is_file() and p.suffix in EXTS:
            rec = state["files"].get(str(p))
            if rec and rec["ok"] and rec["mtime"] == mtime(p):
                continue  # passed at this exact mtime already
            todo[str(p)] = p
    skipped = max(0, len(todo) - MAX_FILES)
    failed = {}
    for name in sorted(todo)[:MAX_FILES]:
        fails = run_and_record(todo[name], proj, state)
        if fails:
            failed[name] = fails
    save_state(sid, state)
    notes = list(state["notes"]) + ([f"{skipped} more changed files were not checked; run bash tools/check_all.sh"] if skipped else [])
    if failed:
        text = report(failed)
        if payload.get("stop_hook_active"):  # already blocked once: don't loop, tell the user instead
            print(json.dumps({"systemMessage": "edit-checks: the turn ended with failing files.\n" + text}))
            return 0
        print(text, file=sys.stderr)
        return 2
    if notes:
        print(json.dumps({"systemMessage": "edit-checks passed. Not checked: " + "; ".join(notes)}))
    return 0


def manual(files):
    proj = project_dir()
    bad = 0
    for f in files:
        fails, notes = check_file(Path(f).resolve(), proj)
        status = "FAIL" if fails else "ok"
        print(f"{status}  {f}")
        for x in fails:
            print("   " + x.replace("\n", "\n   "))
        for n in notes:
            print(f"   note: {n}")
        bad += bool(fails)
    return 1 if bad else 0


def main(argv):
    if os.environ.get("EDIT_CHECKS") == "0" or len(argv) < 2:
        return 0
    mode = argv[1]
    if mode == "check":
        return manual(argv[2:])
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return 0
    if mode == "post":
        return hook_post(payload)
    if mode == "stop":
        return hook_stop(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
