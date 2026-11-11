# VFX craft

How we built effects that read as AAA in Roblox, and the engine limits we hit along the way. The rules sit in the [vfx skill](../../.claude/skills/vfx/SKILL.md); this page is the craft and the history behind them.

## The hierarchy inside one effect

**One hero, two support layers, an ambient trickle.**
- The hero is the flash or the column: the brightest, white-hot core, 1–2 frames.
- Support carries the shape and direction (rings, slashes, swirls).
- Ambient is sparkles and embers, tapering off.
- Ink outlines only on normal-blend pieces, never on additive glow.

**Draw order (ZOffset), from front to back:**

| Layer | ZOffset |
|---|---|
| flash core | 5.2 |
| flash rim | 5 |
| needles | 4.6 |
| speed lines | 4.4 |
| embers | 4.3 |
| swirls | 4.2 |
| ink | 4 |
| shards | 3.5 |
| cloud | 3 |
| smoke | 2 |
| glow | −0.6 |
| rays | −2 |

## The four craft levers

1. **Real shapes, not flat beams.** Flat beams stood up as triangles or ovals from other angles. Use mesh rings, domes, crescents, swirls and star shapes (pooled clones), animated with eased spin, ease-out growth, thinning, squash and **hard-stepped fades** (2–3 steps, not smooth).
2. **Toon flipbooks.** Smoke, bursts and dust are rendered in Blender:
   - noise-displaced sphere lobes
   - a 3-step toon ramp from N·L (constant ColorRamp → Emission)
   - an inverted-hull ink outline at constant world width
   - a dissolve that re-inks every hole's rim

   They're baked to 4×4 flipbook sheets (`blender -b --factory-startup --python gen.py -- [keys]`). Simple shapes (flash stars, ring waves, speed lines, glow steps) come from a PIL generator with `--preview` contact sheets.
3. **Physical particles.** Streaks use VelocityParallel + Squash + Drag + gravity. Sizes use multi-key pops. Hot cores sit at Brightness 2–3. Radial bursts emit outward in code, because a shape Part would hide occluded Highlights. Rates follow curves (accelerating suck-in, tapering trickles).
4. **Camera feel**, gated by priority:
   - pushes only replace a lower-priority push (unlock 5 > hatch 3 > level-up 1)
   - background events never push
   - shake, push and flash bind their own RenderStep (Camera + 2) only while running, then unbind
   - Reduced Motion turns shake and push off

## Effect recipes that shipped

- **Pickup pop (0.35 s):** broken ring snap (0.24, ease-out, stepped out) + colour flash star (0.13) + white core (0.09) + 3–4 inked sparkles with drag stop. The rare variant is ×1.25 with 2 star bits.
- **Level-up (1.6 s):** ground ring wave + flat 3-band glow + dust → a light column shoots up, holds and thins → a spiral cone winds up and collapses → rising sparkles and speed lines → a "ding" 4-point flash at 0.9 s.
- **Hatch / reveal, scaled by rarity** (A = 0.65 s Common … 2.1 s Mythic):
  - the egg rocks with ramping speed and amplitude, glow charges in steps, embers get sucked in
  - crack stages at 0.3A / 0.58A / 0.84A, each with a jolt, specks and a twinkle
  - Legendary+ adds a rune circle and a light pillar
  - at A: hero flash (plays through the hit-stop), crescent slashes, burst cloud, shards, a ring wave, a dome (Epic+), shake and a 0.05–0.1 s hit-stop
  - A + 0.04: the item pops with overshoot, a ray fan, stars, and confetti (rainbow on Mythic)
- **Area unlock:** rune circle drops in → summon pillar + spiral cone → a light wave sweeps the new tiles (glints on sampled tiles, dust bursts on the coast) → finale flash, dome, star burst, shower, shake.

## Limits we hit

- **Live EditableMeshes are capped at roughly 7 per client** (the map used 2). Effects therefore clone pre-made template MeshParts saved in the place (`ReplicatedStorage.VfxMeshes`), coloured with Color + Neon (glow) or SmoothPlastic (ink) + Transparency.
- **Store meshes the place doesn't own can't be fetched by id at runtime** ("MeshContentProvider failed"). Save templates into the place first.
- Check each template's orientation from its bounding box: most are Y-up, but pin any odd one explicitly.
- An edge-on flipbook frame of a flat sprite shows as a bare ink line (a "stick"), so redraw tumble frames so none are edge-on.
- **Caps per effect and in total** (hatch 8, pickup 16, level-up 4, unlock 2, 48 overall). Hit-stop freezes everything except the hero flash.
- Readable at any zoom: size multiplier `clamp(cameraDistance / 290, 1, 2.4)`.

## QA hooks

Every effect gets a dev hook: `_G.__vfx("egg_hatch", "Mythic")`, `_G.__vfx("hatch_all")`, `"stats"` (live counts vs caps) and `"stop"`. Studio QA then becomes "run each one at each rarity and screenshot".
