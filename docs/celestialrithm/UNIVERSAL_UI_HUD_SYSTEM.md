# Celestialrithm Universal UI/HUD Matrix

## Purpose
This document expands the project beyond any one game. The fixed promise is **high-end stylized UI that is artistically cohesive, clear, and performant**. A visual preset is a collection of materials, behaviors and semantics—not an excuse to replace the approved art.

## Design space
14 genres × 20 components × 20 material families × 3 device classes = **16,800 generated candidate recipes**, created via `python3 tools/celestialrithm/build_ui_catalog.py`. These are *possible configurations*, NOT 16,800 working shaders or designs. Use `ui_recipe_catalog.jsonl` with `rg`/`jq` or a local index, then implement and test winners.

### Genre presets
Incremental (numerical dominance), roguelike (combat urgency), tower defense (upgrade paths), simulator (progression and collection), crafting (item comparison), racing (speed and positional feedback), collection (rarity and identity), survival (threat and survival), social (avatars and affordances), strategy (density and information grouping), platformer (low occlusion), dungeon (loot/reward), tycoon (economy and affordance), RPG (character stats and skill trees).

### Components
Primary/secondary keys; side nav; currency/XP/health meters; inventory slots; shop cards; rarity frames; tooltips; modals; notifications; skill tree; quest tracker; hotbar; avatar stage; reward reveal; world selection; crafting slot; settings toggle.

### Material and motion stages
Materials: hydroglass, prism gel, solar plasma, ice crystal, slime, holo foil, void, molten gold, brushed steel, neon ink, pearl, obsidian, biolume, aurora, frosted glass, ceramic, copper, iridescent, sandstone, pixel chrome. Motion: spring presses, elastic rebound, moving caustics, gradient flow, masked shine, edge tracing, number odometers, staggered rewards, SDF reveals, vertex bend, icon relief, squash/stretch, material memory, light sweeps, pulse, fracture/heal, wave coupling, progress flow, focus brackets, depth parallax.

## System blocks (production intent)

| Block | Required state | Attention contract | Minimum output |
|---|---|---|---|
| Shop | locked, affordable, owned, equipped, sale | price + one Buy must win | data-driven purchase cards |
| Inventory | selected, available, rarity, equipped | selected silhouette wins; no slot spam | adaptive grid + details |
| Taskbar | idle, selection, alert, cooldown | navigation quiet at rest | safe-edge anchors |
| Top HUD | currency, XP, level, event | numbers before labels | format-and-fit counters |
| Combat HUD | HP, threat, ability | threats win over decorative loot | protected health/telegraph |
| Reward | reveal, accept, dismiss | one ceremony at a time | skippable and reduced-motion |
| Avatar hero | equipped aura and rank | character readable at all times | sockets/proxy meshes; no arbitrary mesh promises |
| World/map overlay | waypoint, region, target | playable traversable areas unobscured | authored geometry remains authoritative |

## Performance policy: starting targets, not benchmark results
60 Hz frame = 16.67 ms for **the whole game**, not 16.67 ms to spend on FX. Proposed per-frame FX budget: low mobile ≤0.7 ms, mid mobile ≤1.5 ms, desktop ≤2.5 ms until device profiling justifies changes. Fall back to baked PNG/SDF first, then reduce simulation resolution/cadence, then disable secondary geometry. Use existing `lib/frontier/Atlas.luau` and `Uploader.luau` for prioritized shared uploads; never assume each material owns an independently refreshing EditableImage. Budget/LOD decisions use live measured p95 frame time with 10% hysteresis and minimum 2-second recovery, not instantaneous oscillation. These are engineering targets and require Studio measurements.

## Readability and safety gates from existing HIERARCHY.md
- One strongest action per panel; the text/icon region stays above simulated materials.
- APCA |Lc| ≥75 for play-critical numbers and ≥60 for typical labels, unless explicitly verified.
- Audit `tools/hierarchy/hierarchy.py`: predicted first fixation in focus, lift ≥1.5, competitor <0.9, squint gap ≥0.08 OKLab L, and deutan/protan checks.
- Flash-rate guard ≤3 flashes/s for relevant large-area contrast changes; provide reduced-motion and no-audio modes.
- Critical HUD cannot be covered by ambient effect passes. No always-on cursor magnetism.
- Calm frames are still; only selected/active elements receive minimal ambient motion.

## Real renderer/baker road map
1. Read source-of-truth Figma keycaps or authored 3D meshes and import/reference UVs, materials, and alpha masks.
2. Bake albedo, normals, height, silhouette SDF/MSDF, pressure response maps, specular/caustic masks, and event sprites using an offline GPU/CPU renderer.
3. Export stable mesh, compact atlas textures and normalized event curves.
4. Implement with UI labels as separate guaranteed-readable GUI objects and optional `EditableMesh` under-face structures.
5. Record 60 FPS output as a *video verification* and independently profile the actual Roblox implementation. Compare against approved animated-board target at exact phone presentation sizes.
6. Maintain A/B and ablation runs: each algorithm must justify its increased render cost or measurable quality.

## Self-improvement protocol
A candidate does not become a winner until it passes screenshot QA, content legibility, event motion, reduced-motion mode, no-hue-only signaling, and device-performance gates. Keep rejected candidates and attribution. Do not allow a self-ranking algorithm to rewrite art direction, source assets, or gameplay controls. Human approval before promotion to shipping components.
