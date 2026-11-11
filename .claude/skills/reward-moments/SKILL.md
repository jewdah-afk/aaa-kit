---
name: reward-moments
description: Use when building a payoff moment - chest, egg, crate or capsule opening, RNG reels and roulettes, gacha/summon beams, card or pet reveals, level-up, evolution, rebirth/prestige, big count-ups, daily rewards and purchase confirmations. Triggers on "open", "reveal", "hatch", "spin", "roll", "gacha", "level up", "rebirth", "prestige", "reward screen", "make the reward feel good".
---

# reward-moments

Rewards are tier 1 (HIERARCHY.md §2), the loudest layer. They own the screen for a beat, so they have to be rare, earned, readable and skippable.

## When to use

- Any moment the player receives something: drops, unlocks, level-ups, resets
- Any RNG roll the player watches

**Not for:** ambient pickups during play (use `vfx` with a tier-2/3 budget), shop layout (`ui-hud`).

## Method

1. **Decide first, animate second.** The server rolls the result (weighted, seeded, logged) before any animation plays. The animation only reveals it and never decides it.
2. **Pick the beat lengths by rarity.** Common takes ~1 s in total and Mythic takes 3–4 s (see `RewardSequence` scales). Never make a Common wait like a Mythic.
3. **Sequence attention** (§14): container → item → identity (name, rarity, stats) → delta (what changed in the build) → continue. Each beat starts when the last settles.
4. **Build anticipation honestly.** Reels decelerate with an ease-out and a small overshoot. Show one near-miss (the next tier up beside the landing), never fake odds.
5. **Escalate the tell by tier.** The colour of the charge-up, the beam or the rays tells the tier one beat before the reveal: blue → purple → gold → pink/rainbow.
6. **Dim the world.** At the ceremony rung (3) the world drops to the lowest band and ambient keeps playing quietly. The HUD steps back except for currency.
7. **Count up big numbers.** Exponential roll (`10^(p·k)`), with a ring burst at each tier threshold.
8. **Always skippable.** A press during the sequence jumps to the final state. A press on the final state continues.
9. **Sound**: a rising tone through the anticipation, a hit on the reveal, a sting by tier. Mute-safe: the visuals carry everything.
10. Run the self-check.

## Hierarchy rules it obeys

- §2: tier 1, one at a time.
- §3: ceremony owns rank 7 and covers everything.
- §4: sets the intensity rung to 3 (ceremony) while open.
- §7: the reveal escalates with the rarity ladder.
- §14: reward sequencing with skip.
- §5: currency gold is reserved for the payout number and the continue button.

## Engine notes

**Roblox.** Run the sequence on the client from a server-sent result. Use `TweenService` for UI, a `ViewportFrame` for 3D item spins, `Lighting` `BlurEffect` and `ColorCorrectionEffect` to dim the world (restore them on skip), and `SoundService` for stings. Lock input to the reveal UI with a modal frame; free it on continue.

**Web.** Canvas 2D for reels and rays, WebGL for beams and bloom.

## Example

`examples/Reel.luau` gives a weighted pick, a strip that lands on a pre-decided result with one near-miss, an ease-out-quint landing with overshoot and settle, and tick events. `examples/RewardSequence.luau` is the beat machine with rarity-scaled timing and skip. Both are tested in `examples/Reward.test.luau`. The live gacha beam, portal, reel, chest, card flip, count-up, rebirth and XP-bar level-up are in tier 1 of [effects-gallery.html](../../../examples/web/effects-gallery.html).

```lua
local Reel = require("./examples/Reel")
local RewardSequence = require("./examples/RewardSequence")

-- server: roll and send `result`
local result = Reel.pick(pool, rng:NextNumber())

-- client: build the strip that lands on it, then play
local strip = Reel.strip(pool, result, 40, 34, function() return rng:NextNumber() end)
local seq = RewardSequence.new(result.tier, function(beat)
	-- "container" → shake the crate; "item" → burst; "identity" → name + rarity frame; ...
end)
-- every frame: x = Reel.position(t, 3.2, 34); seq:step(dt)
-- on tap: seq:press()
```

## Make it insane

1. **Tier-escalating beam:** the summon beam climbs visibly through each tier colour, pausing a beat at each threshold it passes. Mythic splits the screen with a portal backdrop and a time-freeze tint.
2. **Physical payout:** coins arc out of the chest under gravity, bounce once, then magnetise into the HUD counter. Each one that lands ticks the odometer (cap at 30 coins; the rest arrive as one bundle).
3. **Rebirth implosion:** the runaway number collapses into a point, a shockwave resets the screen to calm, and the new multiplier stamps in with a 6-frame hit-stop.

## Self-check

- [ ] The result is decided on the server before the animation starts.
- [ ] Common reveals are short (≤ ~1 s); Mythic gets the full ceremony.
- [ ] Skip works at every beat and leaves the world restored (blur, colour, input).
- [ ] The near-miss is real data, not a fake higher result.
- [ ] Beats run in order: container → item → identity → delta → continue.
- [ ] Only one tier-1 moment at a time; extra rewards queue or merge.
- [ ] Readable on a phone with sound off.
