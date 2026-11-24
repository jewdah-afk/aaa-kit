---
name: vfx
description: Use when making or tuning combat and world visual effects - multi-phase ability and impact blueprints (telegraph, core flash, ground runes, orbiting trails, lingering smoke), hits and impacts, hit-stop, screen shake, muzzle flashes, trails, beams, lightning, explosions, shockwaves, void and arcane rings, vortexes and singularities, crystal and slash bursts, dissolves and death effects, auras, freezes, magnets, telegraphs, ParticleEmitter/Beam/Trail setup, flipbooks and particle budgets. Triggers on "VFX", "effect", "impact", "juice", "hit feel", "screen shake", "explosion", "trail", "lightning", "aura", "dissolve", "blueprint", "telegraph", "vortex", "slash", "make it punchier".
---

# vfx

Combat effects are tier 2 (HIERARCHY.md §2): they read instantly, then get out of the way. The intensity ladder (§4) decides how much they may do right now.

## When to use

- Any effect tied to an action: hits, casts, kills, pickups, telegraphs
- Any effect with more than one layer: write the blueprint first (Method 2)
- Tuning "feel" (hit-stop, shake, flash) and particle budgets

**Not for:** reward reveals (`reward-moments`), surface looks (`materials`), raw shader maths (`shaders-and-sdf`).

## Method

1. **Name the job.** Telegraph (warn), impact (confirm), status (persist) or ambient (decorate). Each job has different rules.
2. **Write the blueprint before any Instance.** Copy the nearest template (table below) and change the data. Every layer is in one of five phases on a 60 fps frame clock, and all five are required:

| Phase | Frames | What it is | Hard rules (⚙ = checked by `Blueprint.validate`) |
|---|---|---|---|
| Telegraph / Anticipation | 0 to hit−1 | motes drawn in, a ground tell, a light swell | ⚙ starts before the hit, ends by hit+4. A mechanic with no wind-up still gets a 3-frame tick. Hostile: never gated or scaled, red allowed |
| Core Focal Point | on the hit frame | bloom + mesh core: the one layer at peak 1 | ⚙ starts hit..hit+2, highest `ZOffset`; the brightest frame of the effect |
| Ground Projection | by hit+8 | runes, rings, cracks, decals on the floor | ⚙ starts by hit+8; never over the hero or a threat |
| Secondary Motion | hit..hit+12 | orbiting trails and arcs, debris | ⚙ starts hit..hit+12, peak ≤ 0.7 |
| Dissipation / Lingering Smoke | hit+6 to the last frame | alpha-blended smoke + a few embers | ⚙ peak ≤ 0.35, tier 4, gated `ambient`, lowest `ZOffset`, runs to the last frame |

3. **Validate it.** `Blueprint.validate(bp)` returns `{}`. Louder means shorter: peak > 0.7 lasts ≤ 24 frames, peak > 0.35 lasts ≤ 60, the effect is ≤ 180 frames, nothing loops. Emitters, beams and trails set their own `LightEmission`, `LightInfluence` and `ZOffset`; trails set `MinLength` and `MaxLength`.
4. **Plan per rung.** `Blueprint.plan(bp, Intensity.BUDGET[level])` drops gated layers (the impact flash at rungs 0–1, lingering smoke at 2, 4, 5), scales counts by `particles` and keeps a hostile Telegraph whole.
5. **Build with the patterns** in [patterns.md](patterns.md) (❌ DO NOT / ✅ DO for Beam and Trail attachments, emitter dials, EditableImage flipbooks, frame scheduling). `examples/Rig.luau` implements them.
6. **Schedule on frames.** One `Timeline` per effect on one `PreRender` connection. Never `task.wait` chains or `Completed` hops.
7. **Add feel** from `examples/Impact.luau`: 2-frame hit-stop on a normal hit, up to 6 on a kill; trauma shake (offset = 6 px × trauma², trauma decays in 450 ms); a 1–2 frame flash. Hit-stop only when the rung allows impact.
8. **Respect ownership.** Friendly FX stamp at hero rank and never cover threats, UI or ceremonies (§3, §8). Inside a hostile shot's lane, drop branches and sparks. Decoration slots: 6 in the world; skip extras, never delay them. Friendly coverage ≤ 40 % of the play area, ≤ 20 % near the hero.
9. **Colour.** Friendly effects use the hero's palette. Red is for threats only (⚙ checked). Peak brightness is for the onset frame only.
10. Run the self-check.

## Reference templates

Each is a complete blueprint: five phases, frame times, rung gates, particle budget, the assets it needs and how to play it.

| Template | Use it for | Frames | Notes |
|---|---|---|---|
| `examples/blueprints/VoidRings.luau` | Multi-ring void and arcane impacts | 100, hit 18 | Friendly. Rune seal, three staggered rings, orbiting arcs and trails, violet smoke |
| `examples/blueprints/VortexSingularity.luau` | Vertical vortexes and singularities, boss attacks | 168, hit 48 | Hostile. 0.8 s red telegraph, light column, helix trails, collapsing core |
| `examples/blueprints/CrystalSlash.luau` | Directional crystal and slash bursts | 72, hit 6 | Directional. 6-frame micro-telegraph, crescent flash, shard fan, frost line |

To make a new effect: copy the closest file, rename it, change the data, add it to the `templates` list in `examples/Blueprint.test.luau` and run that test.

## Hierarchy rules it obeys

- §2: tier 2 (combat), tier 4 (the lingering Dissipation layers).
- §3: hero rank for friendly FX; never paint over threat, UI or ceremony.
- §4: the intensity budget gates impact frames, particle counts, bloom and lingering smoke.
- §5: red is for threats only.
- §8: urgency beats rarity, so even a Mythic weapon's FX back off near threats.
- §9: a hostile Telegraph always draws on time at full strength; decoration waits by being skipped, never delayed.
- §10: protected regions around the hero, shots and pickups.

## Engine notes

**Roblox.** Prefer `ParticleEmitter:Emit(n)` bursts over always-on emitters. `Beam` handles lightning and lasers (animate `CurveSize`, set both attachments' `Axis`), `Trail` handles swings, and `Highlight` gives a 1-frame hit flash (cap at 31 on screen). Shake the camera with `Camera.CFrame *= CFrame.new(x, y, 0) * CFrame.Angles(0, 0, roll)` in `PreRender` after the camera script runs (`BindToRenderStep` priority `Camera.Value + 1`). Hit-stop scales your own simulation's dt; Roblox physics can't be paused. Effects are built on the client from a seed and an origin.

**EditableImage and particles.** `ParticleEmitter`, `Beam` and `Trail` texture slots are not documented to accept an EditableImage (research ch. 20 §5.5). Bake flipbook sheets offline for emitters; use a runtime sheet (`examples/Flipbook.luau`) on an `ImageLabel` or `Decal`. Details in [patterns.md §3](patterns.md). For pixel games, draw FX into the EditableImage through the owner buffer (`editable-image`). Live EditableMeshes are capped at about 7 per client, so effects clone pre-made MeshPart templates (`editable-mesh`).

**Web.** Canvas 2D with `globalCompositeOperation = "lighter"` for additive glow; WebGL for dissolves and distortion. Clamp `dt` to [0, 1/20].

## Process

Surface effects that move across a model (dissolve with a burning rim, a scan sweep, frost spreading from a hit, pulsing runes) are `Animate` effects over a baked texture: [procedural textures playbook §5](../../../docs/playbooks/procedural-textures.md#5-moving-surfaces-realtime).

The craft behind these rules (one hero + two supports, ZOffset order, toon flipbooks, mesh templates, camera priorities, engine limits) is in the [VFX craft playbook](../../../docs/playbooks/vfx-craft.md); stress-test new effects with the [look-dev loop](../../../docs/playbooks/look-dev-loop.md#stress-testing-vfx).

## Example

`examples/Blueprint.luau` (the standard and its validator), `Timeline.luau` (frame cues), `Flipbook.luau` (procedural sheets), `Impact.luau` (hit-stop, trauma shake, flash) and the three blueprints are pure and tested (`examples/Blueprint.test.luau`, `Timeline.test.luau`, `Flipbook.test.luau`, `Impact.test.luau`). `examples/Rig.luau` is the Roblox adapter: compile-checked, not yet play-tested. [effects-gallery.html](../../../examples/web/effects-gallery.html) runs shockwave, branching lightning and ember dissolve live.

```lua
local Blueprint = require("./examples/Blueprint")
local VoidRings = require("./examples/blueprints/VoidRings")
local Impact = require("./examples/Impact")
local Intensity = require("../../../examples/framework-starter/src/shared/Systems/Intensity")

assert(#Blueprint.validate(VoidRings) == 0)
local fx = Impact.new()
local function cast(level: number)
	local budget = Intensity.budget(level)
	local plan = Blueprint.plan(VoidRings, Intensity.BUDGET[level]) -- layers, particles, bloom for this rung
	-- Roblox client: Rig.play(VoidRings, CFrame.new(position), Intensity.BUDGET[level], { onHit = function() fx:hit(1, budget.impact) end })
	return plan.particles
end
-- every frame:
local function frame(dt: number, reducedMotion: boolean): (number, number, number, number)
	local simDt = fx:step(dt) -- 0 during hit-stop; feed this to gameplay
	local ox, oy, roll = fx:shake(reducedMotion)
	return simDt, ox, oy, roll -- apply the offset to the camera after its own update
end
```

## Make it insane

1. **Kill chains:** every kill spawns a short branching arc to the next kill within 80 px, so a crowd clear draws a lightning tree across the swarm (decoration slot; dropped near threats).
2. **Impact frames:** on a boss hit, render 2 frames of a high-contrast inverted silhouette (hero white, everything else ink) before returning to colour. It's the anime impact-frame look, gated to the boss rung.
3. **Time-freeze sweep:** everything halts, the frame tints cold, a clock hand sweeps the stop and particles hang mid-air (`timeline.timeScale = 0`). On release they resume with the stored velocity plus a burst.

## Self-check

- [ ] `Blueprint.validate` returns `{}` and the blueprint is in `Blueprint.test.luau`; `lune run` of it passes.
- [ ] `Blueprint.plan` is within `maxParticles` at all six rungs; the impact flash is gone at rungs 0–1 and lingering smoke at 2, 4, 5.
- [ ] The onset is the brightest frame; every loud layer is short; the effect fades out instead of cutting.
- [ ] No friendly effect covers a hostile shot, the hero or any UI; red appears only on threats.
- [ ] Beam and Trail attachments exist before the Beam or Trail; `MinLength` and `MaxLength` are set; nothing is parented until it is configured.
- [ ] Bursts are `Rate = 0` + `Emit`; cleanup waits for the longest particle life; no `task.wait` sequencing.
- [ ] Hit-stop and shake are off at the calm rung and reduced with reduced motion.
- [ ] Studio play test at rungs 0, 2 and 3 (not possible from the cloud: say so), with measured frame cost (ms) for the worst case, and the effect still reads at phone size.
