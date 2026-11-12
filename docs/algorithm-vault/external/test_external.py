#!/usr/bin/env python3
"""Checks external/methods.json: valid JSON, unique ids, required keys, combos resolve,
verification values, null url when unverified, implemented_in_kit paths exist.

Usage: python3 docs/algorithm-vault/external/test_external.py
Prints "N entries, 0 errors" and exits non-zero if anything is wrong. Stdlib only.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
METHODS = os.path.join(HERE, "methods.json")

REQUIRED = [
    "id", "name", "family", "principle", "source", "implementation_refs", "license",
    "visual_result", "difficulty", "cost", "roblox_fit", "offline_fit", "combos",
    "verification", "implemented_in_kit",
]
SOURCE_KEYS = ["title", "authors", "year", "url", "kind"]
KINDS = {"paper", "repo", "blog", "docs", "book"}
FAMILIES = set("ABCDEFGHIJ") | {"X-other"}
VERIFICATION = {"source-verified", "unverified-source"}
ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def check(entries):
    errors = []
    if not isinstance(entries, list):
        return ["top level must be a JSON array"]
    ids = [e.get("id") for e in entries if isinstance(e, dict)]
    known = set(ids)
    seen = set()
    for i, e in enumerate(entries):
        where = f"entry {i} ({e.get('id', '?') if isinstance(e, dict) else '?'})"
        if not isinstance(e, dict):
            errors.append(f"{where}: not an object")
            continue
        for k in REQUIRED:
            if k not in e:
                errors.append(f"{where}: missing key '{k}'")
        eid = e.get("id")
        if not isinstance(eid, str) or not ID_RE.match(eid):
            errors.append(f"{where}: id must be kebab-case")
        elif eid in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(eid)
        if e.get("family") not in FAMILIES:
            errors.append(f"{where}: family must be A-J or X-other")
        d = e.get("difficulty")
        if not isinstance(d, int) or not 1 <= d <= 5:
            errors.append(f"{where}: difficulty must be an int 1-5")
        src = e.get("source")
        if not isinstance(src, dict):
            errors.append(f"{where}: source must be an object")
            src = {}
        for k in SOURCE_KEYS:
            if k not in src:
                errors.append(f"{where}: source missing '{k}'")
        if src.get("kind") not in KINDS:
            errors.append(f"{where}: source.kind must be one of {sorted(KINDS)}")
        ver = e.get("verification")
        if ver not in VERIFICATION:
            errors.append(f"{where}: verification must be one of {sorted(VERIFICATION)}")
        url = src.get("url")
        if ver == "unverified-source" and url is not None:
            errors.append(f"{where}: url must be null when unverified")
        if ver == "source-verified" and not (isinstance(url, str) and url.startswith("https://")):
            errors.append(f"{where}: verified entry needs an https url")
        refs = e.get("implementation_refs")
        if not isinstance(refs, list):
            errors.append(f"{where}: implementation_refs must be a list")
        else:
            for r in refs:
                if not (isinstance(r, dict) and {"title", "url", "license"} <= set(r)):
                    errors.append(f"{where}: implementation_refs items need title, url, license")
        combos = e.get("combos")
        if not isinstance(combos, list):
            errors.append(f"{where}: combos must be a list")
        else:
            for c in combos:
                if c not in known:
                    errors.append(f"{where}: combo '{c}' is not an id")
                if c == eid:
                    errors.append(f"{where}: combos itself")
        kit = e.get("implemented_in_kit")
        if kit != "no":
            if not isinstance(kit, str) or kit.startswith("/") or ".." in kit.split("/"):
                errors.append(f"{where}: implemented_in_kit must be 'no' or a repo-relative path")
            elif not os.path.exists(os.path.join(REPO, kit)):
                errors.append(f"{where}: implemented_in_kit path not found: {kit}")
    return errors


def main():
    try:
        with open(METHODS, encoding="utf-8") as f:
            entries = json.load(f)
    except (OSError, ValueError) as exc:
        print(f"0 entries, 1 errors\n  cannot load methods.json: {exc}")
        return 1
    errors = check(entries)
    for err in errors:
        print("  " + err)
    print(f"{len(entries)} entries, {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
