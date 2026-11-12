# Celestialrithm integration — review-only patch

**Status:** locally packaged, NOT pushed or merged.

This package organizes existing authored artifacts under the current `aaa-kit` layout. It does not overwrite existing repo files and does not silently replace the game's art, icons, or Figma source.

## Read first

- `CLAUDE.md` (already in target repo)
- `HIERARCHY.md` (already in target repo)
- `docs/playbooks/figma-to-roblox-ui.md`
- `docs/algorithm-vault/README.md`
- `docs/celestialrithm/ARCHITECTURE_V1.md`
- `docs/celestialrithm/QA_GATES_V1.md`

## File placement

- `docs/algorithm-vault/`: indexed methods, provenance, searchable recipes and SQLite catalog
- `tools/algorithm_vault/`: build, query, local repo ingestion, mutation, evaluation, and tests
- `lib/celestialrithm/`: experimental pure Luau components and avatar hero adapter (Studio UNVERIFIED)
- `examples/algorithm-vault/`: procedural material test
- `examples/celestialrithm/`: offline renderer and tests, T11 studies, flat reactor
- `media/celestialrithm/`: visual target and representative reference output

## Non-negotiable visual contract

The approved visual target is `media/celestialrithm/approved-material-visual-target.gif`: stationary squared keys, deep stylized under-face materials, no text/PLAY symbol on material specimens. It is a **reference animation**, not proof of runtime algorithms. Match/exceed it before saying a renderer passes visual QA. Legacy flat reactor is a historical experiment, not a baseline to revert toward.

Original six loudness tiers remain separate from R&D T11–T16 milestones. Preserve the fixed Figma keycap shape and ink. No constant full-screen bloom or cursor magnetism.

## Installation

From the unzipped package's directory, run:

```sh
python3 install_into_aaa_kit.py /path/to/aaa-kit
```

Installer refuses to overwrite existing files. Review diffs, then in the repository run:

```sh
python3 tools/algorithm_vault/test_vault.py
python3 examples/celestialrithm/test_system.py
bash tools/check_all.sh
git checkout -b research/celestialrithm-vault-integration
git add docs/algorithm-vault docs/celestialrithm tools/algorithm_vault lib/celestialrithm examples/algorithm-vault examples/celestialrithm media/celestialrithm
git commit -m "research: organize Celestialrithm material systems and algorithm vault"
```

Check external artwork/model/code licenses before publishing; **LihFolk third-party models and its source code were deliberately not included**. No model or avatar is claimed to be runtime-meshed. The `lib/celestialrithm` modules are research prototypes, not certified production runtime.

## QA known gaps

- Roblox Studio EditableMesh/EditableImage, avatar hardware, Lune and Selene: NOT VERIFIED here.
- Real-time 60 FPS: NOT VERIFIED in Studio; any 60 FPS MP4 merely establishes playback cadence.
- All 12,000 vault recipes are candidates, not implemented algorithms.
- Full repo QA and hierarchy scanpath must run after installation.
- External style target GIF has no guarantee of a 60 FPS source.

## Ownership

Review this package before merging. Existing repo code, icons and designs remain untouched until integration is approved.

## Added: UI/UX motion and procedural stud-world extension

- `lib/celestialrithm/MotionDirector.luau`: deterministic event priority, spring-like sampling, calm-state, no cursor magnetism. Pure Luau, **Lune not yet run**.
- `lib/celestialrithm/StudWorld.lua`: deterministic new-chunk terrain substrate, preserves authored map.
- `tools/celestialrithm/world_preview.py`: offline generated stud map PNG and OBJ.
- `tools/celestialrithm/test_world.py`: deterministic generation, terracing, road, model export QA.
- `docs/celestialrithm/MOTION_WORLD_RESEARCH.md`: 85 motion / world algorithm candidates, externally sourced methods, implementation and hierarchy thresholds. **Catalog entries are not implemented methods.**

Validation: Python map generator and its tests executed locally. No live Studio playback, no verified Luau compiler, no real device profiling. UI motion must be visually evaluated against `media/celestialrithm/approved-material-visual-target.gif`; never claim the 2D engineering preview meets it.

## Added: Universal UI/HUD architecture and recipe search

- `docs/celestialrithm/UNIVERSAL_UI_HUD_SYSTEM.md`: shop, inventory, HUD, taskbar, combat, avatar and procedural world policies; design and performance quality gates.
- `docs/celestialrithm/ui_recipe_catalog.jsonl`: **16,800 generated and UNTESTED** design combinations across 14 genres, 20 components, 20 materials and 3 device rungs.
- `tools/celestialrithm/build_ui_catalog.py`: deterministic recipe generator.
- `tools/celestialrithm/test_ui_catalog.py`: five structural tests, passing locally.

No live Roblox Studio visual or runtime performance claim is made for these combinations. Existing painted button art and approved reference GIF remain the quality target.
