# Bio Slime (`bio_slime`)

**Family:** living fluid · **Source:** [materials.py:183](../../../../tools/celestialrithm/foundry/materials.py) · **Palette:** `base #5fbf12` `highlight #f4ffb8` `shadow #1f4a05` `rim #a8ff2e`

## How to recreate it

1. metaball membrane field + morphing Worley cytoplasm + rising bubbles; wrap-lit subsurface + membrane specular

Every material then goes through the shared shell (`keycap.compose`): stepped extrusion, black ink, lit bezel, inner glass rim, clearcoat strip and top lip. Faces never move.

## Contract

| Field | Value |
|---|---|
| geometry | metaball heights over a cellular gel |
| optics | wrap diffuse (SSS approximation), wet specular, bubble caps |
| motion | blobs drift on Lissajous paths, cells breathe, bubbles rise |
| interaction | press = blobs swell 25% and merge, then wobble back (spring) |
| hierarchy | tier 5; bubbles are the only small bright marks |
| rarity | Epic: toxic magenta nuclei |
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
python3 -m tools.celestialrithm.foundry.board --ids bio_slime --cols 1 --size 400x260 --seconds 6 --out /tmp/bio_slime
```
