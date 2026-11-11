#!/usr/bin/env python3
"""Checks every skill in .claude/skills:

1. Frontmatter: `name` (lowercase-hyphenated, equal to the folder name) and `description`
   (40–1024 characters, says when to trigger).
2. Required sections: When to use, Method, Hierarchy rules, Engine notes, Example,
   Make it insane, Self-check (the prompt-amplifier swaps "Example" for "Examples").
3. Every file the skill's Example section names under examples/ exists.
4. Trigger test: each sample prompt below must rank its intended skill first when scored
   against every skill's description (word overlap, phrase hits weighted). This is a
   proxy for Claude's matching, not the real thing, but it catches vague descriptions.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILLS = ROOT / ".claude" / "skills"
REQUIRED = ["When to use", "Method", "Hierarchy rules", "Engine notes", "Example", "Make it insane", "Self-check"]

SAMPLES = {
    "ui-hud": ["the coin counter jitters, fix the HUD", "add a cooldown icon to the ability bar", "damage numbers are unreadable"],
    "reward-moments": ["make the egg hatch feel exciting", "add a gacha summon beam", "level up screen is boring"],
    "vfx": ["hits have no impact, add screen shake", "make a lightning chain effect", "enemy death dissolve"],
    "editable-image": ["write a pixel renderer with EditableImage", "WritePixelsBuffer is slow"],
    "editable-mesh": ["generate a procedural mesh with EditableMesh", "deform mesh vertices at runtime"],
    "materials": ["make the legendary item look chrome and shiny", "holographic foil on mythic cards"],
    "shaders-and-sdf": ["raymarch an SDF scene in GLSL", "signed distance field rounded panel"],
    "algorithms": ["which algorithm for a corruption pattern", "chain a godrithm of passes"],
    "procedural-world": ["generate a map and scatter trees", "procedural dungeon biome layout"],
    "game-economy": ["balance the upgrade cost curve", "rebirth prestige formula is too grindy"],
    "roblox-luau-standards": ["where should this RemoteEvent handler go", "save data with DataStore session lock"],
    "art-direction": ["the palette looks muddy and I can't see the enemies", "review the art direction"],
    "prompt-amplifier": ["make it cool", "fix the ui", "make it better"],
    "kit-doctor": ["hi", "what do I need installed on my pc", "is my game good, audit it"],
    "hierarchy-audit": ["does the eye go to the buy button", "check contrast of this text", "is this flashing effect safe", "colour blind check on the rarity colours"],
}
STOP = set("a an the and or of to in for on with is it this that use when any make my me i how what which".split())


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    out = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip()
    return out


def words(s):
    return [w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in STOP]


def score(prompt, desc):
    d = desc.lower()
    s = 0.0
    for w in words(prompt):
        if re.search(r"\b" + re.escape(w), d):
            s += 1
    for q in re.findall(r'"([^"]+)"', desc):  # quoted trigger phrases
        if q.lower() in prompt.lower():
            s += 3
    return s


def main():
    errors, descs = [], {}
    dirs = sorted(p for p in SKILLS.iterdir() if p.is_dir())
    for d in dirs:
        f = d / "SKILL.md"
        if not f.exists():
            errors.append(f"{d.name}: no SKILL.md")
            continue
        text = f.read_text(encoding="utf-8")
        fm = frontmatter(text)
        if not fm:
            errors.append(f"{d.name}: missing frontmatter")
            continue
        if fm.get("name") != d.name or not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", fm.get("name", "")):
            errors.append(f"{d.name}: name must be lowercase-hyphenated and match the folder")
        desc = fm.get("description", "")
        if not 40 <= len(desc) <= 1024:
            errors.append(f"{d.name}: description length {len(desc)} not in 40..1024")
        if "use" not in desc.lower():
            errors.append(f"{d.name}: description should say when to use it")
        descs[d.name] = desc
        heads = re.findall(r"^##\s+(.+)$", text, re.M)
        for r in REQUIRED:
            if not any(h.startswith(r) for h in heads):
                errors.append(f"{d.name}: missing section '{r}'")
        for ref in re.findall(r"`(examples/[^`\s]+)`", text):
            if not (d / ref).exists():
                errors.append(f"{d.name}: names {ref}, which doesn't exist")

    misses = 0
    for skill, prompts in SAMPLES.items():
        for p in prompts:
            ranked = sorted(descs, key=lambda k: -score(p, descs[k]))
            if not ranked or ranked[0] != skill:
                misses += 1
                errors.append(f"trigger: '{p}' → {ranked[0] if ranked else None} (wanted {skill})")
    for e in errors:
        print("FAIL", e)
    total = sum(len(v) for v in SAMPLES.values())
    print(f"{len(dirs)} skills, {total - misses}/{total} sample prompts routed correctly, {len(errors)} errors")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
