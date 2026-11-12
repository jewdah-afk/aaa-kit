# Celestialrithm — System Architecture v1

**Status:** Offline reference implementation and proposed Roblox adapters. **Not** a Studio-verified plugin. The target is a coherent graphics orchestration engine; T12/T14+ are experimental research milestones, not the six visual loudness tiers of `HIERARCHY.md`.

## Non-negotiable visual contract

- Retain AAA-KIT squared Stud UI geometry: near-black ink `#0B0C10`, ink radius ~4 design px, lip/face ~2.5 design px, 1.5 px top highlight, saturated role-based hues. Ink/body/lip move together when pressed; text/icons remain registered on top.
- Flat face **appearance**, physical under-face **depth**. Not photorealistic transparent-glass mobile UI. No gigantic presentation chassis around the in-game HUD.
- Calm idle at rung 0. No bright perpetual sheen on every button. Only current selection may move subtly; key presses temporarily own a higher hierarchy budget.
- No cursor magnetism. Input changes *pressure*, not button location or camera location.
- Never repaint the high-priority text/icon atlas with liquid materials: input hitboxes and text stay native `GuiObject`.

## Modules and ownership

| Module | Input → output | Where it runs | Verification gate |
|---|---|---|---|
| MaterialCatalog | hue role, rarity, material preset → palette and field parameters | pure config | schema, palette contrast |
| MaterialField | time, pressure, UV → RGBA + gradients | offline Python → pure Luau port | frame deltas, bounds, determinism |
| MeshFace | pressure, held state → fixed vertices | optional EditableMesh | topology/winding/normal tests in Lune; Studio render |
| AtlasScheduler | weighted dirty rectangles → <=1 displayed EditableImage upload per frame | Roblox client | upload count, stale region budget |
| HierarchyDirector | context, urgency, priority → effect permissions/intensity | pure Luau | one loud element, protected area, safe motion |
| AudioDirector | event/material → transient + body + tail with group ducking | Roblox SoundService | sound priority, mobile mute parity |
| Shop / Inventory / Taskbar | component data → anchored layout, text and hitboxes | Figma renderer / Roblox GuiObjects | 844×390, 390×844; overlap and legibility |
| RenderBake | GLB/OBJ + masks + camera + stage → renders, texture maps, QA | Three.js/Blender offline | silhouette/angle/UV tests |
| AvatarHero | current character appearance → effect sockets/proxy layers | Roblox client | rig restore, scale, accessory coverage, LOD |
| QA Director | captures + telemetry → failures + experiment lineage | Python/Studio | automatic vs human scores separated |

## Event contracts

Shared event = `{kind, componentId, materialId, eventTime, importance, seed, reducedMotion}`. The same event drives mesh pressure, image wave, GUI whole-key translation, tiny sound cue, and timing. The state owner is an event scheduler; an individual material cannot override screen-wide prioritization.

- Idle: only selected key has low-velocity motion. No sparkle burst.
- Press: whole key travels down by depth D, membrane receives localized impulse, caustic gradient follows pressure, transient SFX.
- Hold: stable compressed state with low-frequency under-face current; no additional cue spam.
- Release: displacement rebounds, material lags by phase offset, brief rim trace, body sound tail.
- Reward: one ceremony owner; lower-priority materials attenuate and music/ambience duck.
- Upgrade: source button, counter, inventory result, avatar aura receive a single event with staggered onsets; never simultaneous unrelated blasts.

## Renderer / model bake

1. Import licensed/user-created GLB or OBJ into offline tool. Do **not** assume all third-party models can be redistributed. The supplied LihFolk ZIP has no clear license in the material inspected earlier: treat as research-only until permission verified.
2. Convert model hierarchy and materials to canonical *mesh, material, UV, socket, mask* manifest. Validate object bounds, disconnected components, degenerate triangles and inverted normals.
3. Create authored or procedurally constructed UV islands and rasterize to normal, depth, ID, occlusion, albedo and emissive masks. Expand islands 1–2 pixels so filtered sampling cannot reveal seams.
4. Simulate surface effects offline at high resolution; use temporal samples across 120–360 frames and compare output to game-art contract.
5. Export fixed-topology LOD meshes, a low-cost material atlas, thumbnail/turntable, and a manifest with provenance and quality gates. `EditableImage` data is **not** an imported magical shader; a Luau algorithm must write its RGBA buffer on the client.
6. The runtime may only render the subset matching its budget. Prioritize the selected inventory mesh and high-rarity hero model; downgrade unselected cells to static baked PNGs.

**Three.js strategy:** start with `GLTFLoader`, UV shader or canvas texture, `WebGLRenderTarget` and a fixed orthographic camera. For Roblox the result is a reference/bake, not a GPU program that can be transferred wholesale. Use authored Luau for runtime EditableMesh and EditableImage effects.

## Flat UI hierarchy: concrete placements

- In-game Top: currency/XP/counters, mostly static. Noncritical currency increase = 110 ms value bump, not sparkle storm.
- Left rail: Shop/Upgrades/Inventory/Index; selected state gets bone-white ring (existing playbook) and one quiet material pass.
- Shop: one featured item may own T1 visual attention. Price and BUY text remain over the material.
- Inventory: grid inactive items receive no continuous material loops; selected cell owns T2. Preview model can animate and use a ViewportFrame. Rarity animation only if hierarchy budget allows.
- Taskbar: small selection change + short contact SFX, no motion that changes click target position.

## AvatarHero modes

**A. Appearance fidelity:** clone `player.Character` when available, stripping gameplay scripts from the display clone, or fetch an appropriate `HumanoidDescription` and create a rig using Roblox's supported avatar APIs. This is the closest practical geometry match and preserves user clothing/accessories. Don't claim conversion into one lossless EditableMesh.

**B. Stylized proxy:** generate extra mesh shells for body volumes/voxel accessories; attach at named body sockets. This shell is independent of the original rig, so hide it at lower LOD and preserve the real avatar underneath.

**C. Stylized aura:** move particles, ribbons, frame-like emitters, geometry auras and small UV-textured meshes with the avatar; use EditableImage only when actual surface masking/texture dynamics add value. Stop off-screen work.

The avatar has one aura focus and one audio cue at a time. Do not decorate every limb continuously.

## T12–T16 proposed escalation and falsifiable tests

- T12 `CoupledFace`: compare image caustic field with and without normal-gradient coupling; require visually obvious difference at 32 px while preserving legibility.
- T13 `MaterialMemory`: advect or store a low-resolution field after interaction; bound memory history and ensure a settled frame returns to calm.
- T14 `HierarchyCompiler`: choose effects by constrained optimization under latency, salience and motion budgets; validate predicted vs captured focus.
- T15 `RenderBakeOptimizer`: search mesh LOD × texture resolution × effect cadence on each device tier, keep a Pareto set of quality/performance solutions.
- T16 `AvatarHeroSynthesis`: rig-conditioned aura/surface overlays with per-socket budget, multi-character degradation and style-safe art direction.

These are research labels, not automatically proven innovations. Every escalation must beat the previous baseline on a measured axis and preserve non-negotiable constraints.

## Research and algorithm families to explore next

XPBD shape matching; projective dynamics; moving least squares deformation; isogeometric splines; lattice deformations; reduced-order simulation; signed-distance morphology; jump flooding; multichannel distance fields; fast marching and eikonal travel; reaction-diffusion; semi-Lagrangian advection; vorticity confinement; divergence-free flow; parallax occlusion; bent normals; screen-space curvature; wavelet noise; sparse Gabor noise; spectral synthesis; stratified blue noise; morphological antialiasing; tone mapping; OKLab palette interpolation; light transport approximations; temporally stable dithering; feedback control; perceptual contrast models; temporal saliency; vector quantization; constrained resource allocation; graph coloring of overlapping FX; multi-armed bandit candidate allocation; Pareto optimization.

Each needs a source, portable algorithm spec, local reference output, measured runtime target and test. Don't label a web paper as a Roblox implementation.

## Integration into `aaa-kit`

Suggested paths:

- `docs/celestialrithm/ARCHITECTURE.md`
- `docs/material-vault/palettes.json`
- `tools/render-bake/` (renderer and QC)
- `examples/celestialrithm/` (working test project)
- `lib/celestialrithm/` (MaterialField, HierarchyDirector, AtlasBridge, AvatarHero)

Wire the already-existing `lib/frontier/Atlas.luau`, `Uploader.luau`, hierarchy QA and Figma UI renderer rather than forking those subsystems. Add a skills routing entry and searchable reference in `CLAUDE.md` after review. Commit on a research branch, not `main`.
