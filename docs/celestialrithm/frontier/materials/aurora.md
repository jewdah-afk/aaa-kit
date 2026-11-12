# Aurora (`aurora`)

**Family:** curtain emission · **Source:** [materials.py:535](../../../../tools/celestialrithm/foundry/materials.py) · **Palette:** `base #06243a` `highlight #d4ffe9` `shadow #020a14` `rim #3dffb0`

## How to recreate it

1. curtain sheets: a 1D fbm-displaced fold line per layer, vertically extruded with exponential ray falloff and altitude colour ramp (green
2. magenta), over a starry gradient

Every material then goes through the shared shell (`keycap.compose`): stepped extrusion, black ink, lit bezel, inner glass rim, clearcoat strip and top lip. Faces never move.

## Contract

| Field | Value |
|---|---|
| geometry | flat |
| optics | additive emission curtains, altitude-coded colour |
| motion | folds travel sideways, rays shimmer |
| interaction | press = substorm: curtains brighten and ripple fast |
| hierarchy | tier 5; calm material: good for idle surfaces |
| rarity | Epic: red top fringe |
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
python3 -m tools.celestialrithm.foundry.board --ids aurora --cols 1 --size 400x260 --seconds 6 --out /tmp/aurora
```
