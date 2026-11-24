#!/usr/bin/env python3
"""Tests for edit_checks.py and session_setup.py. Run: python3 tools/hooks/test_edit_checks.py

Each case runs the real hook as a subprocess with a JSON payload on stdin, the way Claude Code calls it, inside a throwaway
project and TMPDIR. A fake `selene` on PATH makes the lint paths deterministic whatever is installed."""
import json
import os
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
HOOK = ROOT / "tools" / "hooks" / "edit_checks.py"
SETUP = ROOT / "tools" / "hooks" / "session_setup.py"

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
    else:
        failed += 1
        print("FAIL", name, ("-> " + detail[:300]) if detail else "")


FAKE_SELENE = """#!/bin/sh
echo call >> "$SELENE_LOG"
case "$SELENE_MODE" in
  lint) echo "error[unused_variable]: x is defined, but never used"; exit 1 ;;
  std) echo "ERROR: Could not collect standard library: failed to collect roblox standard library"; exit 1 ;;
  *) exit 0 ;;
esac
"""

GOOD_LUAU = "--!strict\nlocal x = 1\nreturn x\n"
BAD_LUAU = "local = = 1\n"
EXIT = 'local process = require("@lune/process")\nprocess.exit({})\n'


class Sandbox:
    def __init__(self, base):
        self.base = pathlib.Path(base)
        self.proj = self.base / "proj"
        self.tmp = self.base / "tmp"
        self.bin = self.base / "bin"
        for d in (self.proj, self.tmp, self.bin):
            d.mkdir()
        sel = self.bin / "selene"
        sel.write_text(FAKE_SELENE)
        sel.chmod(0o755)
        self.log = self.base / "selene.log"

    def calls(self):
        return len(self.log.read_text().split()) if self.log.exists() else 0

    def run(self, mode, payload=None, env=None, args=()):
        e = {**os.environ, "CLAUDE_PROJECT_DIR": str(self.proj), "TMPDIR": str(self.tmp), "SELENE_LOG": str(self.log),
             "SELENE_MODE": "ok", "PATH": str(self.bin) + os.pathsep + os.environ["PATH"], **(env or {})}
        e.pop("EDIT_CHECKS", None) if not (env and "EDIT_CHECKS" in env) else None
        return subprocess.run([sys.executable, str(HOOK), mode, *args], input=json.dumps(payload or {}), text=True,
                              capture_output=True, env=e, timeout=120)

    def post(self, path, sid="s1", **kw):
        return self.run("post", {"session_id": sid, "tool_name": "Edit", "tool_input": {"file_path": str(path)}}, **kw)

    def stop(self, sid="s1", active=False, **kw):
        return self.run("stop", {"session_id": sid, "stop_hook_active": active}, **kw)


with tempfile.TemporaryDirectory() as base:
    sb = Sandbox(base)
    good, bad = sb.proj / "Good.luau", sb.proj / "Bad.luau"
    good.write_text(GOOD_LUAU)
    bad.write_text(BAD_LUAU)

    # ---- Luau: compile
    r = sb.post(good)
    check("good .luau passes silently", r.returncode == 0 and not r.stderr.strip(), r.stderr)
    check("selene ran once on the good file", sb.calls() == 1, str(sb.calls()))
    r = sb.post(bad)
    check("bad .luau exits 2", r.returncode == 2, f"rc={r.returncode} {r.stderr}")
    check("the failure names the file and the compile step", "Bad.luau" in r.stderr and "compile" in r.stderr, r.stderr)
    check("a file that doesn't compile is not linted", sb.calls() == 1, str(sb.calls()))

    # ---- Luau: sibling test
    mod = sb.proj / "Foo.luau"
    mod.write_text("--!strict\nlocal Foo = {}\nreturn Foo\n")
    test = sb.proj / "Foo.test.luau"
    test.write_text(EXIT.format(1))
    r = sb.post(mod)
    check("a failing sibling test exits 2", r.returncode == 2 and "Foo.test.luau" in r.stderr, r.stderr)
    test.write_text(EXIT.format(0))
    r = sb.post(mod)
    check("a passing sibling test exits 0", r.returncode == 0, r.stderr)
    r = sb.post(test)
    check("editing a test file runs it", r.returncode == 0, r.stderr)
    test.write_text(EXIT.format(1))
    r = sb.post(test)
    check("a failing test file exits 2", r.returncode == 2, r.stderr)
    test.write_text(EXIT.format(0))

    # ---- selene
    r = sb.post(good, env={"SELENE_MODE": "lint"})
    check("selene findings fail the check", r.returncode == 2 and "selene:" in r.stderr and "unused_variable" in r.stderr, r.stderr)
    r = sb.post(good, env={"SELENE_MODE": "std"})
    check("selene without its Roblox std is a note, not a failure", r.returncode == 0, r.stderr)
    r = sb.post(good, env={"SELENE_MODE": "lint", "EDIT_CHECKS_SELENE": "0"})
    check("EDIT_CHECKS_SELENE=0 skips lint", r.returncode == 0, r.stderr)

    # ---- Markdown and Python
    md_bad, md_good = sb.proj / "bad.md", sb.proj / "good.md"
    md_bad.write_text("# x\n\n```lua\nlocal = = 1\n```\n")
    md_good.write_text("# x\n\n```lua\nlocal a = 1\n```\n\n```lua\n-- snippet\nlocal = =\n```\n")
    r = sb.post(md_bad)
    check("a Markdown Luau block that doesn't compile exits 2", r.returncode == 2 and "Luau blocks" in r.stderr, r.stderr)
    r = sb.post(md_good)
    check("good Markdown (and a -- snippet block) passes", r.returncode == 0, r.stderr)
    py_bad, py_good = sb.proj / "bad.py", sb.proj / "good.py"
    py_bad.write_text("def (:\n")
    py_good.write_text("x = 1\n")
    r = sb.post(py_bad)
    check("a Python syntax error exits 2", r.returncode == 2 and "syntax" in r.stderr, r.stderr)
    r = sb.post(py_good)
    check("good Python passes", r.returncode == 0, r.stderr)
    (sb.proj / "test_pair.py").write_text("import sys\nsys.exit(1)\n")
    (sb.proj / "pair.py").write_text("x = 1\n")
    r = sb.post(sb.proj / "pair.py")
    check("a failing test_<name>.py next to a .py exits 2", r.returncode == 2 and "test_pair.py" in r.stderr, r.stderr)

    # ---- things that are not checked
    r = sb.post(sb.proj / "data.json")
    check("other extensions are ignored", r.returncode == 0 and not r.stderr)
    r = sb.post(sb.proj / "gone.luau")
    check("a missing file is ignored", r.returncode == 0 and not r.stderr)
    r = sb.run("post", {"session_id": "s1", "tool_name": "Bash", "tool_input": {"command": "ls"}})
    check("a payload without file_path is ignored", r.returncode == 0)
    r = sb.post(bad, env={"EDIT_CHECKS": "0"})
    check("EDIT_CHECKS=0 turns the hook off", r.returncode == 0 and not r.stderr)
    r = sb.run("post", None)
    check("an empty payload is ignored", r.returncode == 0)

    # ---- Stop
    sb2 = Sandbox(tempfile.mkdtemp(dir=base))
    bad2, good2 = sb2.proj / "Bad.luau", sb2.proj / "Good.luau"
    good2.write_text(GOOD_LUAU)
    bad2.write_text(BAD_LUAU)
    sb2.post(good2, sid="a")
    calls_after_post = sb2.calls()
    sb2.post(bad2, sid="a")
    r = sb2.stop(sid="a")
    check("Stop blocks while a changed file fails", r.returncode == 2 and "Bad.luau" in r.stderr, r.stderr)
    check("Stop does not re-check a file that passed at this mtime", sb2.calls() == calls_after_post, f"{sb2.calls()} vs {calls_after_post}")
    r = sb2.stop(sid="a", active=True)
    check("Stop lets the turn end the second time (no loop)", r.returncode == 0, r.stderr)
    check("...and warns the user", "systemMessage" in r.stdout and "Bad.luau" in r.stdout, r.stdout)
    bad2.write_text(GOOD_LUAU)
    r = sb2.stop(sid="a")
    check("Stop passes once the file is fixed", r.returncode == 0 and not r.stderr and not r.stdout.strip(), r.stderr + r.stdout)

    # selene unavailable surfaces at Stop as an honest note
    sb3 = Sandbox(tempfile.mkdtemp(dir=base))
    f3 = sb3.proj / "A.luau"
    f3.write_text(GOOD_LUAU)
    sb3.post(f3, sid="n", env={"SELENE_MODE": "std"})
    r = sb3.stop(sid="n")
    check("Stop reports what was not checked", r.returncode == 0 and "Not checked" in r.stdout and "selene" in r.stdout, r.stdout)

    # edits made through Bash never reach the post hook; git status finds them
    sb4 = Sandbox(tempfile.mkdtemp(dir=base))
    subprocess.run(["git", "init", "-q"], cwd=sb4.proj, check=True)
    (sb4.proj / "viaBash.luau").write_text(BAD_LUAU)
    r = sb4.stop(sid="g")
    check("Stop finds files changed outside Edit/Write via git status", r.returncode == 2 and "viaBash.luau" in r.stderr, r.stderr)
    (sb4.proj / "viaBash.luau").write_text(GOOD_LUAU)
    r = sb4.stop(sid="g")
    check("...and passes once fixed", r.returncode == 0, r.stderr)

    # ---- manual mode and state hygiene
    r = sb.run("check", None, args=[str(good), str(bad)])
    check("manual check exits 1 on a failure and lists both", r.returncode == 1 and "ok  " in r.stdout and "FAIL" in r.stdout, r.stdout)
    r = sb.post(good, sid="../../escape")
    states = list((sb.tmp / "aaa-kit-edit-checks").glob("*.json"))
    check("a hostile session id stays inside TMPDIR", r.returncode == 0 and all(p.parent == sb.tmp / "aaa-kit-edit-checks" for p in states))

    # ---- session_setup
    r = subprocess.run([sys.executable, str(SETUP)], capture_output=True, text=True, env={**os.environ, "CLAUDE_CODE_REMOTE": "false"}, timeout=30)
    check("session_setup does nothing outside a cloud session", r.returncode == 0 and not r.stdout.strip(), r.stdout + r.stderr)
    sys.path.insert(0, str(ROOT / "tools" / "hooks"))
    import session_setup  # noqa: E402

    pins = session_setup.pins()
    check("session_setup reads the rokit.toml pins", {"lune", "selene"} <= set(pins) and all(v[0].isdigit() for v in pins.values()), str(pins))

print(f"{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
