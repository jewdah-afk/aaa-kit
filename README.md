# aaa-kit

The front door to my game development: one place that holds the design hierarchy, the code framework, a 400+ term design vocabulary and a library of Claude Code skills, so every game (and every Claude session) starts at a AAA bar.

## What's here

| | |
|---|---|
| **[HIERARCHY.md](HIERARCHY.md)** | The rules for what owns the screen: loudness tiers 1–6, pixel ownership, the intensity ladder, colour jobs, the rarity ladder |
| **[docs/FRAMEWORK.md](docs/FRAMEWORK.md)** | The five-layer Roblox framework (Kit hub → services → components → content → central systems) and its safety rules |
| **[examples/framework-starter](examples/framework-starter/README.md)** | A copyable starter game on that framework, with 48 headless tests |
| **[LEXICON.md](LEXICON.md)** | The design vocabulary, grouped by domain, with a 40-term starter pack and a prompt phrase per term |
| **[.claude/skills](.claude/skills/)** | 17 skills Claude loads automatically: HUD, rewards, VFX, EditableImage, EditableMesh, materials, shaders, algorithms, worlds, economy, Luau standards, art direction, hierarchy audit, prompt amplifier, kit doctor, and the **LihFolk Stud Voxel pack** (stud/LEGO voxel creatures, bosses, buildings, props and terrain built in headless Blender, exported as rigged GLB), and **voicestudio-sfx** (original sound effects and voice lines made locally with [VoiceStudio](https://github.com/debpalash/voicestudio), loudness by tier) |
| **[lib/](lib/README.md)** | Tested Luau libraries: **frontier** (EditableImage/EditableMesh at the engine's limits) and **pixelfx** (15 pixel effects) |
| **[docs/playbooks/](docs/playbooks/README.md)** | **How we did everything**: the Figma → Roblox UI pipeline, procedural textures on model assets, UI motion and sound, the icon pipeline, world hierarchy, VFX craft, the look-dev loop, the Studio workflow, working with Claude, parity and porting |
| **[docs/research/](docs/research/README.md)** | 31 research chapters (EditableImage/Mesh APIs and cookbooks, Luau performance, VFX and game feel, architecture, security, procgen, AI, live ops, QA, and **Part V: hierarchy science**: attention, contrast and colour blindness, cue timing, audio, grouping, measurement) plus 400+ algorithm ideas |
| **[examples/](examples/)** | Runnable demos: the [showcase](examples/web/showcase.html) (the whole kit on one page, with live combined effects; rebuild with `python3 tools/build_showcase.py`), the [effects hierarchy](examples/web/effects-gallery.html) (48 effects by tier), the [algorithm lab](examples/web/algorithm-lab.html), the [surface bake lab](examples/web/surface-bake.html) (15 algorithm materials and 5 realtime motions on 3D models), the [depth lab](examples/web/depth-lab.html) (parallax occlusion, interior mapping, infinite zoom, shell fur), the framework starter, big numbers, a tier simulator |
| **[tools/hierarchy](tools/hierarchy/README.md)** | The hierarchy auditor: predicted scanpath and focus lift on any screenshot, APCA contrast, colour-blind checks, WCAG flash safety on effect GIFs |
| **[tools/figma](tools/figma/README.md) · [lib/figma-ui](lib/figma-ui/README.md) · [tools/icons](tools/icons/README.md)** | The Figma kit and exporter, the in-game renderer that rebuilds Figma frames node for node, and the icon cutter/QA tools |
| **[.claude/agents/](.claude/agents/)** | Review agents: `ui-qa` (zoomed QA), `style-guard`, `visual-hierarchy`, `roblox-feasibility` |
| **[media/gifs/](media/gifs/)** | Looping GIFs of every tier 5 (materials) and tier 6 (engines) effect (`node tools/capture_gifs.mjs --tier N`), plus the [surface effects reel](media/gifs/surfaces/index.html): dissolve and frost on four surfaces each, runes, lava flow, scans, reactive hits, ice vs lava, a spin-reactive shield, and depth tricks (`node tools/capture_surface_gifs.mjs`) |
| **[tools/](tools/)** | The kit doctor, checkers (Luau compile, links, skills, lexicon, web pages), the GIF recorder, and the research and economy calculators |

## Use it with Claude

1. Open this repo in Claude Code and say **hi**. It replies ready, checks your PC (lune, selene, rojo, Studio, Blender…) and tells you exactly what to install, then offers what to build next. `python3 tools/doctor.py` does the same check by hand.
2. Open any other repo of mine; its `CLAUDE.md` points here.
3. Ask for anything, even vaguely ("make the shop better"). The prompt amplifier turns it into a full brief and carries on.
4. Skills load on their own when the request matches (say "chest opening", "damage numbers", "EditableImage"...).

To use the skills in another repo, copy `.claude/skills/` into it, or symlink this repo's folder into `~/.claude/skills/` so they're available everywhere.

## Map of my repos

See [docs/REPO-MAP.md](docs/REPO-MAP.md).

| Repo | Role |
|---|---|
| **aaa-kit** (this) | Hub: shared knowledge, skills, framework |
| cursed-survivors | Game: a 2D survivors-genre game on an EditableImage pixel renderer |
| ObsidianVault | Lab: research notes, algorithm compendium, HTML labs |
| research-calculator | Archive: its calculator, big-number library, EditableImage/EditableMesh libraries and research now live here |
| WNGU | Lab: "Genesis" web game-system experiments |

## Checks

```sh
bash tools/check_all.sh
```

That runs the Luau compile check, every lune test (kit examples plus the frontier and pixelfx libraries), Selene, the link, skill, lexicon and hook checkers, the doctor, and the web pages in headless Chromium.

Lune 0.10.5 and Selene come from [rokit](https://github.com/rojo-rbx/rokit) (`rokit install`) or `cargo install lune --version 0.10.5 --locked`. Python 3 and Node 18+ cover the rest.

## Live gallery

The effects hierarchy page is also published as a private claude.ai artifact so it opens on any device: https://claude.ai/artifact/5mrPth6QohffALms7XswKK (share it from the page's Share menu).

## Status

Active. See [docs/INVENTORY.md](docs/INVENTORY.md) for what exists and what's left.

## License

The code (examples, tools, `.luau`, `.js`, `.py`, `.html`) is **MIT**: see [LICENSE](LICENSE).

The docs and design content (every `.md`, `lexicon.json`, the skills' text) are **CC BY-ND 4.0**: you may use, share and reference them with credit, but not publish edited versions. See [LICENSE-DOCS.md](LICENSE-DOCS.md).
