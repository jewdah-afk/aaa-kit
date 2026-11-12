# Void Singularity (`void`)

**Family:** lensing · **Source:** [materials.py:289](../../../../tools/celestialrithm/foundry/materials.py) · **Palette:** `base #2a0a4a` `highlight #f2b8ff` `shadow #07020f` `rim #b13cff`

## How to recreate it

1. point-mass lens (deflection theta_E^2 / r) over a hashed starfield + polar-swirled fbm accretion ring + photon ring

Every material then goes through the shared shell (`keycap.compose`): stepped extrusion, black ink, lit bezel, inner glass rim, clearcoat strip and top lip. Faces never move.

## Contract

| Field | Value |
|---|---|
| geometry | flat; distortion is optical |
| optics | gravitational lensing of the backdrop, Einstein ring |
| motion | accretion swirls (Keplerian: faster near the core) |
| interaction | press = lens mass x2, ring flares then relaxes |
| hierarchy | tier 5; dark material: a contrast anchor among bright keys |
| rarity | Mythic: second orbiting singularity |
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
python3 -m tools.celestialrithm.foundry.board --ids void --cols 1 --size 400x260 --seconds 6 --out /tmp/void
```
