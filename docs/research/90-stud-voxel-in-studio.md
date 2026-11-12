# Stud Voxel in Studio: how to make the LihFolk pack better where it runs

The [Stud Voxel skill](../../.claude/skills/lihfolk-stud-voxel/SKILL.md) sculpts in headless
Blender and judges itself on offline renders. The model only matters once it stands in a
Roblox place. This chapter asks what would improve the result **in Studio**, which route gets
it there with the fewest manual steps, and how each step can be tested headlessly with lune.

Researched **2026-11-12**. Official facts come from the kit's own verified chapters
([21](21-roblox-editablemesh-api.md), [41](41-editablemesh-technique-cookbook.md)).
DevForum figures were read through search summaries and are marked **[secondary]**: re-measure
before budgeting on them. Voxel-art advice came from low-authority pages and is marked
**[weak]**. Nothing here was run in Studio or on a phone.

## Short version

- **The skill's weakest link is the hand-off, not the sculpt.** Brick models leave Blender as
  a GLB and need the 3D Importer by hand. Nothing checks the model after that step.
- **A Blender-free route now exists and is tested.** `BrickBoxes.luau` holds a brick grid in
  pure Luau and merges it into boxes; `BrickBuild.luau` turns those into studded Parts on the
  same Motor6D rig the critters use. A 118,656-brick test grid merged to **160 Parts in
  15 ms** under lune.
- **The hard rules can be linted without rendering.** Floating bricks, palette size and part
  count are now checked in Luau, so a model can fail fast before anyone opens Studio.
- **Only the pack's own 17 concept sheets count as references.** All 17 are built; new models need a new concept sheet first.

## What the skill does today, and where it loses

| Step | Today | Loss |
|---|---|---|
| Sculpt | numpy grid in Blender, one script per model | ~200 lines of grid, mesh and render code copied into every example |
| Judge | read the render sheet; `compare.py` gives one silhouette IoU | no score in the loop for palette, connectivity, part or triangle count |
| Export | box rig: Luau data. Brick: skinned GLB | brick models need the importer by hand; box and brick models use different runtimes |
| Run | `ModelBuild` + `ModelAnimator` (box rig only) | brick models get no animator from the skill; nothing is tested after import |
| Runners | PowerShell only | no Linux or macOS runner |

## Facts that set the limits

| Fact | Source | What it means for the pack |
|---|---|---|
| `EditableMesh` caps at 60,000 vertices and 20,000 triangles | official reference, via ch. 21 | a runtime greedy mesh must be chunked per bone, as the GLB export already is |
| `EditableMesh` fails in published games until the owner is ID verified and flips a dashboard toggle | ch. 21 | not a safe default for a pack other people install |
| Runtime meshes cannot be saved as permanent mesh assets | ch. 21 | an `EditableMesh` model must be rebuilt every session |
| `EditableMesh` supports bones, at most four per vertex | DevForum beta post **[secondary]** | rigid one-bone-per-brick skinning fits |
| Clients report a budget of roughly 8 large editable meshes | DevForum **[secondary]** | a 20-piece boss could exhaust it alone |
| The importer rejects meshes over about 20,000 triangles; 10,000 is the older MeshPart figure | DevForum, vendor blogs **[secondary]**, conflicting | keep the 20k split; aim under 10k per piece for phones |
| Parts that share geometry, material and texture are drawn together | Roblox rendering posts, 2017–2018 **[secondary]** | many plain studded boxes are cheap to draw; instance count is the cost to watch |
| The Surface tool was removed in 2020; `TopSurface = Studs` is still scriptable | DevForum **[secondary]** | whether engine studs still look right must be checked in Studio; a `MaterialVariant` with the square stud tile is the fallback |
| Silhouette first, small grids read better, three tones by face direction, palette of 16–32 | agent-skill pages **[weak]** | agrees with the skill's existing rules; adds nothing new |

## Three routes into Studio

| | A. GLB + importer (current) | B. Merged studded Parts (new) | C. Runtime `EditableMesh` |
|---|---|---|---|
| Needs Blender | yes | no | no |
| Manual steps | import, set Neon, add Animator | none: `require` and call | none |
| Survives publish as-is | yes (mesh assets) | yes (plain Parts) | no: rebuilt each session, gated by the toggle |
| Draw cost | one mesh per bone piece | one Part per box; batches | one mesh per chunk |
| Animates with | Roblox Animator, Bones | `ModelAnimator`, Motor6D | Bones (beta) |
| Stud look | baked texture x vertex colour | engine studs or a `MaterialVariant` | UVs + texture |
| Headless test | Blender re-import only | lune, full coverage of the pure part | none (needs the engine) |
| Best for | finished hero bosses | mobs, pets, props, fast iteration, anything built by an agent | destructible or morphing models |

**Recommendation: make B the default for iteration and for small models, keep A for the
final export of large bosses.** B is the only route whose correctness can be proven without
Studio, and it removes every manual step.

## Measured

`BrickBoxes.boxes()` under lune 0.10.5, single bone:

| Model | Bricks | Exposed bricks | Boxes (Parts) | Merge time |
|---|---|---|---|---|
| Stepped ball, 32³ grid | 8,280 | 1,560 | 90 | 2 ms |
| Stepped ball, 64³ grid | 81,456 | 7,440 | 423 | 45 ms |
| Stepped ball, 100³ grid | 333,584 | 19,216 | 1,043 | 386 ms |
| Test mob grid (8 colours, 4-brick voxels) | 118,656 | 19,558 | 160 | 15 ms |

The test mob is the friendly case: chunky 4-brick voxels and few colours. A finely detailed
boss with tone bands and many bones will need more boxes; that has not been measured.

## Upgrade plan, ranked

| # | Upgrade | Why | Headless test | State |
|---|---|---|---|---|
| 1 | `BrickBoxes.luau`: grid, sculpt helpers, greedy box merge | removes Blender and the importer from the loop | lune, 13 checks | **done** |
| 2 | `BrickBoxes.lint`: floating bricks, colours, exposed count | the Rejected list becomes machine-checked | lune | **done** |
| 3 | `BrickBuild.luau`: Parts + Motor6D rig from a grid | same runtime for brick and box models | compile only | written, **not run in Studio** |
| 4 | Export the Python grid to a `BrickBoxes` data module | the 25 shipped models gain the Parts route without re-sculpting | lune: load, lint, count boxes | next |
| 5 | Stud check in Studio: engine studs vs a `MaterialVariant` tile, one stud per 2x2 bricks | the stud look is the pack's identity and is unverified on this route | Studio only | open |
| 6 | Part budget per tier in data: pet, mob, boss | keeps phones safe; lint fails over budget | lune | next |
| 7 | Score in the loop: silhouette IoU per ortho view against the concept, written to JSON | "closer to the concept" becomes a number | Python, no Blender needed for the compare | next |
| 8 | Shared Python core so a new model is only its sculpt | 9,000 lines of examples are mostly copies | Blender | drafted, not committed |
| 9 | Linux and macOS runner | agents and CI can build | shell | drafted, not committed |
| 10 | Visual hull start: intersect the concept's front and side masks into the first grid | big shapes right before any detail | lune on a synthetic pair | idea |
| 11 | Phase swap: a second grid per boss phase, swapped per bone | silhouette shows the phase | lune: both grids lint | idea |
| 12 | LOD grid: halve the resolution, re-merge | far crowds for a fraction of the Parts | lune: box count drops at least 4x | idea |

## References

The pack's references are the 17 concept sheets it ships in `examples/concepts/`, each with a
built model: AbyssalAngler, BoneHydra, EmberDragon, FrostMammoth, Kraken, LichKing,
LivingArmor, MimicChest, ScarecrowKing, ScorpionKing, StormGriffin, SwampCroc, TyrantRex,
VenomWidow, VolcanoTortoise, WarMech, WarRhino.

The AI-generated Christmas sheets on branch `codex/christmas-concept-sheets` are **not** part
of the pack and are not merged here. They are not used as references in this chapter.

**Proposed builds** (each needs its own concept sheet first): a mount with a rider seat
bone, a two-part boss that splits, a turret that tracks, a destructible crate set, a modular
dungeon wall kit, a boat with a water ring, a market stall set, a weapon rack traced from the
user's own pictures.

## Not tested

- Nothing in this chapter ran in Roblox Studio. `BrickBuild.luau` is compile-checked only.
- No phone measurements. Part and triangle budgets above are planning figures.
- The stud appearance on Parts (engine studs or a `MaterialVariant`) is unverified.
- Box counts for a multi-bone, finely detailed boss are unmeasured.

## Sources

- [EditableMesh reference](https://create.roblox.com/docs/en-us/reference/engine/classes/EditableMesh)
- [Skinning and FACS support for EditableMesh (Studio Beta)](https://devforum.roblox.com/t/studio-beta-introducing-skinning-and-facs-data-support-for-editablemesh-objects/3731147)
- [In-experience Mesh and Image APIs (Client Beta)](https://devforum.roblox.com/t/client-beta-in-experience-mesh-image-apis-now-available-in-published-experiences/3267293?page=19)
- [What's Roblox's current mesh triangle limit?](https://devforum.roblox.com/t/whats-roblox-current-mesh-triangle-limit/2414597)
- [Skinned MeshPart Studio Beta](https://devforum.roblox.com/t/skinned-meshpart-studio-beta/705528?page=2)
- [Part instancing pre-release announcement](https://devforum.roblox.com/t/part-instancing-pre-release-announcement/130333/1)
- [Rendering updates, September 2017](https://devforum.roblox.com/t/rendering-updates-september-2017/54148)
- [Changes to Part Surfaces](https://devforum.roblox.com/t/changes-to-part-surfaces/334420)
- [Deprecating Surface Tool API](https://devforum.roblox.com/t/deprecating-surface-tool-api/1222218)
- [Using voxels for simple dioramas](https://80.lv/articles/using-voxels-for-simple-dioramas)
