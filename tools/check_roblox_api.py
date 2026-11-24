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
CLASSES, ENUMS, RETURNS = INDEX["classes"], INDEX["enums"], INDEX.get("returns", {})
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


_DESC = {}


def members_loose(cls):
    """Members of cls, its ancestors and every subclass: a value declared as `Instance` may be narrowed by IsA before use."""
    if cls not in _DESC:
        kids = {}
        for k, v in CLASSES.items():
            kids.setdefault(v["super"], []).append(k)
        out, stack = dict(members_of(cls)), list(kids.get(cls, []))
        while stack:
            k = stack.pop()
            for name, fl in CLASSES[k]["members"].items():
                out.setdefault(name, fl)
            stack.extend(kids.get(k, []))
        _DESC[cls] = out
    return _DESC[cls]


def near(name, pool):
    m = difflib.get_close_matches(name, list(pool), n=1, cutoff=0.7)
    return f" (did you mean {m[0]}?)" if m else ""


def blank_comments(src):
    """Blank out comments but keep line numbers and string contents."""
    src = LONG_COMMENT.sub(lambda m: "\n" * m.group(0).count("\n"), src)
    out = []
    for ln in src.split("\n"):
        keep_flag = "api-ok" in ln
        directive = ln.lstrip().startswith("--!")  # --!strict and friends are not comments
        ln2 = LINE_COMMENT.sub("", ln) if "--" in ln and not directive and not _in_string_dashes(ln) else ln
        out.append(ln2 + ("  --api-ok" if keep_flag else ""))
    return out


def _in_string_dashes(ln):
    i = ln.find("--")
    return ln[:i].count('"') % 2 == 1 or ln[:i].count("'") % 2 == 1 or ln[:i].count("`") % 2 == 1


NEW = re.compile(r'\bInstance\.new\(\s*"([^"]+)"')
SERVICE = re.compile(r':GetService\(\s*"([^"]+)"')
ENUM = re.compile(r"\bEnum\.([A-Za-z_]\w*)(?:\.([A-Za-z_]\w*))?")
CLASSARG = re.compile(r'[:.](?:IsA|FindFirstChildOfClass|FindFirstChildWhichIsA|FindFirstAncestorOfClass|FindFirstAncestorWhichIsA)\(\s*"([^"]+)"')
FUNC_PARAMS = re.compile(r"\bfunction\b\s*[\w.:]*\s*(?:<[^>]*>)?\(([^)]*)\)")
LOCAL_DECL = re.compile(r"^\s*local\s+(?!function\b)([^=]+?)\s*(?:=(?!=)|$)")
LOCAL_FUNC = re.compile(r"^\s*local\s+function\s+([A-Za-z_]\w*)")
FOR_DECL = re.compile(r"^\s*for\s+([\w\s,]+?)\s+(?:in\b|=)")
ANNOT = re.compile(r"^([A-Za-z_]\w*)\s*:\s*([A-Za-z_][\w.]*)(\?)?\s*$")
INIT_NEW = re.compile(r'=\s*Instance\.new\(\s*"([^"]+)"\s*\)')
INIT_SERVICE = re.compile(r'=\s*[\w.]+:GetService\(\s*"([^"]+)"\s*\)\s*$')
INIT_FIND = re.compile(r':(?:FindFirstChildOfClass|FindFirstChildWhichIsA|FindFirstAncestorOfClass|FindFirstAncestorWhichIsA)\(\s*"([^"]+)"\s*\)\s*$')
INIT_CAST = re.compile(r"=[^=].*::\s*([A-Za-z_][\w.]*)\??\s*$")  # local x = expr :: Class
CAST = re.compile(r"\(\s*[^()]*?::\s*([A-Za-z_]\w*)\??\s*\)\s*([.:])([A-Za-z_]\w*)")
SERVICE_MEMBER = re.compile(r':GetService\(\s*"([^"]+)"\s*\)\s*([.:])([A-Za-z_]\w*)')


def indent_of(ln):
    n = 0
    for ch in ln:
        if ch == "\t":
            n += 4
        elif ch == " ":
            n += 1
        else:
            break
    return n


def split_top(text):
    """Split on commas that are not inside (), {} or <>."""
    parts, depth, cur = [], 0, ""
    for ch in text:
        if ch in "({<":
            depth += 1
        elif ch in ")}>":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    return [p.strip() for p in parts if p.strip()]


def declarations(ln):
    """[(name, class_or_None)] declared on this line: locals, loop variables, function parameters."""
    out = []
    m = LOCAL_FUNC.match(ln)
    if m:
        out.append((m.group(1), None))
    m = LOCAL_DECL.match(ln)
    if m:
        names = split_top(m.group(1))
        rhs = ln[m.end(0) - 1 :] if "=" in ln[m.start(1) :] else ""
        single = len(names) == 1
        for piece in names:
            am = ANNOT.match(piece)
            if am:
                name, cls = am.group(1), am.group(2)
            else:
                nm = re.match(r"[A-Za-z_]\w*", piece)
                name, cls = (nm.group(0) if nm else None), None
            if name is None:
                continue
            if cls is not None:
                cls = (cls, True)  # annotated: may be narrowed to a subclass
            elif single:
                for rx in (INIT_NEW, INIT_SERVICE, INIT_FIND, INIT_CAST):
                    r = rx.search(ln)
                    if r:
                        cls = (r.group(1), rx is INIT_CAST or ("WhichIsA" in ln and rx is INIT_FIND))
                        break
            out.append((name, cls))
    m = FOR_DECL.match(ln)
    if m:
        for name in split_top(m.group(1)):
            out.append((name, None))
    for fm in FUNC_PARAMS.finditer(ln):
        for piece in split_top(fm.group(1)):
            am = ANNOT.match(piece)
            if am:
                out.append((am.group(1), (am.group(2), True)))
            else:
                nm = re.match(r"[A-Za-z_]\w*", piece)
                if nm:
                    out.append((nm.group(0), None))
    return out


USER_TYPE = re.compile(r"^\s*(?:export\s+)?type\s+([A-Za-z_]\w*)")


def user_types(lines):
    """Names this file defines with `type X =`: they shadow Roblox classes of the same name (export type Frame = ...)."""
    return {m.group(1) for ln in lines for m in [USER_TYPE.match(ln)] if m}


GLOBAL_CLASS = {"workspace": "Workspace", "game": "DataModel"}
CALL_INIT = re.compile(r"^\s*local\s+([A-Za-z_]\w*)\s*(?::[^=]+)?=\s*(.+?)\s*$")
RECV_CALL = re.compile(r"^([A-Za-z_]\w*)\s*:\s*([A-Za-z_]\w*)\s*\(")
SERVICE_CALL = re.compile(r"^[A-Za-z_][\w.]*\s*:\s*GetService\(\s*\"([^\"]+)\"\s*\)\s*:\s*([A-Za-z_]\w*)\s*\(")


def returns_of(cls, method):
    while cls:
        r = RETURNS.get(cls, {}).get(method)
        if r:
            return r
        cls = CLASSES[cls]["super"] if cls in CLASSES else None
    return None


def whole_call(rhs, open_idx):
    """True when the parenthesis opened at rhs[open_idx] closes at the very end of rhs (the expression is exactly one call)."""
    depth = 0
    for i in range(open_idx, len(rhs)):
        depth += rhs[i] == "("
        depth -= rhs[i] == ")"
        if depth == 0:
            return i == len(rhs) - 1
    return False


def scope_end(lines, decls, i, name, is_func):
    """Index (0-based, exclusive) where a variable declared on line i stops being trustworthy."""
    base = indent_of(lines[i])
    reassign = re.compile(r"^\s*" + re.escape(name) + r"\s*=(?!=)")
    for j in range(i + 1, len(lines)):
        ln = lines[j]
        if not ln.strip():
            continue
        ind = indent_of(ln)
        if (ind <= base) if is_func else (ind < base):
            return j  # the block that declared it has closed
        if any(n == name for n, _ in decls[j]) or reassign.match(ln):
            return j  # shadowed or reassigned: stop trusting the type
    return len(lines)


def typed_scopes(lines, own_types=frozenset()):
    """[(var, class, first_line, last_line, loose)] 1-based inclusive: where a variable's class is known and not shadowed or reassigned.
    Classes come from annotations, `:: Class` casts, Instance.new, GetService, FindFirstChildOfClass, and the declared return
    type of a method called on an already typed value (`local img = AssetService:CreateEditableImage()`)."""
    decls = [declarations(ln) for ln in lines]
    scopes = []
    seen = set()

    def add(i, name, cls, loose):
        is_func = bool(FUNC_PARAMS.search(lines[i])) and not LOCAL_DECL.match(lines[i])
        scopes.append((name, cls, i + 2, scope_end(lines, decls, i, name, is_func), loose))
        seen.add((i, name))

    for i, ds in enumerate(decls):
        for name, tagged in ds:
            if tagged is None:
                continue
            cls, loose = tagged
            if cls in CLASSES and cls not in own_types:
                add(i, name, cls, loose)

    def class_at(var, n):
        for v, c, first, last, loose in scopes:
            if v == var and first <= n <= last:
                return c
        return GLOBAL_CLASS.get(var) if not any(var == nm for ds in decls for nm, _ in ds) else None

    for _ in range(3):  # chains: a = svc:Make(); b = a:Child()
        grew = False
        for i, ln in enumerate(lines):
            m = CALL_INIT.match(ln)
            if not m or (i, m.group(1)) in seen or len(declarations(ln)) != 1:
                continue
            name, rhs = m.group(1), m.group(2)
            recv_cls, method, end = None, None, None
            sm = SERVICE_CALL.match(rhs)
            if sm and sm.group(1) in CLASSES:
                recv_cls, method, end = sm.group(1), sm.group(2), sm.end() - 1
            else:
                rm = RECV_CALL.match(rhs)
                if rm:
                    recv_cls, method, end = class_at(rm.group(1), i + 1), rm.group(2), rm.end() - 1
            if not recv_cls or recv_cls not in CLASSES or not whole_call(rhs, end):
                continue
            ret = returns_of(recv_cls, method)
            if ret and ret in CLASSES and ret not in own_types and ret != "Instance":  # a bare Instance (WaitForChild, Clone) says nothing: its children are read by name
                add(i, name, ret, True)  # the declared return may be narrowed (BasePart -> Part): accept subclass members
                grew = True
        if not grew:
            break
    return scopes


def member_issue(var_label, cls, sep, name, mem, strict, after, n):
    """Issue tuple or None for `<value of class cls><sep><name>`; `after` is the text following the member name."""
    flags = mem.get(name)
    is_assign = bool(re.match(r"\s*=(?!=)", after))
    is_call = after.lstrip().startswith("(") or after.lstrip().startswith("{") or after.lstrip().startswith('"')
    is_event_use = bool(re.match(r"\s*:\s*(?:Connect|Once|Wait|ConnectParallel)\b", after))  # X.Name:Connect(...) can only be an event
    if flags is None:
        if CLASSES[cls]["service"] and sep == "." and not (is_assign or is_call or is_event_use):
            return None  # services are indexed for children (ReplicatedStorage.Packages)
        sev = "error" if (sep == ":" or is_assign or is_call or is_event_use or strict) else "warn"
        what = "method" if sep == ":" else "member"
        return (n, sev, f"{var_label} is a {cls}; it has no {what} {name}{near(name, mem)}")
    if flags[0] == "p" and sep == ":":
        return (n, "error", f"{cls}.{name} is a property, not a method")
    if "D" in flags:
        return (n, "warn", f"{cls}.{name} is deprecated")
    if "N" in flags:
        return (n, "error", f"{cls}.{name} is not scriptable")
    return None


def check_lines(lines):
    """Return [(line_no, 'error'|'warn', message)] for a list of source lines (comments already blanked)."""
    issues = []
    ok = lambda n: "api-ok" in lines[n - 1]
    strict = any(ln.strip().startswith("--!strict") for ln in lines[:5])
    own_types = user_types(lines)
    for n, ln in enumerate(lines, 1):
        if ok(n):
            continue
        for c in NEW.findall(ln):
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
                issues.append((n, "error", f"Enum.{e}: no such enum{near(e, ENUMS)}"))
            elif item and item not in ENUMS[e] and item not in ("GetEnumItems", "FromName", "FromValue"):
                issues.append((n, "error", f"Enum.{e}.{item}: no such item{near(item, ENUMS[e])}"))
        for c in CLASSARG.findall(ln):
            if c not in CLASSES:
                issues.append((n, "error", f'class name "{c}": no such class{near(c, CLASSES)}'))
        for cls, sep, name in [(m.group(1), m.group(2), m.group(3)) for m in SERVICE_MEMBER.finditer(ln)]:
            if cls in CLASSES:
                after = ln[ln.index(name, ln.index(f'"{cls}"')) + len(name) :]
                r = member_issue(f'GetService("{cls}")', cls, sep, name, members_of(cls), strict, after, n)
                if r:
                    issues.append(r)
        for m in CAST.finditer(ln):
            cls, sep, name = m.groups()
            if cls in CLASSES and cls not in own_types:
                r = member_issue("value", cls, sep, name, members_of(cls), strict, ln[m.end() :], n)
                if r:
                    issues.append(r)
    declared = {n for ln in lines for n, _ in declarations(ln)}
    for g, gcls in GLOBAL_CLASS.items():
        if g in declared or gcls in own_types:
            continue
        gpat = re.compile(r"(?<![\w.:\"'])" + g + r"(:)([A-Za-z_]\w*)")
        for n, ln in enumerate(lines, 1):
            if ok(n):
                continue
            for m in gpat.finditer(ln):
                r = member_issue(g, gcls, m.group(1), m.group(2), members_of(gcls), strict, ln[m.end() :], n)
                if r:
                    issues.append(r)
    for var, cls, first, last, loose in typed_scopes(lines, own_types):
        mem = members_loose(cls) if loose else members_of(cls)
        pat = re.compile(r"(?<![\w.:\"'])" + re.escape(var) + r"([.:])([A-Za-z_]\w*)")
        for n in range(first, last + 1):
            if ok(n):
                continue
            ln = lines[n - 1]
            for m in pat.finditer(ln):
                r = member_issue(var, cls, m.group(1), m.group(2), mem, strict, ln[m.end() :], n)
                if r:
                    issues.append(r)
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
