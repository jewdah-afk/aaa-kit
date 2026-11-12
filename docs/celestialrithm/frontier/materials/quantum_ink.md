# Quantum Ink (`quantum_ink`)

**Family:** stable fluid · **Source:** [materials.py:591](../../../../tools/celestialrithm/foundry/materials.py) · **Palette:** `base #140a2a` `highlight #e6fbff` `shadow #05030c` `rim #00e5ff`

## How to recreate it

1. Stam stable fluids (semi-Lagrangian advection, 24 Jacobi pressure iterations, vorticity confinement) with orbiting neon dye emitters in a dark gel

Every material then goes through the shared shell (`keycap.compose`): stepped extrusion, black ink, lit bezel, inner glass rim, clearcoat strip and top lip. Faces never move.

## Contract

| Field | Value |
|---|---|
| geometry | flat gel |
| optics | additive dye emission, faint refraction |
| motion | two emitters orbit, dye curls into vortices |
| interaction | press = central radial burst of white dye |
| hierarchy | tier 5; high entropy: one per screen |
| rarity | Mythic: tri-colour dye |
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
python3 -m tools.celestialrithm.foundry.board --ids quantum_ink --cols 1 --size 400x260 --seconds 6 --out /tmp/quantum_ink
```
