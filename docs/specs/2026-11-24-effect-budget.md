# TICKET: EffectBudget caps concurrent effects

> One session, one shot. `/spec` writes this file from a vague idea; a fresh session executes it with no other context. Every line is a decision already made, so the executor never has to ask. Validate with `python3 tools/check_ticket.py <this file>`.

## 0. How to execute

1. Read this file and the paths under "4. Load". Nothing else: do not open `docs/research/` or any skill that is not named there.
2. Do the rows of "5. Files" in order. After each row run its Check. If a Check fails, fix it (three tries at most), then stop and report.
3. Never ask a question. Anything this ticket does not settle: take the safest option and list it under Deviations in the report.
4. Stay inside "5. Files". Touch nothing in "9. Out of scope".
5. Finish with the commands in "8. Acceptance", then write the report in the shape of "10. Report".
6. Commit on the branch named in "3. Constraints" with a message that says what changed. Open no pull request unless the ticket says so.

## 1. Goal

A pure, lune-tested `EffectBudget` module decides whether a new effect may start, and `Rig.play` uses it in place of its crude `MAX_ACTIVE` counter, so many effects at once are capped by both slot count and live particles.

- Idea as given: "make sure lots of effects at once don't pile up and tank the frame"
- Done looks like: `lune run .claude/skills/vfx/examples/EffectBudget.test.luau` passes, `Rig.luau` no longer mentions `MAX_ACTIVE`, and the vfx skill names the 6-slot and 400-particle caps.

## 2. Decisions

| Question | Decision | Why |
|---|---|---|
| What makes a frame "tank" | Two limits: the number of friendly effects running and the live particles across all effects | Cost is covered area and layers, which particle count tracks; a count of effects alone misses one huge effect |
| How many friendly effects at once | 6 (default) | HIERARCHY.md section 9 gives 6 decoration slots in the world as the start value |
| Particle cap | 400 live particles across all running effects (default) | Three of the larger templates fit (VortexSingularity plans 125 at full rung, VoidRings 84, CrystalSlash 67); a start value, tune in play, not measured on a phone |
| A friendly effect arrives when full | It is skipped; nothing is queued and no older effect is stopped | HIERARCHY.md section 9: decoration is skipped, never delayed |
| A hostile effect arrives when full | It always plays. If the particle cap is exceeded, the oldest friendly effects are stopped until the total fits or none are left | A hostile telegraph is a critical cue (sections 9 and 10), and stopping the oldest friendly effect hurts least |
| Which friendly effect is oldest | Smallest start time, then smallest id (default) | A deterministic order that tests can assert |
| Is a hostile effect ever stopped | No | It would hide a threat |
| Does tier or rarity change priority | No (default) | Smaller than a priority scheme; the rung already scales counts through `Blueprint.plan` |
| Where does the state live | A module-level state in `Rig.luau`, one per client | Effects are built on the client; nothing is shared with the server |
| Pure or Roblox | `EffectBudget.luau` is pure Luau with no Instance and no clock; the caller passes `now` | It stays testable in lune |
| An effect larger than the cap | A friendly one is never admitted; a hostile one always is | A friendly effect that cannot fit would stall the others |

## 3. Constraints

- Repo and branch: aaa-kit, claude/affectionate-maxwell-2k22l0
- Engine and platform: Roblox / Luau, phone first; this ticket adds pure logic and one Roblox call site
- Hierarchy: no new visual; it enforces HIERARCHY.md sections 9 and 10 for every effect at every rung
- Budget: `request` and `release` run once per effect start and stop, never per frame, and allocate at most one small table
- Uses nothing new: `Blueprint.plan`, `Timeline` and the existing Rig; no library

## 4. Load

Skill by name: vfx.

- `.claude/skills/vfx/examples/Rig.luau` - the file to edit; `Rig.play` is near the end
- `.claude/skills/vfx/examples/Timeline.test.luau` - the style to copy for the new test
- `.claude/skills/vfx/SKILL.md` - method step 8, the Example paragraph and the Self-check
- `HIERARCHY.md` - section 9 only (search for "## 9.")

## 5. Files

| # | Action | Path | Change | Check |
|---|---|---|---|---|
| 1 | create | `.claude/skills/vfx/examples/EffectBudget.luau` | the pure budget module | `lune run tools/check_luau.luau .claude/skills/vfx/examples/EffectBudget.luau` |
| 2 | create | `.claude/skills/vfx/examples/EffectBudget.test.luau` | its tests | `lune run .claude/skills/vfx/examples/EffectBudget.test.luau` |
| 3 | edit | `.claude/skills/vfx/examples/Rig.luau` | replace the `active` counter with the budget | `lune run tools/check_luau.luau .claude/skills/vfx/examples/Rig.luau` |
| 4 | edit | `.claude/skills/vfx/SKILL.md` | name the caps, the module and a self-check line | `python3 tools/check_skills.py` |
| 5 | run | `bash tools/check_all.sh` | everything still passes | the last line of its output |

## 6. Per-file spec

### 1. `.claude/skills/vfx/examples/EffectBudget.luau`

Start with `--!strict`, a header comment that says what it is (how many effects may run at once, HIERARCHY.md sections 9 and 10; skip, never queue; pure, the caller passes `now`) and end with `return EffectBudget`. Tabs, camelCase locals, PascalCase types, UPPER_SNAKE constants.

Constants: `EffectBudget.SLOTS = 6` and `EffectBudget.PARTICLE_CAP = 400`.

Types:

```text
export type Entry = { particles: number, hostile: boolean, startedAt: number }
export type State = { slots: number, particleCap: number, entries: { [number]: Entry } }
export type Stats = { friendly: number, hostile: number, particles: number }
```

Functions, exactly these signatures:

```text
EffectBudget.new(slots: number?, particleCap: number?): State
EffectBudget.request(state: State, id: number, particles: number, hostile: boolean, now: number): (boolean, { number })
EffectBudget.release(state: State, id: number)
EffectBudget.stats(state: State): Stats
```

`new` uses the two constants when an argument is nil and starts with an empty `entries`.

`request` follows this order:

1. `assert(particles >= 0, "particles must be zero or more")`. A NaN fails the assert too.
2. If `state.entries[id]` exists, return `true, {}` and change nothing.
3. Read `stats(state)`. A friendly request (`hostile == false`) is admitted only when `friendly < state.slots` and `particles + total <= state.particleCap`. Otherwise return `false, {}` and change nothing.
4. A hostile request is always admitted. After adding it, while `total > state.particleCap` and a friendly entry exists, remove the oldest friendly entry (smallest `startedAt`, then smallest id) and append its id to the evicted list.
5. Store `{ particles = particles, hostile = hostile, startedAt = now }` under `id` and return `true` and the evicted list (an empty table when none).

`release` removes the entry when present and does nothing otherwise. `stats` counts friendly and hostile entries and sums particles.

### 2. `.claude/skills/vfx/examples/EffectBudget.test.luau`

`--!strict`, `local t = require("../../../../tools/lib/t")`, `local EffectBudget = require("./EffectBudget")`, end with `t.done()`. Write one `t.eq` or `t.ok` per line below, each with a name that states the rule.

| Case | Setup | Expect |
|---|---|---|
| Defaults | `EffectBudget.new()` | `slots == 6`, `particleCap == 400` |
| Six friendly fit | ids 1 to 6, 50 particles each, friendly | all admitted; stats friendly 6, particles 300 |
| The seventh is skipped | id 7, 50 particles | `false` with an empty evict list; stats unchanged |
| A skip is not queued | release id 1, then check stats | friendly 5; id 7 is not admitted without a new request |
| A release frees a slot | request id 7 again | admitted |
| Particle cap, boundary | new state; friendly 150, 150, then 120, then 100 | 120 is skipped (420 over 400); 100 is admitted (400 equals the cap) |
| Oversized friendly | friendly 500 on an empty state | `false` |
| Hostile ignores slots | six friendly, then a hostile of 10 | admitted; stats hostile 1 |
| Hostile evicts the oldest | friendly id 1 (now 0, 150), id 2 (now 1, 150), id 3 (now 2, 90); hostile id 9 (now 3, 160) | admitted, evicted `{ 1 }`; stats friendly 2, hostile 1, particles 400 |
| Hostile evicts as many as needed | same three friendly; hostile of 300 | evicted `{ 1, 2 }` |
| A hostile effect is never evicted | three hostile of 200 each, then a friendly of 1 | all hostile admitted (total 600), evicted lists empty; the friendly is skipped |
| Tie on time | friendly ids 5 and 2 both with now 0; hostile forces one eviction | id 2 is evicted |
| Idempotent request | request the same id twice | second returns `true` with an empty list; stats equal |
| Release is safe | release an unknown id, then release a real id twice | no error; counts never go negative |
| Evicted ids are gone | after an eviction, `release` the evicted id | no error; stats unchanged |
| Zero-particle friendly | 0 particles | takes a slot, adds no particles |
| Bad input | `pcall` a request with -1 particles | the call fails |

### 3. `.claude/skills/vfx/examples/Rig.luau`

Make exactly these edits and no others:

1. Under `local Timeline = require("./Timeline")` add `local EffectBudget = require("./EffectBudget")`.
2. Delete the line `Rig.MAX_ACTIVE = 8 ...`. Replace the line `local active = 0` with these three lines:

```text
local budgetState = EffectBudget.new() -- 6 friendly slots, 400 live particles: start values, tune in play
local nextId = 0
local stoppers: { [number]: () -> () } = {}
```

3. In `Rig.play`, replace the block that starts at `if active >= Rig.MAX_ACTIVE and not bp.hostile then` and ends with the line `local plan = Blueprint.plan(bp, budget)` by:

```text
	local plan = Blueprint.plan(bp, budget)
	nextId += 1
	local id = nextId
	local admitted, evicted = EffectBudget.request(budgetState, id, plan.particles, bp.hostile, os.clock())
	if not admitted then
		return nil -- skipped, never queued (HIERARCHY.md section 9)
	end
	for _, other in evicted do
		local stop = stoppers[other]
		if stop then
			stop() -- a hostile cue needs the room: the oldest friendly effects end first
		end
	end
```

4. Delete the line `active += 1`.
5. In `finish`, replace `active -= 1` with `EffectBudget.release(budgetState, id)` and, on the next line, `stoppers[id] = nil`.
6. Directly after the `finish` function ends (before `conn = RunService.PreRender:Connect`), add `stoppers[id] = finish`.
7. After `Rig.play` (before `return Rig`) add:

```text
-- Live effects and particles, for a debug overlay and the budget measurements in the vfx self-check.
function Rig.stats(): EffectBudget.Stats
	return EffectBudget.stats(budgetState)
end
```

8. In the header comment of `Rig.luau`, add one line after the "Patterns it follows" paragraph: `-- Concurrency: EffectBudget caps friendly effects at 6 and live particles at 400; a hostile effect always plays.`

After editing, `grep -rn "MAX_ACTIVE" .claude` must print nothing, and `grep -nE "\bactive\b" .claude/skills/vfx/examples/Rig.luau` must print nothing.

### 4. `.claude/skills/vfx/SKILL.md`

Three edits, the rest unchanged:

1. In Method step 8, replace `Decoration slots: 6 in the world; skip extras, never delay them.` with `Decoration slots: 6 in the world and 400 live particles across all effects (`examples/EffectBudget.luau`, applied by `Rig.play`); skip extras, never delay them, and let a hostile effect evict the oldest friendly ones.`
2. In the Example paragraph, after `Flipbook.luau` (procedural sheets), add `EffectBudget.luau` (slots and particle cap), and add `EffectBudget.test.luau` to the list of tests.
3. In Self-check, add the bullet `- [ ] Effects start through Rig.play, so the slot and particle budget applies; a skipped effect is not queued.` directly above the Studio play test bullet.

## 7. Phases

N/A: not a timed effect.

## 8. Acceptance

```bash
lune run .claude/skills/vfx/examples/EffectBudget.test.luau
lune run tools/check_luau.luau .claude/skills/vfx/examples/Rig.luau
python3 tools/check_skills.py
bash tools/check_all.sh
```

Expect: `0 failed` from the first, `1 checked, 0 failed` from the second, `0 errors` from the third and `all checks passed` as the last line of the fourth.

## 9. Out of scope

- Priority by tier or rarity, and distance or camera culling
- Scaling the caps by device quality or by the intensity rung (the rung already scales counts in `Blueprint.plan`)
- Changing `Blueprint.luau`, `Timeline.luau` or the three templates
- Studio play testing and measuring the real frame cost (not possible from the cloud: say so under Not verified)
- Cleaning up a slot if building an effect throws part-way

## 10. Report

Reply in this shape, and nothing longer:

- **Done:** what changed, by file.
- **Verified:** each command run and its result.
- **Not verified:** what was not checked and why (Studio play test, a real phone, a device measurement).
- **Deviations:** every point settled by a default.
- **Next:** the very next step.
