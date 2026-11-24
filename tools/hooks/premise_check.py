#!/usr/bin/env python3
"""UserPromptSubmit hook: catch Roblox API names in the prompt that do not exist, before the model answers.

Why: in tools/evals/RESULTS.md the model never invented an API on its own, but about half its answers did when the prompt
itself asserted a fake one ("Use EditableImage:Clear ..."). This hook reads the prompt, finds API-shaped names, checks each
against Roblox's real API dump (tools/roblox_api/api-index.json) and, for each one that is missing, tells the model so and
gives the real alternative. It never blocks a prompt and prints nothing when every name is real.

What counts as an API name (kept narrow so ordinary prose and Studio paths are not flagged):
  Class:Method            receiver is an exact class name, `workspace`/`game`, or game:GetService("Class")
  Class.Member(  Class.Member =   Class.Member property|method|event    (a bare Class.Child is a child lookup, not checked)
  Class's Member property|method|...      the Member property of Class
  Service.Member          bare, in prose, only on services that do not hold children (RunService.Update, not ReplicatedStorage.Remotes)
  Class.Event:Connect     the event is checked on the class
  Enum.Type.Item
Strict receivers (exact class name) are flagged when the member is on neither the class, its ancestors nor its subclasses.
Loose receivers (a variable named like a class, `part:Delete`, or a child access, `script.Parent.Humanoid:X`) are flagged only
when no Roblox class defines that member at all.

Hook output: JSON with hookSpecificOutput.additionalContext. Exits 0 on any error so a broken hook can't stop work.
"""
import difflib
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GLOBALS = {"workspace": "Workspace", "game": "DataModel", "Workspace": "Workspace"}
FILE_EXT = {"lua", "luau", "json", "md", "py", "txt", "ts", "js", "mjs", "html", "rbxl", "rbxm", "rbxlx", "rbxmx", "toml", "yml", "yaml", "png", "gif"}
KEYWORD = r"(?:property|method|function|event|signal|callback|field)"
MAX_FINDINGS = 8

ID = r"[A-Za-z_][A-Za-z0-9_]*"
COLON = re.compile(rf"(?<![\w.:])({ID})((?:\.{ID})*):({ID})")         # Recv(.a.b):Method, with the dotted tail
SERVICE = re.compile(rf"GetService\(\s*[\"'](\w+)[\"']\s*\)(:)({ID})")         # GetService("X").Child is a child lookup
DOT_CALL = re.compile(rf"(?<![\w.:])({ID})\.({ID})(\(|\s*=(?!=)|\s+{KEYWORD}\b)")
POSSESSIVE = re.compile(rf"\b([A-Z]\w*)['’]s\s+({ID})(?:\(\))?\s+{KEYWORD}\b")
OF_FORM = re.compile(rf"\b([A-Z]\w*)(?:\(\))?\s+{KEYWORD}\s+(?:of|on)\s+(?:the\s+|a\s+|an\s+)?([A-Z]\w*)\b")
BARE = re.compile(rf"(?:(?<=\s)|(?<=^)|(?<=`))({ID})\.({ID})(?=`|\s|$|[,;!?]|\.(?:\s|$))", re.M)  # Service.Member as a prose word
SIGNAL_USE = {"Connect", "Once", "Wait", "ConnectParallel"}
# Services that hold children people name in paths (ReplicatedStorage.Remotes, Players.Alice): a bare dot there is a child lookup.
CONTAINERS = {"Workspace", "ReplicatedStorage", "ReplicatedFirst", "ServerStorage", "ServerScriptService", "StarterGui", "StarterPack",
              "StarterPlayer", "Lighting", "Players", "Teams", "SoundService", "Chat", "TextChatService", "MaterialService", "CoreGui", "Packages"}
ENUM = re.compile(rf"\bEnum\.({ID})(?:\.({ID}))?")


def api_dir(root=None):
    for base in [root, os.environ.get("CLAUDE_PROJECT_DIR"), str(HERE.parent.parent)]:
        if base and (Path(base) / "tools" / "roblox_api" / "api-index.json").exists():
            return Path(base) / "tools" / "roblox_api"
    return None


class Api:
    def __init__(self, folder: Path, curated=None):
        idx = json.loads((folder / "api-index.json").read_text(encoding="utf-8"))
        self.classes, self.enums = idx["classes"], idx["enums"]
        self.folder = folder
        self.children = {}
        for name, c in self.classes.items():
            if c["super"]:
                self.children.setdefault(c["super"], []).append(name)
        self.anywhere = {}
        for name, c in self.classes.items():
            for m in c["members"]:
                self.anywhere.setdefault(m, []).append(name)
        if curated is None:
            p = folder / "premise-alternatives.json"
            curated = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
        self.fakes = curated.get("fakes", {})
        self.deprecated = curated.get("deprecated", {})
        self._detail = None

    def detail(self):
        if self._detail is None:
            p = self.folder / "api-detail.json"
            self._detail = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
        return self._detail

    def chain(self, cls):
        out = []
        while cls:
            out.append(cls)
            cls = self.classes[cls]["super"]
        return out

    def descendants(self, cls):
        out, todo = [], list(self.children.get(cls, []))
        while todo:
            c = todo.pop()
            out.append(c)
            todo += self.children.get(c, [])
        return out

    def lookup(self, cls, member):
        """(owner, flags) for member on cls or an ancestor, else (None, None)."""
        for owner in self.chain(cls):
            f = self.classes[owner]["members"].get(member)
            if f is not None:
                return owner, f
        return None, None

    def curated(self, table, cls, member):
        for owner in self.chain(cls):
            hit = table.get(f"{owner}.{member}")
            if hit:
                return hit
        return None

    def show(self, ref):
        """`Class:Method(sig)` or `Class.Prop` for a real Class.Member reference."""
        cls, member = ref.split(".", 1)
        if cls not in self.classes:
            return f"`{ref}`"
        owner, flags = self.lookup(cls, member)
        if not owner:
            return f"`{ref}`"
        if flags[0] in "fc":
            sig = self.detail().get(owner, {}).get(member, "")
            m = re.match(r"[fc] (\([^)]*\))", sig)
            args = re.sub(r"= (\w+)\{[^}]*\}\}?", r"= \1{...}", m.group(1)) if m else "(...)"
            return f"`{cls}:{member}{args}`"
        return f"`{cls}.{member}`" + (" (event)" if flags[0] == "e" else " (property)")


def candidates(text):
    """Yield (receiver, sep, member, mode) where mode is 'strict', 'loose' or 'enum'."""
    for m in SERVICE.finditer(text):
        yield m.group(1), m.group(2), m.group(3), "strict"
    for m in COLON.finditer(text):
        head, tail, member = m.group(1), m.group(2), m.group(3)
        if tail:  # Recv.a.b:Method -> the last segment is an instance name, not a type
            yield tail.rsplit(".", 1)[1], ":", member, "loose-child"
            if member in SIGNAL_USE and tail.count(".") == 1:  # RunService.Update:Connect -> is Update an event of RunService?
                yield head, ".", tail[1:], "var"
        else:
            yield head, ":", member, "var"
    for m in DOT_CALL.finditer(text):
        if m.group(1) != "Enum":
            yield m.group(1), ".", m.group(2), "var"
    for m in BARE.finditer(text):
        yield m.group(1), ".", m.group(2), "service"
    for m in POSSESSIVE.finditer(text):
        yield m.group(1), ".", m.group(2), "strict"
    for m in OF_FORM.finditer(text):
        yield m.group(2), ".", m.group(1), "strict"
    for m in ENUM.finditer(text):
        yield m.group(1), ".", m.group(2) or "", "enum"


def resolve(api, recv, mode):
    """(class, strict?) for a receiver, or (None, None) when it is not a Roblox type."""
    if mode == "strict":
        return (recv, True) if recv in api.classes else (None, None)
    if mode == "service":  # bare RunService.Update: only a non-container service, where a child lookup is unlikely
        c = api.classes.get(recv)
        return (recv, True) if c and c["service"] and recv not in CONTAINERS else (None, None)
    if recv in GLOBALS:
        return GLOBALS[recv], True
    if mode == "var" and recv in api.classes:
        return recv, True
    low = {c.lower(): c for c in api.classes}
    if recv.lower() in low:  # `part:Delete()`, `script.Parent.Humanoid:X`: probably that class, maybe a subclass or a child name
        return low[recv.lower()], False
    return None, None


def as_recv(api, ref, cls):
    """Show an inherited alternative on the class the user wrote (Instance.Destroy -> Part.Destroy for a Part)."""
    owner = ref.split(".", 1)[0]
    return f"{cls}.{ref.split('.', 1)[1]}" if owner in api.chain(cls) else ref


def alternative(api, cls, member, sep):
    hit = api.curated(api.fakes, cls, member)
    if hit:
        return "Use " + " / ".join(api.show(as_recv(api, r, cls)) for r in hit["use"]) + f": {hit['note']}."
    pool = {m: f for c in api.chain(cls) for m, f in api.classes[c]["members"].items() if "D" not in f and "N" not in f}
    if re.match(r"(Set|Get)[A-Z]", member) and member[3:] in pool and pool[member[3:]][0] == "p":
        return f"It is a property, not a method: {api.show(f'{cls}.{member[3:]}')}; read or assign it directly."
    near = [m for m in pool if len(m) >= 4 and (member.startswith(m) or m.startswith(member))]
    near += [m for m in difflib.get_close_matches(member, list(pool), n=3, cutoff=0.6) if m not in near]
    if near:
        return "Closest real members: " + ", ".join(api.show(f"{cls}.{m}") for m in near[:3]) + "."
    elsewhere = api.anywhere.get(member)
    if elsewhere:
        return (f"No close real member on {cls}. (`{member}` is a member of {', '.join(sorted(elsewhere)[:3])}, which may do "
                f"something else; check it before using it here.)")
    return "No close real member; describe the real approach instead of inventing one."


LOCAL_DEF = re.compile(rf"\blocal\s+({ID})\s*(?::[^=\n]*)?=\s*(?:\{{|require\b|setmetatable\b)|\bfunction\s+({ID})[.:]|\b({ID})\.__index\b")
LOCAL_VAR = re.compile(rf"\blocal\s+({ID})\s*(?::[^=\n]*)?=(?!=)\s*([^\n]*)")


BINDING = re.compile(rf"\bfor\s+([^\n]*?)\s+in\b|\bfunction\b[^(\n]*\(([^)\n]*)\)")


def bound_names(text):
    """Names the prompt's own code binds as variables: loop vars, parameters, locals (`for _, Model in`, `function(Player)`)."""
    out = set()
    for m in BINDING.finditer(text):
        out |= set(re.findall(ID, re.sub(r":\s*" + ID + r"\??", "", m.group(1) or m.group(2) or "")))
    for m in LOCAL_VAR.finditer(text):  # `local Model = x:Clone()` is a variable; `local TweenService = game:GetService("TweenService")` stays the service
        if not re.match(rf"game:GetService\(\s*[\"']{m.group(1)}[\"']", m.group(2)):
            out.add(m.group(1))
    return out


INSTANCE_RHS = re.compile(r"game\b|workspace\b|script\b|Instance\.new|:Clone\(|:FindFirst|:WaitForChild|:GetChildren|:GetDescendants|::")


def own_modules(text):
    """Names the prompt defines as its own module: `local X = {}`, `local X = require(...)`, `local X = Framework.X`, `function X.f`."""
    own = {g for m in LOCAL_DEF.finditer(text) for g in m.groups() if g}
    own |= {m.group(1) for m in LOCAL_VAR.finditer(text) if not INSTANCE_RHS.search(m.group(2))}
    return own


def roblox_shaped(member):
    """Roblox members are PascalCase. A lowercase, snake or ALL_CAPS member is the user's own code (Noise.fbm, Light.WARM)."""
    return member[:1].isupper() and "_" not in member and not (len(member) > 1 and member.isupper())


def findings(prompt, api):
    text = re.sub(r"https?://\S+", " ", prompt)
    own = own_modules(text)  # `local Light = {}` / require / Framework.X: the prompt's own module, not the Roblox class
    bound = bound_names(text)  # a variable named like a class may hold a subclass or another class: check it loosely
    out, seen = [], set()
    for recv, sep, member, mode in candidates(text):
        if mode == "enum":
            key = ("Enum", recv, member)
            if key in seen:
                continue
            seen.add(key)
            if recv not in api.enums:
                near = difflib.get_close_matches(recv, list(api.enums), n=3, cutoff=0.6)
                out.append(f"- `Enum.{recv}` does not exist." + (f" Closest real enums: {', '.join('Enum.' + n for n in near)}." if near else ""))
            elif len(member) > 1 and member not in api.enums[recv] and member not in ("GetEnumItems", "FromName", "FromValue"):
                near = difflib.get_close_matches(member, api.enums[recv], n=3, cutoff=0.5)
                out.append(f"- `Enum.{recv}.{member}` does not exist." + (f" Real items that are close: {', '.join(near)}." if near else f" Real items: {', '.join(api.enums[recv][:12])}."))
            continue
        if member == "new" or member.lower() in FILE_EXT:
            continue
        if recv in own:
            continue
        cls, strict = resolve(api, recv, mode)
        if not cls:
            continue
        if mode == "service" and recv in bound:
            continue  # a local named like a service, used in code: not prose about the service
        if recv in bound and mode != "strict":
            strict = False
        key = (cls, member)
        if key in seen:
            continue
        seen.add(key)
        owner, flags = api.lookup(cls, member)
        label = f"{recv}{sep}{member}"
        if owner:
            if "D" in flags:
                hit = api.curated(api.deprecated, cls, member)
                tip = ("Use " + " / ".join(api.show(as_recv(api, r, cls)) for r in hit["use"]) + f": {hit['note']}.") if hit else f"Check `python3 tools/rbx.py class {owner}` for the current member."
                out.append(f"- `{label}` exists but is deprecated (on {owner}). {tip}")
            continue
        if not roblox_shaped(member):
            continue
        if strict and any(member in api.classes[d]["members"] for d in api.descendants(cls)):
            continue  # real on a subclass (BasePart.MeshId on a MeshPart): loose wording, not a fake
        if not strict and member in api.anywhere:
            continue  # a variable or child named like a class may be another class that has it
        where = " < ".join(api.chain(cls)) if strict else "any Roblox class"
        out.append(f"- `{label}` does not exist ({'no member `' + member + '` on ' + where if strict else 'no `' + member + '` on ' + where}). "
                   + alternative(api, cls, member, sep))
        if len(out) >= MAX_FINDINGS:
            break
    return out


def context(lines):
    return ("API premise check (from Roblox's real API dump in tools/roblox_api): the prompt names Roblox API that does not "
            "exist as written. Do not call it, even if the prompt says to and even behind a cast or pcall. Say in one line "
            "that it does not exist, then solve the task with the real API:\n" + "\n".join(lines)
            + "\nUnsure of anything else? `python3 tools/rbx.py member Class.Member` looks it up.")


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return
    prompt = data.get("prompt") or ""
    if not prompt.strip():
        return
    folder = api_dir(data.get("cwd"))
    if not folder:
        return
    lines = findings(prompt, Api(folder))
    if lines:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": context(lines)[:9000]}}))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # never break the user's prompt
        pass
    sys.exit(0)
