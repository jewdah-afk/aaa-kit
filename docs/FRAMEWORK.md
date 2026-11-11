# Framework

The standard shape for a Roblox game in this kit. It's a five-layer stack where every feature has one obvious home, every rule is enforced in one place, and the logic that matters runs in headless tests.

The runnable version is [examples/framework-starter](../examples/framework-starter/README.md). Copy it to start a new game.

## The five layers

```
Kit hub            shared/Kit/        utilities only, no game logic, no mutable globals
   ↓
Services           server/Services/   authority: data, validation, rules (one table each)
   ↓
Components         client/Components/ per-instance behaviour bound to a tag, with a Maid
   ↓
Content data       shared/Content/    plain tables: upgrades, unlocks, reset layers, loot
   ↓
Central systems    shared/Systems/    save, economy, automations, unlocks, resets, intensity
```

Each layer matches a level of [HIERARCHY.md](../HIERARCHY.md): the hub is background, services are the world's rules, components are what's on screen, content is what gets shown, and the central systems are the conductor that decides what is loud right now.

## Where things go

| You are adding | It goes in | Never |
|---|---|---|
| A number that affects balance | `shared/Content/*` | Hard-coded in a service or component |
| A new save field | `Systems/Save.TEMPLATE` (reconcile fills old saves) | A one-off migration in a service |
| A per-second effect (income, regen, timers) | An entry in `Systems/Automations` | A new `while true` loop |
| Gated content | A row in `Content/Unlocks` + a client listener | Scattered `if level >= 10` checks |
| A prestige / rebirth | A row in `Content/ResetLayers` | Custom wipe code |
| Server authority over an action | A Service method behind a validated remote | Logic in a LocalScript |
| Something on screen that reacts to data | A Component bound to a CollectionService tag | A loose LocalScript polling values |
| How loud the frame is | `Systems/Intensity` (read its budget) | Each system deciding alone |
| A shared helper (format, guard, signal) | `shared/Kit/*` | Copy-pasted into three scripts |
| Third-party packages | `Packages/` (Wally), untouched | Edited in place |

## Shapes

### Kit hub

One frozen table of shared modules. Everything requires it; it requires nothing game-specific.

```lua
local Kit = require(ReplicatedStorage.Shared.Kit)
Kit.Format.short(1234)        --> "1.23K"
Kit.Guard.count(n, 1000)      --> whole number in [1, 1000]
local maid = Kit.Maid.new()
```

### Service

A plain table with a `name` and an optional `init`, `start`, `playerAdded` and `playerRemoving`. Services register with a `Registry` in dependency order. All `init`s run before any `start`, and `playerRemoving` runs in reverse order.

```lua
-- snippet: shape only
local MyService = { name = "MyService" }
function MyService.init(registry) Data = registry:get("DataService") end
function MyService.start() Remote.OnServerEvent:Connect(onEvent) end
function MyService.playerRemoving(player) perPlayer[player] = nil end
return MyService
```

### Component

Bound to a tag. `construct` stores references and creates `self._maid`. `start` connects everything through the maid. `stop` cleans the maid.

```lua
-- snippet: shape only
function C.construct(inst) local self = setmetatable({}, C); self._maid = Kit.Maid.new(); return self end
function C.start(self) self._maid:give(signal:connect(function(v) ... end)) end
function C.stop(self) self._maid:clean() end
```

### Content module

Returns one frozen table of rows. No requires and no side effects. To add a row, copy one and change its numbers.

### Central system

A pure module (no `game:GetService`) that takes a save table and content rows and returns results. That's what makes it testable in lune.

## Rules (each one exists because something broke)

| Rule | Why |
|---|---|
| **The server validates everything:** type, range, NaN/∞, whitelist keys, ownership, cost, distance, rate. | Client checks are cosmetic; an exploiter calls the remote directly. |
| Reject NaN and infinity: `v ~= v`, `math.abs(v) == math.huge`. | One NaN in a currency field corrupts the save forever. |
| Counts are whole numbers ≥ 1 with a cap. | Negative or fractional counts turn purchases into refunds. |
| Whitelist string keys against a content table. | A free-form key lets a client write any save field. |
| The maid always lives in `self._maid` (lower case). | A capitalisation mismatch leaks every connection silently. |
| Every ModuleScript ends with `return X`. | A missing return breaks every requirer. |
| After copying a file, grep it for the old name. | Copy-paste bugs check the wrong list. |
| No `print` in hot paths (per hit, per frame, per sale). | Output spam costs frames and hides real errors. |
| Admin and debug data go to staff only. | Error and memory dumps leak internals to every client. |
| Big-number strings are parsed before comparing; never use `>` on strings. | `"9" > "10"` is true. |
| Developer products: dedupe by `PurchaseId`; always return a `ProductPurchaseDecision`. | Receipts retry; a missing decision double-grants or never grants. |
| Secrets go through `HttpService:GetSecret`, never a literal. | Source leaks; webhooks get spammed. |
| Saves use a session lock, retries with backoff, and read-only mode after a failed load. | A failed load followed by a save wipes the player. |
| One Heartbeat drives every system's `step`; no system starts its own loop. | Ten loops at ten rates are impossible to profile or pause. |
| Pure logic gets a lune test before it ships. | Studio play-tests miss edge cases; headless tests don't. |

## Where my own repos already do better

- **Render-layer split (cursed-survivors).** Gameplay never depends on FX modules, and FX write through one ownership table (`Blit.CAN`). Kept as the [editable-image](../.claude/skills/editable-image/SKILL.md) standard.
- **Headless tests and goldens (cursed-survivors).** Around 30 suites plus render goldens and checksum chains, so a change that alters a single pixel gets caught. This kit makes tests mandatory for central systems.
- **Save safety (cursed-survivors).** The session-lock save is stronger than plain reconcile; `DataService` in the starter follows it.

## Checks before calling a change done

1. `lune run tools/check_luau.luau <dir>` prints `0 failed` (compile check).
2. `selene <dir>` is clean, or every warning is explained.
3. The starter's or the game's lune tests pass.
4. Grep for `_Maid`, `print(` in hot paths, and modules without `return`.
5. Play test in Studio with zero errors in server and client output. Replay one remote with bad arguments and confirm the server refuses.
