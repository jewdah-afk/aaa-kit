# Algorithms for EditableImage: families, best picks, chains

Our private research catalogues ~10,000 algorithms (an atlas of ~9,000 kept entries across imaging, maths and graphics) and a 57-chapter compendium. This page is the EditableImage-relevant subset: what earns its pixels at 320×180–480×270 in interpreted Luau. Longer idea lists in the kit: [EDITABLEIMAGE_ALGORITHMS.md](../../../../docs/research/ideas/EDITABLEIMAGE_ALGORITHMS.md) (1,000+ effect ideas by category), [ALGORITHMS_CORE.md](../../../../docs/research/ideas/ALGORITHMS_CORE.md) (100 core algorithms), [PICKS.md](../../../../docs/research/ideas/PICKS.md). Sibling skills: [`algorithms`](../../algorithms/SKILL.md), [`shaders-and-sdf`](../../shaders-and-sdf/SKILL.md).

**Cost key** (interpreted, per frame, at game resolution): **A** bake once at load · **B** cheap every frame (< 0.3 ms) · **C** per frame only in a small region or at half res/rate · **D** amortize over frames or full tier only.

## Families and best picks

| Family | Best picks for pixels | Cost | Pixel job |
|---|---|---|---|
| Noise | Value/gradient noise, fBm, domain warping, Worley F2−F1, curl noise | A (bake tiles), C live | Ground, fog, cracks, ember motion |
| Distance fields | Exact distance transform (Felzenszwalb), jump flooding, 2D SDF composition | A per sprite, C live | Outlines, glows, soft shadows, shape morphs |
| Dithering & palettes | Bayer 4×4, blue-noise threshold, Floyd–Steinberg/Atkinson, OKLab nearest, band quantise | B (ordered), A (error diffusion) | The hard-pixel look; snap any effect to the palette |
| Palette-index rendering | Index buffer + colour cycling, LUT grades | B | Water, magic, rarity rims, day/night with no per-pixel maths |
| Pixel-art scaling | Integer nearest, Scale2x/EPX, rotsprite | A | Upscale authored sprites at load only |
| Rasterisation | Bresenham, scanline polygons, span lists | B | Everything; spans feed `SpanBlit` |
| Glyphs | Density glyph ramps, bitmap fonts, glyph scramble/decode | B | Crowd LOD, numbers, text reveals |
| Edges & stylisation | Contrast-adaptive outline, rim from distance field, morphological erode/dilate | A/B | Figure-ground: bodies never sink into the ground |
| 2D lighting | Banded light map, recursive shadowcasting, radiance cascades | C (half res), D (cascades) | Lantern pools, FOV, GI |
| Grid fluids | Stam stable fluids, shallow water / pipe model, damped wave equation, Lattice Boltzmann | C (small grid, upsample) | Smoke, puddles, ripples |
| Particle fluids & granular | Sand CA (angle of repose), SPH splashes, FLIP | C with sleeping chunks | Sand, splashes, coin heaps |
| Constraint physics | Verlet, PBD/XPBD ropes and cloth, mass-spring, FABRIK | B | Whips, tethers, capes, jelly sprites |
| Springs & easing | Critically damped springs, second-order dynamics, trauma² shake, hit-stop | B | UI juice, pops, camera feel |
| Cellular automata | Cave 4-5, cyclic CA, Brian's Brain, forest fire, Lenia, Reiter snowflake | C | Spirals, crackle, frost, decor |
| Reaction-diffusion | Gray–Scott, Gierer–Meinhardt | D (bake) or C small | Lichen, corruption, organic patterns |
| Crowds | Spatial hash, boids, flow/Dijkstra fields, density splat + LOD | B per body | Thousands of enemies readable |
| Growth | DLA, space colonisation, L-systems, dielectric breakdown, Physarum | A grow, B reveal | Lightning, frost, trees, tendrils |
| Sampling | Poisson disc, blue noise (void-and-cluster), low-discrepancy | A | Scatter, dissolve thresholds |
| Filtering & post | Separable box blur ×3 ≈ Gaussian at half res, bloom limited to one tier, chromatic split, vignette | C | Glow on the loudest tier only |
| Dissolve & fire | Blue-noise dissolve, Doom-fire column field, burn edges, ash fall | B | Deaths, vanishes, transitions |
| Trails | Ring-buffer ribbons, persistence trails, arc-length chases | B | Projectiles, rarity comets |
| Oscillators | Kuramoto sync, Lissajous, phyllotaxis | B | Fireflies, candles, bursts |
| Chaos & fractals | Clifford/de Jong attractors, fractal flames, IFS | A (accumulate once) | Unique sigils per seed, reveals |
| Geometry & contouring | Marching squares, Voronoi/Delaunay, convex hull, union-find | A/B | Puddle outlines, shatter, gem merging |
| Fourier | Epicycles, FFT filters | A | Sigils drawn stroke by stroke |
| Attention models | Saliency, scanpath prediction, motion budget | QA tool | Prove the threat is the loudest thing |
| Frame timing | Budget manager, tiered effect scheduler, time-slicing | B | Keeps 60 fps at the worst minute |

## The top picks to build first

1. **Frame budget manager + tiered effect scheduler.** Every effect asks for ms; low tiers drop first.
2. **Contrast-adaptive outline** and **crowd density darkening.** Readability before spectacle.
3. **Effect density limiter + brightness ceiling.** No late-game wall of effects.
4. **Damage-number stacking** (one growing number per target) and **HP damage ghost.**
5. **Swarm LOD** (glyph or shimmer cells) for 1,000+ bodies on phones.
6. **Hit stop + hit flash** from data, not code.
7. **Palette-index rendering** with colour cycling.
8. **Exact distance transform / jump flooding** — the base of outlines, glows, shadows and morphs.
9. **Radiance cascades** on the full tier only.
10. **Shallow water** and **position-based dynamics** — the two sims that cover most liquid and rope/cloth needs.

## Godrithms: chain small algorithms into one moment

A Godrithm is a chain of 8–15 small algorithms that together make one unforgettable moment, ending in band quantise + dither so it stays hard-pixel. Rules that made ours work:

- **Name the tier first** (WORLD, THREAT, HERO, REWARD, CEREMONY). Bloom and the loudest colours belong to CEREMONY only.
- **Each link is cheap** (A or B); the spectacle comes from composition, not one heavy pass.
- **End every chain** with band quantise + Bayer dither, and for gameplay moments with a saliency check that the danger telegraph is still the brightest danger-coloured thing.
- **Phone path for every chain:** drop the D links, halve the C links.

Generic examples of the shape:

| Moment | Chain |
|---|---|
| Weapon evolution | PBD rope → arc-length param → jump-flood field around it → curl-noise embers seeded on the field → small stable-fluid smoke → Gray–Scott flare at the tip → spring icon pop → thin-film foil → CEREMONY-only bloom → trauma² shake → hit-stop → quantise |
| Liquid lands on a horde | fBm heightfield → erosion bake (hollows) → shallow water fills them → wave ripples → normals → caustics → marching-squares puddle outlines → boids steer by the flow → blue-noise dissolve on kills → Poisson-disc drops → quantise |
| Boss arrival | fast-marching front → jump-flood Voronoi shatter along it → Physarum tendrils → dielectric-breakdown lightning → accumulated attractor silhouette → glyph-scramble name decode → chromatic split + hit-stop → saliency check → quantise |
| Night map around the hero | Poisson props → space-colonisation trees → Worley stones → WFC paths → shadowcasting from the hero's light → wind field + Verlet grass → lit fBm fog → Kuramoto fireflies → glyph LOD at the edge → quantise |
| Legendary reward | spring reel → PBD coins → angular god rays → per-seed attractor sigil → jump-flood glow frame → arc-length light chase → foil + tilt → spring magnet into the counter → odometer → curl-noise confetti → quantise |
| Worst-minute horde | spatial-hash boids → Dijkstra flow field → density splat + glyph LOD → MST chain lightning → union-find pickup merging → number stacking → motion-budget arbiter → protected dark ring around the hero → quantise |

Build a chain one link at a time, measure each link with paired A/B, and keep the per-link ms in the effect's notes.
