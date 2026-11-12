# Nebula (`nebula`)

**Family:** volumetric emission · **Source:** [materials.py:461](../../../../tools/celestialrithm/foundry/materials.py) · **Palette:** `base #1a0b3d` `highlight #ffd6ff` `shadow #05030f` `rim #8a5cff`

## How to recreate it

1. 4-slice ray-marched emission/absorption through warped fbm density + twinkling stars + a comet arc on a parametric curve

Every material then goes through the shared shell (`keycap.compose`): stepped extrusion, black ink, lit bezel, inner glass rim, clearcoat strip and top lip. Faces never move.

## Contract

| Field | Value |
|---|---|
| geometry | flat; depth is from 4 parallax slices |
| optics | front-to-back emission-absorption compositing |
| motion | slices drift at different speeds (parallax), comet traces a slow arc |
| interaction | press = star birth: a core brightens and blows a bubble |
| hierarchy | tier 5; dark: pairs with bright neighbours |
| rarity | Legendary: gold dust lane |
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
| C_studio_adapter | not built |
| D_studio_timing | not measured |
| E_viewport_hierarchy_approval | not run (needs Studio capture + owner approval) |

## Reproduce

```sh
python3 -m tools.celestialrithm.foundry.board --ids nebula --cols 1 --size 400x260 --seconds 6 --out /tmp/nebula
```
