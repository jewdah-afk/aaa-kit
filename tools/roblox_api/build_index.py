#!/usr/bin/env python3
"""Build tools/roblox_api/api-index.json from Roblox's Full-API-Dump.json.

  python3 tools/roblox_api/build_index.py [path-to-Full-API-Dump.json]

With no argument it downloads the dump from MaximumADHD/Roblox-Client-Tracker (the current client's API).
The index keeps only what the checker needs: per class its superclass, tags and members (kind, deprecated,
not-scriptable, creatable, service), plus every enum with its items. Commit the result; re-run it when Roblox ships new API.
"""
import json
import sys
import urllib.request
from pathlib import Path

URL = "https://raw.githubusercontent.com/MaximumADHD/Roblox-Client-Tracker/roblox/Full-API-Dump.json"
OUT = Path(__file__).with_name("api-index.json")
DETAIL = Path(__file__).with_name("api-detail.json")


def load(src):
    if src:
        return json.loads(Path(src).read_text(encoding="utf-8"))
    with urllib.request.urlopen(URL, timeout=120) as r:
        return json.loads(r.read())


def build(dump):
    classes = {}
    for c in dump["Classes"]:
        tags = c.get("Tags", [])
        members = {}
        for m in c["Members"]:
            mt = m["MemberType"]
            kind = {"Property": "p", "Function": "f", "Event": "e", "Callback": "c"}[mt]
            mtags = m.get("Tags", [])
            flags = ""
            if "Deprecated" in mtags:
                flags += "D"
            if "NotScriptable" in mtags:
                flags += "N"
            members[m["Name"]] = kind + flags
        classes[c["Name"]] = {
            "super": c["Superclass"] if c["Superclass"] != "<<<ROOT>>>" else None,
            "creatable": "NotCreatable" not in tags,
            "service": "Service" in tags,
            "deprecated": "Deprecated" in tags,
            "members": members,
        }
    enums = {e["Name"]: [i["Name"] for i in e["Items"]] for e in dump["Enums"]}
    return {"version": dump.get("Version"), "classes": classes, "enums": enums}


def tname(t):
    return t["Name"] if isinstance(t, dict) else str(t)


def sec(m):
    s = m.get("Security")
    if isinstance(s, dict):
        r, w = s.get("Read"), s.get("Write")
        return r if r == w else f"{r}/{w}"
    return s or "None"


def build_detail(dump):
    """Per class: {member: "p Type [security]" | "f (a: T, b: T) -> R" | "e (a: T)"} with tags, for tools/rbx.py lookups."""
    out = {}
    for c in dump["Classes"]:
        mem = {}
        for m in c["Members"]:
            tags = ",".join(t for t in m.get("Tags", []) if isinstance(t, str))
            sc = sec(m)
            note = ("" if sc in ("None", None) else f" [{sc}]") + (f" ({tags})" if tags else "")
            if m["MemberType"] == "Property":
                mem[m["Name"]] = f"p {tname(m['ValueType'])}{note}"
            elif m["MemberType"] in ("Function", "Callback"):
                args = ", ".join(f"{a['Name']}: {tname(a['Type'])}" + (f" = {a['Default']}" if "Default" in a else "") for a in m.get("Parameters", []))
                kind = "f" if m["MemberType"] == "Function" else "c"
                mem[m["Name"]] = f"{kind} ({args}) -> {tname(m.get('ReturnType', {'Name': 'void'}))}{note}"
            else:
                args = ", ".join(f"{a['Name']}: {tname(a['Type'])}" for a in m.get("Parameters", []))
                mem[m["Name"]] = f"e ({args}){note}"
        out[c["Name"]] = mem
    return out


if __name__ == "__main__":
    dump = load(sys.argv[1] if len(sys.argv) > 1 else None)
    idx = build(dump)
    OUT.write_text(json.dumps(idx, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    DETAIL.write_text(json.dumps(build_detail(dump), separators=(",", ":"), sort_keys=True), encoding="utf-8")
    print(f"{OUT.name}: {len(idx['classes'])} classes, {len(idx['enums'])} enums, {OUT.stat().st_size // 1024} KB; {DETAIL.name}: {DETAIL.stat().st_size // 1024} KB")
