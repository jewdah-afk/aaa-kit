# Solar Plasma (`solar_plasma`)

**Family:** emission · **Source:** [materials.py:157](../../../../tools/celestialrithm/foundry/materials.py) · **Palette:** `base #d26a08` `highlight #fff1b0` `shadow #4a1402` `rim #ffb21f`

## How to recreate it

1. curl-advected ridged multifractal temperature field + Worley granulation
2. blackbody-ordered temperature ramp
3. filmic shoulder

Every material then goes through the shared shell (`keycap.compose`): stepped extrusion, black ink, lit bezel, inner glass rim, clearcoat strip and top lip. Faces never move.

## Contract

| Field | Value |
|---|---|
| geometry | flat face; granulation cells modulate temperature |
| optics | pure emission (Planck), filmic highlight roll-off |
| motion | filaments flow along curl noise; granules boil |
| interaction | press = flare: +1800 K travelling front from the centre |
| hierarchy | tier 5; brightest emissive material, so one per screen at most |
| rarity | Legendary: blue-white 9000 K core |
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
python3 -m tools.celestialrithm.foundry.board --ids solar_plasma --cols 1 --size 400x260 --seconds 6 --out /tmp/solar_plasma
```
