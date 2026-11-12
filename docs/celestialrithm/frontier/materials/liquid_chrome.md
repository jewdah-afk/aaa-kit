# Liquid Chrome (`liquid_chrome`)

**Family:** mirror fluid · **Source:** [materials.py:498](../../../../tools/celestialrithm/foundry/materials.py) · **Palette:** `base #9aa4b5` `highlight #ffffff` `shadow #1d2230` `rim #dfe8ff`

## How to recreate it

1. metaball + noise height with wave-sim ripples
2. normals
3. reflected vector sampled against a studio softbox strip environment + sun lobe

Every material then goes through the shared shell (`keycap.compose`): stepped extrusion, black ink, lit bezel, inner glass rim, clearcoat strip and top lip. Faces never move.

## Contract

| Field | Value |
|---|---|
| geometry | fluid mirror height |
| optics | environment reflection (matcap), sharp horizon line |
| motion | mercury beads merge and split slowly |
| interaction | press = ripple rings bend the reflected horizon |
| hierarchy | tier 5; neutral: lets the icon colour lead |
| rarity | any; gold variant = Molten Gold |
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
python3 -m tools.celestialrithm.foundry.board --ids liquid_chrome --cols 1 --size 400x260 --seconds 6 --out /tmp/liquid_chrome
```
