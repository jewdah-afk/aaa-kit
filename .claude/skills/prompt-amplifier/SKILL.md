---
name: prompt-amplifier
description: Use FIRST when a request is short, vague or low-effort - no clear target, no deliverable, no constraints, or taste words like "make it cool", "fix the ui", "make it better", "add juice", "make it pop", "improve the shop", "do the thing". Turns the request into a strong brief (goal, hierarchy tier, deliverable, constraints, quality bar, done-check), adds fitting lexicon terms and solid/bold/insane options, then proceeds on solid without waiting. Skip it when the prompt is already specific.
---

# prompt-amplifier

A vague prompt shouldn't produce vague work. This skill rewrites a weak request into a brief in a few seconds, shows it, and then gets on with the work. It never blocks and never invents requirements.

## When to use

- The request is under ~12 words, or names no target ("make it better")
- No deliverable is named (a file? a screen? an effect?)
- Taste words carry the whole request: cool, clean, pop, juicy, AAA, polished, better, insane
- The `UserPromptSubmit` hook added a note saying the prompt looks weak

**Skip it when** the prompt already names a target, a deliverable and at least one constraint, or when the user says "just do it". Never amplify a question that wants an answer ("what does X do?").

## Method

1. **Detect.** Weak if two or more apply: short (< 12 words); no target file, screen or system; no deliverable; no constraint (engine, platform, budget); only taste words.
2. **Ground it.** Read what's there before writing the brief: the repo's README and CLAUDE.md and the file or screen the request most likely means. A brief about code you haven't read is a guess.
3. **Restructure** into six lines:
   - **Goal:** what the player or user gets, in one sentence
   - **Tier:** the hierarchy tier and owner (HIERARCHY.md §2–§3), plus the intensity rungs it appears on
   - **Deliverable:** the concrete artefact (files, screens, effects)
   - **Constraints:** engine, platform (phone first), performance budget (ms), anything the repo's CLAUDE.md imposes
   - **Quality bar:** the 2–3 rules from the matching skill's self-check that matter most
   - **Done when:** an observable check (a test passes, a capture shows X, numbers hit Y)
4. **Enrich.** Add 5–12 lexicon terms (`lexicon.json`) that fit the domain, with their prompt phrases where they make the brief concrete.
5. **Escalate.** Offer three options drawn from the matching skill's "Make it insane" section:
   - **Solid:** the hierarchy-correct version that ships
   - **Bold:** one signature idea on top
   - **Insane:** the escalation that makes it memorable
6. **Show it compactly** (format below), then **start on Solid immediately**. If the user picks another option later, switch.
7. **Stay honest.** Everything the user didn't say is marked *(suggested)*. Don't add features beyond the request's scope. If the request is ambiguous between two different things, pick the likelier one, say so in one line and proceed.

### Output format

```
> **Brief** (amplified from: "make the shop better")
> **Goal:** players see what's worth buying and feel the purchase.
> **Tier:** 3 HUD (UI owner) for the shop; 1 Moment for the purchase. *(suggested)*
> **Deliverable:** restyled shop cards + a purchase moment in ShopController. *(suggested)*
> **Constraints:** Roblox UI, phone first (390×844), ≤ 0.5 ms per frame while open.
> **Quality bar:** one loud element per card; gold only on price/buy; rarity ladder on frames.
> **Done when:** a phone capture shows readable prices; buying plays a ≤ 1 s moment; skip works.
> **Terms:** rarity frame, odometer counter, call-to-action, ghost bar, purchase moment, near-miss.
> **Options:** Solid: the above · Bold: + coins fly into the counter · Insane: + gyro-tilt foil on Mythic cards
> Going with **Solid**. Say "bold" or "insane" to switch.
```

## Hierarchy rules it obeys

The brief always names a tier (§2), an owner (§3) and the colour jobs that apply (§5), so the work starts hierarchy-correct.

## Engine notes

Default to the repo's engine (Roblox/Luau unless the repo says otherwise), phone first, and the frame budget in the hub's CLAUDE.md. For web labs, default to a single-file HTML page that loads with zero console errors.

## Examples: 10 before/after

| # | Before | After (core of the brief) |
|---|---|---|
| 1 | "make the shop better" | Goal: readable value and a felt purchase. Tier 3 cards + tier 1 purchase moment. Deliverable: shop card restyle (rarity frames, one loud Buy per card, gold price, odometer currency) + a ≤ 1 s purchase moment. Done: phone capture readable, buy → moment → skip works. |
| 2 | "add juice to hits" | Goal: hits feel heavy without hiding threats. Tier 2, hero owner. Deliverable: hit-stop (2 frames normal, 6 on kill), trauma shake (6 px, decays in 450 ms), a 1-frame flash, an impact ring. Constraint: no hit-stop at the calm rung; ≤ 6 decorations. Done: a capture shows the onset as the brightest frame and baseline within 12 frames. |
| 3 | "fix the ui" | Goal: the HUD reads in one glance on a phone. Tier 3, UI owner. Deliverable: audit + fixes (number format 3 sig. digits + suffix, colour jobs, one loud element per panel, safe-area insets). Done: 390×844 and 844×390 captures, nothing moving at rest. |
| 4 | "make the chest opening cool" | Goal: a reveal that escalates with rarity. Tier 1, ceremony owner. Deliverable: RewardSequence beats (container → item → identity → delta → continue), tier-coloured charge-up, rays at Legendary+, skip. Done: Common ≤ 1 s, Mythic ≤ 4 s, skip restores the world. |
| 5 | "I need a map" | Goal: a readable arena for the current game. Tier 4 world. Deliverable: seeded generator (lanes first, Poisson-scattered props with a lane mask, 1–3 landmarks per screen). Done: the same seed gives the same map; the squint test shows lanes and threats. |
| 6 | "balance the upgrades" | Goal: smooth pacing to the first prestige at ~20 min. Deliverable: content rows retuned + a pacing report (`Curves.pacing`, no wait jump > 2×). Constraint: numbers only in content. Done: the simulated player hits the first reset between 15 and 30 min. |
| 7 | "make items look premium" | Goal: rarity readable from the material alone. Tier 5. Deliverable: a rarity → material map applied to frames and icons (flat → satin → brushed → glass → chrome → holo → void). Done: icons pass the 2-band gate at 48 px; Common and Uncommon don't move. |
| 8 | "the game lags" | Goal: hold 60 fps on desktop with headroom for phones. Deliverable: per-layer timings, top 3 costs fixed, budget table updated. Constraint: no visual change unless agreed (golden frame unchanged). Done: worst-case frame time before and after, written down. |
| 9 | "add a level up" | Goal: levelling feels earned and shows what changed. Tier 1. Deliverable: XP bar fill with a leading-edge glow → burst at full → level number stamp → "what changed" card → continue. Done: under 2 s, skippable, XP blue only. |
| 10 | "make it insane" (on a working effect) | Goal: escalate without breaking readability. Deliverable: the effect's "Make it insane" option #1 from its skill, gated to boss/finale rungs. Constraint: stays inside ownership; reduced-motion fallback. Done: a capture at the busiest rung still shows every threat. |

## Make it insane

1. **Repo-aware briefs:** pull the deliverable's file paths from the repo map and the last commit touching that area, so the brief names real files.
2. **Before/after captures:** the brief's done-check includes a headless capture of the current state, so "better" has a baseline.
3. **Brief memory:** store accepted briefs in the repo (`docs/briefs/`) so the next vague prompt about the same area starts from the last brief.

## Self-check

- [ ] Only amplified when the prompt was actually weak.
- [ ] Read the relevant code or screen before writing the brief.
- [ ] All six lines present; additions marked *(suggested)*.
- [ ] 5–12 lexicon terms that fit the domain.
- [ ] Solid / bold / insane offered, then work started on Solid without waiting.
- [ ] Nothing in the brief contradicts the repo's CLAUDE.md.
