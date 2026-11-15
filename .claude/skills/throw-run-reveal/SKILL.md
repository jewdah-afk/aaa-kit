---
name: throw-run-reveal
description: Use when building a throw, launch or fling loop with a flight run and an odds reveal - charge meter, throw camera, flying through a lane of themed zones, zone name ribbon, a luck multiplier ticking during flight, landing, silhouette reveal, "1 in N" odds counting up a rarity ladder, slam words like LUCKY! and the result card. Also for designing the run map itself - zone ladder, biome per stretch, lane readability. Triggers on "throw animation", "flight run", "zone ladder", "lane map", "odds reveal", "1 in", "silhouette reveal", "slam words", "launch loop".
---

# throw-run-reveal

One loop in three acts: **charge → run → reveal**. Each act has exactly one loud thing on screen (HIERARCHY.md §2). The run map is part of the UI: it paces the luck number and gives every zone a name worth reading.

## When to use

- A throw, launch, fling or cannon loop where the player watches the projectile fly and then gets an RNG result
- Designing the lane the projectile flies down: zones, biomes, names, pacing
- An odds reveal that counts "1 in N" up through rarity tiers

**Not for:** chest or egg openings with no flight (use `reward-moments`), map scatter and terrain generation (`procedural-world`), shop or HUD layout (`ui-hud`).

## Method

1. **Roll first.** The server rolls the result and the final odds before the throw animates. Flight distance, zones crossed and the reveal all play back a decided result.
2. **Charge (≈0.5 s).** Only the power meter moves: a vertical capsule beside the player, fill green → red, power number above, "HOLD TO THROW" below. The rest of the HUD stays at rest.
3. **Throw camera.** Swing to a front 3/4 view for the wind-up (≈1 s, no UI), cut over the shoulder on release, then lock behind the projectile.
4. **Run HUD: one centred block.** Big ×luck number, small LUCK label under it, a "+0.09×" delta chip off its top-right corner, and the zone name on a dark fading ribbon beneath. Nothing else is on screen during flight.
5. **Zone ladder.** A new zone every ~0.3 s of flight (`ZoneLadder.paced`). Each zone has a name, a palette and one landmark silhouette. The ribbon name crossfades in 120 ms, and the luck number's colour follows the zone palette.
6. **Landing.** The projectile slows, a ground ring expands over 200 ms, the HUD clears to the ribbon only, and the camera tilts up.
7. **Silhouette.** The result enters as a black silhouette with a white rim. Odds start quiet: "1 in 2" in white, top centre.
8. **Odds climb.** Count up with `OddsLadder.steps`: slow at first, fast at the end, landing exactly on the rolled odds. The number's colour steps the rarity ladder. On each `TierUp`, a tier word slams in at an angle (2 frames), shrinks to 40% (3 frames), and parks at the side; the screen edge flashes in the tier colour.
9. **Peak (top tiers only).** White flash 100% → 0 over 0.5 s, a sunburst behind the odds, the tier word under them, and confetti.
10. **Unveil and result card.** The rim fades and the real model appears. Bottom-centre stack: tier (small) / name (big) / income per second counting up (green) / one grey info line.
11. Run the self-check.

## Hierarchy rules it obeys

- §2: one loud element per act: meter, then luck, then odds.
- §3: the reveal owns the screen; the HUD steps back to nothing.
- §4: charge and run are rung 1–2; the reveal climbs to rung 3; peak effects only on the top tiers.
- §7: the rarity ladder is colour first, so the tier reads before the words.
- §14: sequence charge → run → landing → silhouette → climb → unveil → card, each beat starting when the last settles.

## Engine notes

**Roblox.** The server rolls and fires the result. The client drives the camera with `Camera.CFrame` tweens (wind-up orbit, then a follow rig behind the projectile part). Zone swaps change `Lighting` and `Atmosphere` colours by crossfade, never a cut. Use `ViewportFrame` or a duplicated model with `Highlight` (FillColor black, FillTransparency 0, OutlineColor white) for the silhouette. Use `ColorCorrectionEffect` for the edge tint and the white flash, `TweenService` for slam words (`UIScale` 2.2 → 1 → 0.4), and `TextLabel` with `UIStroke` for every number. Skip jumps straight to the card.

**Map.** Build the lane as a straight run with zone sections of equal length (speed × 0.3 s). Each section: two wall modules, one floor material, one landmark, one colour grade. Keep the centre line clear so the projectile and its trail always read.

## Example

`examples/ZoneLadder.luau` paces zones, finds the current zone with a crossfade blend, and computes luck per zone. `examples/OddsLadder.luau` builds the "1 in N" climb that lands on the rolled odds, flags tier steps for slam words, and gives the slam-word scale curve. Both are tested in `examples/Throw.test.luau`.

```lua
local ZoneLadder = require("./examples/ZoneLadder")
local OddsLadder = require("./examples/OddsLadder")

local zones = ZoneLadder.paced(ZoneNames, ProjectileSpeed, 0.3)
-- every frame during flight
local idx, blend = ZoneLadder.at(zones, Distance, 6)
-- reveal
for _, s in OddsLadder.steps(Tiers, Result.Odds, 24) do
	-- set "1 in s.Odds", colour Tiers[s.Tier].Colour; if s.TierUp then slam Tiers[s.Tier].Word end
end
```

## Make it insane

1. **Zone postcards:** each zone entry stamps a tiny postcard of its landmark into the ribbon for 300 ms, then the name takes over.
2. **Near-miss tier:** the climb hovers one step below the next tier for 3 extra ticks before landing, using the real next threshold, never fake odds.
3. **Trophy wall:** the parked slam words stay on the result card as a row of stickers, one per tier crossed.

## Self-check

- [ ] The result and odds are decided on the server before the throw plays.
- [ ] Each act has one loud element; nothing else animates.
- [ ] Every zone has a name, a palette and a landmark, and the centre lane stays clear.
- [ ] The odds climb lands exactly on the rolled number and only gets slam words at real tier steps.
- [ ] Peak effects (flash, sunburst, confetti) appear only on the top tiers.
- [ ] Skip at any beat jumps to the result card with lighting restored.
- [ ] Readable on a phone at 390 px wide with sound off.
