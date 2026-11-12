<!-- Paste into Discord one block at a time: each message below is under Discord's 2,000-character limit. -->

# aaa-kit: Discord guide

Four messages for a forum or suggestions post. Title: `aaa-kit: free Claude Code skill vault for Roblox devs`. Attach 2-4 GIFs from `media/gifs/` (all under 6 MB), e.g. `surfaces/react-ice-vs-lava-sphere.gif`, `surfaces/dissolve-gold-torus.gif`, `tier5-holo.gif`, `surfaces/depth-shell-fur.gif`, plus `media/map-guide/map_hero.jpg`.

---

<!-- Message 1: the post (1924 characters) -->

# aaa-kit: a Claude Code skill vault for Roblox devs
Free, open source. Clone it, open it in Claude Code, say **hi**, and Claude starts working like it knows Roblox at a AAA bar: UI, VFX, rewards, materials, economy, worlds and clean Luau.
<https://github.com/jewdah-afk/aaa-kit>

## What's in it
- **17 skills** that load by themselves when your ask matches, each with a tested example (full list below), plus **22 LihFolk skills** one install away
- **Lexicon (hyperlexicon)**: 464 real design terms across 15 areas. Each has a meaning, when to use it, what it pairs with and a phrase to paste into a prompt
- **HIERARCHY.md**: 6 loudness tiers, so effects stop fighting over the screen
- **Framework**: a 5-layer Roblox project structure and a starter game with 48 tests
- **Luau libraries**, tested headless: `frontier` (EditableImage/Mesh pushed to the limit), `pixelfx` (15 pixel effects), `surfacebake` (procedural materials baked onto your meshes)
- **36 research docs, 1000+ algorithm ideas, 10 playbooks** (Figma to Roblox UI, VFX craft, look-dev)
- **Tools**: a hierarchy auditor (where the eye goes on a screenshot, plus contrast, colour-blind and flash checks), economy calculator, and 4 review agents (`ui-qa`, `style-guard`, `visual-hierarchy`, `roblox-feasibility`)

## How it helps
Vague ask like "make the shop better"? The prompt amplifier turns it into a real brief. Say "chest opening" and the reward skill brings the beats, timing and juice.

## Example
**loudness tier** → `put this in loudness tier 2: bright on the onset frame, back to baseline within 12 frames`
```lua
Apply.bakeMeshPart(workspace.Barrel, Presets.rustedIron, { size = 512 })
```

## Start
`git clone https://github.com/jewdah-afk/aaa-kit`, open it in Claude Code, type `hi`. It checks your setup first. Want the skills in your own game? Copy `.claude/skills/` into it.

-# Code MIT · docs CC BY-ND 4.0 · WIP, drop suggestions below

---

<!-- Message 2: first reply (1855 characters) -->

## All 17 skills
Each is a `SKILL.md` Claude loads by itself, with a tested example in `.claude/skills/<name>/examples/`. ✅ = checks passing in lune
- `ui-hud`: counters, bars, cooldowns, shop cards · `Odometer` ✅12 · Figma→Roblox playbook
- `vfx`: impacts, hit-stop, shake, trails, lightning, dissolves · `Impact` ✅7 · VFX craft playbook
- `reward-moments`: chest/egg opens, RNG reels, level-ups, rebirth · `RewardSequence`+`Reel` ✅15
- `materials`: chrome, gem, glass, holo, molten, rarity as material · `RarityStyle` ✅6 · `surfacebake`
- `editable-image`: pixel renderers, procedural textures · `PixelFrame` ✅11 · `frontier`, `pixelfx`, API research
- `editable-mesh`: runtime geometry, terrain, deformation, LOD · `GridMesh` ✅9 · API + 3D maths research
- `shaders-and-sdf`: SDFs, raymarching, noise, thin film, no real shaders needed · `Sdf` ✅13 · depth lab
- `algorithms`: noise, jump flood, cellular automata, reaction-diffusion · `Chain` ✅7
- `procedural-world`: maps, biomes, dungeons, scatter, L-system trees · `Poisson` ✅4 · world playbook
- `game-economy`: cost curves, numbers past 1e308, buy-max, prestige · `Curves` ✅10 · `EternityNum`
- `roblox-luau-standards`: structure, remotes, server checks, saves, receipts · `Receipts` ✅7 · starter game
- `art-direction`: palettes, values, contrast, silhouettes · `Contrast` ✅8 · HIERARCHY.md
- `hierarchy-audit`: where the eye goes, contrast, colour-blind, flash safety · `Perceptual` ✅25 · `tools/hierarchy`
- `prompt-amplifier`: turns "make it better" into a full brief · hook tests ✅12
- `kit-doctor`: say hi, it checks your PC and repo · `tools/doctor.py`
- `lihfolk-stud-voxel`: stud/LEGO voxel models, rigged GLB out · Oak build `RIG_OK`
- `voicestudio-sfx`: local SFX + voice lines via VoiceStudio · client ✅17
-# Routing: 43/43 sample prompts pick the right skill (`tools/check_skills.py`)

---

<!-- Message 3 (1664 characters) -->

## LihFolk vault: 22 more skills (separate repo)
<https://github.com/lihfolk-cy/v2-vault> · in Claude Code: `/plugin marketplace add lihfolk-cy/v2-vault` then `/plugin install lihfolk@lihfolk`
Backed by 1,300+ vault notes you can also read in Obsidian. Scored **91–94%** on four blind-graded test sets (`benchmark/`). A hook catches 17 common Roblox mistakes as files are written.
- **Ready code:** `lihfolk-systems` (data, net, currency, shop, inventory, eggs, codes, daily, leaderboard) · `lihfolk-ui` · `lihfolk-vfx` · `lihfolk-sfx` · `lihfolk-figma` (Figma → ScreenGui, tested)
- **Building:** `lihfolk-worldbuilding` · `roblox-blender-modeling` · `roblox-asset-import` · `lihfolk-assets` · `lihfolk-tutorial` · `roblox-trend-game` · `roblox-system-builder` · `roblox-ui-builder`
- **Safety:** `roblox-secure-remotes` · `roblox-anti-exploit-review` · `roblox-datastore-safety` · `roblox-monetization-compliance` · `roblox-performance-audit` · `roblox-debugging`
- **Judging:** `quality-score` (0–10 rubrics) · `council-method` (blind multi-agent verdict) · `lihfolk` (vault router)

## Stud Voxel pack (inside aaa-kit)
`lihfolk-stud-voxel`: stud/LEGO voxel models built in headless Blender, exported as rigged GLB for Roblox. 25 examples that rebuild exactly: 7 animated critters (duck, fox, red panda…), 12 bosses (rhino, dragon, hydra, kraken, T-rex…), plus a mech, lich, mimic and train. It also covers buildings (shop, tower, gate), props (oak, pine, well, lamp, fence) and terrain (cliff, waterfall, walls). Each boss ships its concept sheet and a side-by-side.
-# Proof: the Oak test build prints `RIG_OK` at 7,928 triangles (Roblox's mesh cap is 20,000)

---

<!-- Message 4 (1267 characters) -->

## Look around first
Clone it and open these in a browser (no install needed):
- `examples/web/showcase.html`: the whole kit on one page. A dimension ladder (tesseract, Hopf fibration, penteract), a surface lab and the hyperlexicon, all running live
- `examples/web/effects-gallery.html`: 48 effects sorted by loudness tier
- `examples/web/surface-bake.html`: 15 algorithm materials and 5 live motions on 3D models
- `examples/web/depth-lab.html`: parallax windows, interior mapping, infinite zoom, shell fur
- `examples/web/algorithm-lab.html`: the algorithms one by one
- `docs/playbooks/map-guide.md`: a stud map built from the pack, with screenshots and a `.glb` you can import
- `media/gifs/`: 36 looping GIFs of materials, generative engines and surface effects

## The six tiers
1 Moments and rewards · 2 Combat and impact · 3 HUD · 4 World and atmosphere · 5 Materials · 6 Generative engines
Only one thing is loud at a time, and the numbers are researched: text contrast Lc 75+, flashes at most 3 per second, 500 ms between reward beats.

## Where to start reading
`README.md` → `HIERARCHY.md` → `LEXICON.md` (40-term starter pack) → `docs/playbooks/`

Run `bash tools/check_all.sh` to check everything: Luau compile, tests, links, skills, lexicon and pages.
