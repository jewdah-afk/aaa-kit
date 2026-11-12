# Verdant Coral (`verdant_coral`)

**Family:** reaction-diffusion · **Source:** [materials.py:402](../../../../tools/celestialrithm/foundry/materials.py) · **Palette:** `base #0f8a5a` `highlight #d8fff0` `shadow #033823` `rim #2bf0a0`

## How to recreate it

1. Gray-Scott reaction-diffusion (f,k drifting through the coral/mitosis regime)
2. height
3. normals
4. emerald subsurface + wet specular

Every material then goes through the shared shell (`keycap.compose`): stepped extrusion, black ink, lit bezel, inner glass rim, clearcoat strip and top lip. Faces never move.

## Contract

| Field | Value |
|---|---|
| geometry | RD concentration as relief |
| optics | subsurface tint by thickness, wet specular |
| motion | pattern grows and reorganises (never loops exactly) |
| interaction | press = feed rate pulse -> spots divide (mitosis) |
| hierarchy | tier 5; fine pattern: keep the face >= 96 px tall or switch to mid tier |
| rarity | Epic: bioluminescent tips |
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
python3 -m tools.celestialrithm.foundry.board --ids verdant_coral --cols 1 --size 400x260 --seconds 6 --out /tmp/verdant_coral
```
