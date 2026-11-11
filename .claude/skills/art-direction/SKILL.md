---
name: art-direction
description: Use for the overall look and its readability - palettes and colour jobs, value structure and luminance bands, the figure-ground contrast gate, silhouettes, readability at high density, phone-first framing, visual consistency across screens, and style reviews ("does this look AAA?"). Triggers on "art direction", "palette", "colours", "looks muddy", "can't see the enemies", "too busy", "too dark", "style guide", "make it look professional", "review the look".
---

# art-direction

Art direction here means one thing: the player reads the frame correctly in under a second, on a phone, in the busiest moment. Beauty comes after that and stays inside it.

## When to use

- Setting a game's palette and value structure
- Reviewing a screen, a stage or a capture for readability
- "Too busy", "muddy" or "can't see X" feedback

**Not for:** individual effects (`vfx`), surfaces (`materials`) or HUD layout details (`ui-hud`).

## Method

1. **Value first.** Design in greyscale. Use 8 perceptual luminance bands (OKLab L, B0–B7). Assign bands by owner: world B1–B3, pickups B4–B5, threats and hero get the contrast they need against their ground, UI B5–B7 on a dark plate.
2. **Colour jobs** (§5). Write the table for this game: currency, XP, danger, rarity, the hero's light and UI focus. Every other colour is decoration and stays desaturated.
3. **Figure-ground gate** (§11). Every gameplay silhouette is ≥ 2 bands from the 1–2 px ring around it, at its worst pixel. Give the hero a thin ring that darkens what's under it by 2 bands.
4. **Silhouettes.** Each enemy family and pickup is identifiable from its shape alone at 16 px. Test it with a black-fill view.
5. **Density.** Look at the worst frame (max enemies, max FX). Check the detail and motion budgets (§12) and that crowd LOD kicks in.
6. **Phone framing.** Test at 390×844 and 844×390. Thumbs cover the bottom corners. Text ≥ 14 px, and important numbers ≥ 20 px.
7. **Consistency.** One light direction and one outline rule for every sprite and icon. Every screen uses the same palette ramps.
8. **Review views.** Squint (blur 4 px), greyscale, tier view (colour by owner) and saliency. Fix what draws the eye that shouldn't.
9. Run the self-check.

## Hierarchy rules it obeys

All of HIERARCHY.md, especially §2 tiers, §3 ownership, §5 colour jobs, §6 calm frames, §11 figure-ground gate, §12 density and §13 one loud element per panel.

## Engine notes

**Roblox.** Use `Lighting` (`Ambient`, `OutdoorAmbient`, `ColorCorrectionEffect`, `Atmosphere`) for global value structure, keep `Bloom` low (threshold ≥ 0.9) so only true emitters bloom, and use `Highlight` for silhouette checks in a debug mode. For pixel games, quantise to bands in the renderer (see `editable-image`).

**Review captures.** Use headless Chromium screenshots for web labs (`node tools/check_examples.mjs --shots dir`) and Studio screenshots at the phone emulator sizes.

## Example

`examples/Contrast.luau` provides sRGB → OKLab lightness, 8-band quantisation, the figure-ground gate (worst-case gap) and a hue-preserving band shift for the hero's ring. It's tested in `examples/Contrast.test.luau`.

```lua
local Contrast = require("./examples/Contrast")
local enemy = { { 120, 120, 120 }, { 140, 130, 128 } }   -- sprite colours
local floor = { { 110, 110, 115 }, { 96, 100, 104 } }     -- ground colours under it
local ok, gap = Contrast.gate(enemy, floor)               -- false, 0: grey on grey fails
if not ok then
	-- fix: shift the ground down 2 bands, or give the enemy a darker 1 px ring
	local ring = Contrast.shiftBands({ 96, 100, 104 }, -2)
end
```

## Make it insane

1. **Saliency-driven grading:** a debug overlay computes a saliency map of each frame and flags anything that draws more attention than its tier allows (e.g. a decal brighter than a pickup).
2. **Lantern world:** the hero carries the only warm light. The world is cool and banded, and everything important glows only when inside the lantern's radius, which makes exploration a lighting mechanic.
3. **Adaptive palette:** as intensity climbs, the world desaturates one band and threat colours gain saturation, so the screen gets *clearer* exactly when it gets busier.

## Self-check

- [ ] Greyscale capture still reads (hero, threats, pickups, lanes).
- [ ] The colour-job table exists and nothing breaks it.
- [ ] Every gameplay silhouette passes the 2-band gate at its worst pixel.
- [ ] Shapes identify families at 16 px.
- [ ] The worst frame stays inside the density budgets.
- [ ] Checked at 390×844 and 844×390.
