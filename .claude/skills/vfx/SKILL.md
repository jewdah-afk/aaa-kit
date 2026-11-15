---
name: vfx
description: Use when making or tuning combat and world visual effects - hits and impacts, hit-stop, screen shake, muzzle flashes, trails, lightning, beams, explosions, shockwaves, dissolves and death effects, auras (including hero-tier showpiece auras), freezes, magnets/vortexes, telegraphs, screen-space effects and particle budgets. Triggers on "VFX", "effect", "impact", "juice", "hit feel", "screen shake", "explosion", "trail", "lightning", "aura", "dissolve", "make it punchier".
---

# vfx

Combat effects are tier 2 (HIERARCHY.md §2): they read instantly, then get out of the way. The intensity ladder (§4) decides how much they may do right now.

## When to use

- Any effect tied to an action: hits, casts, kills, pickups, telegraphs
- Tuning "feel" (hit-stop, shake, flash)
- Particle budgets and readability under spectacle

**Not for:** reward reveals (`reward-moments`), surface looks (`materials`), raw shader maths (`shaders-and-sdf`).

## Method

1. **Name the job.** Telegraph (warn), impact (confirm), status (persist) or ambient (decorate). Each job has different rules.
2. **Write the timeline** (§9): anticipation (only if the mechanic has a wind-up) → onset (frame 0–2: the brightest frame) → active → resolution → recovery (back to baseline within 12 frames).
3. **Build the onset from three layers.** A core (small, brightest, 1–2 frames), a shape (ring, arc or burst carrying the direction) and debris (sparks, dust: the decoration slot).
4. **Add feel** from `examples/Impact.luau`: 2-frame hit-stop on a normal hit and up to 6 on a kill; trauma shake (offset = 6 px × trauma², trauma decays in 450 ms); a 1–2 frame flash on the target. Hit-stop only when the rung allows impact.
5. **Respect ownership.** Friendly FX stamp at hero rank and never cover threats, UI or ceremonies (§3, §8). Inside a hostile shot's lane, drop branches and sparks.
6. **Budget.** Decoration slots: 6 in the world at once. Friendly FX coverage ≤ 40 % of the play area, ≤ 20 % near the hero. Skip extras, never delay them.
7. **Colour.** Friendly effects use the hero's palette. Red is for threats only. Peak brightness is for the onset frame only.
8. **Scale with intensity.** Read `Intensity.budget(level)`: particle multiplier, impact on/off, ambient on/off.
9. Run the self-check.

## Hero auras (layered ambient VFX that has to look top-tier)

An aura is tier 4-5 decoration the player owns, but a top-tier one is judged as a showpiece. This is the method that got one to "best in the game", in order; each step has an exit you can check.

1. **Start from a reference clip**, not an idea. One line per element (core size against the character, what erupts and how often, streak, smoke, floor). Keep a side-by-side as you go.
2. **Build the core as an orb ladder** on one point, back to front by ZOffset: bright rims behind -> a near-black body disc (LightEmission 0, so the orb reads solid) -> interior flipbooks at low brightness -> wisps and slashes with dark twins -> a cross flare at high brightness but ~0.94 transparency -> a slow swirl on top. The core is about as wide as the character is tall. Every layer crossfades in and out at a random rotation.
3. **Write a tier ladder and measure it:** 1 the core's edge (sharpest, most contrast) / 2 eruption / 3 smoke and floor (dim, desaturated) / 4 sparks and stars. Run `tools/hierarchy/hierarchy.py audit` on 3+ frames with the core as the focus box. **Exit: focus lift >= 1.5, squint gap >= 0.08, `hierarchy.py flash` passes on every burst.** A white blob means the core and interior are too bright: dim them and put a dark swirl in front of the interior.
4. **Save that version untouched** before any bigger pass.
5. **Check it in the engine, then copy the numbers back into data.** Browser previews over-bloom. Freeze each burst at ~0.1 s and ~0.4 s. Expect the engine to want lights at a third of the preview value and floor glow far dimmer, and the signature burst bigger and denser.
6. **Scale it, then add what only exists at that size**, each piece borrowed from a real phenomenon so depth reads as physics: a thin ring painted by an orbiting emitter (the sharpest line on screen), writhing beams out of the poles, a shell of tangent particles (its rim stacks brighter, like a fresnel), short prominence flares that fall back in, 2-3 star shells at different radii spinning against each other, and on the signature a smeared shock sphere plus a dark ground shock that rolls far past the aura. **Parallax rule:** every depth band moves at its own speed.
7. **Give the core an inside:** 2-3 mist slices between the dark body disc and the front detail, each with its own spin and colours, plus a small inward star shell.
8. **Make the floor readable:** a near-black disc under every floor layer, then two counter-rotating radiant flipbooks so the light rakes across itself. Lay flat layers on the real ground every frame (one raycast down). A negative ZOffset pushes a flat particle into the floor.
9. **No layer sits still.** Each one spins, travels, plays a flipbook or breathes in size, in character: the body turns slowly, the hot core flickers fast, a streak stays flat but stretches. Exit: diff two engine frames ~0.6 s apart; every band moves and the sky (the control) stays near 0.
10. **The sound ladder mirrors the visual ladder.** Each beat is transient + body + tail; the loudest beat is the visual peak; time a riser by its real length so its hard end lands on the release; one quiet looped bed under everything; other players' auras quieter and far ones silent. A person judges the mix by ear.
11. **Budget per rung** (own aura on desktop, own aura on phone, others nearby, far), and scale huge auras down for phones and crowds, because big particles cost screen fill.
12. **Variants change the palette only**, and each gets its own one-line concept. Keep the body and shadow colours near black in every palette, or the core loses its depth.

Tried and failed at large scale: dark smoke at LightEmission 0 (draws hard squares and half-domes), a halo ring around a very bright core (invisible), ring-swirl textures used as dust (they stack into noise), and floor rays sized for the small version (they read as a tiny star at the feet).

## Hierarchy rules it obeys

- §2: tier 2 (combat), tier 4 (world ambient).
- §3: hero rank for friendly FX; never paint over threat, UI or ceremony.
- §4: the intensity budget gates impact frames, particle counts and bloom.
- §8: urgency beats rarity, so even a Mythic weapon's FX back off near threats.
- §9: decoration waits by being skipped, never delayed.
- §10: protected regions around the hero, shots and pickups.

## Engine notes

**Roblox.** Prefer `ParticleEmitter:Emit(n)` bursts over always-on emitters. `Beam` handles lightning and lasers (animate `CurveSize`, swap `Attachment` positions), `Trail` handles swings, and `Highlight` gives a 1-frame hit flash (cap at 31 on screen). Shake the camera with `Camera.CFrame *= CFrame.new(x, y, 0) * CFrame.Angles(0, 0, roll)` in `RenderStepped` after the camera script runs (`BindToRenderStep` priority `Camera.Value + 1`). Hit-stop scales your own simulation's dt; Roblox physics can't be paused. For pixel games, draw FX into the EditableImage through the owner buffer (`editable-image`).

**Web.** Canvas 2D with `globalCompositeOperation = "lighter"` for additive glow; WebGL for dissolves and distortion. Clamp `dt` to [0, 1/20].

## Process

Surface effects that move across a model (dissolve with a burning rim, a scan sweep, frost or corruption spreading from a hit, pulsing runes) are `Animate` effects over a baked texture: [procedural textures playbook §5](../../../docs/playbooks/procedural-textures.md#5-moving-surfaces-realtime).

The craft behind these rules (one hero + two supports, ZOffset order, toon flipbooks, mesh templates, camera priorities, engine limits) is in the [VFX craft playbook](../../../docs/playbooks/vfx-craft.md); stress-test new effects with the [look-dev loop](../../../docs/playbooks/look-dev-loop.md#stress-testing-vfx).

## Example

`examples/Impact.luau` covers hit-stop, the trauma shake with smooth noise and a reduced-motion option, and the flash timer (tested in `examples/Impact.test.luau`). [effects-gallery.html](../../../examples/web/effects-gallery.html) runs shockwave, branching lightning and ember dissolve live.

```lua
local Impact = require("./examples/Impact")
local Intensity = require("../../../examples/framework-starter/src/shared/Systems/Intensity")

local fx = Impact.new()
local function onHit(strength: number, level: number)
	fx:hit(strength, Intensity.budget(level).impact)
end
-- every frame:
local function frame(dt: number, reducedMotion: boolean): (number, number, number, number)
	local simDt = fx:step(dt)               -- 0 during hit-stop; feed this to gameplay
	local ox, oy, roll = fx:shake(reducedMotion)
	return simDt, ox, oy, roll              -- apply the offset to the camera after its own update
end
```

## Make it insane

1. **Kill chains:** every kill spawns a short branching arc to the next kill within 80 px, so a crowd clear draws a lightning tree across the swarm (decoration slot; dropped near threats).
2. **Impact frames:** on a boss hit, render 2 frames of a high-contrast inverted silhouette (hero white, everything else ink) before returning to colour. It's the anime impact-frame look, gated to the boss rung.
3. **Time-freeze sweep:** everything halts, the frame tints cold, a clock hand sweeps the stop and particles hang mid-air. On release they resume with the stored velocity plus a burst.

## Self-check

- [ ] The onset is the brightest frame; recovery reaches baseline within 12 frames.
- [ ] No friendly effect covers a hostile shot, the hero or any UI.
- [ ] Decoration count ≤ 6; extras skipped, not queued.
- [ ] Hit-stop and shake are off at the calm rung and reduced with reduced motion.
- [ ] Red appears only on threats.
- [ ] The effect still reads at phone size and at the busiest intensity rung.
- [ ] Measured frame cost noted (ms) for the worst case.
- [ ] Hero auras: every step's exit above is met (audit numbers, engine check, frame diff, rung budgets) and written down.
