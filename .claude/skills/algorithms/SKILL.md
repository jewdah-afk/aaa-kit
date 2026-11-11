---
name: algorithms
description: Use when picking or chaining algorithms for a game look or system - noise, domain warping, distance transforms and jump flooding, cellular automata, reaction-diffusion, Voronoi, flow fields, dithering, palette quantisation, spatial hashing, pathfinding, and "Godrithms" (layered chains of small algorithms that make one look). Triggers on "algorithm", "procedural", "chain", "godrithm", "what technique", "how do I generate", "pattern", "distance field", "cellular automata", "flow field", "spatial hash".
---

# algorithms

One algorithm makes a demo; a chain of five makes a look. A **Godrithm** is a chain of small, typed passes (each one job, each swappable), so a new look is a new order of passes rather than new code.

## When to use

- Turning a mood ("corrupted", "frozen", "arcane") into a concrete technique
- Choosing between techniques for a system (crowds, placement, paths)
- Building a reusable procedural pipeline

**Not for:** world layout specifically (`procedural-world`) or shader maths in depth (`shaders-and-sdf`).

## Method

1. **Name the output first:** a mask, a field, a set of points, a path or a palette index.
2. **Pick passes from the library** below. Each pass has typed input and output (field → field, points → field, …).
3. **Chain shape → life → structure → finish:**
   - *shape:* noise, SDF, Voronoi, L-system
   - *life:* domain warp, advection, cellular automaton steps
   - *structure:* threshold, distance transform, edge detect
   - *finish:* bands, dither, palette, glyph map
4. **Make it deterministic.** Seed everything; hash-based noise; no `math.random` inside passes.
5. **Cache what doesn't change.** Bake static passes once and recompute only the animated tail.
6. **Measure each pass.** Write the ms per pass next to the chain.
7. Run the self-check.

### Library → game use

| Algorithm | One job | Game uses |
|---|---|---|
| Value / gradient noise, fBm | Smooth randomness | Terrain, clouds, wobble, dissolve masks |
| Domain warping | Organic distortion | Marble, smoke, corruption, living backgrounds |
| Worley / Voronoi | Cells and edges | Stained glass, cracks, biomes, shields |
| Distance transform / jump flooding | Distance to the nearest feature | Outlines, glows, bevels, safe-zone fields |
| Cellular automata | Local rules → global pattern | Caves, fire spread, corruption, life |
| Reaction–diffusion (Gray–Scott) | Self-organising spots and stripes | Coral, skin patterns, infection spread |
| Flow fields | A direction per cell | Crowd steering, particle silk, wind |
| Boids | Flocking from 3 rules | Fish, birds, bats, swarms |
| Poisson disk | Even random points | Props, trees, spawns (see `procedural-world`) |
| L-systems | Grammar-grown branching | Trees, lightning, coral, upgrade trees |
| Spatial hash | Neighbour queries in O(1) | Collision, crowd separation, pickups |
| A* / Dijkstra maps | Paths and distance-to-goal | AI pathing, flee maps, fog reveal |
| Ordered (Bayer) dithering | Hard-pixel gradients | Pixel art lighting, fades |
| Palette quantisation (OKLab bands) | Cel steps with perceptual spacing | Banded lighting, consistent palettes |
| Midpoint displacement | Jagged fractal lines | Lightning, coastlines, cracks |
| Verlet integration | Stable ropes and cloth | Whips, banners, capes, chains |

The full 57-chapter compendium and 1,361 idea cards live in the ObsidianVault repo (`Cursed Survivors/Research/Algorithm Compendium/`, `Library/Ideas/`).

## Hierarchy rules it obeys

- §2: generative engines are tier 6. They feed louder tiers but never compete for attention themselves.
- §12: glyph and aggregate representations carry one meaning each, with hysteresis.
- §6: at the calm rung, animated passes slow down or freeze.

## Engine notes

**Roblox.** Run passes on `buffer`s or flat arrays (not tables of tables). Use `--!native` for inner loops in Studio, but measure interpreted too. Split heavy chains across frames (`task.wait()` between passes during a bake) or precompute on load.

**Web.** Typed arrays on the CPU for ≤ 256², and WebGL ping-pong framebuffers for anything larger or animated.

## Process

To put an algorithm render on a model (not just a flat canvas), evaluate it in 3D at each texel's surface point, or project a tiling 2D render triplanar: [procedural textures playbook §2](../../../docs/playbooks/procedural-textures.md#2-getting-2d-algorithm-renders-onto-the-model).

## Example

`examples/Chain.luau` runs fBm noise → domain warp → threshold → chamfer distance transform → quantised bands. It's deterministic per seed and tested in `examples/Chain.test.luau`.

```lua
local Chain = require("./examples/Chain")
local base = Chain.noise(128, 72, 16, 5, 1234)              -- shape
local look = Chain.run(base, {
	Chain.warp(6, 24, 7),                                   -- life
	Chain.threshold(0.52),                                  -- structure: mask
	Chain.distance(),                                       -- structure: distance from mask
	Chain.bands(4, 8),                                      -- finish: 4 cel steps → palette index
})
-- look.v[i] is 0..3: map to a 4-colour ramp, or to glyphs " .:#"
```

## Make it insane

1. **Self-assembling chains:** a planner that works backwards from the requested output type ("a glow mask") and picks the cheapest chain of passes that produces it, sharing intermediates between looks.
2. **Corruption that spreads by reaction-diffusion:** the boss's influence grows across the map as a Gray–Scott pattern seeded by its attacks, and the player can see the next tiles about to flip.
3. **Glyph renderer:** the whole world is drawn as a lit ASCII field (luminance → glyph ramp, edge direction → `/ | \ -`), with a rune wave washing across on big events.

## Self-check

- [ ] Each pass does one job and has a typed input and output.
- [ ] Same seed → same output (a test proves it).
- [ ] Static passes are cached; only the animated tail runs per frame.
- [ ] Per-pass cost measured and written down.
- [ ] No pass uses `math.random`; RNG is passed in.
