---
name: materials
description: Use when designing how a surface looks - metal, chrome, brushed metal, gold, gems, crystal, glass, holo/foil, soap film, molten and emissive surfaces, ice, cel-shaded materials, and rarity expressed as material on items, frames, icons and UI. Triggers on "material", "shiny", "metallic", "chrome", "gem", "glass", "holographic", "foil", "emissive", "glow", "make the item look premium", "rarity look".
---

# materials

Materials are tier 5 (HIERARCHY.md §2). They make an item look like what it is and how rare it is. Pick one material per rarity and use it consistently on frames, icons and 3D items.

## When to use

- Item, icon, card and frame looks
- Rarity tiers that need to read at a glance
- Premium or VIP surfaces, currency icons

**Not for:** animated combat effects (`vfx`) or shader maths in depth (`shaders-and-sdf`).

## Method

1. **Map rarity to material** (HIERARCHY §7): flat → satin → brushed → glass/gem → chrome/molten → holo → void/glitch. Write the map down and never swap it per item.
2. **Build every material from the same four parts:** base colour (albedo), a highlight shape (where light catches), an edge response (Fresnel rim) and motion (sweep, sparkle or none).
3. **Metal.** Dark base, sharp bright highlight, coloured reflection (gold reflects gold). Brushed metal stretches the highlight into a streak along the grain.
4. **Gem.** Facets with alternating light and dark plus sparse star glints (≤ 3 at once). The internal colour is deeper than the surface.
5. **Glass.** Mostly what's behind it, a thin bright rim and a slight chromatic split at the edges.
6. **Holo foil.** A hue that shifts with view angle or tilt, a fine line pattern and a sheen band that follows the pointer or gyro.
7. **Emissive.** Glow only for things that are actually a light source or currently active. A glow that never turns off is noise.
8. **Readability.** The material must not lower the icon's figure-ground contrast (§11). Test the icon at 48 px on a phone.
9. Run the self-check.

## Hierarchy rules it obeys

- §2: tier 5, below the HUD in loudness.
- §5: currency gold is a colour job; a gold *material* on a Legendary item stays inside its frame and never as a plain fill.
- §7: the rarity ladder: each tier adds one behaviour.
- §6: material motion (sweeps, sparkles) only from Rare upward, and slow.

## Engine notes

**Roblox 3D.** `SurfaceAppearance` (ColorMap, NormalMap, MetalnessMap, RoughnessMap) for PBR, `Material = Neon` only for true emitters, `Highlight` for outlines, `PointLight`/`SurfaceLight` for real glow. Environment reflections need `Lighting.EnvironmentSpecularScale` > 0.

**Roblox UI.** `UIGradient` (with `Rotation` tweened for spin and `Offset` tweened for sweeps), `UIStroke` for frames, layered ImageLabels for foil lines. Use one tween per frame, not per-frame code.

**Web.** Canvas gradients plus `globalCompositeOperation` (`overlay`, `lighter`) for 2D, and GLSL with Fresnel `pow(1 - dot(n, v), 5)` for 3D.

## Example

`examples/RarityStyle.luau` holds the seven-tier ladder as data (each tier names the one behaviour it adds) and an applier that styles a Roblox frame with `UIStroke` and `UIGradient` plus tweens. `examples/RarityStyle.test.luau` enforces "adds at most one behaviour per tier" and "no rarity uses danger red". [effects-gallery.html](../../../examples/web/effects-gallery.html) shows the holographic foil and rarity frames live.

```lua
local RarityStyle = require("./examples/RarityStyle")
local style = RarityStyle.get(5)      -- Legendary
print(style.material, style.adds)     -- "chrome"  "edge sparks + glow"
-- Roblox: local cleanup = RarityStyle.apply(slotFrame, 5) ... cleanup() when the slot is reused
```

## Make it insane

1. **Gyro foil:** on phones, the holo hue and sheen band follow the device tilt (`UserInputService.DeviceRotationChanged`), so a Mythic card shimmers as you move your hand.
2. **Molten-to-cooled:** a Legendary forge item starts molten (black-body ramp, crawling noise) when crafted and cools over 2 s into chrome with a single heat-shimmer left at its core.
3. **Void material for Secret:** a starfield seen *through* the item (parallax sampled in screen space), glitch slices on the rim and the tier name hidden until the reveal's final beat.

## Self-check

- [ ] The rarity → material map is written down and every item follows it.
- [ ] Each tier adds exactly one behaviour; Common and Uncommon don't move.
- [ ] Icons pass the 2-band figure-ground gate at 48 px.
- [ ] Glow is only on things that emit or are active.
- [ ] No rarity uses danger red; currency gold isn't used as a rarity fill.
- [ ] Motion speeds are slow (sweeps ≥ 2 s apart) and respect reduced motion.
