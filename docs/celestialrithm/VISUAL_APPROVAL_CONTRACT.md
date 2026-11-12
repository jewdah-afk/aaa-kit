# Celestialrithm visual approval contract

## Read first
- `CLAUDE.md`, `README.md`, `HIERARCHY.md`, `docs/playbooks/figma-to-roblox-ui.md` in the parent aaa-kit repo remain authoritative.
- Approved *visual reference*: `media/celestialrithm/approved-material-visual-target.gif` — 12 square keycaps with rich internal motion, crisp black borders, restrained depth, no symbols or labels on faces.
- `media/celestialrithm/engineering-v1-preview.gif` is a functional baseline and **does not pass the target quality bar**. Never use it as the replacement style guide.

## Scope
Build a universal dynamic material component for Shop, Inventory, Taskbar, progression, rewards, and avatar effects. Button positions are fixed during material demos: NO cursor magnetism. The fully squared silhouette and icon/label legibility survive all effects.

## Acceptance gates
1. Material: a visibly distinct simulated subsurface phenomenon, not a single linear gradient or border-only glow.
2. Geometry: static ink silhouette with optional stepped extrusion underneath; underlying simulated mesh may deform but cannot warp critical text/icons.
3. Palette: two recognizably distinct tones + directional highlights + controlled low-energy region; no clipping into the ink.
4. Timeline: 60 unique computed frames each second for final MP4; video metadata MUST be checked. This does **not** imply Studio 60 FPS.
5. Hierarchy: annotate one attention owner, protected areas, bright-pixel budget and worst-case readability. Run `tools/hierarchy/hierarchy.py` once installed into full repo.
6. System: one shared EditableImage atlas page/update priority where possible, performance degradations by tier, deterministic material state.
7. QA: keep output frames, source, seed, test metrics, screenshot and failure notes. Reject if result looks weaker than target even if code tests pass.
8. Roblox: Lune + Selene compile, Studio rendering, MicroProfiler on representative phone; never mark these as passing based on offline renders.
9. License: review external voxel-pack rights before shipping copied assets/code. Its meshing *ideas* can be reimplemented without bundling third-party assets.
10. Human gate: don't replace existing Studio UI with a renderer unless owner approves the matching captured state.

## Next implementation backlog
- Reactivated material viewer: 12 target material families at close-up with stable square faces and baked material masks.
- Real Three.js/Blender UV bake adapter for imported GLB and generated voxel geometry; measure atlas edge bleed and seam quality.
- Reactive-material sampler: pressure -> normal -> caustics -> mask -> palette -> EI atlas upload.
- Shop & inventory hierarchy capture with original art overlaid, identify primary focus regions *before* increasing effect intensity.
- Avatar heroized effect sockets from HumanoidDescription/character clone; never claim arbitrary avatar is converted to a single exact EditableMesh.
- Run measurable optimization: compare per-millisecond quality cost, save winners and rejection reasons.

## Commit workflow
Create a dedicated branch, add `docs/algorithm-vault`, `docs/celestialrithm`, `lib/celestialrithm`, `tools/algorithm_vault`, `tools/celestialrithm`, `examples/celestialrithm`, `media/celestialrithm`; avoid replacing existing kit files. Run `python tools/celestialrithm/verify_integration.py` and then `bash tools/check_all.sh`. Review assets and licenses before PR merge.
