# Hierarchy

These rules decide what owns the screen, when it gets it and how loud it may be. Every skill in this kit enforces some of them. When two rules disagree, the one higher on this page wins.

The rules come from two places: the visual-hierarchy work in the Cursed Survivors renderer (owner buffer, intensity ladder, attention contract) and the 48-effect Living Effects Lab (loudness tiers).

## Contents

1. [The one question](#1-the-one-question)
2. [Screen loudness tiers 1–6](#2-screen-loudness-tiers-16)
3. [Pixel ownership](#3-pixel-ownership)
4. [The intensity ladder](#4-the-intensity-ladder)
5. [Colour has jobs](#5-colour-has-jobs)
6. [Calm frames stay calm](#6-calm-frames-stay-calm)
7. [Rarity ladder](#7-rarity-ladder)
8. [Urgency beats rarity](#8-urgency-beats-rarity)
9. [Time: critical cues never wait](#9-time-critical-cues-never-wait)
10. [Protected regions](#10-protected-regions)
11. [Figure-ground gate](#11-figure-ground-gate)
12. [Density and crowd LOD](#12-density-and-crowd-lod)
13. [One loud element per panel](#13-one-loud-element-per-panel)
14. [Reward sequencing](#14-reward-sequencing)
15. [Framework layers mirror the hierarchy](#15-framework-layers-mirror-the-hierarchy)
16. [Quick audit](#16-quick-audit)

---

## 1. The one question

> How much can this frame hold while the player still makes the next correct decision?

Every other rule on this page is a way of answering that. Brightness is only one of the levers. The others are contrast, scale, detail density, motion, occlusion, space, time, representation and sound.

---

## 2. Screen loudness tiers 1–6

**Rule.** Every effect belongs to exactly one tier. Tier 1 is the loudest, and the louder the tier, the rarer and shorter its effects.

| Tier | Name | Loudness | What lives here | Budget |
|---|---|---|---|---|
| 1 | Moments & Rewards | 5 | Reveals, reels, gacha beams, level-ups, rebirth, boss intros | Owns the whole screen for a beat; at most one at a time; skippable |
| 2 | Combat & Impact | 4 | Hits, lightning, shockwaves, dissolves, auras, freezes | Reads instantly, then gets out of the way (≤ 400 ms per accent) |
| 3 | HUD & Interface | 3 | Currency, bars, cooldowns, feeds, combo, rarity frames | Always on screen, so it stays still until a number changes |
| 4 | World & Atmosphere | 2 | Aurora, god rays, snow, fireflies, cloth, ink | Slow, soft, never brighter than the HUD |
| 5 | Materials | 2 | Chrome, gem, glass, holo foil, molten, brushed metal | One material per rarity, used consistently |
| 6 | Generative Engines | 1 | Reaction-diffusion, L-systems, Voronoi, boids, flow fields, ASCII | Runs underneath and makes content; never competes for attention |

**Why.** If everything is loud, nothing is. Ranking effects by loudness up front turns a style argument into a lookup.

**Do.** Put the chest-open burst in tier 1 and let the world dim while it plays.
**Don't.** Give the ambient fireflies the same glow strength as the level-up burst.

**Enforced by:** `vfx`, `reward-moments`, `ui-hud`, `materials`, `procedural-world`, `art-direction`.

---

## 3. Pixel ownership

**Rule.** Each pixel has one owner, from the lowest to the highest priority:

`background (0) < ambient (1) < world (2) < reward (3) < threat (4) < hero (5) < UI (6) < ceremony (7)`

A write may paint over owners at or below its own rank, never above. In a pixel renderer the owner rank is stored per pixel in an owner buffer (one byte per pixel, cleared every frame). In an instance renderer it becomes ZIndex bands and a fixed draw order.

| Owner | Examples | May be covered by |
|---|---|---|
| 0 background | sky, void, letterbox | anything |
| 1 ambient | fog, motes, distant parallax | world and up |
| 2 world | ground, props, decals | reward and up |
| 3 reward | gems, coins, chests, drops | threat and up; friendly FX only through a sparse dither |
| 4 threat | enemies, hostile shots, telegraphs | hero, UI, ceremony |
| 5 hero | the player, their weapon FX | UI, ceremony |
| 6 UI | HUD, HP bars, prompts | ceremony only |
| 7 ceremony | full-screen moments | nothing |

**Why.** Draw order says what paints over what, not what matters. A hostile shot drawn under a friendly effect still has to win.

**Do.** Let friendly weapon FX stamp at hero rank, so they never cover a threat, the UI or a ceremony.
**Don't.** Let an effect move or bend a gameplay object's pixels: a whip cut that shears enemies 2 px off their real spot is lying about where they are.

**Enforced by:** `editable-image`, `vfx`, `ui-hud`, `art-direction`.

---

## 4. The intensity ladder

**Rule.** The game state owns one number from 0 to 5. Every visual layer reads it and stays inside that rung's budget.

| Rung | Name | Enters when (start values, tune in play) | Allowed |
|---|---|---|---|
| 0 | calm | Nothing near the player, menus at rest | Ambient on, no impact frames, music back and muffled |
| 1 | build | The crowd grows (≥ 40 on screen; exits at ≤ 30) | Ambient on, full weapon ornament (the celebration rung) |
| 2 | surge | A dense crowd near the player (≥ 12 within reach; exits at ≤ 8), a hostile shot near, or HP < 30 % (exits at > 40 %) | Impact frames on, ambient off, HUD ornament waits |
| 3 | ceremony | A level-up, chest or reward screen is open | The ceremony owns the screen, world drops to the lowest band |
| 4 | boss | A boss is on screen | Impact on, ambient off, grade floor raised |
| 5 | finale | The final fight or countdown | Everything allowed, brightest music |

Rising is immediate. Falling steps down one rung every 1.5 s, and each trigger has separate enter and exit thresholds (hysteresis), so a crowd hovering at the edge doesn't make the screen flicker between treatments.

**Why.** Peaks only read as peaks if the frames around them are calmer.

**Do.** Drive bloom strength, particle caps, music level and HUD ornament from the rung.
**Don't.** Let each system decide its own loudness from local events.

**Enforced by:** `vfx`, `reward-moments`, `art-direction`, `roblox-luau-standards` (the ladder is a central system).

---

## 5. Colour has jobs

**Rule.** A hue that carries meaning carries only that meaning.

| Colour | Job | Never use it for |
|---|---|---|
| Gold `#ffd24a` | Currency and the main call to action | Decoration, borders, generic "nice" accents |
| Blue `#4ea8ff` | XP, experience gems, the XP bar | Currency, danger |
| Red `#ff4a4a` | Danger only: threats, damage taken, low HP | Sale badges, "new" dots, rarity |
| Warm lantern light | The hero's own light and the logo | Pickups |
| Bone / off-white | UI focus and selection | Background fills |
| Rarity colours | Rarity only (see §7) | Unrelated UI |

**Why.** When gold means everything, players stop seeing currency. A red "NEW" badge reads as damage.

**Do.** Show a sale with a gold price and a bone-white tag.
**Don't.** Make the top-tier XP gem red; use gold or a brighter blue.

**Enforced by:** `art-direction`, `ui-hud`, `vfx`, `materials`.

---

## 6. Calm frames stay calm

**Rule.** At rung 0 nothing loops except the current selection and slow ambient motion. The screen goes back to baseline within 12 frames (200 ms at 60 fps) after an event resolves.

**Why.** A calm baseline is what gives a peak its contrast. It also costs less to render.

**Do.** Let a full XP bar sit still with a quiet glow, then burst once when it fills.
**Don't.** Pulse every button, shimmer every frame border and bob every icon all the time.

**Enforced by:** `ui-hud`, `vfx`, `art-direction`.

---

## 7. Rarity ladder

**Rule.** Each rarity step adds exactly one new visual behaviour on top of the step below. Motion and particles are kept for the top of the ladder.

| Rarity | Colour | Frame behaviour | Material | Reveal |
|---|---|---|---|---|
| Common | grey `#9aa4b2` | Static border | Flat | No ceremony; drops into the slot |
| Uncommon | green `#4fd17a` | Static border + 1 px inner highlight | Satin | Short pop (120 ms scale overshoot) |
| Rare | blue `#3f9bff` | A shine band sweeps every 2–3 s | Brushed metal | Pop + one ring |
| Epic | purple `#b25cff` | Rotating conic edge | Glass or gem | Pop, ring, a brief backdrop dim |
| Legendary | gold-orange `#ffb02e` | Rotating edge + sparks running along it + outer glow | Chrome or molten | Rays behind the item, camera nudge, sting |
| Mythic | pink-magenta `#ff3d7f` | Rainbow conic edge, stronger glow | Holo foil | Full tier-1 moment: charge-up, beam, burst |
| Secret | white on black `#ffffff` | Starfield inside, glitch slices on the edge | Void / glitch | The reveal hides its tier until the last beat |

**Why.** A ladder only reads if the steps are distinct and cumulative. Seven tiers that all glow look like one tier.

**Do.** Make Epic the first tier that moves.
**Don't.** Give Common items a shimmer "so they look nice"; that spends the motion Rare needs.

Mythic uses the rarity pink, so it never borrows danger red. Gold-orange for Legendary is a rarity colour, kept apart from currency gold `#ffd24a` by hue and by always appearing inside a frame.

**Enforced by:** `ui-hud`, `reward-moments`, `materials`.

---

## 8. Urgency beats rarity

**Rule.** When several situations are true at once, this order wins each channel: hostile shot near > low HP > boss > dense crowd > calm. A Legendary weapon's ornament backs off near a threat exactly like a Common one does.

**Why.** The player dies to the shot they didn't see, not to the one under a pretty effect.

**Do.** Drop a friendly lightning bolt's side branches inside a hostile shot's lane.
**Don't.** Let a Mythic aura paint over an enemy projectile.

**Enforced by:** `vfx`, `editable-image`, `art-direction`.

---

## 9. Time: critical cues never wait

**Rule.** Hits on the player, hostile shots, boss attacks, level-ups and HP changes always draw on time. Decoration (crit stars, sparks, trail flashes, number pops) competes for a fixed number of slots (start: 6 in the world, 1 in the UI). An accent that loses its slot is shortened or skipped, never delayed.

Every event has the same timeline: baseline → anticipation (only if the mechanic really has one) → onset → active → resolution → recovery.

**Why.** Late feedback lies about when something happened.

**Do.** Skip the seventh spark.
**Don't.** Queue it for 300 ms later.

**Enforced by:** `vfx`, `ui-hud`, `reward-moments`.

---

## 10. Protected regions

**Rule.** Decoration reduces itself inside protected masks. Gameplay footprints, start times and durations never change; only the ornament does.

| Mask | Size (start) | Inside it |
|---|---|---|
| Hero silhouette + ring | sprite + 2 px | No FX over the hero except its own hit flash; ground detail drops one band |
| Hostile shots | sprite + 3 px, plus a 6 px lane ahead | Friendly FX lose branches and sparks; no trail flash |
| Enemies about to touch the player | sprite + 1 px | Drawn in full even in darkness |
| Pickups | sprite + 1 px | At least 60 % of the sprite stays visible |
| Text and buttons | glyph box + 1 px | Patterns thin out behind text, no animation |

Allowed reductions: drop one or two brightness bands, raise the dither threshold, skip branches or sparks, freeze glyph animation. Cap the masks: if they cover more than 35 % of the play area, distant crowds switch to aggregate glyphs instead (§12).

**Enforced by:** `vfx`, `editable-image`.

---

## 11. Figure-ground gate

**Rule.** Every gameplay silhouette keeps a contrast gap of at least 2 luminance bands (out of 8, perceptual OKLab lightness) against the 1–2 px ring around it, measured at its worst pixel. The hero gets a thin ring that darkens whatever is under it by 2 bands, never pure black.

**Why.** The player has to find themselves and every threat in a single glance at phone size.

**Do.** Squint-test the frame, or render a tier view and a luminance-band view.
**Don't.** Put a mid-grey enemy on a mid-grey floor and rely on hue.

**Enforced by:** `art-direction`, `editable-image`, `vfx`.

---

## 12. Density and crowd LOD

**Rule.** When a region gets too dense, its representation simplifies before its readability fails. Aggregate glyphs carry one meaning each.

- A cell turns into an aggregate glyph at ≥ 6 entities and returns to sprites at ≤ 3, with at least 0.5 s between switches.
- Glyph density means count only: 3 = `.`, 4–5 = `:`, 6–7 = `*`, 8–10 = `#`, 11+ = `@`.
- Glyph shape means entity class, colour means family (red = danger), and a given entity keeps its glyph between frames (stable per-entity seed, never per-frame random).

Detail budgets per 16×12 px cell near the hero: ≤ 3 non-gameplay movers, ≤ 15 % of pixels changing per frame, friendly FX covering ≤ 40 % of the play area and ≤ 20 % within two cells of the hero, and no more than 30 % of a hostile shot hidden.

**Enforced by:** `editable-image`, `procedural-world`, `vfx`.

---

## 13. One loud element per panel

**Rule.** Menus and screens have one loud element per panel. In combat it's one loud *decoration* per region, with any number of critical cues.

**Do.** Make the Buy button the loudest thing on a shop card.
**Don't.** Animate the price, the icon, the frame and the button at once.

**Enforced by:** `ui-hud`, `art-direction`.

---

## 14. Reward sequencing

**Rule.** A reward hands attention along in order: container → item → what it is → what changed → continue. Each step starts once the one before it settles. Skipping always works and jumps straight to the final state.

**Enforced by:** `reward-moments`, `ui-hud`.

---

## 15. Framework layers mirror the hierarchy

Code structure follows the same top-down shape, so a feature always has one obvious home. See [docs/FRAMEWORK.md](docs/FRAMEWORK.md).

| Code layer | Owns | Matches |
|---|---|---|
| Kit hub | Shared utilities, no game logic | The background: always there, never loud |
| Services | Authority, data, validation | The world's rules |
| Components | Per-instance behaviour bound to tags | Things on screen |
| Content data | Plain tables of numbers and names | What gets displayed |
| Central systems | Intensity ladder, automations, unlocks, resets, save | The conductor that decides what is loud now |

**Enforced by:** `roblox-luau-standards`, `game-economy`.

---

## 16. Quick audit

Run this on any frame, screen or effect before calling it done.

- [ ] Which loudness tier is it in, and is it the only tier-1 thing on screen?
- [ ] Does each pixel's owner outrank everything it covers?
- [ ] Which intensity rung is the game in, and does the effect stay inside that rung's budget?
- [ ] Is every meaningful colour used only for its job?
- [ ] Does the calm state actually look calm?
- [ ] Do rarity tiers each add exactly one new behaviour?
- [ ] Does any decoration cover a threat, the hero or text?
- [ ] Does every silhouette pass the 2-band figure-ground gate at phone size?
- [ ] Do dense regions simplify, with hysteresis?
- [ ] Does the screen return to baseline within 12 frames?
