# Celestialrithm — primary entry point (2026-11-11)

## Mandatory source order

1. Root `CLAUDE.md`, `README.md`, `HIERARCHY.md`, and `docs/playbooks/figma-to-roblox-ui.md`.
2. `media/celestialrithm/approved-material-visual-target.gif` = minimum visual benchmark. This is reference animation, not evidence of Roblox runtime performance.
3. `docs/algorithm-vault/README.md` and `docs/celestialrithm/UNIVERSAL_UI_HUD_SYSTEM.md` for searchable algorithm families and UI design configurations.
4. `lib/frontier/Atlas.luau` / `Uploader.luau` and `lib/celestialrithm/` for math/adapter building blocks.
5. `examples/celestialrithm/` contains reproducible offline experiments and tests. Do NOT confuse engineering-v1-preview.gif with the approved quality bar.

## Non-negotiable style contract

- No PLAY text or icon on pure material specimens. No extra housing/frame or mouse magnetism. Stationary square buttons with animated subsurface media.
- At rest preserve the painted face, strong near-black ink, tight corners and real under-face depth. Improved material animation may alter internal light but not the label/icon readability or hitbox.
- For actual Shop, Inventory, HUD, Taskbar, crafting and avatar effects: assign one owner and one sound/motion priority per event; never animate all components loudly at once.
- Frozen Lake map and its camera geometry are source-of-truth; world generation applies only to authored extensions or separately approved changes.

## Proof ladder (every new algorithm or design must say which passed)

A. Pure math validated by tests and reproducible seed.
B. Captured OFFLINE renderer frames and verified GIF/MP4 metadata.
C. Actual Roblox EditableMesh/EditableImage adapter runs in Studio, logs failures/fallbacks.
D. Measured Studio client frame time, EditableImage upload cadence, mesh vertices/triangles and memory for phone tiers.
E. Real viewport captures pass hierarchy (first fixation, APCA, color vision, squint and flash) and owner approval.

60-FPS encoded video alone only satisfies B, not D. Generated recipe count is not implemented effect count.

## Next concrete build task

Build a full-size 4x3 motion material board with no text or glyph inside specimens, with 12 *different* shader/field methods and consistent motion. The approved animation above is the minimum appearance target. Add an A/B render per method, measured memory and time in the OFFLINE renderer, a deterministic param manifest, then one Studio prototype of the best-ranked material. Apply that treatment to one actual game button only after the isolated specimen passes visual QA.

## Test commands from repository root

```bash
python3 tools/algorithm_vault/test_vault.py
python3 tools/celestialrithm/test_ui_catalog.py
python3 tools/celestialrithm/test_world.py
python3 examples/celestialrithm/test_system.py
bash tools/check_all.sh
```

No third-party voxel pack assets or source are bundled without established redistribution rights. GitHub write actions were not available in the session; package is **NOT pushed**, and no commit SHA exists.
