# Figma → Roblox UI

How we design game UI in Figma and get it into Roblox exactly as designed. Claude does the Figma work through the Figma MCP (`use_figma`, `get_screenshot`, `get_metadata`, `upload_assets`) and the game work through Rojo.

Tools: [tools/figma](../../tools/figma/README.md) · runtime: [lib/figma-ui](../../lib/figma-ui/README.md) · QA agents: [.claude/agents](../../.claude/agents/)

## 1. The loop

```
inventory → hero design → kit-built frames → spec card → owner review
     → export → build layouts → render in game → zoomed QA → handout
```

1. **Inventory first.** List every screen, panel, popup and HUD element the game needs. Mark each **E** (exists and is correct), **D** (exists but differs) or **M** (missing), and show the owner the list before designing anything.
2. **Hero design before building.** One polished frame sets the style (the owner approves it), and every other screen copies it. Never build a screen in code before its Figma hero exists.
3. **Build frames with the kit**, never freehand. Paste `kit.js` at the top of every `use_figma` call (each call is a fresh context) and keep each script under ~45 KB. Build a window in a few calls: frame + header + tabs, then rows, then details.
4. **Duplicate, don't redraw.** New windows clone an existing one and change only text, icons and theme colours.
5. **Spec card beside every window** (`SPEC(...)`): size + layout, visual hierarchy, build notes, states, motion, sound, open questions.
6. **Show the owner a screenshot** after each window or group. Ask before redesigning anything that already exists.
7. **Export → build → render** (section 4), then QA zoomed in (section 7), then write what changed into the handout.

## 2. Parallel design agents

Many windows were built at once by giving each design agent one column of a shared board. The brief each agent got:

- **Where:** the file key, the page, the board, and the agent's column: board-local `x0 = 40 + col × 1400`, width 1360, a fixed `y0`. Never create, move or delete anything outside that column; never edit components, the HUD board, the icon strip or other windows.
- **References:** 2–5 finished windows to screenshot first and match exactly.
- **Kit:** paste the whole `kit.js` at the top of every script.
- **Icons:** only the glossy painted PNGs. To add one, create `icons/<slug>` frame with 72×72 `src/<name>` rectangles, `upload_assets` with those node ids (`scaleMode: "FIT"`), then POST each PNG to the returned URL (`curl -X POST -H "Content-Type: image/png" --data-binary @file.png <submitUrl>`). The next kit run picks them up.
- **Data:** a believable mid-game state (some owned, some buyable, some locked) using real numbers from the game data.
- **QA before returning:** screenshot at full size (`maxDimension` 1600), check the list in section 7, fix, repeat (max 4 rounds), then add the spec card and report what's still imperfect.

## 3. Style rules (learned the hard way)

| Rule | Detail |
|---|---|
| Squared | Ink body radius 4, faces and lips 2.5, plates 4, wells 3. One black ink outline (`#0B0C10`). No coloured rims, no glows on frames. |
| Keycaps | Ink body → lip (face colours × 0.58, shifted down by depth D) → face (stripes 12 %) → gloss cap (0.45 → 0.04 over the upper 42 %). Dark faces: gloss ≤ 0.2. |
| Pressed | The **whole key** drops by D: ink body and face move down together, the body loses D height, the lip hides. A face sinking inside a full-height body (a black band on top) is wrong. |
| Top highlight | A 1.5 px highlight strip inside the outline. Never a white inner shadow over an inside stroke: it greys the top outline. |
| Window | Square-top modal, 1000–1200 wide, ≤ 880 tall. Continuous 4 px ink outline drawn last, header included (5 px read too thick). Close key 44 px at (W − 54, 10), never moved or duplicated. |
| Header | Title only, centred. Ends in one clean edge: a full-width 4 px ink line with at most one uniform 1–2 px highlight above it. No fading bevel strips or partial depth bands. |
| Text | One display family for all UI text. Body text gets a light 1.2 px ink outline and a 1 px ink drop. Minimum 12 px. Never type symbols on keys (+, −, ×, ✓, arrows); use drawn, centred glyphs. |
| Zero clipping | Size every box for the longest real value (big numbers like `1.84e+308` formatted as the game shows them). Measure with `textW`. |
| No dead space, no notches | Fill widths, centre content; joins share one outline and sit flush. |
| One CTA | Exactly one bright call to action per view (green BUY/CLAIM; gold for premium). Everything secondary sits on dark steel. The selected item gets a 3 px white ring. |
| Connector lines | Draw all ink segments first, then all coloured segments on top, square ends overlapping at elbows. Ink + colour per segment lets the next segment cut the joint. |
| Textures | Only the kit's seamless tiles (stripes, lattice, halftone). Check for seams wherever a frame clips one. |
| Colour by hero | Each window takes its palette from its hero icon: a deep base hue (header, hero, body), a bright contrasting hue for buttons and the active tab, and a third for stat text. Never three shades of one hue. |
| Upgrades look better | Anything that upgrades must look visibly better at each step; size tiers must grow. |

## 4. How Figma becomes game UI

1. `exporter.js` (read-only) dumps a frame's node tree in 19 KB slices.
2. `collect.py` reassembles the slices from the session transcripts.
3. `build_layouts.py` writes one Luau module per frame (node id in its header).
4. `lib/figma-ui/Render.luau` builds that table as GuiObjects at the Figma coordinates.

To re-export a changed frame, run the same three steps for that node id. Features a frame doesn't have yet go in an explicit patch module applied once to a copy, then move into Figma later so the patch can be deleted.

### Layer-name contract

The renderer and binders find things by name, so keep these exact:

| Layer name | Meaning |
|---|---|
| `header` (children `glow`, `top highlight`, `ink`), `window outline`, `btn/close` | window chrome |
| `tab/<LABEL>`, `tab/<LABEL> (active)` | tabs |
| `seg/<LABEL>` | segmented switches |
| `btn/<action>` | keys (buy, max, claim, craft, hatch, …); a keycap = `ink body` + `lip` + `face` |
| `ico/<name>` | an icon; must exist in the game's `Icons` table |
| `glyph/<name>` | a drawn symbol |
| `tex/…` | a tiled texture fill |
| `fx/shine`, `fx/pulse`, `fx/float`, `fx/spin`, `fx/glow`, `fx/sparkle` | animates while its window is open |
| `row/…` | list rows; lists clone the **first** row, so keep one clean template row |

Every `btn/`, `tab/` and `seg/` name needs a description entry (the hover card).

### What the importer can't reproduce (design around it)

- Vector "swoosh" shapes are dropped: use rectangles, gradients or an uploaded image.
- Radial and conic gradients become a soft ellipse: prefer linear.
- Letter spacing is ignored (Roblox has none): don't rely on it for fit.
- Rotated gradient strips inside clipping frames are approximate: keep sweeps axis-aligned.
- Images taller than ~2048 px don't render.

## 5. Placement in game

- Design canvas 1080 tall; `UIScale = viewport height / 1080`.
- One spacing table for everything: EDGE 24, GAP 8 (inside a group), GAP2 16 (between groups), WIN 24.
- One top edge (top-bar inset rounded up + 8) shared by the banner, meter and top-right group; one bottom edge (H − 24) for the icon row.
- Write an anchor table (element → anchor in design px) and keep it in the handout. Groups that might collide **compact** (scale down to a minimum) before they overlap.
- Windows scale into a **window region** that avoids the HUD groups. Opening a window closes the other one, and Esc / B / the close key close the window only.

## 6. Visual hierarchy for every screen

- **Emphasis levels:** L1 = one saturated primary key per window or list, the only element allowed to breathe or shimmer. L2 = steel secondary keys (MAX, inactive tabs, popup actions). L3 = text and ghost labels.
- **Colour semantics:** green = buy / go / affordable; gold = premium / maxed; red = close / danger / can't afford; violet = reset; blue = info; steel = neutral. (Matches [HIERARCHY.md §5](../../HIERARCHY.md#5-colour-has-jobs).)
- **Numbers lead:** bigger, white, ink-outlined. Labels follow, smaller and muted. Costs are icon + number.
- **Motion budget:** only the open window idles; the HUD has at most one attention animation and two badges; no key ever bounces; no per-frame loops.

## 7. QA (zoomed in, before the owner sees it)

Crop and upscale every region 2–3× and check:

- clipping (text, icons or outlines cut by a parent edge)
- overlap, misaligned sibling edges, uneven gaps
- broken or doubled outlines, light streaks, grey top outlines
- texture seams, notches, dead areas
- text under 12 px, placeholder text, icons off-centre
- more than one bright CTA

In game, also check that every key presses in and makes a sound, nothing scrolls sideways at phone width, and the console has zero errors. The [`ui-qa` agent](../../.claude/agents/ui-qa.md) does this crop-and-check pass and reports defects with locations.

### Headless UI harness

Before any Studio pass, the real UI modules ran on lune's Roblox instance model (`@lune/roblox`) with tween-completion chains simulated. The harness opened every window, tab and view; pressed every key; and asserted:

- every window sits inside the window region
- tab switches neither re-pop nor rebuild
- every button-like node is registered with press-in and a sound (a key audit: 1,036 of 1,036 wired at the last run)
- every icon name resolves
- lists and filters behave

A second script turned the layout dump into a 1920×1080 placement mock to check margins and overlaps. Build one per game; the method carries over.

## 8. Gotchas

- `use_figma` writes run one at a time. Re-fetch nodes after a component edit, because instance child ids change.
- The Figma connection can drop mid-session: reload the tools and continue (node ids are stable).
- Check file keys letter by letter (`l` vs `I`); a wrong key opens a file you can't access.
- A UIGradient on a CanvasGroup tints everything inside it: put gradients on a child frame.
- Only one UIScale applies per object: put the fit-to-height scale on a wrapper.
- The Roblox top-left menu covers HUD y < 60.
- Some fonts lack glyphs (e.g. `↔`): write words instead.
