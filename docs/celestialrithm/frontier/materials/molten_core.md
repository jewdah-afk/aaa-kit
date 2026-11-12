# Molten Core (`molten_core`)

**Family:** emission / crust · **Source:** [materials.py:373](../../../../tools/celestialrithm/foundry/materials.py) · **Palette:** `base #8a0f12` `highlight #ffd27a` `shadow #24030a` `rim #ff3b30`

## How to recreate it

1. drifting Worley crust plates; F2-F1 cracks carry a travelling heat pulse
2. Planck colour in cracks, cooled basalt plates with ember speckle

Every material then goes through the shared shell (`keycap.compose`): stepped extrusion, black ink, lit bezel, inner glass rim, clearcoat strip and top lip. Faces never move.

## Contract

| Field | Value |
|---|---|
| geometry | raised crust plates (height = F1 dome) |
| optics | Planck emission in cracks, matte crust with rim light |
| motion | plates drift and grind; heat pulses run along cracks |
| interaction | press = crust splits wider, cracks reach 2400 K |
| hierarchy | tier 5; red reserved for danger in HUD, so use as rarity/material only |
| rarity | Legendary: gold cracks |
| bevel | stepped 3-band extrusion under a squared cap, lit bezel ring |
| ink | near-black 4 px silhouette + 2 px inner line, never tinted |
| reduced motion | time x0.2, no light sweep, press = exposure lift only |
| tiers | high: full simulation at face resolution; mid: half-res field, bilinear up; low: pre-baked 32-frame loop in an atlas page |

## Measured

- Offline cost: run a board render to measure.

## Proof ladder

| Rung | Status |
|---|---|
| A_math_tests | pass (tools/celestialrithm/foundry/test_foundry.py) |
| B_offline_render | pass (board MP4 + JSON, ffprobe-checked) |
| C_studio_adapter | Luau port exists, not run in Studio |
| D_studio_timing | not measured |
| E_viewport_hierarchy_approval | not run (needs Studio capture + owner approval) |

## Reproduce

```sh
python3 -m tools.celestialrithm.foundry.board --ids molten_core --cols 1 --size 400x260 --seconds 6 --out /tmp/molten_core
```
