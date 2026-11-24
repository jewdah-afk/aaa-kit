#!/usr/bin/env python3
"""Audit the prose of the research chapters, playbooks and skills against Roblox's real API dump.

  python3 tools/audit_research.py [paths...]      default: docs/research, docs/playbooks, .claude/skills. Exit 1 on any finding.
  python3 tools/audit_research.py --unverified    count the [UNVERIFIED] markers per chapter instead

check_roblox_api.py checks code blocks. This checks the inline `code` spans in the text around them, where a chapter says
"`ParticleEmitter.Rate` ..." or "`Part:Foo()`" or "`Enum.Material.Plasma`" and may be wrong or out of date:
  `Class.Member`, `Class:Method(...)`, `Enum.Name.Item`, `Enum.Name`   Class / Enum is a real name and the member / item exists
Only spans that start with a real class or enum name are judged, so prose, file names and other libraries are left alone.
A span is skipped when its line says it is wrong on purpose (contains "not a real", "does not exist", "no such", "invented",
"hallucinat", "removed", "deprecated", "legacy", "never use", "old signature", "no documented", "**Then:**") or when the line
carries `api-ok` (for example in an HTML comment).
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check_roblox_api as api  # noqa: E402

CLASSES, ENUMS = api.CLASSES, api.ENUMS
KIT = HERE.parent
SPAN = re.compile(r"(?<!`)`([^`\n]+)`(?!`)")
ENUM_SPAN = re.compile(r"^Enum\.([A-Za-z_]\w*)(?:\.([A-Za-z_]\w*))?$")
MEMBER_SPAN = re.compile(r"^([A-Z][A-Za-z0-9_]*)([.:])([A-Za-z_]\w*)\s*(?:\(.*)?$")
EXCUSE = re.compile(r"not a real|does not exist|doesn.t exist|no such|invented|hallucinat|removed|deprecated|legacy|never use|not exist|"
                    r"gone|renamed|replaced|old name|old signature|used to|instead of|not available|unavailable|no documented|there is no|"
                    r"\*\*then:?\*\*|\[UNVERIFIED\]|api-ok", re.I)
FENCE = re.compile(r"^```")
KNOWN_CHILDREN = api.KNOWN_CHILDREN


def audit_text(text):
    out, in_code, prev_excused = [], False, False
    for n, ln in enumerate(text.splitlines(), 1):
        if FENCE.match(ln.strip()):
            in_code = not in_code
            continue
        excused = bool(EXCUSE.search(ln))
        skip = in_code or excused or prev_excused  # an excuse also covers the continuation line right after it
        prev_excused = excused
        if skip:
            continue
        for m in SPAN.finditer(ln):
            span = m.group(1).strip()
            em = ENUM_SPAN.match(span)
            if em:
                e, item = em.groups()
                if e not in ENUMS:
                    out.append((n, f"`{span}`: no such enum{api.near(e, ENUMS)}"))
                elif item and item not in ENUMS[e]:
                    out.append((n, f"`{span}`: Enum.{e} has no item {item}{api.near(item, ENUMS[e])}"))
                continue
            mm = MEMBER_SPAN.match(span)
            if mm and mm.group(1) in CLASSES and mm.group(1) != "Object":
                cls, sep, name = mm.groups()
                if name[0].islower():
                    continue  # API members are PascalCase: this is `Instance.new`, `X.yaml`, `Object.keys`
                if sep == "." and (CLASSES[cls]["service"] or name in KNOWN_CHILDREN.get(cls, ())):
                    continue  # services and Player are looked up by child name: ReplicatedStorage.Packages, Player.PlayerGui
                mem = api.members_loose(cls)  # prose often means "any subclass"; stay precise-first
                if name not in mem:
                    out.append((n, f"`{span}`: {cls} has no member {name}{api.near(name, mem)}"))
    return out


def collect(args):
    roots = [Path(a) for a in args] or [KIT / "docs" / "research", KIT / "docs" / "playbooks", KIT / ".claude" / "skills"]
    for r in roots:
        if r.is_file():
            yield r
        else:
            yield from sorted(p for p in r.rglob("*.md") if not ({"node_modules", ".git"} & set(p.parts)))


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if "--unverified" in argv:
        rows = sorted(((p.read_text(encoding="utf-8", errors="replace").count("[UNVERIFIED]"), p) for p in collect(args)), reverse=True)
        for c, p in rows:
            if c:
                print(f"{c:4}  {p.relative_to(KIT) if KIT in p.parents else p}")
        print(f"{sum(c for c, _ in rows)} [UNVERIFIED] markers in {sum(1 for c, _ in rows if c)} files")
        return 0
    found = checked = 0
    for p in collect(args):
        checked += 1
        for n, msg in audit_text(p.read_text(encoding="utf-8", errors="replace")):
            print(f"{p.relative_to(KIT) if KIT in p.parents else p}:{n}: {msg}")
            found += 1
    print(f"{checked} files, {found} findings")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
