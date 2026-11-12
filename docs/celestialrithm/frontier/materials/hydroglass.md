# Hydroglass (`hydroglass`)

**Family:** fluid / optics · **Source:** [materials.py:82](../../../../tools/celestialrithm/foundry/materials.py) · **Palette:** `base #0b4f86` `highlight #bff6ff` `shadow #06233f` `rim #2fd3ff`

## How to recreate it

1. 3D-noise swell + damped wave equation
2. Snell refraction photon-splat caustics
3. Fresnel sky + Blinn glints

Every material then goes through the shared shell (`keycap.compose`): stepped extrusion, black ink, lit bezel, inner glass rim, clearcoat strip and top lip. Faces never move.

## Contract

| Field | Value |
|---|---|
| geometry | water height field (noise swell + wave sim) |
| optics | real refraction caustics (photon splat), Schlick Fresnel, sun glints |
| motion | slow swell; rain-sized drops every ~0.4 s |
| interaction | press = central drop; ring waves refract into caustic rings |
| hierarchy | tier 5 material; caustic peaks capped at 18% face area |
| rarity | Rare: deeper blue, gold caustics |
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
python3 -m tools.celestialrithm.foundry.board --ids hydroglass --cols 1 --size 400x260 --seconds 6 --out /tmp/hydroglass
```
