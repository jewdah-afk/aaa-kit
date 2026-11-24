# TICKET: EmberSlash fire variant of the slash template

> One session, one shot. `/spec` writes this file from a vague idea; a fresh session executes it with no other context. Every line is a decision already made, so the executor never has to ask. Validate with `python3 tools/check_ticket.py <this file>`.

## 0. How to execute

1. Read this file and the paths under "4. Load". Nothing else: do not open `docs/research/` or any skill that is not named there.
2. Do the rows of "5. Files" in order. After each row run its Check. If a Check fails, fix it (three tries at most), then stop and report.
3. Never ask a question. Anything this ticket does not settle: take the safest option and list it under Deviations in the report.
4. Stay inside "5. Files". Touch nothing in "9. Out of scope".
5. Finish with the commands in "8. Acceptance", then write the report in the shape of "10. Report".
6. Commit on the branch named in "3. Constraints" with a message that says what changed. Open no pull request unless the ticket says so.

## 1. Goal

The vfx skill ships a fourth reference template, EmberSlash: the CrystalSlash blueprint recoloured and renamed as a fire slash, valid at every rung.

- Idea as given: "make a fire version of the slash"
- Done looks like: `lune run .claude/skills/vfx/examples/Blueprint.test.luau` passes with EmberSlash in its template list, and the vfx skill's template table has a row for it.

## 2. Decisions

| Question | Decision | Why |
|---|---|---|
| Which slash is "the slash" | CrystalSlash, the only directional template (default) | A slash needs a direction and a micro-telegraph; it has both |
| New file or a theme switch on CrystalSlash | A new blueprint file | Blueprints are plain data and the validator checks each file as a whole |
| Palette | Ember orange, hot yellow-white, charred brown, ash grey (default) | Orange is not red, and red is reserved for hostile effects (HIERARCHY.md section 5) |
| Timing and counts | Unchanged from CrystalSlash | Its numbers already pass the standard; retune in play |
| Friendly or hostile | Friendly | The idea names no threat |
| New assets | None: same mesh template and texture roles | Assets are the owner's to supply |
| Tests | Add it to the `templates` list so it is validated and planned at all six rungs | A template nobody tests rots |

## 3. Constraints

- Repo and branch: aaa-kit, feat/ember-slash
- Engine and platform: Roblox / Luau, phone first (390x844 portrait, 844x390 landscape)
- Hierarchy: tier 2 for combat layers and tier 4 for Dissipation, as CrystalSlash; appears at every rung
- Budget: at most 100 particles at rung 5, as CrystalSlash
- Uses nothing new: `Blueprint.luau` only; no new library

## 4. Load

Skill by name: vfx.

- `.claude/skills/vfx/examples/blueprints/CrystalSlash.luau` - the file to copy
- `.claude/skills/vfx/examples/Blueprint.test.luau` - where the template list lives
- `.claude/skills/vfx/SKILL.md` - the Reference templates table

## 5. Files

| # | Action | Path | Change | Check |
|---|---|---|---|---|
| 1 | create | `.claude/skills/vfx/examples/blueprints/EmberSlash.luau` | CrystalSlash copied, renamed and recoloured | `lune run tools/check_luau.luau .claude/skills/vfx/examples/blueprints/EmberSlash.luau` |
| 2 | edit | `.claude/skills/vfx/examples/Blueprint.test.luau` | require EmberSlash and add it to `templates` | `lune run .claude/skills/vfx/examples/Blueprint.test.luau` |
| 3 | edit | `.claude/skills/vfx/SKILL.md` | one row in the Reference templates table | `python3 tools/check_skills.py` |
| 4 | run | `bash tools/check_all.sh` | everything still passes | the last line of its output |

## 6. Per-file spec

### 1. `.claude/skills/vfx/examples/blueprints/EmberSlash.luau`

Copy `CrystalSlash.luau`, then apply exactly these changes. Frames, counts, peaks, tiers, gates and `props` keys do not change.

| In CrystalSlash | In EmberSlash |
|---|---|
| `local CrystalSlash`, `name = "CrystalSlash"`, `return CrystalSlash` | `EmberSlash` |
| header comment | Rewrite as a fire slash; keep the frame table and the assets line |
| `ICE = { 0.55, 0.90, 1.0 }` | `EMBER = { 1.0, 0.55, 0.12 }` |
| `WHITE = { 0.92, 0.98, 1.0 }` | `HOT = { 1.0, 0.93, 0.75 }` |
| `DEEP_ICE = { 0.12, 0.30, 0.42 }` | `CHAR = { 0.30, 0.10, 0.04 }` |
| `color = { 0.55, 0.70, 0.80 }` on ColdMist | `ASH = { 0.30, 0.24, 0.20 }`, declared as a local like the others |
| every use of `ICE`, `WHITE`, `DEEP_ICE` | `EMBER`, `HOT`, `CHAR` |
| layer `FrostRing` | `HeatRing` |
| layer `ColdMist` | `SmokePlume`, `texture = "smoke_puff"` |
| layer `CrystalDust` | `FallingEmbers` |
| layer `ShardFan` | `SparkFan` |
| layer `ShardStreaks` | `EmberStreaks` |

After the copy, grep the new file for `Crystal`, `Frost`, `Cold`, `Ice`, `ICE` and `Shard`: there must be no match. Keep the asset roles `shard` and `crack_line` as they are.

### 2. `.claude/skills/vfx/examples/Blueprint.test.luau`

Add `local EmberSlash = require("./blueprints/EmberSlash")` under the CrystalSlash require, and change the list to `local templates = { VoidRings, VortexSingularity, CrystalSlash, EmberSlash }`. Change nothing else.

### 3. `.claude/skills/vfx/SKILL.md`

In the Reference templates table add this row directly under the CrystalSlash row:

```text
| `examples/blueprints/EmberSlash.luau` | Directional fire slash | 72, hit 6 | Directional. CrystalSlash in embers: heat ring, smoke plume, falling embers |
```

## 7. Phases

Unchanged from CrystalSlash (60 fps frames, hit on frame 6, 72 frames in all).

| Phase | Frames | Layers | Gate |
|---|---|---|---|
| Telegraph | 0-5 | AimGlint, ChargeSpark | none |
| Core | 6-11 | SlashFlash, FlashStar | none |
| Ground | 6-70 | LineCrack, HeatRing | none |
| Secondary | 6-24 | SparkFan, EmberStreaks | none |
| Dissipation | 14-72 | SmokePlume, FallingEmbers | `ambient` |

## 8. Acceptance

```bash
lune run .claude/skills/vfx/examples/Blueprint.test.luau
python3 tools/check_skills.py
bash tools/check_all.sh
```

Expect: `0 failed` from the first, `0 errors` from the second and `all checks passed` as the last line of the third.

## 9. Out of scope

- Changing CrystalSlash, VoidRings, VortexSingularity or `Blueprint.luau`
- New texture roles or mesh templates
- Studio play testing (not possible from the cloud; say so under Not verified)

## 10. Report

Reply in this shape, and nothing longer:

- **Done:** what changed, by file.
- **Verified:** each command run and its result.
- **Not verified:** what was not checked and why (Studio play test, a real phone, a device measurement).
- **Deviations:** every point settled by a default.
- **Next:** the very next step.
