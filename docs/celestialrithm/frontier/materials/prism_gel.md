# Prism Gel (`prism_gel`)

**Family:** thin film / gel · **Source:** [materials.py:126](../../../../tools/celestialrithm/foundry/materials.py) · **Palette:** `base #3a1670` `highlight #ffe4ff` `shadow #1a0638` `rim #d77bff`

## How to recreate it

1. two-level domain-warped thickness field
2. spectral thin-film interference (CIE-integrated) over a violet gel with dispersion fringes

Every material then goes through the shared shell (`keycap.compose`): stepped extrusion, black ink, lit bezel, inner glass rim, clearcoat strip and top lip. Faces never move.

## Contract

| Field | Value |
|---|---|
| geometry | gel height = warped fbm |
| optics | thin-film 34-wavelength spectrum, Fresnel-weighted |
| motion | film drains downward and swirls (warp in time) |
| interaction | press = film thins at centre -> colour bands race outward |
| hierarchy | tier 5; iridescence saturation capped so it never outshines tier 6 |
| rarity | Mythic: gold-black film |
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
python3 -m tools.celestialrithm.foundry.board --ids prism_gel --cols 1 --size 400x260 --seconds 6 --out /tmp/prism_gel
```
