# Brief: stud-voxel enemy from a concept sheet (static, brick pipeline)

Goal: a model that matches `<Folder>\concept_sheet.jpg` 1:1 with zero visible flaws (it becomes a reference example in the skill).

Setup
- Read `<skill>\SKILL.md` (brick pipeline + Rejected list) and study the closest examples in `<skill>\examples\brick\` with their sheets in `examples\previews\` (`*_sheet.png`, `*_vs_concept.png`).
- Copy `<skill>\examples\brick\war_rhino_brick.py` to `<Folder>\<name>_brick.py` and rewrite the model part. Set the ID. Set `STUD_PNG = r'<skill>\assets\roblox_square_studs.png'` (absolute path; `<skill>` = this skill's folder).
- Build: `powershell -File "<skill>\scripts\run_brick.ps1" <file.py>` (no view argument = all views) -> `out_<file>\sheet.png`.
- After every round write `<Folder>\side_by_side.png` (concept views left, matching renders right, same height) with Pillow; keep helper scripts inside `<Folder>` (the shared scratchpad gets overwritten by other agents).
- The Read tool caches images by path: copy an image to a new filename before re-reading it.

Rules
- HUGE, menacing boss; NOT chibi; heroic/real proportions from the concept (no hunched golem / box-torso brute look).
- Sculpt forms with blended shapes (sd_ell + smin, cylinders, wedges), then stepped bricks. Chunky readable forms, big plates, clear silhouette from front, side, back and 3/4.
- Eyes recessed and flush, never covered, never protruding.
- Glow only eyes, cores, runes, flames you actually want blooming. Cracks, seams, trims and markings are SOLID bright bricks. Use `# GLOW: strong` only if it doesn't tint the surface; else `# GLOW: subtle`.
- Palette <= 16 colours, surface-only seams, one black silhouette outline, the square stud texture (pipeline handles it).
- Drop any brick not 26-connected to the main body before meshing (flood fill). Nothing floats.
- Static model, no rig, no animation. Headless Blender only. Don't edit the stud-voxel-creatures folder.

Process
1. Read the concept; write a list of proportions (measure ratios in the front and side views) and 5-8 signature traits.
2. Build, Read sheet + side_by_side, list every difference (silhouette/proportions first, then features, then details), fix, rerun. Up to 8 rounds.
3. Final audit of every view at full size: floating bricks, holes, clipping, z-fighting, odd colour patches, glow smudges.
4. Report: .py path, sheet path, side_by_side path, honest score /10, remaining gaps (short).
