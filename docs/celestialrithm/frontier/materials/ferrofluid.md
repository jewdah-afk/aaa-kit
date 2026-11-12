# Ferrofluid (`ferrofluid`)

**Family:** magnetic fluid · **Source:** [materials.py:562](../../../../tools/celestialrithm/foundry/materials.py) · **Palette:** `base #15161c` `highlight #e8ecff` `shadow #050507` `rim #7a8cff`

## How to recreate it

1. Rosensweig-style spike lattice: hexagonal cone field whose height follows a moving magnet potential; glossy black dielectric with sharp env highlights

Every material then goes through the shared shell (`keycap.compose`): stepped extrusion, black ink, lit bezel, inner glass rim, clearcoat strip and top lip. Faces never move.

## Contract

| Field | Value |
|---|---|
| geometry | hex spike lattice gated by magnet strength |
| optics | black gloss, coloured env reflection, rim light |
| motion | magnet circles; spikes rise and fall in a travelling crown |
| interaction | press = magnet pulls to the centre, spikes stand up |
| hierarchy | tier 5; dark but sharp: high detail per pixel, keep away from small text |
| rarity | Legendary: liquid-gold variant |
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
python3 -m tools.celestialrithm.foundry.board --ids ferrofluid --cols 1 --size 400x260 --seconds 6 --out /tmp/ferrofluid
```
