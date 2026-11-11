#!/usr/bin/env python3
"""Builds lexicon.json and LEXICON.md from tools/lexicon/src/*.txt.

Source format, one entry per line:
    term | tier | meaning | use-when | pairs-with (comma list) | prompt-phrase | source
`@domain name` lines set the domain for the entries below. `#` lines are comments.
The starter pack (the 40 highest-leverage terms) is listed in STARTER below.
Fails (exit 1) on malformed lines, duplicate terms or pairs-with that don't resolve.
"""
import json
import pathlib
import sys
from collections import OrderedDict

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "tools" / "lexicon" / "src"

STARTER = [
    "loudness tier", "pixel ownership", "intensity ladder", "calm frame", "colour job", "currency gold",
    "danger red", "rarity ladder", "figure-ground gate", "one loud element per panel", "urgency beats rarity",
    "critical cue", "decoration slot", "reward sequencing", "skippable reveal", "decide-then-animate",
    "hit-stop", "screen shake", "impact flash", "onset frame", "recovery window", "telegraph",
    "odometer counter", "big-number suffix", "ghost bar", "rarity frame", "call to action", "safe area",
    "holo foil", "rarity-as-material", "signed distance field", "fBm", "godrithm", "Poisson disk",
    "balance in data", "pacing", "server authority", "remote validation", "frame budget", "brief",
]

DOMAIN_ORDER = ["hierarchy", "ui", "reward", "vfx", "materials", "shaders", "algorithms", "world",
                "economy", "code", "performance", "art", "audio-feel", "game-feel", "process"]
DOMAIN_TITLES = {
    "hierarchy": "Hierarchy", "ui": "UI & HUD", "reward": "Rewards & Moments", "vfx": "VFX",
    "materials": "Materials", "shaders": "Shaders & SDF", "algorithms": "Algorithms", "world": "World",
    "economy": "Economy", "code": "Code & Framework", "performance": "Performance", "art": "Art Direction",
    "audio-feel": "Audio & Feel", "game-feel": "Game Feel", "process": "Process",
}


def parse():
    entries, errors = [], []
    for path in sorted(SRC.glob("*.txt")):
        domain = None
        for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("@domain "):
                domain = line.split(None, 1)[1].strip()
                continue
            parts = [p.strip() for p in line.split(" | ")]
            if len(parts) != 7 or not all(parts[i] for i in (0, 1, 2, 3, 5, 6)):
                errors.append(f"{path.name}:{n}: expected 7 non-empty fields, got {len(parts)}")
                continue
            if domain is None:
                errors.append(f"{path.name}:{n}: entry before any @domain")
                continue
            term, tier, meaning, use, pairs, phrase, source = parts
            entries.append(OrderedDict([
                ("term", term), ("tier", tier), ("domain", domain), ("meaning", meaning),
                ("use-when", use), ("pairs-with", [p.strip() for p in pairs.split(",") if p.strip()]),
                ("prompt-phrase", phrase), ("source", source),
                ("starter", term in STARTER),
            ]))
    return entries, errors


def validate(entries):
    errors = []
    seen = {}
    for e in entries:
        k = e["term"].lower()
        if k in seen:
            errors.append(f"duplicate term: {e['term']}")
        seen[k] = e
    for e in entries:
        for p in e["pairs-with"]:
            if p.lower() not in seen:
                errors.append(f"{e['term']}: pairs-with '{p}' does not resolve")
            elif p.lower() == e["term"].lower():
                errors.append(f"{e['term']}: pairs with itself")
    for s in STARTER:
        if s.lower() not in seen:
            errors.append(f"starter term missing: {s}")
    if len(set(STARTER)) != 40:
        errors.append(f"starter pack must have 40 unique terms, has {len(set(STARTER))}")
    return errors


def anchor(term):
    return "".join(c if c.isalnum() else "-" for c in term.lower()).strip("-")


def markdown(entries):
    by_term = {e["term"]: e for e in entries}
    out = ["# Lexicon", "",
           f"{len(entries)} design terms from my repos and standard practice. Each has a ready-to-paste prompt phrase. "
           "The machine-readable version is [lexicon.json](lexicon.json) (schema: [lexicon.schema.json](lexicon.schema.json)); "
           "this page is generated from it by `python3 tools/lexicon/build.py`, so edit `tools/lexicon/src/*.txt`, not this file.",
           "", "## Starter pack (40 terms)", "",
           "The highest-leverage terms. Know these and most briefs write themselves.", "",
           "| Term | Domain | Prompt phrase |", "|---|---|---|"]
    for s in STARTER:
        e = by_term[s]
        out.append(f"| [{e['term']}](#{anchor(e['term'])}) | {e['domain']} | {e['prompt-phrase']} |")
    out += ["", "## Domains", ""]
    counts = {}
    for e in entries:
        counts[e["domain"]] = counts.get(e["domain"], 0) + 1
    out.append(" · ".join(f"[{DOMAIN_TITLES.get(d, d)}](#{anchor(DOMAIN_TITLES.get(d, d))}) ({counts[d]})"
                          for d in DOMAIN_ORDER if d in counts))
    for d in DOMAIN_ORDER:
        group = [e for e in entries if e["domain"] == d]
        if not group:
            continue
        out += ["", f"## {DOMAIN_TITLES.get(d, d)}", ""]
        for e in group:
            pairs = ", ".join(f"[{p}](#{anchor(p)})" for p in e["pairs-with"])
            out += [f"### {e['term']}", "",
                    f"{e['meaning']} **Use when:** {e['use-when']}", "",
                    f"> {e['prompt-phrase']}", "",
                    f"Tier: {e['tier']} · Pairs with: {pairs or '—'} · Source: {e['source']}", ""]
    return "\n".join(out).rstrip() + "\n"


def main():
    entries, errors = parse()
    errors += validate(entries)
    if errors:
        print("\n".join(errors))
        print(f"{len(entries)} entries, {len(errors)} errors")
        sys.exit(1)
    order = {d: i for i, d in enumerate(DOMAIN_ORDER)}
    entries.sort(key=lambda e: (order.get(e["domain"], 99),))
    data = OrderedDict([("$schema", "./lexicon.schema.json"), ("version", 1), ("count", len(entries)),
                        ("terms", entries)])
    (ROOT / "lexicon.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (ROOT / "LEXICON.md").write_text(markdown(entries), encoding="utf-8")
    print(f"{len(entries)} entries written")


if __name__ == "__main__":
    main()
