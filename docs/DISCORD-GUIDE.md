<!-- Paste into Discord one block at a time: each "message" below is under Discord's 2,000-character limit. -->

# aaa-kit: Discord guide

Five messages, ready to paste. Each block between the `---` lines fits in one Discord message.

---

# 🎮 aaa-kit: the game-dev super repo
**One repo that makes every Roblox game (and every Claude session) start at a AAA bar.**
<https://github.com/jewdah-afk/aaa-kit>

**What's inside**
> 📐 **Hierarchy:** the rules for what owns the screen and how loud it may be
> 🧠 **15 Claude skills:** HUD, rewards, VFX, materials, shaders, worlds, economy, Luau…
> 📚 **30 research chapters + 10 playbooks:** what works and *how we actually did it*
> 🧪 **3 tested Luau libraries:** pixels, meshes, and textures baked onto models
> 🗣️ **444-term lexicon:** design words with ready-to-paste prompt phrases
> 🔧 **Tools:** kit doctor, hierarchy auditor, Figma pipeline, GIF recorder, one-command checks
> 🎞️ **Labs + 36 GIFs:** every effect running live

**Start in 10 seconds**
```
git clone https://github.com/jewdah-afk/aaa-kit
```
Open it in Claude Code and type **`hi`**. The kit doctor checks your PC (lune, rojo, selene, node, python, ffmpeg…), lists what's missing with install commands, and suggests next steps.
Type something vague like **"make the shop cool"** and the prompt amplifier turns it into a full brief with solid / bold / insane options, then gets to work.

---

# 📐 Hierarchy: the core idea
Every pixel has a job. `HIERARCHY.md` decides what wins:
• **Loudness tiers 1–6:** 1 moments & rewards → 2 combat → 3 HUD → 4 world → 5 materials → 6 generative engines
• **Pixel ownership:** effects never cover threats, UI or ceremony
• **Intensity ladder:** calm → build → surge → ceremony → boss → finale. Every system reads it
• **Colour jobs, rarity ladder, figure-ground gate, one loud element per panel**

**Now backed by science** (attention, contrast, timing, audio), and every rule has a number:
✅ text contrast with **APCA** (75+ for numbers you read in play)
✅ **colour-blind** checks (it caught Rare vs Epic looking the same, now fixed)
✅ **flash safety**: ≤ 3 flashes/s (WCAG). Every GIF is checked automatically
✅ enemy wind-ups ≥ 600 ms; reward beats ≥ 500 ms apart

**Measure it:** `tools/hierarchy` takes a screenshot and predicts where the eye lands 1st → 5th, then flags competitors, squint value and colour-blind failures.

---

# 🧠 Skills, playbooks, research
**Skills** load automatically when your request matches:
`ui-hud` · `reward-moments` · `vfx` · `materials` · `shaders-and-sdf` · `algorithms` · `procedural-world` · `game-economy` · `editable-image` · `editable-mesh` · `roblox-luau-standards` · `art-direction` · `hierarchy-audit` · `prompt-amplifier` · `kit-doctor`
Each one has a method, its hierarchy rules, a tested Luau example and a self-check.

**Playbooks: how we did everything**
Figma → Roblox UI (the kit, exporter and node-for-node renderer) · UI motion & sound · icon pipeline · world hierarchy · VFX craft · look-dev loop · Studio workflow · working with Claude (handouts, owner rules) · parity & porting · **procedural textures on models**

**Review agents:** `ui-qa` · `style-guard` · `visual-hierarchy` · `roblox-feasibility`

**Research:** EditableImage/Mesh APIs + cookbooks, Luau performance, VFX & game feel, architecture, security, procgen, NPC AI, live ops, QA, big numbers, incremental design, hierarchy science.

---

# 🧪 Libraries (pure Luau, headless-tested)
**frontier:** EditableImage/EditableMesh at the limits: image pool, atlas, falling sand, 2D GI, voxel terrain, lightmaps, fracture…
**pixelfx:** 15 pixel effects: lightning, frost, dissolve, bloom, a 1,000-enemy crowd…
**surfacebake:** ⭐ **algorithm textures baked onto YOUR models**
• Reads a mesh's UVs and computes every texel at its 3D point, so there are **no seams**
• Wear follows real geometry: chipped edges, grime in crevices, moss on top faces
• **15 materials:** rust, painted metal, gold, marble, wood, lava, ice, slime, sci-fi panels, carbon fibre, copper patina…
• Outputs colour + normal + roughness + metal → `SurfaceAppearance`
• **Realtime:** rune pulse, lava flow, dissolve, scan, frost spread (~1–2 ms/frame at 128²)
• **Reactive:** hits heat metal and ripple, frost fights lava, shields flare with spin, fur lags on a spring
• **Depth without shaders:** parallax windows, rooms behind windows, infinite zoom, shell fur

Every number is measured (`BENCH.md`) and every limit is written down (verification gate, memory budget, one image upload per frame).

---

# 🎞️ See it · ✅ trust it · 📜 use it
**Labs** (open the HTML in `examples/web`):
• Effects hierarchy: 48 effects by tier
• Algorithm lab · tier simulator · economy calculator
• Surface bake lab: pick a material and model, add motion, **tap to hit**
• Depth lab: parallax, interiors, infinite zoom, fur
• `media/gifs`: 36 looping clips (dissolve and frost on four surfaces, ice vs lava…)

**One command checks everything:**
```
bash tools/check_all.sh
```
Luau compile + tests, links, skill routing, lexicon, hook, flash safety, web pages at phone + desktop. Green means green.

**House rules:** server validates everything · balance lives in data · calm by default · no secrets in source · no third-party IP · Studio is the last check, not the first.

📜 **License:** code MIT · docs CC BY-ND 4.0 (use and share, don't remix the docs)
💬 Questions? Ask here, or type `hi` to the kit 👋
