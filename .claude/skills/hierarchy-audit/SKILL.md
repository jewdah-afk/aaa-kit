---
name: hierarchy-audit
description: Use to measure visual hierarchy instead of guessing - "does the eye go to the buy button", "what does the player look at first", "is this text readable", "check contrast", "colour blind check", "is this flashing safe", "flashing effect safe", "photosensitive", "audit the hierarchy of this screenshot", "salience", "squint test". Predicts the scanpath of a screenshot, scores focus lift and competitors, checks APCA contrast, rarity ladders under colour blindness, and WCAG flash safety on effect GIFs. Python tool plus an in-game Luau module.
---

# hierarchy-audit

HIERARCHY.md states what should win; this skill **measures** whether it does. Every number comes from Part V of the research ([chapters 80–85](../../../docs/research/85-measuring-hierarchy.md)).

## When to use

- Before showing any screen, HUD, reward moment or effect for review
- "Is this readable?", "does it pop?", "is the CTA clear?", "colour-blind safe?", "is this flash safe?"
- Picking or changing theme, rarity or team colours
- A look-dev pass needs numbers in its notes

**Not for:** designing the screen (`ui-hud`, `reward-moments`), designing the effect (`vfx`), choosing a palette from scratch (`art-direction`). Those skills make the thing; this one checks it.

## Method

1. **Capture** the screen at its real size: Studio screenshot, a Figma export, or a Playwright capture of an HTML mock. For an animated cue, capture the frame where it peaks.
2. **Name the focus.** Write down the one element that must win (HIERARCHY §13) and its rect `x,y,w,h`.
3. **Run the audit:** `python3 tools/hierarchy/hierarchy.py audit shot.png --focus x,y,w,h --out pass-03`. Read `pass-03.png`. Green numbered circles are fixations inside the focus; red ones are outside.
4. **Read the verdict:** first fixation in the focus, lift ≥ 1.5, competitor < 90%, squint gap ≥ 0.08 OKLab L, still in the focus under deutan and protan.
5. **Fix the cause, not the symptom.** Lower clutter or a competitor before raising the focus ([ch. 84 §4](../../../docs/research/84-grouping-density-and-choice.md#4-clutter)). Change value before hue. Add a shape or icon when the cue relies on hue.
6. **Text:** `hierarchy.py apca '#fff' '#1a1a2e'`. abs(Lc) ≥ 75 for play-critical numbers, ≥ 60 for labels, ≥ 30 for disabled text.
7. **Effects:** `hierarchy.py flash effect.gif`. A FAIL is a safety bug; throttle the effect to ≤ 3 flashes per second, or shrink it below 2.78% of the screen.
8. **In game:** put the theme and rarity pairs through `Perceptual.audit` and `Perceptual.ladder` at Studio start, and warn on failures.
9. **Confirm with people** a few times per project: first-click and five-second tests ([ch. 85 §5](../../../docs/research/85-measuring-hierarchy.md#5-validating-with-people)).

## Hierarchy rules it obeys

- §2 loudness tiers and §13 one loud element: the focus must hold the first fixation, and competitors stay under 90% of its peak.
- §5 colour jobs and §11 figure-ground gate: the squint value gap, the deutan and protan re-check, and no hue-only codes.
- §7 rarity ladder: `Perceptual.ladder` regression on the shipped colours.
- §9 time: flashes ≤ 3/s over 2.78% of the screen (WCAG 2.3.1), and messages ≥ 500 ms apart (attentional blink).

## Engine notes

- The tool needs only Python 3, numpy and Pillow, and takes about 0.5 s for a 1280 × 800 screenshot.
- The 8-band figure-ground gate (HIERARCHY §11) is a separate module, `Contrast.luau` in [art-direction](../art-direction/SKILL.md). Use it for silhouettes against their surroundings, and `Perceptual.luau` for text, palettes and colour blindness.
- `Perceptual.luau` is pure maths (no Roblox APIs), so it runs in lune, Studio and live servers. Feed it `Color3` values; it reads `.r .g .b`.
- Roblox has no system colour-blind mode, so offer a palette setting and check both palettes with `Perceptual.ladder`.
- `GuiService.ReducedMotionEnabled`: when it's on, swap flashes and shakes for value dips (research ch. 81 §4).

## Example

`examples/Perceptual.luau` (test: `examples/Perceptual.test.luau`) has APCA, WCAG, OKLab, ΔE, OKLab mixing, Machado CVD simulation, theme-pair audit and the rarity-ladder check. Its regression test pins the HIERARCHY.md rarity colours.

```lua
local Perceptual = require("./examples/Perceptual")
local hex = Perceptual.hex
local fails = Perceptual.audit({
	{ name = "coin count", fg = hex("#ffffff"), bg = hex("#1a1a2e"), floor = 75 },
	{ name = "shop label", fg = hex("#9aa4b2"), bg = hex("#1a1a2e"), floor = 60 },
})
for _, f in fails do
	warn(`contrast: {f.name} Lc {math.floor(f.lc)} < {f.floor}`)
end
local problems = Perceptual.ladder({ hex("#9aa4b2"), hex("#4fd17a"), hex("#5ab4ff"), hex("#b25cff") })
assert(#problems == 0, table.concat(problems, "\n"))   -- rarities stay apart under colour blindness
local gradientMid = Perceptual.mixOklab(hex("#5ab4ff"), hex("#ffb02e"), 0.5)  -- no grey mud
```

## Make it insane

- **Live salience overlay in Studio:** capture the viewport, run the auditor through a local HTTP helper, and draw the heatmap and fixation numbers on a debug ScreenGui (F5, next to the F3/F4 overlays in the [studio playbook](../../../docs/playbooks/studio-workflow.md)).
- **Hierarchy CI:** export every Figma frame, audit it with the CTA rect from the layout JSON, and fail the PR on any FAIL. Post the overlays as a gallery.
- **A scanpath movie:** run the audit on every frame of a capture and render fixation 1 as a dot moving over the GIF, to see whether the eye gets pulled off the reward mid-reveal.
- **Calibrate on players:** log first taps in playtests and fit the lift and competitor thresholds to them.

## Self-check

- [ ] The focus was named before the audit ran, not picked afterwards to match.
- [ ] The overlay was opened and read, not just the verdict.
- [ ] Every text pair on the screen has an Lc at or above its floor on its worst background.
- [ ] No information is coded by hue alone (deutan and protan re-check passed).
- [ ] Every new effect GIF passes `flash`.
- [ ] A FAIL on a text-heavy screen was checked with a person (the model can't read meaning).
