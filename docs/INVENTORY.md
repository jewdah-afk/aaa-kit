# Inventory

Snapshot of every repo in the kit, taken 2026-11-11 from read-only clones of every branch. Two of the owner's repos are out of scope by the owner's decision and aren't listed.

Tier key: **Hub** = shared knowledge, front door · **Game** = a shippable game · **Lab** = research, prototypes, reference art · **Private** = never public · **Archive** = keep but freeze.

## Repo table

| Repo | Visibility | What it is | Language / engine | Last activity | Health | Sensitive content | Tier |
|---|---|---|---|---|---|---|---|
| `ObsidianVault` | private (assumed; confirm) | The knowledge vault: design notes, algorithm research, 60+ offline HTML labs, AI memory and an idea library (1,361 idea cards, 46 built Luau blocks). | Markdown, HTML/JS/WebGL labs, Luau snippets | 2026-10-31 (`main`); 10 branches | Docs: strong README and organizing rules. No build. ~208 MB, 2,767 files on `main`. | Yes: local paths, place IDs and third-party game names in research notes. No live secrets. Keep private. | **Lab** (source material for the hub) |
| `cursed-survivors` | private (assumed; confirm) | A 2D survivors-genre Roblox game rendered through an EditableImage pixel pipeline, with a large look-dev archive (1,461 files in `docs/look`). | Luau / Roblox (Rojo 7.5.1, Luau 0.740, Lune 0.10.5, Selene) | 2026-10-25; 129 branches | Tests: **all pass** (2026-11-11, Lune 0.10.5): every top-level suite plus render (52 files), screens (54), store (18), fx (26) and the QA flows. Docs: rich `docs/`, but **no root README or CLAUDE.md**. ~916 MB. | Yes: third-party names in code and docs, local paths, a personal email in 4 docs. No live secrets. Keep private. | **Game** (keep private until a rename pass) |
| `WNGU` | **public** | `main` is only a one-line README ("Calculators"). Branch `claude/project-genesis-…` holds "Genesis": HTML/JS game-system experiments (a factory sim, a genome raster lab, a falling-sand racer). | HTML/JS (canvas) | 2026-10-29 (branch); `main` 2026-07-21 | `main` is empty. The branch has an ARCHITECTURE.md and an experiment registry. No tests. | None found. | **Lab**: merge Genesis into the hub's `examples/` or rename the repo to match its content. UNKNOWN — ask owner what "WNGU" stands for. |
| `research-calculator` | **public** | Not a calculator any more: `main` is a Roblox remake of an existing incremental game (data, icon pipeline and `roblox/` folders) plus a research-calculator page. 31 other branches hold unrelated prototypes (incremental research, tower game, editable images and meshes, map drafts, a survivors mechanics study, icon pipelines). | HTML/JS, Luau / Roblox, Python + Blender icon tools | 2026-10-21 (newest branch); `main` 2026-10-07 | Docs: HANDOUT and CLAUDE.md on most branches. No CI or tests on `main`. 985 files. | Yes: a remake's data on `main` names another game. Place IDs in 2 docs. No secrets. | **Lab**: calculator page and big-number library merged into the hub; the rest stays as a prototype bench. |

## ObsidianVault branches

`main` is the newest; the other branches hold work that never merged.

| Branch | Ahead of `main` | Holds |
|---|---|---|
| `claude/adoring-newton-nhsf5e` | 6 commits, 16 files | Idle-game HUD work: a 14-stage "living numeral" score readout chain, a headless Lune renderer, an EditableImage HUD stack and a playable HUD reference artifact. |
| `claude/brain-vault-seed` | 13 commits, 416 files | The Library seed: 263 Luau blocks, idea cards, jobs, moments, families and the library tools. Mostly already on `main`. |
| `claude/game-ideas-brainstorm-ebm9bo` | 46 commits, 937 files | A sketch-to-life game concept with 911 Roblox files and a port plan. |
| `claude/roblox-algo-game-brainstorm-cznd95` | 20 commits, 153 files | A pet-collector concept (sim, reference, Roblox code, thumbnail) and a draw-it-alive spec. |
| `claude/revolution-fusion` | 5 commits, 7 files | Idle-game HUD artifacts and Luau. |
| `claude/finish-pass-spec` | 2 commits, 1 file | A finish-pass design note. |
| `unity-port-harness` | 2 commits, 31 files | A Roblox-to-Unity port harness: skills, templates, toolchain notes. |
| `wip/ai-hud-attempts` | 1 commit, 10 files | Discarded HUD attempts. |
| `claude/visibility-check-679a53` | 0 | Same as `main`. |

## High-value material (raw input for skills and lexicon)

| Source | Where | Feeds |
|---|---|---|
| Living Effects Lab artifact | claude.ai artifact (48 effects, 6 tiers) | `HIERARCHY.md` skeleton; `vfx`, `reward-moments`, `ui-hud`, `materials`, `procedural-world` examples |
| Hierarchy notes | Vault `Cursed Survivors/Notes/16 Hierarchy Codex.md`, `Artifacts/Cursed Survivors/survivors-hierarchy-codex`, `Artifacts/Godrithms/*godarchy*` | `HIERARCHY.md`, `art-direction` |
| Algorithm Compendium | Vault `Cursed Survivors/Research/Algorithm Compendium/` (00 index + 56 chapters) | `algorithms`, `shaders-and-sdf`, `procedural-world`, lexicon |
| Library | Vault `Library/` (1,361 idea cards, 277 blocks, moments, families) | `algorithms`, lexicon |
| Render Deep Dive, UI FX Stack, VFX Insaneiarchy | Vault `Cursed Survivors/Research/` (16 + 9 + 132 files) | `vfx`, `ui-hud`, `editable-image`, lexicon |
| Godrithms labs | Vault `Artifacts/Godrithms/` (8 labs) | `algorithms` (layered algorithm chains) |
| Cel VFX Lab, Glyph Atlas, Prop Forge | Vault `Artifacts/Cursed Survivors/` (13 labs) | `vfx`, `materials`, `procedural-world` |
| Idle HUD work | Vault `Algorithmic Idle/` + branch `adoring-newton` | `ui-hud`, `game-economy`, `editable-image` |
| Look archive | `cursed-survivors/docs/look/**` (before/after GIFs, render-stack notes) | `vfx`, `art-direction`, `editable-image` |
| EditableImage renderer + tests | `cursed-survivors/src/client`, `tests/render`, `tests/fx` | `editable-image` (the reference implementation) |
| Budgets, naming, decisions | `cursed-survivors/docs/budgets.md`, `naming.md`, `decisions.md` | `roblox-luau-standards`, `STYLE.md` |
| Economy formulas, big numbers | research-calculator `main` (remake data folder: formulas, EternityNum) | `game-economy` (rewritten generically) |
| Genesis experiments | `WNGU` branch `claude/project-genesis-…` | `examples/`, `algorithms` |

Not found as standalone folders: the Algorithm Lab, Material Codex, VFX Atlas and HUD Godrithms. VFX Atlas, Cel VFX Lab and Unreality Stack are embedded as deep labs inside the Living Effects Lab. `Artifacts/Algorithmic Idle/hud-godrithms` and `Artifacts/Cursed Survivors/cursed-algorithm-lab` are the closest matches in the vault. No standalone "Material Codex" folder exists: UNKNOWN — ask owner where it lives.

## Toolchain in this cloud session

| Tool | Status |
|---|---|
| Python 3, Node 22, Chromium (Playwright) | Available |
| Lune 0.10.5, Selene 0.31 | Built from crates.io (`cargo install`) |
| Rokit, Rojo, Blender | Not installed here |
