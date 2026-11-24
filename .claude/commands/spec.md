---
description: Turn a vague idea into a strict, file-by-file task ticket that a fresh session can execute in one shot
argument-hint: the idea, in any words ("make a fire version of the slash")
---

Write a task ticket for this idea: $ARGUMENTS

If the idea above is empty, reply with the usage line `/spec <the idea>` and stop. Otherwise do not ask the user anything: every unknown becomes a decision you make and record.

1. **Read little.** Read `CLAUDE.md`, then only the skill that matches the idea (the router table in `CLAUDE.md` names it) and the one existing file closest to what is wanted, so the ticket can say "copy this". Do not open `docs/research/` unless the skill's text names a chapter you need, and then only that one.
2. **Copy the template.** `docs/playbooks/templates/TASK-TICKET.md` is the layout; `docs/playbooks/templates/TASK-TICKET.example.md` is a finished one. Save yours as `docs/specs/YYYY-MM-DD-<slug>.md` (create the folder if it is missing), and keep every section, in order.
3. **Settle every question.** The idea is vague on purpose. For each thing it leaves open (which file, what palette, how many, friendly or hostile, which rung, what to leave alone) write a row in "2. Decisions" with the answer and one reason, and mark it `(default)` when it is your choice. Pick the option that is smaller, safer and already in the repo. The ticket must contain no question marks, no `<placeholders>` and no TBD.
4. **Make the plan file by file.** One row per file in "5. Files", in the order to do them, with a Check that is a real command and the output to expect. Verify every `edit` path exists (use Glob or `ls`), and say in "6. Per-file spec" exactly what goes in each file: signatures, tables with their numbers, names to grep for after a copy. At most 12 rows; if the idea needs more, write the first ticket only and name the second in "9. Out of scope".
5. **Respect the kit's defaults** when the idea doesn't say: Roblox / Luau, phone first, a 16.6 ms frame budget, every visual naming its tier, pixel owner and intensity rungs (`HIERARCHY.md`). For a VFX, "7. Phases" holds the five-phase table from the vfx skill, and the blueprint must pass `Blueprint.validate`.
6. **Check it.** Run `python3 tools/check_ticket.py docs/specs/<file>` and fix every error until it prints `0 errors`.
7. **Stop.** Do not start the work. Reply with: the ticket's path; three lines on what it builds; the decisions marked `(default)`, so the owner can veto one; and the exact next message to send: `Execute docs/specs/<file>`.

To execute a ticket, a fresh session follows its section 0 and nothing else.
