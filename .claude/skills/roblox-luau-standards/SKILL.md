---
name: roblox-luau-standards
description: Use for any Roblox Luau code - project structure, where new code goes, services/components/content/central systems, remotes and server validation, debounce and rate limits, Maid cleanup, saves and session locking, developer products and receipts, BigNum rules, performance in hot paths, lune tests and compile checks. Triggers on "Roblox", "Luau", "script", "service", "remote", "RemoteEvent", "DataStore", "ProfileStore", "save data", "exploit", "receipt", "developer product", "where should this go".
---

# roblox-luau-standards

Every Roblox game in this kit uses the five-layer framework in [docs/FRAMEWORK.md](../../../docs/FRAMEWORK.md): Kit hub → services → components → content data → central systems. This skill is the procedure for writing code inside it.

## When to use

- Writing or reviewing any Luau
- Adding a feature and deciding where it lives
- Anything touching remotes, saves, purchases or money

**Not for:** visual decisions (other skills) or pure maths with no Roblox API (it still follows the style rules here).

## Method

1. **Find the home** with the "where things go" table:

| Adding | Goes in |
|---|---|
| A balance number | `shared/Content/*` |
| A save field | `Systems/Save.TEMPLATE` |
| A per-second effect | `Systems/Automations` entry |
| Gating | `Content/Unlocks` row |
| A reset | `Content/ResetLayers` row |
| Authority over an action | A Service method + validated remote |
| Something on screen reacting to data | A tagged Component |
| A shared helper | `shared/Kit/*` |

2. **Copy the closest template** (service, component or content row) from the [framework starter](../../../examples/framework-starter/README.md), then grep the copy for the old name.
3. **Validate every remote argument** on the server, in this order: shape (type, whitelist key, whole-number count with a cap, reject NaN/∞) → rate (`Kit.Guard.rate`) → state (ownership, cost, distance, cooldown) from the server's own data.
4. **Clean up.** Per-player tables are cleared in `playerRemoving`. Connections go in `self._maid` (lower case).
5. **Keep hot paths quiet.** No `print`, no table allocation per frame and no `FindFirstChild` chains in loops. Cache references in `init`.
6. **Test.** Pure logic gets a lune test (`lune run …test.luau`); everything compiles (`lune run tools/check_luau.luau <dir>`).
7. **Studio pass** (when available): zero errors in server and client output. Replay a remote with bad arguments and confirm it's refused.
8. Run the self-check.

## Hierarchy rules it obeys

- §15: framework layers mirror the hierarchy.
- §4: the intensity ladder is a central system (`Systems/Intensity`); visual code reads its budget and never decides loudness alone.

## Engine notes

- **String requires** (`require("./X")`, `require("@self/X")`) for shared pure modules so lune can run them; instance requires are fine in server and client boot code.
- **Saves:** session lock, retries with exponential backoff, read-only after a failed load, reconcile against the template, autosave plus `BindToClose`. ProfileStore gives you most of this; keep the rules either way.
- **Receipts:** dedupe by `PurchaseId` persisted in the save. Return `NotProcessedYet` when data isn't loaded or the save fails, and `PurchaseGranted` for duplicates.
- **Secrets:** `HttpService:GetSecret("NAME")`, never a literal. Webhook URLs are secrets.
- **Big numbers:** compare with the library (`EN.me`, `EN.leeq`), never `>` on strings.
- **Debounce:** server-side per player (`Guard.rate`). Client debounce is UX only.
- **Admin data** (errors, memory, logs) goes to staff only.

## Example

The complete example is the [framework starter](../../../examples/framework-starter/README.md): `EconomyService` (validated remotes), `DataService` (session-locked saves), `CoinCounter` (tagged component with a Maid) and 48 lune tests. `examples/Receipts.luau` adds a receipt handler that can't double-grant (tested in `examples/Receipts.test.luau`).

A validated remote handler, end to end:

```lua
--!strict
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Kit = require(ReplicatedStorage.Shared.Kit)
local Upgrades = require(ReplicatedStorage.Shared.Content.Upgrades)

local MAX_BUY = 1000
local limit = Kit.Guard.rate(0.2)

local function onBuy(player: Player, id: unknown, n: unknown): { ok: boolean, reason: string? }
	if not Kit.Guard.oneOf(id, Upgrades) or not Kit.Guard.count(n, MAX_BUY) then
		return { ok = false, reason = "bad request" }   -- shape
	end
	if not limit(player) then
		return { ok = false, reason = "slow down" }     -- rate
	end
	-- state: read the server's save, check cost and unlocks, then mutate (see Economy.buy)
	return { ok = true }
end

return onBuy
```

## Make it insane

1. **Exploit replay harness:** a dev-only command that fires every remote with a fuzzed argument set (NaN, ∞, negatives, huge strings, wrong types, other players' ids) and reports any that weren't refused.
2. **Deterministic sim core:** gameplay runs as a pure step function `(state, inputs, dt) → state`, so lune can replay recorded sessions bit-for-bit and goldens catch any behaviour change.
3. **Hot-reload content:** content rows load from a ModuleScript the server re-requires on a dev command, so balance changes apply live in Studio without restarting.

## Self-check

- [ ] The code is in the layer the table says.
- [ ] Every remote validates shape → rate → state on the server.
- [ ] No NaN/∞, negative, fractional or uncapped counts reach data.
- [ ] Every maid is `self._maid`; every per-player table is cleared on leave.
- [ ] No `print` in hot paths; every module ends with `return`.
- [ ] Receipts dedupe by `PurchaseId`; saves are session-locked.
- [ ] `lune run tools/check_luau.luau` reports 0 failed; pure logic has tests.
