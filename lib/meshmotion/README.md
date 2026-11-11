# meshmotion

Animated creature meshes for Roblox: a segment hierarchy, procedural deformers, keyframe clips and a
distance-LOD scheduler, with build and pool budgets taken from the
[EditableMesh cookbook](../../docs/research/41-editablemesh-technique-cookbook.md).
Pure Luau except `Adapter.luau`, so everything except the Studio push runs headless in lune.

## Layers

| # | Module | Job |
|---|---|---|
| 1 | `Budget` | Build queue under a per-frame ms budget (`CreateMeshPartAsync` ≈ 22 ms + 0.27 ms/1k tris), and a pool of about 8 dynamic meshes with priority eviction. |
| 2 | `Store` | One immutable `MeshData` per creature (f32 rest positions, u32 tris, segment per vertex, jiggle weight, parents-first segment tree), ref-counted and shared by every instance. Rejects cycles, bad indices and anything over 60k verts / 20k tris. |
| 3 | `Rig` | Pose per segment (Y-X-Z rotation, translation, uniform scale about its pivot), world matrices solved parents-first, rigid skin into `rig.out`. No allocation per frame. |
| 4 | `Deform` | `bob`, volume-preserving `squash`, travelling `wave` with a root ramp, `twist` about each segment's posed pivot, spring `jiggle` by vertex weight. Each can be limited to named segments. |
| 5 | `Animator` | Clips (`{length, loop, tracks = {Seg = {{t, rx, ...}}}}`, smoothstep, looping wrap), and a scheduler: near < 40 studs every frame, < 100 every 2nd, < 200 every 4th, else frozen; phase-spread so a tier doesn't land on one frame; least-recently-served under a per-frame vertex budget. |
| 6 | `Creature` | Rig + clip + deformer stack + `onFrame` hooks (the surface link: put surfacebake/frontier texture animators here so texture and geometry tick and freeze together) + `present` (the adapter push). |
| 7 | `Adapter`, `tools/export_blend.py` | Roblox side (compile-checked only) and Blender export. Parts mode: one MeshPart per segment driven by `segmentCFrame`, zero vertex writes, for rigid-only motion. Editable mode: `bind` an uploaded MeshPart (keeps its UVs and texture), then `push` = one `BatchSetValues`. |

## Pipeline

1. Model in Blender with one mesh object per moving segment, parented like the skeleton (object origin = pivot). Optionally paint a `Jiggle` vertex group (0–1).
2. `blender -b creature.blend -P lib/meshmotion/tools/export_blend.py -- creature.json` converts to Roblox axes (Y up), applies modifiers, welds per segment and writes the blueprint.
3. Upload the same model as a MeshPart (FBX). At runtime: `Store.acquire(name, loader)` → `Creature.new(data, {clip, deformers, present})` → `Animator.add(sched, data.n)`, set `entry.dist` and `entry.visible` each frame, and call `creature:step(now - entry.lastTime)` for every entry `Animator.step` returns.
4. Rigid-only creatures use parts mode. Deforming creatures take a slot from `Budget.acquire(pool, ...)` and use editable mode, falling back to parts mode when they are evicted.

## Numbers (lune 0.10.5, this machine)

| Case | ms |
|---|---|
| Rigid skin, 5,120 verts | ~0.12–0.30 |
| Skin + squash + wave + jiggle, 5,120 verts | ~0.6–0.75 |
| Scheduler step, 200 creatures | ~0.07–0.10 |
| Moonfrost Narwhal export (2,772 verts, 8 segments), skin + bob + squash | 0.10 per frame |

Luau work only. The Studio-side `BatchSetValues` re-transcode cost hasn't been measured from this repo.

## Run the tests

```sh
cd lib/meshmotion/qa && lune run test_meshmotion.luau | grep -a '^@@\(CHECK\|DONE\)'
```

31 checks: store ordering, cycles, limits and sharing; rig identity, pivots, chains, scale; squash volume, wave masking, twist radius, jiggle lag and settle, determinism; clip keys, wrap and clamp; scheduler tiers, phase spread and budget fairness; build queue spread and progress; pool cap and eviction; creature hooks.

## Unverified in Studio

- `Adapter.bind` vertex matching after Roblox splits UV/normal seams (it warns with the miss count).
- Whether `BatchSetValues` on a mesh from `CreateEditableMeshAsync(meshPart.MeshContent)` shows next frame on the part made by `Adapter.show`.
