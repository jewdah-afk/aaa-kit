#!/usr/bin/env python3
"""Kit doctor: checks this PC and the current repo for everything the kit's games need.

Usage:
    python3 tools/doctor.py            # toolchain + repo checks, with install commands
    python3 tools/doctor.py --brief    # one screen, fast (used by the greeting hook)
    python3 tools/doctor.py --repo DIR # audit another game repo against the kit's standards
    python3 tools/doctor.py --json     # machine-readable

Read-only: it runs `--version` style commands and reads files. It never installs anything.
"""
import argparse
import json
import os
import pathlib
import platform
import re
import shutil
import subprocess
import sys

KIT = pathlib.Path(__file__).resolve().parents[1]
OS = {"Windows": "windows", "Darwin": "mac"}.get(platform.system(), "linux")


def run(cmd, timeout=4):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (out.stdout or out.stderr).strip()
    except (OSError, subprocess.SubprocessError):
        return None


def version_of(exe, args=("--version",)):
    path = shutil.which(exe)
    if not path:
        return None
    out = run([path, *args]) or ""
    m = re.search(r"\d+\.\d+(\.\d+)?", out)
    return m.group(0) if m else "installed"


def pinned():
    """Versions pinned in the kit's rokit.toml."""
    pins = {}
    f = KIT / "rokit.toml"
    if f.exists():
        for line in f.read_text().splitlines():
            m = re.match(r'\s*(\w+)\s*=\s*"[^@"]+@([\d.]+)"', line)
            if m:
                pins[m.group(1)] = m.group(2)
    return pins


def find_studio():
    if OS == "windows":
        base = pathlib.Path(os.environ.get("LOCALAPPDATA", "")) / "Roblox" / "Versions"
        return any(base.glob("*/RobloxStudioBeta.exe")) if base.exists() else False
    if OS == "mac":
        return pathlib.Path("/Applications/RobloxStudio.app").exists()
    return False


def find_blender():
    if shutil.which("blender"):
        return version_of("blender")
    if OS == "windows":
        for root in [os.environ.get("ProgramFiles", r"C:\Program Files")]:
            hits = list(pathlib.Path(root, "Blender Foundation").glob("Blender*/blender.exe"))
            if hits:
                return hits[-1].parent.name.replace("Blender ", "")
    if OS == "mac" and pathlib.Path("/Applications/Blender.app").exists():
        return "installed"
    return None


def has_python_module(name):
    try:
        __import__(name)
        return True
    except ImportError:
        return False


def playwright_ready():
    node = shutil.which("node")
    if not node:
        return False
    out = run([node, "-e", "require('playwright');console.log('ok')"], timeout=6)
    if out == "ok":
        return True
    npm_root = run(["npm", "root", "-g"]) if shutil.which("npm") else None
    if npm_root:
        out = run([node, "-e", f"require('{npm_root}/playwright');console.log('ok')"], timeout=6)
    return out == "ok"


def vscode_luau_lsp():
    code = shutil.which("code")
    if not code:
        return None
    exts = run([code, "--list-extensions"], timeout=8) or ""
    return "johnnymorganz.luau-lsp" in exts.lower()


INSTALL = {
    "rokit": {"windows": "winget install rojo-rbx.rokit  (or: https://github.com/rojo-rbx/rokit/releases)",
              "mac": "brew install rokit", "linux": "curl -sSf https://raw.githubusercontent.com/rojo-rbx/rokit/main/scripts/install.sh | bash"},
    "pinned": {"all": "rokit install   (run in the repo; installs the lune, selene and rojo versions pinned in rokit.toml)"},
    "git": {"windows": "winget install Git.Git", "mac": "xcode-select --install", "linux": "sudo apt install git"},
    "python3": {"windows": "winget install Python.Python.3.12", "mac": "brew install python", "linux": "sudo apt install python3"},
    "node": {"windows": "winget install OpenJS.NodeJS.LTS", "mac": "brew install node", "linux": "sudo apt install nodejs npm"},
    "playwright": {"all": "npm i -g playwright && npx playwright install chromium"},
    "stylua": {"all": "rokit add JohnnyMorganz/StyLua   (formatter)"},
    "studio": {"windows": "https://create.roblox.com → Start Creating", "mac": "https://create.roblox.com → Start Creating", "linux": "Roblox Studio needs Windows or macOS"},
    "blender": {"windows": "winget install BlenderFoundation.Blender", "mac": "brew install --cask blender", "linux": "sudo snap install blender --classic"},
    "ffmpeg": {"windows": "winget install Gyan.FFmpeg", "mac": "brew install ffmpeg", "linux": "sudo apt install ffmpeg"},
    "pillow": {"all": "python3 -m pip install pillow"},
    "luau-lsp": {"all": "code --install-extension JohnnyMorganz.luau-lsp"},
}


def how(key):
    d = INSTALL[key]
    return d.get("all") or d.get(OS) or ""


def toolchain():
    pins = pinned()
    rows = []

    def add(name, have, need, why, key, required=True):
        ok = bool(have) and (need is None or have == need or have == "installed")
        status = "ok" if ok else ("old" if have else "missing")
        if status == "old" and need:
            status = f"have {have}, kit pins {need}"
        rows.append({"tool": name, "have": have, "need": need, "ok": ok, "status": status, "why": why,
                     "required": required, "fix": "" if ok else (how("pinned") if key == "pinned" else how(key))})

    add("git", version_of("git"), None, "version control", "git")
    add("python3", platform.python_version(), None, "checkers, doctor, hooks", "python3")
    add("node", version_of("node"), None, "web labs and the headless page checker", "node")
    add("rokit", version_of("rokit"), None, "installs the pinned Roblox toolchain", "rokit")
    add("lune", version_of("lune"), pins.get("lune"), "runs Luau tests headless", "pinned")
    add("selene", version_of("selene"), pins.get("selene"), "Luau linter", "pinned")
    add("rojo", version_of("rojo"), pins.get("rojo"), "syncs files into Studio / builds .rbxl", "pinned")
    add("Roblox Studio", "installed" if find_studio() else None, None, "play-testing", "studio", required=OS != "linux")
    add("playwright + chromium", "installed" if playwright_ready() else None, None, "checks web examples headless", "playwright", required=False)
    add("stylua", version_of("stylua"), None, "Luau formatter", "stylua", required=False)
    add("Blender", find_blender(), None, "icon and mesh pipelines", "blender", required=False)
    add("ffmpeg", version_of("ffmpeg", ("-version",)), None, "GIF and trailer captures", "ffmpeg", required=False)
    add("Pillow (Python)", "installed" if has_python_module("PIL") else None, None, "image QA scripts", "pillow", required=False)
    lsp = vscode_luau_lsp()
    if lsp is not None:
        add("VS Code Luau LSP", "installed" if lsp else None, None, "types and autocomplete in VS Code", "luau-lsp", required=False)
    return rows


def repo_audit(root: pathlib.Path):
    """What a game repo needs to meet the kit's bar. Each check is a file or pattern that's cheap to verify."""
    def exists(*names):
        return any((root / n).exists() for n in names)

    def grep(pattern, globs=("**/*.luau", "**/*.lua")):
        rx = re.compile(pattern)
        for g in globs:
            for f in root.glob(g):
                if any(p in f.parts for p in (".git", "Packages", "node_modules", "tests", "test", "tools", "qa")):
                    continue
                try:
                    if rx.search(f.read_text(encoding="utf-8", errors="ignore")):
                        return True
                except OSError:
                    pass
        return False

    claude = (root / "CLAUDE.md").read_text(encoding="utf-8", errors="ignore") if exists("CLAUDE.md") else ""
    checks = [
        ("README.md", exists("README.md"), "Add a README with the kit's headings (docs/STYLE.md)."),
        ("CLAUDE.md with the amplifier block", "amplifier:start" in claude, "Copy the amplifier block from aaa-kit/CLAUDE.md."),
        ("rokit.toml (pinned toolchain)", exists("rokit.toml", "aftman.toml"), "Copy aaa-kit/rokit.toml."),
        ("Rojo project", exists("default.project.json"), "Start from examples/framework-starter/default.project.json."),
        ("selene.toml", exists("selene.toml"), "Add selene.toml with std = \"roblox\"."),
        ("headless tests", exists("tests", "test") or any(root.glob("**/*.test.luau")), "Add lune tests for pure modules (tools/lib/t.luau)."),
        ("intensity ladder", grep(r"Intensity"), "Add a central intensity system (framework-starter Systems/Intensity)."),
        ("server-side remote validation", grep(r"OnServerEvent|OnServerInvoke") and grep(r"math\.huge|~= *\w+ *then|Guard\."),
         "Validate every remote: shape, rate, state (skill: roblox-luau-standards)."),
        ("save session lock / reconcile", grep(r"UpdateAsync|ProfileStore|reconcile|Reconcile"), "Use session-locked saves (framework-starter DataService)."),
        ("no secrets in source", not grep(r"discord(app)?\.com/api/webhooks/\d+", ("**/*.luau", "**/*.lua", "**/*.json", "**/*.md")),
         "Move webhooks and keys to HttpService:GetSecret, then rotate them."),
        ("no prints in hot paths", not grep(r"(RenderStepped|Heartbeat|Stepped):Connect\(function[^\n]*\n(?:(?!\nend\)).){0,600}?\bprint\(", ("**/*.luau", "**/*.lua")), "Remove print() from per-frame handlers."),
    ]
    return [{"check": c, "ok": bool(ok), "fix": "" if ok else fix} for c, ok, fix in checks]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--repo", default=None)
    a = ap.parse_args()

    tools = toolchain()
    root = pathlib.Path(a.repo or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()).resolve()
    is_kit = (root / "HIERARCHY.md").exists() and (root / "lexicon.json").exists()
    audit = [] if is_kit and not a.repo else repo_audit(root)

    if a.json:
        print(json.dumps({"os": OS, "tools": tools, "repo": str(root), "audit": audit}, indent=2))
        return

    req_missing = [t for t in tools if not t["ok"] and t["required"]]
    opt_missing = [t for t in tools if not t["ok"] and not t["required"]]
    print(f"Kit doctor · {platform.system()} {platform.release()} · {root.name}")
    if a.brief:
        ok = [t["tool"] for t in tools if t["ok"]]
        print(f"Ready: {', '.join(ok) or 'nothing yet'}")
        if req_missing:
            print("Needed:")
            for t in req_missing:
                print(f"  - {t['tool']} ({t['status']}): {t['fix']}")
        if opt_missing:
            print("Nice to have: " + ", ".join(f"{t['tool']}" for t in opt_missing))
        if audit:
            bad = [c for c in audit if not c["ok"]]
            print(f"Repo: {len(audit) - len(bad)}/{len(audit)} kit standards met" + (":" if bad else ""))
            for c in bad[:5]:
                print(f"  - {c['check']}: {c['fix']}")
        return

    print("\nToolchain")
    for t in tools:
        mark = "✓" if t["ok"] else ("✗" if t["required"] else "·")
        print(f"  {mark} {t['tool']:<24} {t['status']:<26} {t['why']}")
        if t["fix"]:
            print(f"      → {t['fix']}")
    if audit:
        print(f"\nRepo standards ({root})")
        for c in audit:
            print(f"  {'✓' if c['ok'] else '✗'} {c['check']}")
            if c["fix"]:
                print(f"      → {c['fix']}")
    else:
        print("\nThis is the kit itself. Run `bash tools/check_all.sh` for its full checks, or `--repo DIR` to audit a game.")
    print("\n✗ = needed for the kit's workflow · = optional")


if __name__ == "__main__":
    main()
