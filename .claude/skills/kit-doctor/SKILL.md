---
name: kit-doctor
description: Use when the user greets you or opens a session with no task ("hi", "hello", "hey", "yo", "what can you do", "where do I start"), asks what they need installed ("set up my pc", "what do I need", "check my setup", "is my toolchain ok"), or asks whether a game repo meets the bar ("is my game good", "audit my game", "health check", "what's missing"). Runs the kit doctor, reports readiness and missing tools with install commands, audits the repo against the kit's standards, and recommends the next steps.
---

# kit-doctor

The front desk. A user who types "hi" gets a ready, useful answer in one screen: what works, what's missing on their PC, what the repo still needs, and what to build next.

## When to use

- A greeting or an empty opener
- "What do I need?", "set up my PC", "check my setup"
- "Is my game good?", "audit this repo", "what's missing?"

**Not for:** a specific build request (go straight to the matching skill) or a vague build request (`prompt-amplifier`).

## Method

1. **Run the doctor.** `python3 tools/doctor.py --brief` in the kit, or `python3 <kit>/tools/doctor.py --brief --repo .` from a game repo. The greeting hook may already have put its output in context; reuse that instead of running it again.
2. **Greeting reply** (≤ 15 lines):
   - one line: "Ready." plus what this repo is
   - **Installed:** the tools that pass, on one line
   - **Missing:** each missing required tool, with the exact command from the report
   - **Repo:** standards not met, if any (from the audit)
   - **Next:** 3–4 concrete options tied to this repo (build an effect, run the checks, audit the game, start a new game from the starter), then ask which
3. **Setup request:** list every missing tool, required first, with the command for their OS. Group them so one copy-paste installs the lot. Re-run the doctor after they install to confirm.
4. **Audit request** ("is my game good"):
   1. `python3 tools/doctor.py --repo <game>` for the structural standards
   2. the game's own tests (`sh tests/all.sh` or equivalent) and the kit checks that apply (`lune run tools/check_luau.luau <game>/src`)
   3. the hierarchy quick audit in [HIERARCHY.md §16](../../../HIERARCHY.md#16-quick-audit) on its main screens
   4. report pass/fail per item, then the 3 changes with the biggest payoff, each pointing at the skill that does it
5. Never install anything without the user's go-ahead; print commands instead.

## Hierarchy rules it obeys

The audit applies all of HIERARCHY.md through its quick audit (§16). The greeting itself follows "one loud element per panel" (§13): the single loudest thing in the reply is what's missing or the next step.

## Engine notes

- **Required for the Roblox workflow:** git, Python 3, Node, rokit, then `rokit install` in the repo for the pinned lune, selene and rojo. Roblox Studio is needed for play-testing (Windows or macOS).
- **Optional:** Playwright + Chromium (web example checks), StyLua (formatting), Blender (icon and mesh pipelines), ffmpeg (GIF captures with `tools/capture_gifs.mjs`), Pillow (image QA), the VS Code Luau LSP extension.
- Selene's `std = "roblox"` downloads the Roblox API definitions once, so it needs network the first time.

## Example

A user types `hi` in the kit. The hook runs the doctor; the reply:

```text
Ready. This is aaa-kit: the hierarchy, framework, skills and lexicon for every game.
Installed: git, Python 3.12, Node 22, lune 0.10.5, selene 0.31, Playwright, ffmpeg
Missing (needed):
  - rokit:  winget install rojo-rbx.rokit
  - rojo:   rokit install   (in this repo; installs the pinned rojo 7.5.1)
Nice to have: StyLua, Blender
Next:
  1. Build an effect (tell me the moment: chest open, hit, level-up…)
  2. Audit a game repo against the kit (python3 tools/doctor.py --repo ../my-game)
  3. Start a new game from examples/framework-starter
  4. Run every kit check (bash tools/check_all.sh)
Which one?
```

## Make it insane

1. **One-command setup:** after the user agrees, run the printed install commands in order, re-run the doctor after each, and stop at the first failure with its error.
2. **Repo scorecard:** turn the audit into a page with a pass/fail grid per standard and hierarchy rule, plus captures of each main screen, and re-run it on every PR.
3. **Phone budget check:** run the game's benches, multiply by the phone factor (×5) and flag every layer that would push a phone over 33 ms.

## Self-check

- [ ] Ran the doctor (or reused the hook's report) instead of guessing what's installed.
- [ ] Every missing required tool has an exact command for the user's OS.
- [ ] Nothing was installed without the user's go-ahead.
- [ ] Next steps are specific to this repo, at most four, ending with a question.
- [ ] The greeting reply is 15 lines or fewer.
