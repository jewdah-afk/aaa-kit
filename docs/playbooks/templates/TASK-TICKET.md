# TICKET: <what it adds, in six words or fewer>

> One session, one shot. `/spec` writes this file from a vague idea; a fresh session executes it with no other context. Every line is a decision already made, so the executor never has to ask. Validate with `python3 tools/check_ticket.py <this file>`.

## 0. How to execute

1. Read this file and the paths under "4. Load". Nothing else: do not open `docs/research/` or any skill that is not named there.
2. Do the rows of "5. Files" in order. After each row run its Check. If a Check fails, fix it (three tries at most), then stop and report.
3. Never ask a question. Anything this ticket does not settle: take the safest option and list it under Deviations in the report.
4. Stay inside "5. Files". Touch nothing in "9. Out of scope".
5. Finish with the commands in "8. Acceptance", then write the report in the shape of "10. Report".
6. Commit on the branch named in "3. Constraints" with a message that says what changed. Open no pull request unless the ticket says so.

## 1. Goal

<One sentence: what exists afterwards that does not exist now.>

- Idea as given: "<the user's words, verbatim>"
- Done looks like: <what a person sees or runs to know it worked>

## 2. Decisions

Every question the idea raised, answered. `(default)` marks a choice made without the owner, who can veto it.

| Question | Decision | Why |
|---|---|---|
| <the question> | <the answer> (default) | <one reason> |

## 3. Constraints

- Repo and branch: <repo>, <branch>
- Engine and platform: <Roblox / Luau, phone first (390x844 portrait, 844x390 landscape), 44 px touch targets>
- Hierarchy: <tier from HIERARCHY.md section 2, pixel owner, the rungs it appears on>
- Budget: <frame ms, particle count, bytes>
- Uses nothing new: <the existing modules and libraries it may use>

## 4. Load

At most six paths, and at most one under `docs/research/`. Skills by name: <skill>.

- `<path>` - <why this file and not another>

## 5. Files

| # | Action | Path | Change | Check |
|---|---|---|---|---|
| 1 | create | `<path>` | <what it holds, in one line> | `<command that proves it>` |

Actions: `create`, `edit`, `delete`, `run` (the Path is then a command). At most 12 rows; more means two tickets. `edit` and `delete` paths must exist.

## 6. Per-file spec

One `### n.` subsection for every `create` and `edit` row, named by its number.

### 1. <path>

<Exact contents or signatures, the data tables with their numbers, the edge cases, and the names to grep for after a copy.>

## 7. Phases

<For a VFX or a sequence: a table of phase, frames, layers and gate (the vfx skill's five phases). Otherwise write "N/A: not a timed effect.">

## 8. Acceptance

```bash
<every command, in order>
```

Expect: <the exact line each one prints>

## 9. Out of scope

- <the thing someone will be tempted to do, and does not>

## 10. Report

Reply in this shape, and nothing longer:

- **Done:** what changed, by file.
- **Verified:** each command run and its result.
- **Not verified:** what was not checked and why (Studio play test, a real phone, a device measurement).
- **Deviations:** every point settled by a default.
- **Next:** the very next step.
