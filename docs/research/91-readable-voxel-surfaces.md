# Readable voxel surfaces: layering, value and how to measure them

Chapter [90](90-stud-voxel-in-studio.md) covered how a stud-voxel model reaches Studio. This
chapter covers what makes its **surface** read: why the shipped war rhino's armour looks
painted on while its concept looks like overlapping shields, which method fits which kind of
surface, and how to score the difference without rendering.

Researched **2026-11-13**. The craft sources found by search are thin: hobby guides, forum
tutorials and one builder blog, marked **[weak]**. The measurement sources are solid. Roblox
limits come from the kit's verified chapters. Nothing here was run in Studio or on a phone.

## Short version

- **Armour reads through overlap, not lines.** Every craft source agrees on the same three
  cues: plates that physically overlap like shingles, a hard light edge on top with a deep
  shadow under the lip, and plate sizes that vary (largest over the chest and shoulders).
- **The shipped rhino has none of the three in geometry.** Its plates are dark seam lines on
  a smooth barrel. That is measurable: see `relief` and `backed` below.
- **The grid is the right place to measure.** A flat view of the brick grid under a fixed
  measuring light gives the same numbers every run, in seconds, on any Blender version.
- **At 100 studs a boss is bigger on a phone than its own brick grid.** Distance is not what
  costs detail; small on-screen size is. The scorecard therefore also scores at 48 px tall.

## 1. How builders make surfaces read

| Surface | What carries the read | Source |
|---|---|---|
| Plate armour | staggered, overlapping plates over a built core; build the body's curve first, then layer | [MOC dragon guide](https://htbi-moc.com/blogs/guides/lego-moc-dragon-breathe-fire-into-your-builds) **[weak]** |
| Plate armour | sharp bright highlight against a dark, deep shadow; fix the light direction first | [armour shading thread](https://www.pokecommunity.com/threads/any-advice-on-shading-armor.361887), [Wesnoth armour tutorial](https://wiki.wesnoth.org/Armour_Tutorial) **[weak]** |
| Scales | overlapping plate-like scales signal rigidity; the largest sit on the neck and throat; rows follow the body | [necks and scales tutorial](https://www.deviantart.com/tes92/art/Tutorial-2-1-necks-scales-872309285) **[weak]** |
| Fur | never draw strands at small size; imply fur with clumps and a broken outline | [pixel fur tutorial](https://art.cleberg.net/post/faustbane/Pixel-Fur-tutorial-149272131?p=2) **[weak]** |
| Cloth, skin | soft, diffuse light spot; low contrast | [basic pixel shading](https://springhole.net/art_tutorials/mspshading.htm) **[weak]** |
| Any | shadows shift hue, not only lightness | [Pixnote shading guide](https://pixnote.net/en/learn/shading) **[weak]** |
| Any | sideways and fractional offsets let rows step finer than one brick | [SNOT techniques](https://bricknerd.com/home/lego-snot-advanced-techniques-and-implementations-5-12-21) **[weak]** |

The search found nothing specific on keeping brick texture legible at small scale. The kit's
own rule fills that gap: value carries the read when detail is lost
([HIERARCHY.md](../../HIERARCHY.md) §11, eight lightness bands).

## 2. Roblox limits that bound the answer

| Limit | Value | Source |
|---|---|---|
| Triangles per mesh | 20,000 (`EditableMesh`); importer about the same | ch. [21](21-roblox-editablemesh-api.md), ch. 90 **[secondary]** for the importer |
| Texture size | 1024 × 1024 for `EditableImage` | ch. [20](20-roblox-editableimage-api.md) |
| `EditableImage` memory | per-device budget; creation returns `nil` when exhausted | ch. 20 |
| Publishing | Mesh / Image APIs need a 13+, ID-verified owner and a dashboard toggle | ch. 20, 21 |
| Mobile draw cost | no verified figure; parts sharing geometry and material batch | ch. 90 **[secondary]** |

Geometry layering is free of every limit except triangles, and the rhino's largest piece is
4,880 of the 20,000 allowed. So layering goes into geometry first; baked texture comes after.

## 3. Measures that work headlessly

| Measure | Definition | Source |
|---|---|---|
| Value bands | how many of 8 OKLab lightness bands hold 3 % or more of the surface | HIERARCHY.md §11; ch. [81](81-contrast-colour-and-colour-blindness.md) |
| Edge density | share of pixels on a lightness step of one band or more | [Rosenholtz, Li and Nakano 2007](https://dspace.mit.edu/handle/1721.1/37593), tested against search performance |
| Flat share | share of the surface with no edge within 3 bricks | this chapter |
| Relief | share of the interior surface 0.75 brick or more proud of, or recessed from, its surroundings | this chapter |
| Backed | share of lightness edges that sit on a real depth step | this chapter |
| Small-size survival | detail energy left after shrinking to 48 px tall and back | this chapter |

Edge density is the only one validated on people, and only as a clutter measure: more is not
better. The kit's lexicon caps detail density at 25 %, so the scorecard rewards 8–25 % and
penalises more. `relief`, `backed` and `flat` are this chapter's own and are **not validated
against human judgement**. They are trusted only as far as they agree with the owner's eye on
the three anchors.

## 4. Decisions

| Decision | Options considered | Pick | Reason |
|---|---|---|---|
| What to measure on | Blender renders; shipped preview sheets; flat views of the brick grid | grid views | exact, seconds per model, same on every Blender version |
| Baseline storage | a table in Markdown; one JSON file; git history | `examples/BASELINE.json` + `scorecard.py check` | a script can fail a build on it |
| Thresholds | absolute pass marks; relative to each model's own baseline | relative, with small tolerances | the measures are unvalidated, so only "not worse than before" is safe |
| Anchors | highest scores; the owner's picks | swamp croc, war rhino, kraken | the owner approved them by eye |
| Classifying a part's surface | vision on the concept; geometry descriptors; a declared tag | declared tag per part, checked by descriptors | a tag is testable; automatic vision is unproven here |
| Geometry or bake | bake only; geometry only; geometry first then bake | geometry first | no texture limit applies and the triangle budget has room |
| Rhino rebuild | edit the shipped file; a new file | new file | the shipped rhino stays 1:1 for comparison |

## 5. Surface types in the 17 models

| Surface | Models | Anchor | Geometry | Bake later |
|---|---|---|---|---|
| Layered plate armour | war rhino, living armor, war mech (panels) | war rhino (rebuilt) | plates raised 2 bricks, shingled front to back, varied sizes | lip shadow, rim wear |
| Scales and hide | swamp croc, tyrant rex, ember dragon, volcano tortoise (skin) | swamp croc | scute rows and ridge lines raised 1–2 bricks | belly gradient |
| Soft body, tentacles | kraken, abyssal angler | kraken | tapered curves, sucker rows, fin rays | wet highlight |
| Fur and feathers | frost mammoth, storm griffin | frost mammoth | stepped tufts, shingled feather blocks | none needed |
| Bone and horn | bone hydra, all horns and teeth | bone hydra | facet bands, gaps between ribs | tip lightening |
| Cloth and robes | lich king, scarecrow king | lich king | vertical folds, tattered hem | none needed |
| Rock and lava | volcano tortoise (shell), ember dragon (cracks) | volcano tortoise | plates split by solid bright cracks | emissive mask |
| Chitin and jointed legs | scorpion king, venom widow | scorpion king | segment bands with a gap at each joint | gloss band |
| Wood and metal fittings | mimic chest, war mech | mimic chest | plank rows, iron bands proud of the wood, rivets | none needed |

The anchors for rows without an owner-approved model are provisional: they are the model
whose scorecard is highest in that row.

## Not tested

- No measure here is validated against people beyond the owner's three anchors.
- Concept sheets are drawn in perspective; the `match` score compares them with flat views
  and is only useful for comparing a model with its own earlier version.
- Nothing ran in Studio or on a phone.

## Sources

- [LEGO MOC dragon guide](https://htbi-moc.com/blogs/guides/lego-moc-dragon-breathe-fire-into-your-builds)
- [LEGO SNOT: advanced techniques](https://bricknerd.com/home/lego-snot-advanced-techniques-and-implementations-5-12-21)
- [Necks and scales tutorial](https://www.deviantart.com/tes92/art/Tutorial-2-1-necks-scales-872309285)
- [Wesnoth armour tutorial](https://wiki.wesnoth.org/Armour_Tutorial)
- [Advice on shading armour](https://www.pokecommunity.com/threads/any-advice-on-shading-armor.361887)
- [Pixel fur tutorial](https://art.cleberg.net/post/faustbane/Pixel-Fur-tutorial-149272131?p=2)
- [An overview of basic pixel shading](https://springhole.net/art_tutorials/mspshading.htm)
- [Pixnote: shading and lighting](https://pixnote.net/en/learn/shading)
- [Feature Congestion and Subband Entropy measures of visual clutter](https://dspace.mit.edu/handle/1721.1/37593)
- [Rosenholtz, Li and Nakano, Measuring visual clutter (Journal of Vision, 2007)](https://pubmed.ncbi.nlm.nih.gov/18217832)
