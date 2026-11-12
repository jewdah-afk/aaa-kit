# Holographic Foil (`holo_foil`)

**Family:** interference + diffraction · **Source:** [materials.py:260](../../../../tools/celestialrithm/foundry/materials.py) · **Palette:** `base #b9bfd0` `highlight #ffffff` `shadow #4c5168` `rim #e8d6ff`

## How to recreate it

1. high-order thin-film interference on brushed silver (thickness = slow warped fbm, gives pastel swirls) + embossed Worley micro-cells as diffraction-grating sparkle under a sweeping light

Every material then goes through the shared shell (`keycap.compose`): stepped extrusion, black ink, lit bezel, inner glass rim, clearcoat strip and top lip. Faces never move.

## Contract

| Field | Value |
|---|---|
| geometry | embossed micro-cells on a flat foil |
| optics | thin film (orders 2-4 -> pastel), grating sparkle, anisotropic brushed silver |
| motion | swirls drift; sparkle follows a slowly tilting light |
| interaction | press = tilt sweep: every band shifts one full order |
| hierarchy | tier 5; saturation capped at rest, full on press |
| rarity | any: the foil itself reads as premium |
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
python3 -m tools.celestialrithm.foundry.board --ids holo_foil --cols 1 --size 400x260 --seconds 6 --out /tmp/holo_foil
```
