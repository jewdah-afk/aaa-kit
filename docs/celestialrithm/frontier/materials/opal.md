# Opal (`opal`)

**Family:** diffraction / milk · **Source:** [materials.py:433](../../../../tools/celestialrithm/foundry/materials.py) · **Palette:** `base #d9e4f2` `highlight #ffffff` `shadow #6f7f99` `rim #ffd6f4`

## How to recreate it

1. milky domain-warped fbm body + Worley silica domains, each diffracting toward its own direction: angle-selective flashes with spectral hue under a circling light

Every material then goes through the shared shell (`keycap.compose`): stepped extrusion, black ink, lit bezel, inner glass rim, clearcoat strip and top lip. Faces never move.

## Contract

| Field | Value |
|---|---|
| geometry | smooth dome |
| optics | per-patch diffraction (silica-sphere lattice idea), milky scatter |
| motion | patches flash in and out as the light drifts |
| interaction | press = light swings, every patch flashes once in sequence |
| hierarchy | tier 5; bright pastel: needs the dark ink to read |
| rarity | Mythic: black opal (dark body) |
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
python3 -m tools.celestialrithm.foundry.board --ids opal --cols 1 --size 400x260 --seconds 6 --out /tmp/opal
```
