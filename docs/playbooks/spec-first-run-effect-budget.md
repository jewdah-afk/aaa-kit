# First run of a /spec ticket: EffectBudget

The first time a fresh session executed a `/spec` ticket ([effect-budget](../specs/2026-11-24-effect-budget.md)) start to finish. It worked: no questions asked, every edit anchor matched once, `bash tools/check_all.sh` ended with `all checks passed`. These are the gaps it showed in the harness.

## What worked

- The ticket's decisions table left nothing to ask. Edit anchors were exact, so the Rig edits applied with no fix-ups.
- Per-file Checks (lune test, `check_luau`, `check_skills`) caught nothing wrong because the spec was precise; they also gave a fast signal before the slow full run.

## Gaps

| Gap | What happened | Fix to make |
|---|---|---|
| Session branch differs from the ticket's branch | The ticket named `claude/affectionate-maxwell-2k22l0`; the session was pinned to another branch that lacked the spec, `Rig.luau` and `Timeline.luau`. The spec had to be found in git history and the ticket's branch merged in. | `/spec` writes the branch the session will actually use, or the launcher starts the session on the ticket's branch. A ticket should also say "if this file is missing, run `git fetch` and look on branch X". |
| Hooks only exist on the newer branch | Until that merge, the SessionStart install, per-edit checks and Stop check did not run, so lune was missing and had to be fetched by hand. | Merge the harness commits to `main` so every session branch starts with them. |
| `check_all.sh` is slow | It takes over two minutes and exceeds the shell's default timeout. | Run it in the background, or add a `--fast` mode that skips the web examples and flash checks for per-ticket runs. |
| "Read nothing else" vs. a missing file | Section 0 forbids opening anything outside the ticket's Load list, but the ticket itself was not in the working tree. | Same fix as the branch gap. |

## Still not verified

Studio play test and a real device measurement. The 6-slot and 400-particle caps are start values, not tuned. See the ticket's section 9.
