# aaa-kit

The front door to my game development: one place that holds the design hierarchy, the code framework, a 400+ term design vocabulary and a library of Claude Code skills, so every game (and every Claude session) starts at a AAA bar.

## What's here

| | |
|---|---|
| **[HIERARCHY.md](HIERARCHY.md)** | The rules for what owns the screen: loudness tiers 1–6, pixel ownership, the intensity ladder, colour jobs, the rarity ladder |
| **[docs/FRAMEWORK.md](docs/FRAMEWORK.md)** | The five-layer Roblox framework (Kit hub → services → components → content → central systems) and its safety rules |
| **[examples/framework-starter](examples/framework-starter/README.md)** | A copyable starter game on that framework, with 48 headless tests |
| **[LEXICON.md](LEXICON.md)** | The design vocabulary, grouped by domain, with a 40-term starter pack and a prompt phrase per term |
| **[.claude/skills](.claude/skills/)** | 13 skills Claude loads automatically: HUD, rewards, VFX, EditableImage, EditableMesh, materials, shaders, algorithms, worlds, economy, Luau standards, art direction, prompt amplifier |
| **[examples/](examples/)** | Small runnable demos that the skills point to |
| **[tools/](tools/)** | Checkers (Luau compile, links, skills, lexicon, web examples) and the research calculator |

## Use it with Claude

1. Open any repo of mine in Claude Code. Its `CLAUDE.md` points here.
2. Ask for anything, even vaguely ("make the shop better"). The prompt amplifier turns it into a full brief and carries on.
3. Skills load on their own when the request matches (say "chest opening", "damage numbers", "EditableImage"...).

To use the skills in another repo, copy `.claude/skills/` into it, or symlink this repo's folder into `~/.claude/skills/` so they're available everywhere.

## Map of my repos

See [docs/REPO-MAP.md](docs/REPO-MAP.md).

| Repo | Role |
|---|---|
| **aaa-kit** (this) | Hub: shared knowledge, skills, framework |
| cursed-survivors | Game: a 2D survivors-genre game on an EditableImage pixel renderer |
| ObsidianVault | Lab: research notes, algorithm compendium, HTML labs |
| research-calculator | Lab: prototypes bench (its calculator and big-number library now live here) |
| WNGU | Lab: "Genesis" web game-system experiments |

## Checks

```sh
lune run tools/check_luau.luau .
python3 tools/check_links.py && python3 tools/check_skills.py && python3 tools/check_lexicon.py
node tools/check_examples.mjs
lune run examples/framework-starter/tests/run.luau
```

Lune 0.10.5 and Selene come from [rokit](https://github.com/rojo-rbx/rokit) (`rokit install`) or `cargo install lune --version 0.10.5 --locked`. Python 3 and Node 18+ cover the rest.

## Status

Work in progress. See [docs/INVENTORY.md](docs/INVENTORY.md) for what exists and what's left.

## License

The code (examples, tools, `.luau`, `.js`, `.py`, `.html`) is **MIT**: see [LICENSE](LICENSE).

The docs and design content (every `.md`, `lexicon.json`, the skills' text) are **CC BY-ND 4.0**: you may use, share and reference them with credit, but not publish edited versions. See [LICENSE-DOCS.md](LICENSE-DOCS.md).
