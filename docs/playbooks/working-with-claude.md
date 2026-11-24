# Working with Claude

How we ran long game projects across many Claude sessions (desktop, phone and cloud) without losing work or repeating mistakes.

## Handouts

Every project keeps a `HANDOUT.md` at the repo root that any new session reads first:

1. **"New chat? Paste this first"**: one short paragraph: repo, branch, what to read, the current job.
2. **Start here**: build status as a table (part, where it lives, state).
3. **Latest sections at the top**, each dated, with the owner's quote that triggered it, what was done, what's verified and what isn't.
4. **Rules (non-negotiable)**: the owner's decisions, in their words where possible.
5. **Where everything is**: a table of paths, branches, Figma node ids, tools.
6. **Next steps, in order.**
7. **Gotchas**: every surprise that cost time.

Companion files:
- **`NEXT_CHAT_PROMPT.md`**: the exact text to paste into a fresh session.
- **`PHONE_HANDOUT.md`**: plain text with no markdown symbols, so it pastes cleanly from a phone into a cloud session.

Update the handout after every group of work, then commit and push before the session ends.

## Owner rules, captured as they happen

When the owner corrects something ("the square corners look sweet, we are not using the bubbly style"), write it down at once as a numbered rule, with the date and the quote. Keep the list in the handout and in `CLAUDE.md`. Examples that stuck:

- Hero design first, then build to it.
- Upgrade approved screens, never replace them.
- Screenshots on every visual change, before and after.
- One bright call to action per view.
- QA everything zoomed in before showing it.
- Kid-safe images only, uploaded one at a time.
- Ask before redesigning anything that already exists.

These become the "slip-ups as rules" tables in each repo's `CLAUDE.md` ([FRAMEWORK.md](../FRAMEWORK.md)).

## Specialist agents

Short, sharp subagents in `.claude/agents/` that review instead of build:

| Agent | Job |
|---|---|
| [`ui-qa`](../../.claude/agents/ui-qa.md) | Zoomed-in visual QA of screenshots or pages: clipping, overlap, alignment, outlines, text size, overflow, console errors. Read-only, reports defects with locations and a PASS/FAIL. |
| [`style-guard`](../../.claude/agents/style-guard.md) | Checks a change against the locked style rules. |
| [`visual-hierarchy`](../../.claude/agents/visual-hierarchy.md) | Checks emphasis levels, one CTA, colour semantics, numbers-before-labels. |
| [`roblox-feasibility`](../../.claude/agents/roblox-feasibility.md) | Flags designs Roblox can't render (radial gradients, letter spacing, tall images, vector swooshes) before they're built. |

## Autonomous loop (phone or PC)

A session you can't watch has to catch its own mistakes and never stop to ask. Four pieces, all in the repo, so a cloud session from a phone gets them too:

| Piece | File | What it does |
|---|---|---|
| Setup | [`session_setup.py`](../../tools/hooks/session_setup.py), a `SessionStart` hook | In a cloud session, installs the lune and selene versions pinned in `rokit.toml` when they're missing |
| Check every edit | [`edit_checks.py post`](../../tools/hooks/edit_checks.py), a `PostToolUse` hook | After each `.luau`, `.py` or `.md` write: lune compile, the sibling test, selene, the Markdown Luau blocks. A failure goes straight back to the model |
| Check before finishing | `edit_checks.py stop`, a `Stop` hook | Re-checks every changed file, including edits made through Bash (it reads `git status`), and keeps the turn going until they pass. It blocks once, never in a loop |
| Plan in one shot | [`/spec`](../../.claude/commands/spec.md) and the [task ticket](templates/TASK-TICKET.md) | Turns a vague idea into a file-by-file ticket with every question already answered; `python3 tools/check_ticket.py` rejects a ticket that would stall |

The routine: `/spec <idea>` → read the ticket's `(default)` decisions and veto any → in a fresh session, `Execute docs/specs/<file>` → the report names what ran and what wasn't verified. The ticket's own Load list keeps the executing session from reading the research shelf; `tools/check_context.py` holds `CLAUDE.md` and the skills inside a size budget.

Limits, stated plainly:
- **selene needs its Roblox std.** It downloads it with its own TLS roots, which fail behind a proxy that re-signs HTTPS (the cloud container). Run `selene generate-roblox-std` once on a PC with a direct connection and commit `roblox.yml`; until then the hooks say "selene skipped" instead of failing. Not verified from the cloud, where the download is blocked.
- **Nothing here runs Studio.** Rig code and every Roblox-side pattern are compile-checked only; a session reports "play test pending".
- **Hooks check what changed, not what it affects.** `bash tools/check_all.sh` is still the last step.
- `EDIT_CHECKS=0` turns the hooks off for a session; `EDIT_CHECKS_SELENE=0` skips lint.

## Parallel sessions

- **One branch and worktree per job** (`claude/<game>-ui`, `-vfx`, `-mech`) so sessions don't collide. Merge into an integration branch when each lands.
- **Design agents get a column of a shared board** (see the [Figma playbook](figma-to-roblox-ui.md#2-parallel-design-agents)) and never touch anything outside it.
- **The handout names who owns what** ("another session owns the pickup sprites") so nobody overwrites another session's work.

## Honest reporting

- State what ran, what passed, and what wasn't checked ("not seen in Studio", "not measured on a phone").
- Flag ambiguous rules (e.g. "the footer says X keeps Y, not verified in the data") as **open questions** instead of guessing.
- A pass ends with "Where I stopped" and "Questions for the user".
