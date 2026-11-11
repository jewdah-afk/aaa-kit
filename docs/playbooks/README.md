# Playbooks

How we actually made our games: the processes, pipelines and hard-won rules behind the work, written so anyone (or any Claude session) can repeat them. The rules of *what* good looks like are in [HIERARCHY.md](../../HIERARCHY.md) and the [skills](../../.claude/skills/); these pages are *how* we got there.

| Playbook | Covers | Tools |
|---|---|---|
| [Figma → Roblox UI](figma-to-roblox-ui.md) | Inventory, hero design, the Figma kit, parallel design agents, style rules, export → layouts → render, layer-name contract, importer limits, placement, visual hierarchy, zoomed QA, headless UI harness, gotchas | [tools/figma](../../tools/figma/README.md), [lib/figma-ui](../../lib/figma-ui/README.md) |
| [UI motion and sound](ui-motion-and-sound.md) | Key press-in feel, window open/close/tab motion, HUD feedback, a fully tuned pull-down board, the sound event system, layered sounds, the dev sound board | `lib/figma-ui/Motion.luau` |
| [Icon pipeline](icon-pipeline.md) | Icon style, generate → cut → re-ring → QA, uploads, Blender cel icons and the 3D export plan | [tools/icons](../../tools/icons/README.md) |
| [World hierarchy](world-hierarchy.md) | The 7 world tiers, composition, value check, outline budget, the Explorer tree contract | — |
| [VFX craft](vfx-craft.md) | One hero + two supports, ZOffset order, the four craft levers, shipped recipes, engine limits we hit, QA hooks | `lib/pixelfx`, `lib/frontier` |
| [Look-dev loop](look-dev-loop.md) | Pass → capture → measure → NOTES → tests + golden → review; VFX stress tests; benches and budgets | `tools/capture_gifs.mjs` |
| [Studio workflow](studio-workflow.md) | Repo as source, one test place, fast HTTP sync, Studio MCP, one-image uploads, dev saves, debug commands and attributes | — |
| [Working with Claude](working-with-claude.md) | Handouts, owner rules captured live, specialist agents, parallel sessions, honest reporting | [.claude/agents](../../.claude/agents/), [handout template](templates/HANDOUT.md) |
| [Parity and porting](parity-and-porting.md) | Parity harness, value-by-value verification, inventory and checklists, skeleton-first porting | [examples/bignum](../../examples/bignum/README.md) |
