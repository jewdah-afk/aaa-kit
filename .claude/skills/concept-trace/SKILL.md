---
name: concept-trace
description: Use to make a brick model match its concept drawing by measuring and tracing instead of eyeballing - "match the concept", "trace the reference", "trace mapping", "line it up against the concept", "outline overlay", "side by side with the concept", "make it exact", "plates are in the wrong place", "trace the plates", "why doesn't it look like the concept". Outlines the concept, fits it to the model's flat view, reports overlap and line distance, traces the concept's plates into a map, and builds them as flat faceted slabs with lit tops and dark walls.
---

# concept-trace

Matching a model to its concept by eye stalls after a few rounds. This skill **measures the gap** and **traces the layout** from the drawing. Method and evidence: [research ch. 92](../../../docs/research/92-trace-and-match.md) (trace and match) and [ch. 91](../../../docs/research/91-readable-voxel-surfaces.md) (readable surfaces). The war rhino is the benchmark.

## When to use

- A brick model exists and "doesn't look like the concept", or its plates, scales or panels sit in the wrong places
- You want an overlay and numbers before and after a change, not an opinion
- A new creature needs its armour layout taken from a concept sheet's side view
- A surface reads as paint (lines on a smooth body) and should read as layered slabs

**Not for:** sculpting the model in the first place (`lihfolk-stud-voxel`), judging where the eye lands on a finished render (`hierarchy-audit`), or flat objects such as weapons and signs (trace those with `scripts/trace_ref.py` in the Stud Voxel skill).

## Method

All tools live in the Stud Voxel skill's `scripts/` folder.

1. **Measure first.** `python3 scripts/concept_match.py <model.py> <concept.jpg> x0 y0 x1 y1 <out dir>` (the crop is the concept's side view). Read `report.png`: fitted concept, the model's flat side view, and the overlay (concept orange, model blue).
2. **Read the checklist in order.** Silhouette overlap, then plate-line distance, then relief and backed edges, then value bands and small-size survival. Fix the first WARN before the ones below it: detail on a wrong silhouette is wasted.
3. **Trace the layout.** Add `--trace refs/<Name>_plates.npz` on the model whose body shape you trust. The concept's plates are its lit top faces; the map holds one plate number per brick of the side view and a height level per plate, chosen so touching plates never share a level.
4. **Build from the map.** In the model file, look each hide brick up by `(z, y)` to get its plate, then call `slabs.fit(...)`: one flat slab per plate on a fitted plane, tilt snapped to flat, 1:2 or 1:1, lifted by its level. Copy the block from the Stud Voxel skill's `war_rhino_plated_brick.py`; for a model with voronoi cells, copy its `ember_dragon_slab_brick.py`.
5. **Paint by job.** The slab's outer layer takes the lit tone (faces that look up are lighter); everything under it is the dark wall. Lift the base colour until the model reaches six or more value bands.
6. **Measure again**, and keep the pair of numbers in the notes. Then render in Blender and look: the numbers place things, the eye judges appeal.
7. **Check it in motion.** `python3 scripts/rig_anim.py <ID_rig.glb> out.mp4` plays walk, charge and idle on the exported rig in a fast preview. Thick slabs on limbs clip into the body: give them clearance.
8. **Check the first look.** Run `hierarchy-audit` on the 3/4 render with the head as the focus.

### Working marks

From the war rhino benchmark. They say where to look first; they are not validated limits.

| Measure | Mark | Shipped rhino | Traced slabs |
|---|---|---|---|
| Silhouette overlap (IoU) | ≥ 0.75 | 0.76 | 0.80 |
| Concept plate line → model | ≤ 1.0 brick | 1.78 | 0.85 |
| Relief | ≥ 20 % | 15 % | 30 % |
| Edges backed by geometry | ≥ 70 % | 60 % | 74 % |
| Featureless area | ≤ 10 % | 16 % | 3 % |
| Value bands | ≥ 6 | 5.7 | 7.0 |
| Survives at 48 px | ≥ 0.60 | 0.79 | 0.80 |

### What goes wrong

- **The fit is a stretch, not a camera solve.** Concepts are drawn in perspective and often mid-stride, so legs, head and tail will not line up. Trust the torso.
- **Line distances compare versions of one model**, not different models.
- **A free tilt ripples.** Never tilt a plate's thickness; snap the plane.
- **Slabs cost triangles** (about 10–17 % more). The exporter still splits every piece to 20,000 or fewer, but total count grows: check it for big models.
- **Dark-line tracing fails on small concept images**: the lines do not close. Lit-face tracing does.

## Hierarchy rules it obeys

- [HIERARCHY.md](../../../HIERARCHY.md): bosses are tier 2. Read order is silhouette, then slabs (value), then studs. Value carries the read when detail is lost (§11), so slabs are separated by value bands, not by hue.
- One silhouette outline per model; glow stays on eyes, cores and lava. Slab walls are dark, never glowing.
- 16 colours or fewer after the lift.

## Engine notes

**Roblox.** Nothing here changes the export route: one mesh per bone, each 20,000 triangles or fewer, vertex colours × the stud texture, glow pieces set to Neon. The slab style adds triangles, so re-read the exporter's `RIG_OK` line. Nothing in this skill has been run in Studio or on a phone.

**Blender.** Building the grid needs `bpy` (`pip install bpy`; EEVEE renders also need `libegl1`). Scoring, tracing and the slab library need only numpy and Pillow. `rig_anim.py` needs `ffmpeg`.

## Example

`examples/match_rhino.sh` traces the war rhino's plates from its concept and writes the match report; `examples/WarRhino_report.png` and `examples/WarRhino_report.json` are its output.

```sh
bash .claude/skills/concept-trace/examples/match_rhino.sh
# ok   concept plate line to model, bricks   0.85   (<= 1.0)
# MATCH_OK /tmp/rhino_match/report.png
python3 .claude/skills/lihfolk-stud-voxel/scripts/slabs.py     # SLABS_OK: the slab library's self-test
```

## Make it insane

1. **Three-view trace:** trace the concept's front and back views as well and intersect the three plate maps, so plates wrap correctly round corners instead of projecting straight through from the side.
2. **Self-correcting match:** let a search nudge the body's shape parameters until silhouette overlap stops improving, then re-trace; the model tunes itself between hand passes.
3. **Phase maps:** trace a second, damaged concept and swap plate maps mid-fight, so slabs break away in the pattern the art shows.

## Self-check

- [ ] Ran `concept_match.py` before and after; both sets of numbers are in the notes.
- [ ] Fixed the first WARN in the checklist before touching anything below it.
- [ ] Plate tops are flat and studded; every plate edge is a real brick step; no free tilts.
- [ ] Outer layer lit, walls dark; six or more value bands; 16 colours or fewer.
- [ ] Rendered in Blender and compared with the concept by eye; sent the picture.
- [ ] `RIG_OK` and every piece at or under 20,000 triangles; total triangles reported.
- [ ] Said what was not tested (Studio, phone, front and back views if only the side was traced).
