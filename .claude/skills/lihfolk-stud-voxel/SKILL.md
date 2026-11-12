---
name: lihfolk-stud-voxel
description: LihFolk Stud Voxel Pack. Build stud/LEGO-style voxel models for Roblox in headless Blender - cute critters and pets (box rig with bones + clips exported to Luau) and bosses, mobs, machines, objects and vehicles (brick pipeline). Ships 25 examples that rebuild exactly (7 chibi critters; 12 animal bosses incl. rhino, dragon, griffin, hydra, kraken, T-rex, spider, angler, tortoise; 5 non-animal enemies: war mech, living armor, lich, scarecrow, mimic chest; a train), each boss with its concept sheet. Use for any stud, voxel, blocky or LEGO-style animal, creature, pet, mob, boss or vehicle, "make a duck / fox / rhino / train", "like the rhino", or matching a voxel reference image, even if Blender or Roblox is not named.
---

# LihFolk Stud Voxel Pack

Made by LihFolk (LihFolk Studios). Part of the LihFolk pack.

Always copy the closest example and edit it. Every model uses the **default Roblox square stud as a texture** (`assets/roblox_square_studs.png`); never round or modelled studs.

| Method | For | Examples | Run |
|---|---|---|---|
| Box rig | critters, pets, small animated mobs | examples/*.py (duck, arctic_fox, red_panda, penguin, owl, axolotl, bunny) | `powershell -File scripts/run.ps1 <file.py> [render\|all\|export\|video]` |
| Brick pipeline | bosses, big mobs, vehicles, reference matches | examples/brick/*_brick.py | `powershell -File scripts/run_brick.ps1 <file.py> [views]` |

### Catalogue (copy the closest)
| Example | Copy it for | Notes |
|---|---|---|
| duck / penguin / owl | biped birds | owl: round eyes = 2 crossed boxes per layer |
| arctic_fox / red_panda / bunny | quadruped critters | bunny sits upright, big pom tail |
| axolotl | low crawler, gill fringes | each gill its own bone |
| war_rhino | heavy quadruped boss | reference for eyes, hide folds, hooves |
| frost_mammoth | huge furry boss, tusks | |
| swamp_croc | long low reptile, jaws and teeth | |
| scorpion_king / venom_widow | arthropods: jointed legs, pincers, fangs | widow: head pushed forward of the abdomen |
| tyrant_rex | biped boss, big head, stripes | chevron stripe bands, few big fangs |
| ember_dragon | winged boss, ~540k bricks | wings = finger bones + scalloped glow band |
| storm_griffin | winged hybrid | wings = 3 shingled rows of separate feather blocks |
| bone_hydra | multi-neck boss | necks fanned wide from the shoulders |
| kraken | tentacle boss in water | tentacles = tapered curves, water ring |
| abyssal_angler | floating fish boss | no `GLOW: strong`; point lights only |
| volcano_tortoise | shell/terrain boss, smoke | shell = one volcanic mound |
| arcane_train | vehicles | primitives on the grid |
| war_mech | robots, machines with limbs | reverse-joint legs, gatling, claw, rivets |
| living_armor | armoured humanoid knight | rounded plates, cape, held sword, ghost-fire |
| lich_king | floating robed caster | robe tatters into flames, staff, orb |
| scarecrow_king | lanky humanoid, cloth + straw | coat strips, glowing carved head, scythe |
| mimic_chest | object-creature on legs | open lid jaw, teeth, coins kept by ground contact |

Every brick example has its concept in examples/concepts/<Name>_concept.jpg and its result + comparison in examples/previews/<Name>_sheet.png / `_vs_concept.png`. Box-rig examples have `<Name>_sheet.png` + `<Name>_walk.gif`. `examples/concepts/style_refs/roblox_square_stud_ref.png` is the default Roblox square stud to match. `WarRhino_user_ref.png` is an extra hand-picked rhino reference.

Outputs: box rig -> `out/<Name>/` (sheet.png, loop.gif, `<Name>Data.luau`, `<Name>Clips.luau`); brick -> `out_<file>/` (sheet.png, renders). Approved looks: `examples/previews/`. Needs Blender 4.2+ (newest in `C:\Program Files\Blender Foundation`, or `$env:BLENDER_EXE`; headless only) and `py` with Pillow + numpy. When copying a brick example elsewhere, point `STUD_PNG` at `assets/roblox_square_studs.png`.

## When to use

- Any stud, voxel, blocky or LEGO-style model for Roblox: critters and pets, mobs, bosses, machines, vehicles, weapons
- Buildings, props, foliage and terrain modules in the same stud look (shops, towers, gates, trees, cliffs, waterfalls, walls)
- Matching a voxel reference image or concept sheet 1:1

**Not for:** runtime-generated geometry (`editable-mesh`), smooth sculpted or realistic models, or map layout (`procedural-world`).

## Method
1. Note what it is, 2-4 signature traits, clips (default Idle, Walk, an action, an emote).
2. A user reference image is the spec: match its silhouette, markings, colours, glow. Otherwise sample 2-3 images online first.
3. New enemy/boss: make a concept sheet in ChatGPT (browser): "Generate an image: a character concept/turnaround sheet for <creature> for a Roblox game. Style: chunky stud voxel / LEGO-brick look, blocky stepped boxes with studs, bold black silhouette outline, flat cel colours. NOT chibi, NOT cute, NOT a pet: a real, menacing boss with realistic anatomy, aggressive stance. <traits, palette>. Front, side, back, 3/4 views on light grey plus a face close-up." Save it as `concept_<name>.jpg`.
4. Run, Read the sheet, list defects, patch (Python edits with `encoding='utf8'`), repeat. Compare to the reference side by side, full views and face/feet close-ups.
5. Send the sheet (+ loop GIF) with SendUserFile. No MP4s or Studio install unless asked.

## Box rig (duck, fox)
- Units metres, Z up, front -Y, left +X; `STUDS` = studs per metre (5 for critters).
- `K.span(y0, y1, x0, x1, z0, z1, key, bone)` (**y, x, z order**), `K.sym` mirrors (`'%'` = sided bone), `K.limb`, `K.spike`, `K.box`.
- `HEAD = dict(scale, pivot, bones)` scales the head around the neck: 1.3 (duck) / 1.35 (fox) = the cute look.
- Clips: `fn(frame) -> {bone: (rx, ry, rz), 'root_loc': ...}`, 30 fps, per joint, rx+ = forward/down; loops via `sin(TAU*f/L)`.
- `PREVIEW = dict(target, ortho, pitch, shots, loop, player=0)` (`player=9` adds a scale dummy).
- Look: few big stepped boxes; one hue in 4 tones with fixed jobs (light tops, main ~70%, side, dark underside); small saturated accents; eyes = dark block + iris + 2 white shines, 0.01-0.03 proud; blush; oversized traits (duck tuft + bill, fox big curled tail + wide short ears); pale creatures need dark markings.
- Studs: square tile, Non-Color, **colour x (2 x texture)** (overlay can't darken white). Like the train, ONE continuous model-wide grid of exact 1x1 studs, so studs carry straight across neighbouring boxes (UV = world coords x STUDS). Tilted boxes can't share it: they get their own whole, centred 1x1 studs. Never restart the grid per box (studs then misalign between boxes) and never stretch studs to fit.
- Z-fighting: `box()` grows each later box 0.2 mm + 0.06 mm per box (render only), so shared face planes don't flicker.
- Animation: waddle = root roll ±9 + yaw ±5, legs ±26 alternating, tail/wings lag. Trot = diagonal pairs ±28, tail chain lag. Actions = anticipation, fast peak, decaying settle. Walks stay in place.
- Roblox: `ModelBuild(require(Data), CFrame, name)` builds studded Parts + Motor6Ds; `ModelAnimator.new(model, Data, Clips):Play("Walk", true, .2)` + `:Step(dt)`; add a black outline `Highlight`.

## Brick pipeline (rhino, train)
One numpy script in Blender: occupancy/colour grids -> exposed faces -> stud texture -> EEVEE.
- Grid: 1 voxel = 1 unit (2.5 studs), front -z. Voxel centres sit at `lo + .5 + i`, so every `box()` range must hold whole centres (an off-by-half range drops a layer). Later `put()` wins: paint eyes after the head.
- Creatures: sculpt anatomy as blended ellipsoids (`sd_ell` + `smin`), e.g. rhino = barrel, shoulder hump, round rump, belly sag, thick neck, leg muscles. Hide = big shields split by deep carved folds, rear edges swelling over the fold. Head = sloped profile table with a rounded section, mouth line, muzzle plate, nostrils, ears.
- Eyes: recessed and flush (nothing sticking out), dark socket, 3-row slit with the outer corner high, angry brow stepping down to the horn. Glowing eyes are ONE flat glow colour (no hot centre, no rim colour, no glint, no pupil inside the glow). Strong glow = point light per eye in that colour + `# GLOW: strong`.
- Feet: 3 toes per hoof with 1-voxel black gaps, darker than the plain leg columns.
- Vehicles: primitives on the grid (cylinders, discs, domes); glow pieces in their own colours (train: rune disc, domes, lanterns).
- Seams: darken the lower part where two parts meet on the surface only. Snap all solid bricks to a palette of 16 or fewer colours.
- Studs: square tile, Non-Color, **OVERLAY**, UV = brick coords / 16 (one stud per 2x2 bricks). Glow objects untextured.
- Render: EEVEE, Standard view, frontal key sun + side fills + back light. `post_glow.py` = one silhouette outline + glow (`GLOW_STRONG=1` for big eye halos). Check 4 ortho silhouettes.
- Brick models are always rigged (see Rig below).
- Glowing eyes = ONE flat glow colour: no hot/white centre, rim colour, glint or pupil inside the glow.
- Held weapons (staff, scythe, sword): build the fist AROUND a straight shaft (shaft through the fist centre, fingers wrapping the front, shaft visible above and below), the arm visibly reaching shoulder -> fist, and the weapon >= 2 bricks clear of body, sleeves, cloth and hat everywhere except the fist. Hold it out at arm's length, angled, not glued to the side. Test it: weapon cells must not overlap any non-hand cell. Pose with intent: bent knees, one foot forward, slight lean/twist, free hand doing something.
- Glow budget: `GLOW: strong` halos every glow brick and tints nearby surfaces. Glow only eyes, cores, craters, lures; make cracks, seams, lava rivers, drips and markings SOLID bright bricks (dragon, tortoise, widow hourglass). If a whole surface goes orange/cyan, drop `GLOW: strong` and keep point lights (angler).
- Big shapes first: compare silhouettes to the concept before details. Recurring misses: wings as flat triangles (build separate feather/finger blocks), necks too short so heads clump, bodies too slim (bulk legs/chest 1.3x), beaks too long from the front, shells/cones as thin spires.
- Many models: one background agent per model with a full brief (copy which example, concept path, traits list, rules, run command, build `side_by_side.png`, report score + gaps); review each side-by-side and send back targeted fixes. Gains stop after ~10 rounds. A ready brief template is `BRIEF.md` in this folder.
- Every model drops bricks not 26-connected to the body before meshing (smoke / ground-resting coins excepted). The Read tool caches images by path: copy a re-rendered image to a new name before reviewing it.
- Run `run_brick.ps1 <file.py>` with no view argument to render all views. Keep helper scripts in the model's own folder (a shared scratchpad gets overwritten by parallel agents).

## Rig (always, brick pipeline)
Every brick model ends with `scripts/brick_rig.py` (examples: war_rhino = quadruped + jaw + tail, kraken = 8 tentacles x 4, living_armor = biped + sword + cape).
- Declare `RIG = [(bone, parent, head_xyz, tail_xyz), ...]` in brick coords, root first (`parent None`). A bone named `root` gets no bricks unless an override gives it some (kraken water).
- Bricks go to the nearest bone segment; fix the misses with `overrides = [(mask, bone), ...]` (applied in order, last wins): weapon -> hand, eyes/ears/horns -> head, legs by column, loincloth -> hips. `brick_rig.limb(X, Y, Z, mask, chain)` splits one mask (a tentacle, a cape) between its own chain only.
- Call last, after `render_all()`: `brick_rig.export(ID, OUT, lo, kind, col, RIG, overrides, glow=GLOW, pose={bone: (rx, ry, rz)}, render='render' in argv)` (it resets the Blender session).
- Out (in `out_<file>/`): `<ID>_rig.glb` (skinned, 1 brick = 2.5 studs, Y-up, rigid 1.0 weights, every child copies 1 brick of its parent so posed joints have no holes), `<ID>_rig.json` (bones, parents, pivots in studs, tris per piece), `stud_mul.png`, and `render/<ID>_rigrest.png` + `<ID>_posed.png` from a fresh re-import. Look for `RIG_OK`.
- 20k rule: Roblox allows ~20k triangles per mesh. Faces are greedy-merged (same colour, coplanar) and each bone is its own mesh (+ one per glow colour), split by region until every piece is <= 20,000 tris.
- Colours = vertex colours (COLOR_0) x base texture `stud_mul.png` (2 x stud overlay, world UVs); glow pieces = emissive, untextured (set them to Neon in Studio).
- Roblox: Avatar/3D Importer -> the `.glb`, Rig type: keep bones (custom rig), scale unit = Stud; it lands as one Model with a MeshPart per piece and Bones. Add `AnimationController` + `Animator`, animate in the Animation Editor. Front ends up as LookVector (the importer turns GLBs 180 about Y).

## Studio route without Blender (BrickBoxes)
For chunky pets, mobs and props on a coarse grid, build the grid in Luau and skip Blender and the 3D Importer. Research and measurements: [Stud Voxel in Studio](../../../docs/research/90-stud-voxel-in-studio.md).
- `references/roblox/BrickBoxes.luau` (pure, lune-tested): `BrickBoxes.new(nx, ny, nz)`, `grid:set`, `grid:fill` (box or any test function), `grid:ellipsoid`; each brick stores a palette index and a bone index. Later writes win.
- `grid:boxes()` merges the bricks into as few boxes as possible: every exposed brick is covered once by a box of its own colour and bone, hidden bricks are free filler. Measured on shipped bosses: war_rhino 2,009 boxes, ember_dragon 41,758, so keep fine-detail bosses on the GLB route.
- `grid:lint(groundOk)` returns `bricks`, `exposed`, `colours`, `floating`. Fail the model when `floating > 0` or `colours > 16`, before opening Studio.
- `references/roblox/BrickBuild.luau`: `BrickBuild(grid, { Palette, Glow, Bones, StudsPerBrick, MaterialVariant }, CFrame, name)` builds studded Parts on the same Motor6D rig as `ModelBuild`, so `ModelAnimator` plays clips on it. Compile-checked only: not yet run in Studio.
- Test: `lune run references/roblox/BrickBoxes.test.luau`.

## Rejected (don't repeat)
Round or modelled studs · overlay on white models · stacked-box or smooth-mesh bosses · hunched golem proportions · chibi enemies · small bosses · covered or protruding eyes · per-part strokes · heavy bloom on normal models · square armour tiles on creatures.

## Buildings (shops, huts, towers, gates)

Copy the closest of `examples/brick/shop_brick.py` (house/shop), `tower_brick.py` (tall tower), `gate_brick.py` (castle gate/walls); previews `examples/previews/Shop_sheet.png`, `Watchtower_sheet.png`, `CastleGate_sheet.png`. They use `scripts/bld.py`:
- `Grid(nx, ny, nz, R=3)`: big shapes in UNITS (2.5 studs) with `box(x0,x1,y0,y1,z0,z1, colour, pat=...)` / `cut(...)`; x and z are centred, front = -z.
- `pat`: `stone` (running bond + seams), `plank` (row seams), `log`, `shingle`; carved at FINE resolution (R=3 bricks per unit = 0.83 studs, one stud per 2x2 fine bricks).
- Details in fine bricks (fine = unit x R): `fbox` / `fcut`, `window(x0,x1,y0,y1, zf, frame)` = recessed glowing pane + frame + mullion + sill. Glow = `k=2/3` with `GLOW` colours.
- Run: `blender -b --factory-startup --python <file> -- render` -> `out_<ID>/<ID>_rig.glb` (1 root bone), `render/<ID>_tex.png` (textured preview).
- Unit-only buildings look far too low-detail (user: "way too low detail"): always put the trims, roof rows, door planks, windows, props in fine bricks. Roofs = a shell 4 fine bricks thick (a solid wedge hides the gable).
- **Scale first:** characters are ~5-6 studs tall. Doors >= 8 studs tall x 5 wide, ceilings >= 12, walkways >= 6 wide. Measure in studs, not voxels.
- **Read as architecture:** 3 bands top to bottom: roof (overhang 1-2 voxels past the walls, darkest or most saturated tone), walls (main tone, one trim band at floor and roof line), base/plinth (dark, 1-2 voxels proud). One accent colour for door, sign and window frames.
- **Openings:** windows = dark recessed panel 1 voxel deep + light frame + optional warm GLOW pane; doors = recessed 1-2 voxels with a frame. Never just paint a dark square on the wall.
- **Roofs:** stepped (1 voxel in per 1 up) or gabled with a ridge cap; add a chimney, sign or banner-free ornament for silhouette. No flat box roofs unless it's a fortress with crenels.
- **Detail rhythm:** repeat posts/pillars/rivets at even spacing; corners get a pillar or quoin column. Big flat walls need a texture job (plank rows, brick courses as alternating tone rows by job, not random).
- **Collision:** export a separate set of plain boxes (floor, walls, roof) for CanCollide; the visual mesh stays CanCollide off. Walkable floors must be flat.
- **Modular:** big builds = pieces on a fixed grid (e.g. 4x4-stud wall panels, corner, roof, door piece) so they snap together.
- **Animation (optional):** moving bits (sign swing, windmill, door, smoke) get their own bone, same as creatures.
- **Props + foliage:** `examples/brick/props_brick.py` (run `-- render <Prop>`: Oak Pine Bush Rocks Well Cart Lamp Fence Gym CrimsonBlade VoidCrystal ThornBow Sniper Pistol Rifle (the four ranged weapons were TRACED 1:1 from a private reference picture, which is not in this public copy, so those four props need your own picture; hand-drawn profiles were "pretty bad and not very close to pic");
- **Matching a reference picture of a flat-ish object (weapons, signs, icons): TRACE it, don't redraw it.** Save the picture to examples/brick/refs/ (create it), then per object `py scripts/trace_ref.py <img> x0 y0 x1 y1 <cell px> refs/<Name>.npz [colours]` (transparent or white background; keeps only the biggest connected piece so neighbours in the crop drop out; neutral tones reduced to a palette, accents (gold/orange/blue) get their own palette, lights flagged on the raw colour) and build with `g.trace(npz, depth, stroke=1)` (1 cell = 1 fine brick, bevelled edge cells, glow -> its own kind, stroke = 1-brick black outline round the silhouette and holes). Cell size ~ half the picture's own voxel size. See `traced()` in props_brick.py. blades preview `examples/previews/Blades_sheet.png` (built from user references: sharp angular segmented silhouettes = piecewise width profile with shoulders, diagonal cut-ins and barbs; chevron facet colouring; sawtooth only on tip/lower edges; open slots cut through; a PROPS entry may add R and its own GLOW dict); preview `examples/previews/Gym_sheet.png`; preview `examples/previews/Props_sheet.png`). Organic shapes via `g.blob(...)` (lumpy ellipsoid, never a smooth sphere) and `g.fshape(fn, colour_fn)` (any mask in fine bricks). Trees = tapered trunk with root flare + bark rows, 4-6 overlapping leaf clumps shaded underside dark -> top light (`leaf_col`), NO separate light tufts stuck on top (read as weird leaves); pines = notched cone tiers. Ground props sit on a mossy base disc with grass tufts.
- **Terrain:** `examples/brick/terrain_brick.py` (`-- render <Piece>`: Cliff Waterfall Wall WallCorner; preview `examples/previews/Terrain_sheet.png`). Modules are 60 fine bricks (50 studs) wide so they line up. Cliff = terraced lumpy rock face with strata bands by height + cracks, grass cap that drips over the edge, boulders at the foot. Waterfall = notched cliff, water sheet in 3-tone vertical lanes bulging out as it falls, foam lip, stepped stone pool with splash + ripple rings. Walls = running-bond stone with ONE tone per block (a sine pattern made diagonal stripes), crenels, stepped buttresses, slits, moss on base blocks; corner = round turret + 2 arms.
- **No blocky lights or token pieces** (user rule): never a lone glowing cube/rectangle as a gem, beacon, sign icon, brazier or torch, and no plain cube-on-a-stick finials. Lights sit INSIDE a shaped holder (lantern cage with bars + cap, window frame + mullion, slit with lintel); fire = stepped `flame()` (wide base, narrow tip, small glow core) on a bowl/cup; emblems are drawn shapes (coin ring, crossed swords, stepped spire).
A whole area assembled from these pieces, with layout rules and a downloadable `.glb`: the [stud map guide](../../../docs/playbooks/map-guide.md).
Checklist: door fits a player, nothing floats, roof overhang reads from the front, silhouette reads at 100 studs.

## Hierarchy rules it obeys

- [HIERARCHY.md](../../../HIERARCHY.md) and the [world hierarchy playbook](../../../docs/playbooks/world-hierarchy.md): props, foliage and terrain are world tiers 4 to 6 (muted, no outline, no glow); bosses and mobs are tier 2 (clear silhouette, their own light).
- One silhouette outline per model, no per-part strokes. Glow only on eyes, cores and lights you want to bloom (the glow budget above).
- Palette of 16 colours or fewer, one hue in 4 tones with fixed jobs, so models stay readable at phone size and 100 studs away.

## Engine notes

**Roblox.**

- Box-rig critters: `ModelBuild(require(Data), CFrame, name)` builds studded Parts + Motor6Ds; `ModelAnimator` plays the exported clips (`references/roblox/`).
- Brick models: import the `.glb` with the 3D Importer (keep bones, unit = Stud). Each bone is its own MeshPart under the ~20k-triangle mesh cap; glow pieces are untextured, set them to Neon.
- Ink outline = one `Highlight` per model; Roblox draws at most 31 at once.
- Collision: use the separate plain boxes, keep the visual mesh CanCollide off.

**Blender.** Headless only (4.2+), driven by `scripts/run.ps1` and `scripts/run_brick.ps1`, or `blender -b --factory-startup --python <file> -- render` on macOS/Linux.

## Example

`examples/duck.py` is the box-rig reference (sheet, walk loop, `DuckData.luau` + `DuckClips.luau`; a built sample is in `examples/output_sample/`). `examples/brick/war_rhino_brick.py` is the brick-pipeline boss reference with its concept `examples/concepts/WarRhino_concept.jpg` and result `examples/previews/WarRhino_sheet.png`. `examples/brick/props_brick.py` builds the props (Oak, Pine, Bush, Rocks, Well, Cart, Lamp, Fence…), and the rigged result ships as `examples/brick/out_Oak/Oak_rig.glb`.

```sh
blender -b --factory-startup --python examples/brick/props_brick.py -- render Oak
# prints RIG_OK and writes examples/brick/out_Oak/render/Oak_tex.png
```

## Make it insane

1. **Living props:** every tree, lamp and sign gets one idle bone (sway, flicker, swing) from the same rig export, so a whole stud map breathes for the cost of a few Motor6Ds.
2. **Boss phase swaps:** build a second brick grid per boss phase (cracked armour, exposed glowing core) and swap meshes per bone mid-fight, so the silhouette itself shows the phase change.
3. **Reference-to-brick in one pass:** trace a concept's front and side views and intersect them into a visual hull as the starting brick grid, then sculpt from there.

## Self-check

- [ ] Copied the closest example; nothing on the Rejected list.
- [ ] Silhouette matches the reference in all four ortho views before any detail.
- [ ] Square Roblox stud texture on one continuous grid; no round or stretched studs.
- [ ] 16 colours or fewer; glow only where intended; one outline.
- [ ] Nothing floats (26-connected); doors fit a player; buildings read as roof, walls and base.
- [ ] Rig exported (`RIG_OK`) and every piece is at or under 20,000 triangles.
