# Eval results: Roblox hallucination traps

Measured 2026-11-24 with the `claude` CLI's default model, 37 cases in three tiers (see `roblox_traps/cases.json`).
**Invented** means the answer calls something that is not in Roblox's real API dump, or a call the case forbids. A different but
valid solution (hand-rolled math, another real event) is not counted as invented.

## Method
- **Baseline:** `claude -p` from an empty directory. No `CLAUDE.md`, no hooks, no tools.
- **Harness:** the same from a clean `git clone` of this repo at a committed revision (its `CLAUDE.md`, hooks and `rbx.py`).
  A first harness run was made inside the live working tree while it was being edited; the model answered about the uncommitted
  work instead of the prompt, so that sample is discarded.
- **Chat mode:** the answer is text. No file is written, so the edit hook cannot fire. This measures the instructions alone.
- **Agentic mode** (`AGENTIC=1`): the answer is a file the model writes. The edit hook can reject an invented API and the model can
  fix it. This measures the loop. Only the `rare` and `false-premise` tiers were run.

## Results (invented-API count / cases)

| Arm | basic | rare | false-premise |
|---|---|---|---|
| chat, baseline, run 1 | 0/15 | 0/14 | 4/8 |
| chat, baseline, run 2 | 0/15 | 0/14 | 3/8 |
| chat, harness (clean clone) | 0/15 | 0/14 | 2/8 |
| agentic, baseline | not run | 0/14 | 3/8 |
| agentic, harness | not run | 0/14 | 1/8 |

## What it says
1. **The model did not invent an API on its own in any arm** (0 of 29 basic and rare answers in each chat run, 0 of 14 rare answers in each agentic run).
   The basic and rare tiers cannot tell the arms apart.
2. **It invents when the prompt asserts an API that does not exist** (`EditableMesh:AddQuad`, `EditableImage:Clear`,
   `DataStore:SaveAsync`, `workspace:RaycastDistance`). About half of the baseline false-premise answers did, sometimes with a
   comment saying it was unsure and the call left in anyway.
3. **The harness lowered that count** (3 to 4 of 8 down to 1 to 2 of 8) but did not remove it.
4. In one agentic run the model wrote `(store :: any):SaveAsync(...)` and told the user `SaveAsync` does not exist. The checker
   now rejects that cast for a variable of known class (`check_roblox_api.py`).
5. In a rerun of that case the model wrote correct code at the first attempt and the hook passed it, so the rerun does **not**
   show the hook rescuing an answer. One probe on `EditableImage:Clear` did: the first write used `:Clear`, the PostToolUse hook
   rejected it, and the rewrite used `DrawRectangle`.

## Limits
- One or two samples per case and eight false-premise cases per arm: the difference between arms is suggestive, not statistically
  established. Re-run with `FORCE=1` and more samples before drawing a firm line.
- One model, one date. Results will move with the model.
- Rules (`must_use`, `must_not`) were corrected three times after reading failures; every correction made the rule looser toward
  valid answers, none was tuned to favour an arm.
- The cases were written by the same author as the checker, so the checker is known to catch every known-bad fixture (37 of 37).
  That is a regression test, not a measure of coverage on unseen hallucinations.

## Reproduce
```sh
bash tools/evals/run_claude.sh OUT                      # chat answers, from the directory you run it in
AGENTIC=1 ONLY_TIERS="rare false-premise" bash tools/evals/run_claude.sh OUT   # file answers, hooks in play
python3 tools/evals/score.py OUT
```
