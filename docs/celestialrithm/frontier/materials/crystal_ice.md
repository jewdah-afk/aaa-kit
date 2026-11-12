# Crystal Ice (`crystal_ice`)

**Family:** crystal / refraction · **Source:** [materials.py:229](../../../../tools/celestialrithm/foundry/materials.py) · **Palette:** `base #9cc9f2` `highlight #ffffff` `shadow #2a4d7a` `rim #cfe9ff`

## How to recreate it

1. Worley facets with per-cell tilted normals
2. faceted refraction of a noise backdrop + per-facet Blinn glints under an orbiting light; F2-F1 fracture lines; frost speckle

Every material then goes through the shared shell (`keycap.compose`): stepped extrusion, black ink, lit bezel, inner glass rim, clearcoat strip and top lip. Faces never move.

## Contract

| Field | Value |
|---|---|
| geometry | faceted (piecewise-planar) relief from Worley cells |
| optics | per-facet refraction offset + sharp glints, frosted edges |
| motion | light orbits slowly so facets twinkle in sequence; facets do not move |
| interaction | press = crack-light: a bright fracture front runs facet to facet |
| hierarchy | tier 5; glint count capped per frame |
| rarity | Legendary: rose-gold facets |
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
python3 -m tools.celestialrithm.foundry.board --ids crystal_ice --cols 1 --size 400x260 --seconds 6 --out /tmp/crystal_ice
```
