#!/usr/bin/env python3
"""UserPromptSubmit hook: flag weak prompts and suggest lexicon terms.

Reads the hook JSON on stdin (field `prompt`). If the prompt looks weak, prints a JSON object
with hookSpecificOutput.additionalContext telling Claude to run the prompt-amplifier skill,
plus up to 10 lexicon terms that match the prompt's words. Strong prompts get no output.
Never blocks a prompt. Exits 0 on any error so a broken hook can't stop work.
"""
import json
import os
import re
import sys

TASTE = {"cool", "better", "nicer", "pop", "juice", "juicy", "clean", "polish", "polished", "aaa",
         "insane", "awesome", "good", "fix", "improve", "amazing", "epic", "sick", "fire", "hella", "slick"}
TARGET_HINTS = re.compile(r"(\.\w{2,5}\b|/|`|\bline \d+|\bfunction\b|\bclass\b|\bmodule\b|\bservice\b|\bcomponent\b)", re.I)
CONSTRAINT_HINTS = re.compile(r"(\d+\s?(ms|px|fps|%|s\b)|phone|mobile|desktop|roblox|luau|webgl|canvas|budget|must|should not|don't|never)", re.I)
QUESTION = re.compile(r"^\s*(what|why|how|where|when|who|which|is|are|does|do|can|could|explain)\b.*\?\s*$", re.I | re.S)


def weak(prompt: str) -> bool:
    text = re.sub(r"<pasted_content[\s\S]*?</pasted_content[^>]*>", " ", prompt)
    words = re.findall(r"[a-zA-Z']+", text.lower())
    if not words or text.strip().startswith("/") or QUESTION.match(text):
        return False
    if "just do it" in text.lower() or "no brief" in text.lower():
        return False
    signals = 0
    signals += len(words) < 12
    signals += not TARGET_HINTS.search(text)
    signals += not CONSTRAINT_HINTS.search(text)
    signals += any(w in TASTE for w in words)
    return signals >= 3


def terms_for(prompt: str, lexicon_path: str, limit: int = 10):
    try:
        with open(lexicon_path, encoding="utf-8") as f:
            entries = json.load(f)["terms"]
    except (OSError, ValueError, KeyError):
        return []
    stop = {"make", "the", "and", "for", "with", "this", "that", "better", "cool", "good", "nice", "fix", "add",
            "more", "some", "thing", "stuff", "please", "just", "really", "look", "looks", "feel", "feels"}
    stop |= {"it", "to", "of", "in", "on", "an", "is", "me", "my", "do", "so", "up", "be", "at", "or", "we", "us"}
    words = {w for w in re.findall(r"[a-z]{2,}", prompt.lower()) if w not in stop}
    scored = []
    for e in entries:
        hay = " ".join([e["term"], e["domain"], e["use-when"], e["meaning"]]).lower()
        score = 0
        for w in words:
            if re.search(r"\b" + re.escape(w) + r"s?\b", hay):  # whole word (plural ok), not substring
                score += 3 if re.search(r"\b" + re.escape(w), e["term"].lower()) else 1
        if score:
            scored.append((score, e.get("starter", False), e["term"], e["prompt-phrase"]))
    if not scored:  # nothing specific: fall back to the starter pack, hierarchy terms first
        return [(e["term"], e["prompt-phrase"]) for e in entries if e.get("starter")][:limit]
    scored.sort(key=lambda s: (-s[0], not s[1], s[2]))
    return [(t, p) for _, _, t, p in scored[:limit]]


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return
    prompt = data.get("prompt") or ""
    if not weak(prompt):
        return
    root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or "."
    lex = os.path.join(root, "lexicon.json")
    if not os.path.exists(lex):
        lex = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "lexicon.json")
    terms = terms_for(prompt, lex)
    lines = ["This prompt looks underspecified. Run the prompt-amplifier skill: show a compact brief "
             "(goal, tier, deliverable, constraints, quality bar, done-check, solid/bold/insane), "
             "mark additions as suggestions, then proceed on Solid without waiting."]
    if terms:
        lines.append("Lexicon terms that may fit:")
        lines += [f"- {t}: {p}" for t, p in terms]
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                             "additionalContext": "\n".join(lines)[:9000]}}))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # never break the user's prompt
        pass
    sys.exit(0)
