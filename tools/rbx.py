#!/usr/bin/env python3
"""Look Roblox facts up instead of recalling them. Every answer comes from Roblox's real API dump or this kit's own docs.

  python3 tools/rbx.py class ParticleEmitter [--inherited]   what a class is: parents, flags, its members with types (own only by default)
  python3 tools/rbx.py member ParticleEmitter.Emit           one member, found through inheritance (also: Workspace.Raycast)
  python3 tools/rbx.py member Raycast                        which classes define a member of that name
  python3 tools/rbx.py enum Material [filter]                an enum's items
  python3 tools/rbx.py find <term>                           classes, enums and members whose name contains the term (fuzzy suggestions if none)
  python3 tools/rbx.py research <words...> [-n 5]            ranked sections of docs/research, playbooks and skills (BM25), with file:line

Rule for sessions: if you are about to write a Roblox class, property, method, event or Enum item from memory and you are
not certain, run this first. `check_roblox_api.py` will reject names that do not exist, but a lookup is cheaper than a retry.
Data: tools/roblox_api/api-index.json and api-detail.json (rebuild with tools/roblox_api/build_index.py).
"""
import difflib
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KIT = HERE.parent
API = HERE / "roblox_api"
_cache = {}


def index():
    if "i" not in _cache:
        _cache["i"] = json.loads((API / "api-index.json").read_text(encoding="utf-8"))
    return _cache["i"]


def detail():
    if "d" not in _cache:
        _cache["d"] = json.loads((API / "api-detail.json").read_text(encoding="utf-8"))
    return _cache["d"]


def chain(cls):
    out = []
    while cls:
        out.append(cls)
        cls = index()["classes"][cls]["super"]
    return out


def fmt(sig):
    sig = sig.replace("-> null", "-> ()")
    return re.sub(r"= (\w+)\{[^}]*\}", r"= \1{...}", sig)  # RaycastParams{IgnoreWater=false, ...} defaults are noise


def suggest(name, pool):
    m = difflib.get_close_matches(name, list(pool), n=3, cutoff=0.6)
    return f"  did you mean: {', '.join(m)}" if m else ""


def cmd_class(args):
    inherited = "--inherited" in args
    names = [a for a in args if not a.startswith("--")]
    if not names:
        return "usage: rbx.py class <Name> [--inherited]"
    name = names[0]
    classes = index()["classes"]
    if name not in classes:
        return f"no class {name!r}.{suggest(name, classes)}"
    c = classes[name]
    flags = [f for f, on in (("service", c["service"]), ("creatable", c["creatable"]), ("DEPRECATED", c["deprecated"])) if on]
    lines = [f"{name}  <  {' < '.join(chain(name)[1:]) or '(root)'}  [{', '.join(flags) or 'not creatable'}]"]
    for owner in chain(name) if inherited else [name]:
        mem = detail()[owner]
        if not mem:
            continue
        if inherited:
            lines.append(f"-- {owner}")
        for kind, title in (("p", "properties"), ("f", "methods"), ("e", "events"), ("c", "callbacks")):
            rows = [f"  {k}: {fmt(v[2:])}" for k, v in sorted(mem.items()) if v[0] == kind]
            if rows:
                lines.append(f" {title}:")
                lines += rows
    if not inherited:
        lines.append(f"(own members only; --inherited adds {', '.join(chain(name)[1:]) or 'nothing'})")
    return "\n".join(lines)


def find_member(cls, member):
    for owner in chain(cls):
        if member in detail()[owner]:
            return owner, detail()[owner][member]
    return None, None


def cmd_member(args):
    if not args:
        return "usage: rbx.py member Class.Member | Member"
    target = args[0]
    classes = index()["classes"]
    if "." in target:
        cls, member = target.split(".", 1)
        if cls not in classes:
            return f"no class {cls!r}.{suggest(cls, classes)}"
        owner, sig = find_member(cls, member)
        if not sig:
            pool = {m for o in chain(cls) for m in detail()[o]}
            return f"{cls} has no member {member!r} (checked {' < '.join(chain(cls))}).{suggest(member, pool)}"
        via = "" if owner == cls else f"  (inherited from {owner})"
        return f"{cls}.{member}: {fmt(sig)}{via}"
    hits = [(c, m[target]) for c, m in detail().items() if target in m]
    if not hits:
        pool = {k for m in detail().values() for k in m}
        return f"no class defines {target!r}.{suggest(target, pool)}"
    return "\n".join(f"{c}.{target}: {fmt(s)}" for c, s in sorted(hits)[:40]) + (f"\n... {len(hits) - 40} more" if len(hits) > 40 else "")


def cmd_enum(args):
    if not args:
        return "usage: rbx.py enum <Name> [filter]"
    enums = index()["enums"]
    if args[0] not in enums:
        return f"no enum {args[0]!r}.{suggest(args[0], enums)}"
    items = enums[args[0]]
    if len(args) > 1:
        items = [i for i in items if args[1].lower() in i.lower()]
    return f"Enum.{args[0]} ({len(items)} items): " + ", ".join(items)


def cmd_find(args):
    term = " ".join(args).strip()
    if not term:
        return "usage: rbx.py find <term>"
    t = term.lower()
    idx = index()
    out = [f"class  {c}" for c in sorted(idx["classes"]) if t in c.lower()][:15]
    out += [f"enum   {e}" for e in sorted(idx["enums"]) if t in e.lower()][:10]
    for c, mem in sorted(detail().items()):
        for m, sig in mem.items():
            if t in m.lower():
                out.append(f"member {c}.{m}: {fmt(sig)}")
    if not out:
        pool = set(idx["classes"]) | set(idx["enums"]) | {m for mem in detail().values() for m in mem}
        return f"nothing matches {term!r}. {suggest(term, pool)}".rstrip()
    return "\n".join(out[:40]) + (f"\n... {len(out) - 40} more; narrow the term" if len(out) > 40 else "")


# ---- research search: BM25 over Markdown sections --------------------------------------------------------------------
WORD = re.compile(r"[A-Za-z][A-Za-z0-9_]+")
HEAD = re.compile(r"^(#{1,4})\s+(.*)$")


def sections():
    if "s" in _cache:
        return _cache["s"]
    files = sorted((KIT / "docs" / "research").glob("*.md")) + sorted((KIT / "docs" / "playbooks").glob("*.md"))
    files += sorted((KIT / ".claude" / "skills").glob("*/SKILL.md")) + sorted((KIT / ".claude" / "skills").glob("*/patterns.md"))
    out = []
    for f in files:
        title, start, body, in_code = f.stem, 1, [], False
        lines = f.read_text(encoding="utf-8", errors="replace").splitlines()

        def flush(end):
            text = "\n".join(body)
            if text.strip():
                out.append({"file": f.relative_to(KIT).as_posix(), "line": start, "title": title, "text": text})

        for n, ln in enumerate(lines, 1):
            if ln.startswith("```"):
                in_code = not in_code
            m = None if in_code else HEAD.match(ln)
            if m:
                flush(n)
                title, start, body = f"{f.stem}: {m.group(2).strip()}", n, []
            else:
                body.append(ln)
        flush(len(lines))
    _cache["s"] = out
    return out


def tokens(text):
    return [w.lower() for w in WORD.findall(text)]


def cmd_research(args):
    n = 5
    if "-n" in args:
        i = args.index("-n")
        n = int(args[i + 1])
        args = args[:i] + args[i + 2 :]
    q = tokens(" ".join(args))
    if not q:
        return "usage: rbx.py research <words...> [-n 5]"
    secs = sections()
    docs = [tokens(s["title"] + " " + s["title"] + " " + s["text"]) for s in secs]  # the heading counts double
    avg = sum(map(len, docs)) / len(docs)
    df = {}
    for d in docs:
        for w in set(d):
            df[w] = df.get(w, 0) + 1
    scored = []
    for s, d in zip(secs, docs):
        tf = {}
        for w in d:
            tf[w] = tf.get(w, 0) + 1
        score = 0.0
        for w in set(q):
            if w in tf:
                idf = math.log(1 + (len(docs) - df[w] + 0.5) / (df[w] + 0.5))
                score += idf * tf[w] * 2.2 / (tf[w] + 1.2 * (0.25 + 0.75 * len(d) / avg))
        if score:
            scored.append((score, s))
    scored.sort(key=lambda x: -x[0])
    if not scored:
        return "no section matches. Try the exact API or term name (python3 tools/rbx.py find <term>)."
    out = []
    for score, s in scored[:n]:
        body = [ln.strip() for ln in s["text"].splitlines() if ln.strip() and not ln.startswith("```")]
        hit = next((ln for ln in body if any(w in ln.lower() for w in q)), body[0] if body else "")
        out.append(f"{s['file']}:{s['line']}  {s['title']}\n    {hit[:200]}")
    return "\n".join(out)


COMMANDS = {"class": cmd_class, "member": cmd_member, "enum": cmd_enum, "find": cmd_find, "research": cmd_research}


def main(argv):
    if not argv or argv[0] not in COMMANDS:
        print(__doc__)
        return 2
    print(COMMANDS[argv[0]](argv[1:]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
