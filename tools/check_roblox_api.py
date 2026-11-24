#!/usr/bin/env python3
"""Reject Roblox API names that do not exist, so code (and Markdown Luau blocks) cannot ship a hallucinated class, enum or member.

  python3 tools/check_roblox_api.py [paths...]     files or folders; default: the whole repo. Exit 1 on any error.

Checked against tools/roblox_api/api-index.json (built from Roblox's real API dump, see build_index.py):
  Instance.new("X")                      X is a real, creatable class
  game:GetService("X")                   X is a real service
  Enum.A.B                               A is a real enum and B one of its items
  :IsA("X") / :FindFirstChildOfClass("X") / :FindFirstChildWhichIsA / :FindFirstAncestor(OfClass|WhichIsA)   X is a real class
  local v = Instance.new("X"); v.Prop / v.Prop = / v:Method()   the member exists on X or an ancestor (variables bound once only)
Deprecated members and classes are warnings. Put `-- api-ok` on a line to silence it (private test doubles, mocks).
Code outside these patterns is not checked: this is a high-precision net, not a type checker.
"""
import difflib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
INDEX = json.loads((HERE / "roblox_api" / "api-index.json").read_text(encoding="utf-8"))
CLASSES, ENUMS = INDEX["classes"], INDEX["enums"]
SKIP_DIRS = {".git", "node_modules", "__pycache__", "media", "Packages", "ServerPackages"}

LONG_COMMENT = re.compile(r"--\[(=*)\[.*?\]\1\]", re.S)
LINE_COMMENT = re.compile(r"--(?!\[=*\[).*")


def members_of(cls):
    """All members of a class including inherited ones: {name: flags}."""
    out = {}
    while cls:
        c = CLASSES.get(cls)
        if not c:
            break
        for k, v in c["members"].items():
            out.setdefault(k, v)
        cls = c["super"]
    return out


def near(name, pool):
    m = difflib.get_close_matches(name, list(pool), n=1, cutoff=0.7)
    return f" (did you mean {m[0]}?)" if m else ""


def blank_comments(src):
    """Blank out comments but keep line numbers and string contents."""
    src = LONG_COMMENT.sub(lambda m: "\n" * m.group(0).count("\n"), src)
    out = []
    for ln in src.split("\n"):
        keep_flag = "api-ok" in ln
        ln2 = LINE_COMMENT.sub("", ln) if "--" in ln and not _in_string_dashes(ln) else ln
        out.append(ln2 + ("  --api-ok" if keep_flag else ""))
    return out


def _in_string_dashes(ln):
    i = ln.find("--")
    return ln[:i].count('"') % 2 == 1 or ln[:i].count("'") % 2 == 1 or ln[:i].count("`") % 2 == 1


NEW = re.compile(r'\bInstance\.new\(\s*"([^"]+)"')
SERVICE = re.compile(r':GetService\(\s*"([^"]+)"')
ENUM = re.compile(r"\bEnum\.([A-Za-z_]\w*)(?:\.([A-Za-z_]\w*))?")
CLASSARG = re.compile(r'[:.](?:IsA|FindFirstChildOfClass|FindFirstChildWhichIsA|FindFirstAncestorOfClass|FindFirstAncestorWhichIsA)\(\s*"([^"]+)"')
BIND = re.compile(r'^\s*(?:local\s+)?([A-Za-z_]\w*)\s*(?::\s*[^=]+?)?=\s*Instance\.new\(\s*"([^"]+)"')


def check_lines(lines):
    """Return [(line_no, 'error'|'warn', message)] for a list of source lines (comments already blanked)."""
    issues = []
    ok = lambda n: "api-ok" in lines[n - 1]
    bindings = {}  # var -> set of classes bound via Instance.new
    other_assign = set()
    for n, ln in enumerate(lines, 1):
        m = BIND.match(ln)
        if m:
            bindings.setdefault(m.group(1), set()).add(m.group(2))
    for n, ln in enumerate(lines, 1):
        if ok(n):
            continue
        for (c,) in [(x,) for x in NEW.findall(ln)]:
            if c not in CLASSES:
                issues.append((n, "error", f'Instance.new("{c}"): no such class{near(c, CLASSES)}'))
            elif not CLASSES[c]["creatable"]:
                issues.append((n, "error", f'Instance.new("{c}"): class is not creatable'))
            elif CLASSES[c]["deprecated"]:
                issues.append((n, "warn", f'Instance.new("{c}"): class is deprecated'))
        for c in SERVICE.findall(ln):
            if c not in CLASSES or not CLASSES[c]["service"]:
                issues.append((n, "error", f'GetService("{c}"): no such service{near(c, [k for k, v in CLASSES.items() if v["service"]])}'))
        for e, item in ENUM.findall(ln):
            if e not in ENUMS:
                if e not in ("GetEnums",):  # Enum:GetEnums() style calls are methods, not names
                    issues.append((n, "error", f"Enum.{e}: no such enum{near(e, ENUMS)}"))
            elif item and item not in ENUMS[e] and item not in ("GetEnumItems", "FromName", "FromValue"):
                issues.append((n, "error", f"Enum.{e}.{item}: no such item{near(item, ENUMS[e])}"))
        for c in CLASSARG.findall(ln):
            if c not in CLASSES:
                issues.append((n, "error", f'class name "{c}": no such class{near(c, CLASSES)}'))
    for var, classes in bindings.items():
        if len(classes) != 1:
            continue
        cls = next(iter(classes))
        if cls not in CLASSES:
            continue
        mem = members_of(cls)
        pat = re.compile(r"(?<![\w.:])" + re.escape(var) + r"([.:])([A-Za-z_]\w*)")
        for n, ln in enumerate(lines, 1):
            if ok(n):
                continue
            for sep, name in pat.findall(ln):
                flags = mem.get(name)
                if flags is None:
                    issues.append((n, "error", f"{var} is a {cls}; it has no member {name}{near(name, mem)}"))
                elif "D" in flags:
                    issues.append((n, "warn", f"{cls}.{name} is deprecated"))
                elif "N" in flags:
                    issues.append((n, "error", f"{cls}.{name} is not scriptable"))
    return sorted(set(issues))


FENCE = re.compile(r"^```(?:lua|luau)\s*$(.*?)^```\s*$", re.S | re.M)


def check_file(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    out = []
    if path.suffix in (".luau", ".lua"):
        out += check_lines(blank_comments(text))
    elif path.suffix == ".md":
        for m in FENCE.finditer(text):
            base = text[: m.start(1)].count("\n")
            out += [(n + base, s, msg) for n, s, msg in check_lines(blank_comments(m.group(1)))]
    return out


def collect(args):
    roots = [Path(a) for a in args] or [HERE.parent]
    for r in roots:
        if r.is_file():
            yield r
            continue
        for p in sorted(r.rglob("*")):
            if p.is_file() and p.suffix in (".luau", ".lua", ".md") and not (set(p.parts) & SKIP_DIRS):
                yield p


def main(argv):
    errors = warns = checked = 0
    for p in collect(argv):
        checked += 1
        for n, sev, msg in check_file(p):
            print(f"{p}:{n}: {sev}: {msg}")
            errors += sev == "error"
            warns += sev == "warn"
    print(f"{checked} files, {errors} errors, {warns} warnings (API {INDEX['version']})")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
