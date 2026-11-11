# World hierarchy

How we organised 3D worlds so every frame reads in the right order, and so every part has exactly one home in the Explorer. This is the world-space companion to [HIERARCHY.md](../../HIERARCHY.md) (which covers screen loudness and pixel ownership).

## 1. What the eye finds, in order

Every frame from the game camera reads in this order. Each tier is quieter than the one above it in **value contrast, saturation, detail and motion**.

| Tier | What | How it wins attention | How it stays quiet |
|---|---|---|---|
| 1 Focus | the player, their pickups, companions | the only ink outlines, brightest whites, warm rim light, always moving | — |
| 2 Interactables | NPCs, machines, portals, chests | its own light or glint, clear silhouette, a cleared ring of ground | no outline; at most one per screen region |
| 3 Landmark | **one** hero per area (lighthouse, tower) | tallest silhouette, on the far edge or a corner so it frames the play area | darker than tiers 1–2, slow motion only |
| 4 Structure | paths, fences, lamps, bridges | leads the eye: paths point at the goal and the landmark | mid values, low-saturation browns and greys |
| 5 Dressing | trees, bushes, grass, rocks, critters | texture and life: sway, drift | darkest and most varied greens; denser at the edges (a natural vignette); never on the play path |
| 6 Ground | grass, sand, water, path paint | the stage | flat-ish, two greens, casts no shadows |
| 7 Backdrop | cliffs, sea, far islands, clouds, sky | depth | hazy (Atmosphere), desaturated, cooler, blurred by a tilt-shift DepthOfField |

**Composition per area:**
- **Foreground** (bottom of screen): low dressing only, cut by the frame edge, slightly out of focus. It must never be tall enough to hide the player.
- **Midground** (the play area): tiers 1, 2 and 4, kept open, with dressing hugging the edges.
- **Background** (top of screen): the landmark, big trees and cliff edge, then sea and sky.
- With a camera looking north at a fixed pitch, **tall things go on the north half**.

**Value check on every screenshot:** blur it or squint. The player and pickups must still be the brightest, highest-contrast spots. If a flower bed, lamp glow or the sea is brighter, push it down.

## 2. Outlines and highlights

- Ink outlines (`Highlight`, Occluded) on **tier 1 only**. Scenery has none.
- Roblox renders at most **31 Highlights** at once. Tier 1 uses a couple; hover and interact highlights share the rest.

## 3. The Explorer tree (nothing map-related lives anywhere else)

```
Workspace
  World
    Sky            clouds, far horizon                                       tier 7
    Sea            surface, depth, shelf, life, waves, cliff skirt, splash    tier 7
    Areas          one Model per open area, culled by unparenting
      <area>
        Ground         ground parts, water, painted paths                     tier 6
        Landmarks      the area's hero structure                              tier 3
        Interactables  NPCs, machines, portals                                tier 2
        Props          lamps, benches, fences, bridges                        tier 4
        Foliage        trees, bushes, flowers                                 tier 5
        Rocks          rocks, ore, crystals, logs                             tier 5
        Life           butterflies, birds, critters                           tier 5
        FX             area-local emitters and lights                         tier 4
    Actors         the player, their shadow, pickups                          tier 1
    Atmosphere     wind / pollen / leaf anchors, fireflies, dust
    Vfx            the VFX engine's pools and parts
  Terrain          walkable tops
```

- **One module owns the tree** (`WorldTree`): `root()`, `layerFor(area, kind)` and a `LAYER_OF` table mapping every prop kind to its layer.
- **Builders never pick a folder by hand.** A test checks that every kind in the map data is mapped (0 unmapped).
- **Per-layer rules live with the tree** (`RULES`): max brightness, saturation range, motion allowed, outline allowed, collision.

## 4. Art direction decisions that stuck

- **Lock the direction in writing** before building ("realistic cartoony, golden hour, painted materials" or "pixel art, simple, heavy hierarchy"), with one reference image. Changing direction mid-build cost more than anything else.
- **Hero first:** design the area in Figma or a concept image with the hierarchy tiers labelled, then build to it.
- **Procedural maps get rejected when they look bad, not because they're procedural.** Build the hierarchy in from the start, and ask before adding map variety.
- **Ground stays graded down** so actors pop.
