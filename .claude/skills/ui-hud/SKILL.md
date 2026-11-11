---
name: ui-hud
description: Use when building or fixing any HUD or in-game UI - currency and big-number displays (K/M/B/T), XP/HP/progress bars, cooldown icons, combo meters, loot/kill feeds, damage numbers, rarity frames and inventory slots, shop cards, buttons and UI juice. Triggers on "HUD", "UI", "bar", "counter", "cooldown", "inventory", "shop UI", "damage numbers", "make the UI pop", "fix the ui".
---

# ui-hud

The HUD is tier 3 (HIERARCHY.md §2). It's always on screen, so it stays still until a number changes, and then it tells you exactly what changed.

## When to use

- Laying out a HUD or a menu screen, or fixing one that "feels off"
- Any number the player watches: currency, XP, HP, timers, damage
- Slots, frames and cards that show rarity

**Not for:** full-screen reward reveals (use `reward-moments`), world VFX (`vfx`), colour palettes in general (`art-direction`).

## Method

1. **List what the player decides on this screen.** Each element must answer one of those questions; cut anything that doesn't.
2. **Rank the elements.** One loud element per panel (§13). Usually it's the primary action or the number that just changed.
3. **Place by priority.** On phones, the thumbs cover the bottom corners: put critical status top-left/top-centre and actions bottom-right. Keep a safe-area inset (`GuiService:GetGuiInset()`, `ScreenGui.ScreenInsets = DeviceSafeInsets`).
4. **Format numbers.** Three significant digits plus a suffix (`1.23K`, `45.6M`), floored, tabular-width digits, and the suffix letter in the currency colour. Show the full value with commas on hover or long-press.
5. **Animate only on change.** The value rolls toward the target (odometer, ~140 ms per digit). A gain pops at +8 % scale for 120 ms. Nothing idles.
6. **Bars.** A fill with an eased leading edge plus a delayed "ghost" bar that trails losses by 300–500 ms, so damage reads as a chunk.
7. **Cooldowns.** A radial sweep (dark over the icon), a seconds count under 10 s, then a 1-frame white flash plus a ring when ready.
8. **Feeds and toasts.** Stack from one edge, at most 4 visible, auto-fade at 2.5 s, and merge repeats ("+3 Gems ×4").
9. **Damage numbers.** Pop-scale 1.4→1, drift up 20 px, fade by 600 ms. Crits are bigger and outlined. Cap them at 12 on screen and merge into running totals beyond that.
10. **Rarity frames.** Use the ladder from `materials/examples/RarityStyle.luau`: each tier adds one behaviour.
11. Run the self-check.

## Hierarchy rules it obeys

- §2: HUD is tier 3, below moments and combat and above world.
- §3: UI owns its pixels (rank 6); only ceremonies cover it.
- §5: gold = currency/CTA, blue = XP, red = danger only.
- §6: calm frames stay calm, so nothing loops at rest except the selection.
- §7: the rarity ladder.
- §9: critical numbers (HP) never wait; decorative pops take slots.
- §13: one loud element per panel.

## Engine notes

**Roblox.** Use `UIStroke` for outlines, `UIGradient` for sweeps, `UIAspectRatioConstraint` and `UIScale` for phone scaling, and TextLabels with `FontFace` set to a monospace or tabular font for counters. Tween only what changes (`TweenService`). Avoid per-frame `Text` writes when the value hasn't changed. For pixel-art HUDs drawn into an EditableImage, see `editable-image`.

**Web.** Canvas 2D for juice, DOM for text-heavy menus. Use `font-variant-numeric: tabular-nums` and honour `prefers-reduced-motion`.

## Example

`examples/Odometer.luau` is a pure rolling-digit model used by both a Roblox TextLabel row and an EditableImage HUD (test: `examples/Odometer.test.luau`). The framework starter's `CoinCounter` component shows the Roblox side, and [effects-gallery.html](../../../examples/web/effects-gallery.html) has the odometer, rarity frames and XP bar running live.

```lua
local Odometer = require("./examples/Odometer")
local odo = Odometer.new(7)          -- 7 character slots, right-aligned
odo:set(1234567)                     -- "  1.23M"; only changed digits roll
-- every frame:
if odo:step(dt) then                 -- false when still: skip the redraw entirely
	for i, slot in odo.slots do
		local prevY, curY = Odometer.offsets(slot)   -- in glyph heights
		-- draw slot.prev at y + prevY * glyphH, slot.cur at y + curY * glyphH, clipped to the slot
	end
end
```

## Make it insane

1. **Living numerals:** each digit is a tiny particle system that reassembles into the next digit (≤ 40 particles per digit, only while rolling).
2. **Diegetic HUD:** health as a lantern on the character and currency as a physical coin stack in the corner that topples on spend, with the flat number still shown small for clarity.
3. **Combo ladder:** the combo meter climbs named tiers (NICE → GREAT → INSANE → GODLIKE), each with its own frame material from the rarity ladder, and shatters into the ghost bar when it breaks.

## Self-check

- [ ] At rest, nothing moves except the selection (record 3 s idle; diff the frames).
- [ ] Every number is floored, uses 3 significant digits plus a suffix, and has tabular width.
- [ ] Gold, blue and red each appear only for their job.
- [ ] One loud element per panel.
- [ ] Touch targets ≥ 44 px; nothing important in the bottom corners on a phone.
- [ ] Losses show a ghost bar; gains pop once.
- [ ] Damage numbers capped and merged.
- [ ] Works at 390×844 and 844×390 inside the safe area.
