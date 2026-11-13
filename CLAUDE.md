# CLAUDE.md

How Claude works in any repo of this kit. A repo's own `CLAUDE.md` adds rules on top of these; where they conflict, the repo's rule wins.

<!-- amplifier:start (copy this block verbatim into every repo's CLAUDE.md) -->
## Before you start: greet or amplify

**If the message is only a greeting** ("hi", "hello", "yo") or asks what's needed, run the **kit-doctor** skill: say you're ready, list what's installed and what's missing on this PC (with install commands), note any repo standards not met, and offer 3–4 next steps.


**If the request is short, vague or missing a target** ("make it cool", "fix the ui", "add a shop"), run the **prompt-amplifier** skill before any work:

1. Restate it as a brief: goal → hierarchy tier → deliverable → constraints (engine, platform, performance budget, phone) → quality bar → done-check.
2. Add 5–12 fitting terms from `lexicon.json`, and give three options: **solid / bold / insane**.
3. Show the brief in one compact block, then **proceed on "solid"** unless the user picks another. Never stall waiting for an answer.
4. Mark everything the user didn't say as a *suggestion*. If the prompt is already specific, skip all of this.
<!-- amplifier:end -->

## The kit in one minute

| File | Use it for |
|---|---|
| [HIERARCHY.md](HIERARCHY.md) | What owns the screen and how loud it may be. Every visual decision checks this. |
| [docs/FRAMEWORK.md](docs/FRAMEWORK.md) | Where code goes in a Roblox game, and the rules that keep it safe |
| [LEXICON.md](LEXICON.md) / [lexicon.json](lexicon.json) | 400+ design terms, each with a ready-to-paste prompt phrase |
| [.claude/skills/](.claude/skills/) | Procedures for HUD, rewards, VFX, EditableImage/Mesh, materials, shaders, algorithms, worlds, economy, Luau standards, art direction, hierarchy audit, concept tracing, prompt amplification and the kit doctor |
| [lib/](lib/README.md) | Tested Luau libraries: frontier (EditableImage/EditableMesh at the limits), pixelfx (15 pixel effects) and surfacebake (algorithm textures baked onto model assets) |
| [docs/playbooks/](docs/playbooks/README.md) | How we did everything: Figma UI pipeline, motion + sound, icons, world hierarchy, VFX, procedural textures on models, look-dev loop, Studio, handouts. Follow these before inventing a process |
| [docs/research/](docs/research/README.md) | 31 research chapters: EditableImage/Mesh APIs and cookbooks, Luau performance, VFX, architecture, security, procgen, AI, live ops, QA, and hierarchy science |
| `tools/doctor.py` | Checks this PC's toolchain and a game repo against the kit's standards |
| [docs/STYLE.md](docs/STYLE.md) | Writing, naming and code style |
| [docs/REPO-MAP.md](docs/REPO-MAP.md) | Which repo does what |

## Defaults when the user doesn't say

- **Engine:** Roblox / Luau. Web (canvas, WebGL) for labs and prototypes.
- **Platform:** phone first. Test at 390×844 portrait and 844×390 landscape; touch targets ≥ 44 px.
- **Frame budget:** 16.6 ms on desktop; plan for a phone roughly 4–5× slower. Effects scale down by intensity rung first.
- **Quality bar:** a senior AAA tech-art lead would ship it.
- **Hierarchy:** every new visual names its loudness tier, pixel owner and the intensity rungs it appears on.

## Working rules

1. **Read before writing.** Open the repo's README, CLAUDE.md and the files you'll touch.
2. **Use a skill when one fits.** The skill's self-check runs before you say "done".
3. **Balance lives in data.** Numbers go in content tables, never in logic.
4. **The server validates everything** (see FRAMEWORK rules).
5. **Calm by default.** Nothing loops at rest except the current selection and slow ambient motion.
6. **Test headlessly.** Pure Luau gets a lune test; web examples load in headless Chromium with zero console errors.
7. **Report honestly.** Say what ran, what passed and what wasn't tested (Studio play tests, real phones).
8. **No third-party IP in public material.** Use generic names ("orbiting tome", not a real game's item name).
9. **No secrets in source.** Use `HttpService:GetSecret` or environment config, and never paste key values in chat.
10. **Small commits on a branch** with messages that say what changed.
11. **Show a screenshot of completed work.** Every finished piece ends with an image sent to the user: a render, a capture of the page, or a capture of the results table when the work has no visual of its own.

## Checks

```sh
bash tools/check_all.sh                                 # everything below, in order
lune run tools/check_luau.luau .                      # every .luau file + Luau blocks in Markdown
python3 tools/check_links.py                          # every relative link resolves
python3 tools/check_skills.py                         # skill frontmatter, sections, trigger routing
python3 tools/check_lexicon.py                        # schema, duplicates, pairs-with resolve
python3 tools/hooks/test_amplify.py                   # the prompt-amplifier hook
node tools/check_examples.mjs                         # web examples: zero errors at phone + desktop
```
