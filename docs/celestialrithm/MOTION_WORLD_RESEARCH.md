# Celestialrithm — motion, UI/UX and map-generation research gate

Status: added as source + **offline verified experiments**, not as Roblox runtime proof.

## Source-of-truth contract

1. Existing authored Frozen Lake map, proportions, studded geometry, and camera are authoritative. Procedural techniques may extend/new chunk, repair, add effects, never overwrite the authored world.
2. Approved stationary 12-material UI board is the **minimum optical target**. Actual textless button faces, grounded bevel/depth, and squared ink silhouette must hold. Motion is primarily **in the material**, not the button's position or cursor attraction.
3. T12–T16 are **research quality milestones**; existing hierarchy tiers 1–6 are screen-loudness budgets. Do not equate them.
4. A 60 FPS encoded video is never a 60 FPS Roblox benchmark.

## 45 motion candidates (5 groups)

**Microinteractions:** impulse-to-spring, overshoot, anticipate/settle, hold creep, impact response, compressed bevel, continuous vs stepped timing, material wake, surface-memory trace.

**Navigation:** shared-element transition, visual continuity morph, FLIP layout animation, directional reveal, breadcrumb emphasis, selected-state stroke, accordion sequencing, spatial continuity, focus preservation.

**Rewards:** staging, staggered entrances, particle-funnel arrival, rarity contrast ladder, temporal color economy, elastic prize reveal, incremental meter fill, currency count-up, anticipation/peak/rest.

**Physics & field:** XPBD constraint projection, Verlet update, critically damped spring, eigenmode plate vibration, damped wave equation, semi-Lagrangian advection, curl-noise flow, vorticity confinement, caustic ray Jacobian, SDF contour propulsion.

**Perception & sound:** salience gating, onset saturation budget, color-role locking, dwell and attentional-blink spacing, flash-safe intensity cap, 2–3-part sound cue, per-bus voice stealing, 80 ms retrigger protection, reduced-motion alternatives.

## 40 model/map candidates (5 groups)

**Block geometry:** greedy meshing, surface nets, dual contouring, Marching Cubes (ONLY where an explicit stylized transition is desired), 2.5D slice meshing, orthogonal terracing, stud cap tiling, crack-free LOD skirts.

**Landscape:** ridged multifractal noise, low-frequency FBM, domain warp with amplitude clamp, spline river corridor, signed distance field biome mask, morphological erosion, terrace quantization, terrain stamp blending.

**Layout:** constraint graph towns, Voronoi region assignment, Delaunay route candidates, A* traversable routes, minimum spanning tree roads, path clearance via SDF, authored landmark anchors, modular socket rules.

**Props & vegetation:** stochastic grammar trees, space-colonization branching, impostor LOD, mesh instancing, deterministic prop hashing, silhouette/crowding gate, color-role material distribution, global seed derivation.

**Runtime:** clipmap ring selection, interest-management chunks, work scheduling, weighted dirty regions, fixed topology incremental updates, greedy mesh topology caching, streaming budget, collision proxy, temporal sample reuse.

## Verified constraints and external source registry

- Roblox EditableImage (display side): only **one displayed EditableImage refresh per frame**. Reuse `lib/frontier/Atlas.luau` + `Uploader.luau`, do not create a per-keycap EditableImage stream. https://create.roblox.com/docs/reference/engine/classes/EditableImage
- EditableMesh limit 60,000 vertices / 20,000 triangles per instance, with device memory budgets and nil allocation failure. https://create.roblox.com/docs/reference/engine/classes/EditableMesh
- EditableMesh fixed topology and attribute edits: prefer fixed topology when modifying an imported mesh. https://create.roblox.com/docs/reference/engine/classes/AssetService/CreateEditableMesh
- PositionBasedDynamics XPBD and shape matching: https://github.com/InteractiveComputerGraphics/PositionBasedDynamics
- Real-time fluid solvers: https://developer.nvidia.com/gpugems/gpugems/part-vi-beyond-triangles/chapter-38-fast-fluid-dynamics-simulation-gpu
- MSDF preserving sharp corners: https://github.com/Chlumsky/msdfgen
- Fast procedural blocks greedy meshing: https://0fps.net/2012/06/30/meshing-in-a-minecraft-game/
- Surface extraction and LOD: https://transvoxel.org/
- GPU rendering and tone management references: https://google.github.io/filament/Filament.html
- Roblox authored terrain and terrain voxel basis: https://create.roblox.com/docs/parts/terrain

## Motion architecture proposal

- `MotionDirector.luau` is pure Luau and only coordinates motion signals. One `owner` controls the most salient cue, with 75 ms dedupe and optional reduced motion. Studio components map `sample()` to drawn keycaps, masks, audio and mesh simulations.
- Standby button position is immovable. No magnetism and no continuous bounce. Selected materials are allowed very slow internal phase drift only while selected.
- Events and priorities are semantically driven: reward > alert > purchase > press > select. Critical threat indicators can preempt everything except explicit ceremony.
- Render pixel/geometry layers with the existing hierarchy owner buffer and atlas uploader; UI text/icons draw last.

## Map architecture proposal

- `StudWorld.lua` generates data for **new** chunk extensions; the current map is never overwritten. All voxels are square, block-stepped, deterministic under seed. Path corridor remains clear. No automatic image-generated realistic scenery.
- `world_preview.py` generates an OBJ to inspect topological simplification and a 2D stud map preview; this is **not a Roblox map capture**. Long term: import per-chunk mesh/Part output via a Studio-only adapter after budget checks.
- Heightfield only as a substrate; exact source landmarks, fence placement, bridges, resource nodes remain authored.

## Stress targets (test thresholds, NOT measured budgets)

| System | Proposed mobile allocation | Failure response |
|---|---:|---|
| UI physical motion | <= 0.35 ms main-thread average | lower sample frequency, use native TweenService |
| EditableImage draw preparation | <= 1.0 ms per scheduled atlas update | coarser field, half-rate, smaller dirty tiles |
| Mesh vertex deformation | <= 0.65 ms for one hero item | reduce vertices or use one baked mesh |
| Motion/audio coordination | <= 0.20 ms | skip decor, flatten active event graph |
| Procedural map chunk incremental work | <= 1.0 ms scheduled frame slice | throttle generation/streaming |
| Entire client frame | 16.67 ms for 60 FPS target | reduce effect density based on frame-time EMA |

Above numbers are initial **targets only**. Verify real mobile device percentiles (p50/p95/p99), memory, actual frame present rate, image update latency, and input-to-photon delay.

## Required hierarchy gates

- One primary CTA per window and one animated focus event at a time.
- Pixel ownership: UI above ambient/world; ceremony is explicitly higher.
- Per-button optics must not paint over icon or label masks.
- Three-channel screen audit: resting frame, peak frame, reduced motion.
- Test 390×844 portrait and 844×390 landscape; touch target >=44 px.
- Scanpath focus ≥ 1.5 lift, competitor < .9, OKLab squint gap ≥ .08, and text APCA |Lc| >= 60 (>=75 critical values).
- <= 3 flashes/sec and spatial coverage gate; respect reduced-motion preference.
- New generated map screenshots must match original block size/palette/camera angle against authored anchors.

## Next execution gate

Run pure Luau modules with Lune in the actual checkout, then Studio integration with GUI source binding and real MeshParts. Capture device profiles, compare to the approved animated board, and reject low-quality results despite technical success.
