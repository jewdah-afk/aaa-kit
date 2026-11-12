---
name: procedural-world
description: Use when generating levels, maps and worlds - terrain, biomes, islands, caves, dungeons and arenas, prop and decal placement, Poisson-disk scatter, Voronoi regions, L-system trees, reaction-diffusion and cellular-automata patterns, flow fields, boids crowds, landmarks and set pieces, and readable play spaces. Triggers on "generate a map", "procedural world", "place props", "scatter trees", "biome", "dungeon", "cave", "level layout", "make the world feel alive".
---

# procedural-world

A generated world has to be readable before it's beautiful. The player must see where to go, what's dangerous and what's worth collecting, at phone size, in a crowd.

## When to use

- Maps, arenas, stages, islands, caves
- Placing props, decals, spawns and landmarks
- Ambient life (flocks, fireflies, drifting particles)

**Not for:** single algorithms outside a world context (`algorithms`) or mesh building (`editable-mesh`).

## Method

1. **Design the playable graph first.** Lanes, open fields, choke points and safe pockets, as a coarse grid or graph. Decoration comes last.
2. **Regions.** Voronoi cells or noise thresholds give biomes. Each biome gets one palette ramp and one prop set.
3. **Terrain.** fBm height with a falloff to the edges (islands) or carved valleys along the lanes. Keep walkable slopes walkable.
4. **Landmarks.** 1–3 per screen-width, unique silhouettes, placed at decision points. They're how players navigate.
5. **Scatter.** Poisson disk with a mask (no props on lanes, in water or near spawns). Props have three size classes and the big ones go first.
6. **Decals.** Low-contrast and world-tier, never brighter than pickups. They show history (scorch, footprints) and direction (paths).
7. **Life.** Boids for flocks and fireflies on independent clocks. Ambient motion is slow (tier 4).
8. **Readability pass.** Squint test: lanes and threats must read; props must not form false lanes or hide enemies. Run the figure-ground gate on enemy-versus-ground colours.
9. **Determinism.** One seed per map, so the same seed gives the same world on every client. Store only the seed and the edits.
10. Run the self-check.

## Hierarchy rules it obeys

- §2: world is tier 4 and generative engines are tier 6, so nothing here outshines the HUD or pickups.
- §3: world pixels are rank 2, below rewards, threats and the hero.
- §10: props never cover entities; the hero draws last.
- §11: ground vs. enemy contrast passes the 2-band gate.
- §12: dense regions simplify before readability fails.

## Engine notes

**Roblox.**

- Terrain: `Terrain:FillBlock` and `WriteVoxels` for voxel terrain, or EditableMesh chunks (`editable-mesh`).
- Props: clone from a template folder, set `CFrame` from scatter points and parent in batches (100 per `task.wait()`).
- Use `StreamingEnabled` for big worlds, and put generated models in `Model.ModelStreamingMode = Atomic` groups.
- Generate on the server for gameplay geometry (authoritative), or on each client from the seed for pure decoration.

**Web.** Canvas for 2D maps, typed arrays for fields, three.js for 3D.

## Process

For 3D worlds, follow the [world hierarchy playbook](../../../docs/playbooks/world-hierarchy.md): seven tiers, foreground/midground/background composition, the squint value check, and one Explorer tree owned by a single module. For a worked stud example (layout, numbers, a downloadable `.glb`), see the [stud map guide](../../../docs/playbooks/map-guide.md).

## Example

`examples/Poisson.luau` is Bridson's Poisson-disk sampling with a mask callback and an injectable RNG. It's tested in `examples/Poisson.test.luau` for spacing, determinism and the mask.

```lua
local Poisson = require("./examples/Poisson")
local rng = Random.new(seed)
local trees = Poisson.sample(512, 512, 12, function()
	return rng:NextNumber()
end, 30, function(x, z)
	return not isLane(x, z) and heightAt(x, z) > waterLevel
end)
for _, p in trees do
	-- place a tree at (p.x, heightAt(p.x, p.y), p.y); pick a size class from the hash of (p.x, p.y)
end
```

(`isLane`, `heightAt` and `waterLevel` come from your map's own data.)

## Make it insane

1. **History terrain:** every fight scorches and scars the ground and every path wears in with footsteps, persisted per server, so the map tells the story of the session.
2. **Set-piece director:** a pacing system places a landmark event (collapsing bridge, meteor field, boss arena) where the player's route will cross it, based on their heading over the last 30 s.
3. **Reaction-diffusion biomes:** the boundaries between regions are Gray–Scott patterns, giving organic, unique borders that animate slowly as a corruption front.

## Self-check

- [ ] The playable graph exists before decoration; lanes stay clear.
- [ ] Same seed → same world (test it).
- [ ] Props never hide enemies or pickups; the hero draws on top.
- [ ] Each screen has 1–3 landmarks.
- [ ] Ground vs. enemy contrast passes the gate.
- [ ] Generation time measured; big worlds generate in batches without hitches.
