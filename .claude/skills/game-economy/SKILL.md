---
name: game-economy
description: Use for currencies, prices and progression - upgrade cost curves, income and multipliers, big numbers past 1e308, buy-max and buy-all maths, prestige/rebirth layers, offline earnings, automations, unlock pacing, sinks and faucets, shop pricing, and balance kept in data rather than code. Triggers on "economy", "balance", "upgrade cost", "formula", "incremental", "idle", "rebirth", "prestige", "big numbers", "offline earnings", "pacing", "too grindy", "too easy".
---

# game-economy

Balance lives in data. The maths lives in pure, tested functions. Services only validate and apply.

## When to use

- Designing or tuning costs, income, multipliers, resets
- Any number that grows past what a double can hold
- "It feels too grindy / too fast" complaints

**Not for:** how numbers look on screen (`ui-hud`) or purchase receipts and remotes (`roblox-luau-standards`).

## Method

1. **Write the loop as faucets and sinks.** List every source (tap, passive, rewards, offline) and every sink (upgrades, consumables, resets). An economy without sinks inflates.
2. **Pick curves per row:** geometric for upgrade costs (growth 1.07–1.25), polynomial for XP, soft caps for stats, sublinear prestige payouts (`k · total^0.5`).
3. **Put the numbers in content rows** (`Content/Upgrades.luau`), never in a service.
4. **Use closed forms.** Buy-n cost = `base · r^L · (r^n − 1)/(r − 1)`; max affordable via a log formula plus a boundary check. No loops over levels.
5. **Check pacing.** Simulate a player (always buying the best payback) and plot the wait time to the next purchase. Flag any jump > 2× between consecutive waits (`Curves.pacing`).
6. **Prestige.** The first reset should come at 15–30 min of play. Each layer should multiply the speed of the previous run by ~2–5×.
7. **Big numbers.** Plain numbers below 9e15. Past that, use `EternityNum` (string saves, `lbencode` for leaderboards). Never compare strings with `>`.
8. **Offline.** Cap the hours (e.g. 8) and reduce the rate (e.g. 50 %). Show the total in a reward moment on return.
9. **Automations.** Every per-second effect is one entry in the central Automations system with a catch-up cap.
10. Run the self-check.

## Hierarchy rules it obeys

- §5: currency is gold and only currency is gold.
- §14: the payout of a reset or offline return is a reward moment with sequencing.
- §15: content data → central systems → services; balance never lives in code.

## Engine notes

**Roblox.**

- Server owns all currency. Remotes request purchases and never send amounts.
- Saves store numbers below 9e15 as numbers and larger ones as `EternityNum` strings.
- Leaderboards: `OrderedDataStore` needs integers, so encode with `EternityNum.lbencode`.
- Developer products: see `roblox-luau-standards/examples/Receipts.luau`.

**Web.** The same formulas in JS; `break_eternity.js` for big numbers.

## Example

- `examples/Curves.luau`: geometric, polynomial, soft cap, prestige, payback, offline and a pacing checker that finds walls (tested in `examples/Curves.test.luau`).
- `../../../examples/framework-starter/src/shared/Systems/Economy.luau`: closed-form buy-n and max-affordable plus a validated `buy`.
- `../../../examples/bignum/EternityNum.luau`: big numbers with `geomSum` and `geomAfford`.

```lua
local Curves = require("./examples/Curves")
-- does this upgrade table have a wall in the first 60 levels?
local worst, at = Curves.pacing(function(level)
	return Curves.geometric(25, 1.17, level)
end, function(level)
	return 1 + 0.8 * level                    -- income per second at that level
end, 60)
if worst > 2 then
	warn(`pacing wall at level {at}: wait jumps {worst}x`)
end
```

## Make it insane

1. **Living price tags:** prices tick up in real time with a small "demand" curve when many players on the server buy the same upgrade, then cool off. It's a server-wide sink that creates moments.
2. **Prestige trees:** each reset layer unlocks a node graph whose nodes are content rows (cost, effect, prerequisites), visualised as an L-system tree that grows as you buy.
3. **Algorithmic currencies:** the second currency is earned by solving a tiny procedural pattern (a reaction-diffusion bloom you harvest at the right moment), so the economy has skill expression, not just waiting.

## Self-check

- [ ] Every number is in a content row; services hold none.
- [ ] Buy-n and max-affordable are closed form and tested at the boundaries.
- [ ] Pacing simulated; no wait jump > 2× without an intentional gate.
- [ ] Sinks exist for every faucet.
- [ ] Big numbers never compared as strings; saves round-trip losslessly.
- [ ] The server is the only place currency changes.
