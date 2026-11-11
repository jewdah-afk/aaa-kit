#!/usr/bin/env python3
"""Checks every relative link and #anchor in every Markdown file resolves.

Usage: python3 tools/check_links.py [root]   (default: the repo root)
External links (http, https, mailto) are listed by count but not fetched.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parents[1]).resolve()
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)|!\[[^\]]*\]\(([^)\s]+)\)")
SKIP_DIRS = {".git", "node_modules"}


def anchors(md: pathlib.Path):
    out, counts = set(), {}
    in_code = False
    for line in md.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if m and not in_code:
            text = re.sub(r"[`*_\[\]()]", "", m.group(2)).strip().lower()
            slug = re.sub(r"[^\w\- ]", "", text).replace(" ", "-")
            n = counts.get(slug, 0)
            counts[slug] = n + 1
            out.add(slug if n == 0 else f"{slug}-{n}")
            # the lexicon generator's own anchor style
            out.add("".join(c if c.isalnum() else "-" for c in m.group(2).lower()).strip("-"))
    return out


def main():
    files = [p for p in ROOT.rglob("*.md") if not SKIP_DIRS & set(p.relative_to(ROOT).parts)]
    cache, bad, ext, checked = {}, [], 0, 0
    for md in files:
        text = md.read_text(encoding="utf-8")
        text = re.sub(r"```[\s\S]*?```", "", text)  # ignore code blocks
        text = re.sub(r"`[^`\n]*`", "", text)        # ignore inline code
        for m in LINK.finditer(text):
            target = m.group(1) or m.group(2)
            if re.match(r"^(https?:|mailto:)", target):
                ext += 1
                continue
            checked += 1
            path_part, _, frag = target.partition("#")
            dest = md if not path_part else (md.parent / path_part.replace("%20", " ")).resolve()
            if not dest.exists():
                bad.append(f"{md.relative_to(ROOT)}: {target} (missing file)")
                continue
            if frag and dest.suffix == ".md":
                if dest not in cache:
                    cache[dest] = anchors(dest)
                if frag.lower() not in cache[dest]:
                    bad.append(f"{md.relative_to(ROOT)}: {target} (missing anchor)")
    for b in bad:
        print("FAIL", b)
    print(f"{len(files)} files, {checked} relative links checked, {ext} external skipped, {len(bad)} broken")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
