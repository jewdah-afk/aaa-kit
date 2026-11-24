#!/usr/bin/env python3
"""SessionStart hook: make sure the pinned lune and selene exist, so the edit-time checks can run from a phone.

A cloud session starts in a fresh container, and the checks in tools/hooks/edit_checks.py need lune (tests, compile) and selene
(lint). This installs the versions pinned in rokit.toml from the official GitHub releases when they are missing. It only runs
in a cloud session (CLAUDE_CODE_REMOTE=true), or with --force, so a PC that uses rokit is left alone.

Linux x86_64 only. The archives are fetched from github.com/<owner>/<repo>/releases at the pinned version; GitHub does not publish
checksums for these assets, so the trust is the same as rokit's: the official release over TLS. A failed install is reported in
one line and never blocks the session. Stdout of a SessionStart hook becomes context for Claude, so this prints at most two lines.
"""
import os
import platform
import re
import shutil
import stat
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]

# tool -> (release URL template, executable inside the zip)
RELEASES = {
    "lune": ("https://github.com/lune-org/lune/releases/download/v{v}/lune-{v}-linux-x86_64.zip", "lune"),
    "selene": ("https://github.com/Kampfkarren/selene/releases/download/{v}/selene-{v}-linux.zip", "selene"),
}


def pins():
    out = {}
    try:
        text = (KIT / "rokit.toml").read_text(encoding="utf-8")
    except OSError:
        return out
    for name, version in re.findall(r'^(\w+)\s*=\s*"[^"@]+@([0-9][^"]*)"', text, re.M):
        out[name] = version
    return out


def bin_dir():
    for d in (Path("/usr/local/bin"), Path.home() / ".local" / "bin"):
        try:
            d.mkdir(parents=True, exist_ok=True)
            if os.access(d, os.W_OK):
                return d
        except OSError:
            continue
    return None


def install(name, version, dest):
    url, member = RELEASES[name][0].format(v=version), RELEASES[name][1]
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "pkg.zip"
        with urllib.request.urlopen(url, timeout=60) as r, open(archive, "wb") as f:
            shutil.copyfileobj(r, f)
        with zipfile.ZipFile(archive) as z:
            if member not in z.namelist():  # extract exactly one named member, never a path from the archive
                raise RuntimeError(f"{member} not in {url}")
            data = z.read(member)
        target = dest / name
        target.write_bytes(data)
        target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def main(argv):
    if os.environ.get("CLAUDE_CODE_REMOTE") != "true" and "--force" not in argv:
        return 0
    if platform.system() != "Linux" or platform.machine() not in ("x86_64", "AMD64"):
        return 0
    want = pins()
    missing = [n for n in RELEASES if n in want and not shutil.which(n)]
    if not missing:
        return 0
    dest = bin_dir()
    if dest is None:
        print("aaa-kit: no writable bin directory, so lune/selene were not installed")
        return 0
    done, failed = [], []
    for name in missing:
        try:
            install(name, want[name], dest)
            done.append(f"{name} {want[name]}")
        except Exception as e:  # network, proxy, archive: never block the session
            failed.append(f"{name} ({type(e).__name__}: {str(e)[:80]})")
    if done:
        hint = "" if str(dest) in os.environ.get("PATH", "").split(os.pathsep) else f" (add {dest} to PATH)"
        print(f"aaa-kit: installed {', '.join(done)} in {dest}{hint}")
    if failed:
        print(f"aaa-kit: could not install {', '.join(failed)}; edit checks will skip them")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
