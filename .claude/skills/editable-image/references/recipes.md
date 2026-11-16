# Effect recipes and their costs

Every recipe writes RGBA8 into your frame buffer and goes through the owner rule. Costs are headless interpreter ms unless marked; multiply by ~2–5 for a phone.

## Ready in `lib/pixelfx` (96×96 canvas)

| Effect | Algorithm | Use | Cost |
|---|---|---|---|
| Lichtenberg | Dielectric breakdown | Chain lightning | strike 42 (pool it), frame 1 |
| Physarum | Slime-mould agents | Corruption, curse auras | 3.4 / 2000 agents |
| WaveRing | Damped wave equation | Aura pulses | 1.4–20 |
| FrostDLA | Diffusion-limited aggregation | Freeze frost | grow 30 once, frame < 1 |
| JumpFloodOutline | JFA distance field | Selection, evolved glow | 33 once per sprite |
| BlueNoiseDissolve | Void-and-cluster threshold | Deaths, vanishes, transitions | 39 once (cache), frame < 1 |
| Bloom | Half-res bright pass + 3× box blur | Crits, chest light | 6 |
| PaletteDither | Floyd–Steinberg / Bayer, OKLab nearest | Snap anything to the palette | 11 |
| Phyllotaxis, OrbitTrails, FabrikChain, SlotReel | Vogel spiral, springs, FABRIK IK, landing curve | Bursts, orbiters, whips, reels | < 1 |
| CaveCA | 4-5 cellular automaton per chunk | Decor scatter | 14 per chunk |

Rule: anything with a one-off cost over ~5 ms (strike, grow, noise, outline build) is precomputed at load or pooled.

## In `lib/frontier`

Falling sand (sleeping 64×64 chunks), radiance-cascade 2D GI (cached ray hits, `step(budgetMs)`), Voxel Space terrain (checkerboard mode halves cost), sprite stacking, palette-indexed frames with colour cycling.

## Survivors-genre recipes we built (generic)

| Recipe | How | Cost (desktop Studio) | Phone path |
|---|---|---|---|
| Whip cut mask | Read the owner buffer to cut only bodies | 0.06–0.15 ms | same |
| Spring UI | Critically damped spring (2 floats) per element, integer-snapped output; sleep when settled | < 0.05 ms / 50 springs | same |
| Palette-cycling water/magic | Index spans, rotate an 8-colour ramp, re-resolve every 3rd frame | ~0.1 ms | static |
| Blue-noise screen dissolve | Threshold against a 64×64 blue-noise tile | ~0.4 ms full screen, ~0.01 / sprite | hard cut |
| Threat-value grade | Calm LUT on ground + pickups, threats untouched, baked per stage | ~0 | same |
| Banded lantern light | Half-res light map → 8-band lightness quantiser, 1 px dither at band edges | 0.25 ms (160×90) | half rate |
| Breathing warp ground | Per-row offset copies of the ground | ~1.9 ms ground total | every other frame, half res |
| Gem metaballs, foil cards | Field sum thresholded to the palette; foil only while the card screen is open | +1–2 ms on PC while open | off |
| Battle history | 16×16 blocks allocated where events happen | flat until full | fewer blocks |
| Glyph LOD crowds | Density glyphs with exact counts, hysteresis | 0.1–1.7 ms | same |

## Godrithms that read on a phone

Chain small algorithms into one look rather than one expensive one: noise → domain warp → band quantise → Bayer dither; JFA distance → outline + glow; reaction-diffusion or CA → palette index → colour cycling. See the [`algorithms`](../../algorithms/SKILL.md) and [`shaders-and-sdf`](../../shaders-and-sdf/SKILL.md) skills.

## Textures on 3D assets

UV-rasterise the mesh into a G-buffer, shade per texel in 3D, dilate islands, then apply with `lib/surfacebake` `Apply.bakeMeshPart` (runtime) or bake + upload at edit time (preferred for anything static). Bakes cost 70–3300 ms by size, so they never run per frame; animated texture passes cost 1–6 ms at 128²–256².
