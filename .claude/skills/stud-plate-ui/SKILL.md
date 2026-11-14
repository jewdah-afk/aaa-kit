---
name: stud-plate-ui
description: Use when making Stud Plate buttons and HUD plates for a stud/voxel Roblox game without FrameWisp - plates with an ink rim, sill, gradient or algorithm face and the map's stud texture baked edge to edge, voxel-rendered square icons, the growing luck meter, Figma spec boards (tokens, anatomy, states, motion) and the TweenService motion table that replaces a FrameWisp import. Triggers on "stud plate", "studded button", "without framewisp", "no framewisp", "luck meter", "voxel icons for the hud", "stud texture on the plates", "spec board".
---

# stud-plate-ui

Clickable HUD plates that look like they were built from the same bricks as the world. One plate recipe, one stud tile (the map's), one motion table, used in Figma and rebuilt layer for layer in Roblox, so nothing goes through FrameWisp.

## When to use

- Designing or rebuilding HUD buttons, chips and hotbar slots in the Stud Plate style
- The studs look wrong on plates (stretched, centred with odd gaps, per-stud layers)
- Icons for clickable tiles that should match a stud-voxel world
- Showing luck (or any multiplier) that grows during a moment, like a throw in flight
- Handing a Figma HUD to Roblox without a FrameWisp import

**Not for:** general HUD rules, number formatting and bars (`ui-hud`), reward ceremonies (`reward-moments`), the 3D voxel models themselves (`lihfolk-stud-voxel`).

## Method

1. **Capture first.** Mock over a real in-game capture of the busiest view (for the winter thrower: facing the corridor of worlds). Paint the old HUD out of it (`media/ui/hud-v4/README.md` shows the mirror-fill trick); never mock on a flat colour.
2. **Plate recipe** (`examples/StudPlateSpec.luau`, Figma "2 · Plate anatomy"): glow (22 px, 55%) → ink rim (4 px, radius 12) → sill (7.5% of height) → face (family gradient, or an algorithm texture from `tools/lookdev/stud_fills.py`) → **studs** → sheen (top 40%, white 26% → 0) → bevel line (3 px) → icon → label (Fredoka One, ink stroke 14% of size).
3. **Studs = the map's tile, tiled, nothing else.** Use `.claude/skills/lihfolk-stud-voxel/assets/roblox_square_studs.png`. One tiled fill per face, starting at the face's top-left, 22 px pitch (tile 176 px). Never a grid of stud layers, never centred, never stretched. Figma: an IMAGE fill, TILE, OVERLAY, 85%, using the UI-contrast bake (`media/ui/hud-v4/fills/studs_ui_overlay.png`, contrast ×2.1). Roblox: two tiled ImageLabels from `tools/lookdev/stud_overlay_split.py` (`studs_light` 30%, `studs_dark` 20%), which match the Figma overlay to ~5/255.
4. **Icons are voxel renders**, not vectors or clip art: `python3 tools/lookdev/voxel_icons.py OUT [names]` (needs `pip install bpy`). Each icon is a small voxel model with the map's studs (one per 2×2 voxels), lit warm key / cool fill / rim, then given the ink sticker outline. Clickable tiles are square (168×176) with the icon breaking the top edge and the label across the bottom.
5. **Colour jobs.** The icon must contrast with its plate (an orange paw goes on violet, not gold). One family per button, set in `Spec.BUTTONS`; hide a button with `visible = false` (Upgrades is off for release).
6. **Luck meter** replaces any world/progress banner during play: voxel clover + Luckiest Guy number + caption + rung pill, no plate. `examples/LuckMeter.luau` gives the rung (CALM, WARM, LUCKY, HOT, MYTHIC), scale, gradient, glow, sparkles, count-up curve and punch.
7. **Motion from data.** `examples/StudMotion.luau` holds the motion table that the Figma board shows (press, hover, window open, luck tick, rung-up, rest, currency pop, badge bob, selection breathe). Wire a plate with `StudMotion.wire(plate, onActivate)`.
8. **Spec board.** For every proposal, publish tokens, anatomy (exploded), states (rest, hover, pressed, disabled, notify), the luck ladder, the motion table and the easing curves, cloned from the real mockup plates so the two can't drift.
9. Run the self-check, then the `ui-qa` and `visual-hierarchy` agents.

### v5: socket buttons and the 4×4 checker (current)

- **Clickables only** (HUD buttons, hotbar 1–9 + 0, window close, buy, tabs, filters) are socketed and studded. Balance, luck, window headers and cards stay flat: studs mean "you can press this".
- **Socket:** a dark well (8 px margin) holding a cap: ink rim, a 10 px side (the depth) and the face. Press = the cap sinks 8 px into the well in 40 ms (Quad Out) and rises in 90 ms. No bounce. Selected tabs stay pressed. `examples/SocketSpec.luau` holds the numbers, `examples/StudSocket.luau` builds and wires it.
- **1:1 studs:** one stud is always 12 px at 1080p. Faces are whole 4×4 blocks (multiples of 48 px; `SocketSpec.isWholeBlocks`, `snap`). The stud tile (8×8 studs = 96 px) starts at the face's top-left.
- **On/off 4×4 pattern:** three face layers over the family gradient: the block mask (`studs_checker_blocks.png`, dark blocks −15%, light +9%), then the map stud as overlay (`studs_checker_overlay.png` in Figma, `_light` + `_dark` in Roblox). Bake with `tools/lookdev/stud_checker.py`.
- **Labels sit on the face, never on the side:** bottom 12 px above the face edge (`SocketSpec.LABEL_GAP`), on a dark seat gradient over the bottom 56 px (tiles) / 40 px (slots). Square-tile icons break the top edge by 30 px.
- **Type:** Montserrat Black / ExtraBold, mitred ink stroke ≈ 9% of size, soft 50% shadow. No Fredoka or Luckiest Guy; round joins and hard drops read as bubbly.
- **Windows:** flat header in the window's family colour with a voxel icon breaking the top-left, a ruby 1-block close socket, sections in caps, cards with a rarity-coloured stroke. Shop follows the IMI 2 flow: balance + jumps to packs, featured, packs, passes (OWNED), supporter tiers, codes, Purchase Options with Gift.
- **Animal icons:** render the kit's critters with `tools/lookdev/critter_icon.py` (Cycles, no GPU) and outline them with `voxel_icons.sticker`.

## Hierarchy rules it obeys

- §2: plates are tier 3; the luck meter is tier 2 while a throw is in flight, then rests back to tier 3 (60% opacity, CALM size).
- §5: gold only for coins and luck, lime for buy (+) and the daily reward, ruby only where it's a shop/notify colour.
- §6: at rest only the Daily badge and the selected slot move.
- §13: one loud element per panel: the luck number at the top, the balance at the bottom-left.

## Engine notes

**Roblox.** Frames + `UICorner` for rim, sill and face; `UIGradient` (Rotation 90) for the face; tiled `ImageLabel`s (`ScaleType.Tile`, `TileSize` 176 px × UI scale) for studs; a 9-slice `ImageLabel` (`glow_9slice.png`, SliceCenter 64) tinted the glow colour, since Roblox has no blur; `UIStroke` (half the Figma OUTSIDE width) on labels; `Font.fromEnum(Enum.Font.FredokaOne / LuckiestGuy)`. Press and hover tween Position and transparency only; window pops use a `UIScale`. Scale everything by `Spec.scaleFor(viewport height)` (0.5 floor on phones) and keep touch targets ≥ 44 px after scaling.

**Figma.** Build plates with the Plugin API (rim rect, sill rect, face frame with clip, fills `[gradient, stud IMAGE TILE OVERLAY]`), upload renders with `upload_assets`, and keep the spec board on the same page as the mockup.

**Web.** CSS `background-blend-mode: overlay` with the UI stud tile gives the same face for prototypes.

## Example

`examples/SocketSpec.luau` (test: `examples/SocketSpec.test.luau`) and `examples/StudSocket.luau` (v5 socket buttons), `examples/LuckMeter.luau` (test: `examples/LuckMeter.test.luau`), `examples/StudPlateSpec.luau` (test: `examples/StudPlateSpec.test.luau`), `examples/StudPlate.luau` (builder) and `examples/StudMotion.luau` (motion table).

```lua
local StudPlate = require("./examples/StudPlate")
local StudMotion = require("./examples/StudMotion")
local Spec = require("./examples/StudPlateSpec")

local assets = { studsLight = Ids.StudsLight, studsDark = Ids.StudsDark, glow = Ids.Glow, textures = { frost = Ids.Frost } }
local scale = Spec.scaleFor(workspace.CurrentCamera.ViewportSize.Y)
local shop = StudPlate.build(hud.Left, {
	family = Spec.BUTTONS.Shop.family, size = Vector2.new(168, 176), position = UDim2.fromOffset(28, 342),
	icon = Ids.IconBasket, iconRect = Rect.new(9, -26, 159, 124), label = "Shop", labelSize = 40, labelY = 112, scale = scale,
}, assets)
StudMotion.wire(shop, function() Windows.open("Shop") end)

local luck = StudMotion.luck({ number = top.Luck.Value, gradient = top.Luck.Value.UIGradient, clover = top.Luck.Clover, scale = top.Luck.UIScale, pill = top.Luck.Rung.Label })
Throw.LuckChanged:Connect(luck.set) -- server value, punches on each new rung
Throw.Landed:Connect(luck.rest)
```

## Make it insane

1. **Mesh plates:** the same recipe as EditableMesh geometry (raised studs, slanted lip) so plates catch real light and the press is a true depth change (`editable-mesh`).
2. **Living faces:** algorithm faces (aurora, galaxy) scroll their UV a few px per second only while a rare slot is selected, so the rarity is felt without looping at rest.
3. **Luck in the world:** at MYTHIC the clover sheds stud-sized voxels that fly to the ball, and the corridor's world gates light up in the rung colour.

## Self-check

- [ ] Studs only on clickables; one stud = 12 px; every studded face is whole 4×4 blocks; tiles start at the face's top-left; no stud layers, no stretching.
- [ ] Press sinks the cap into its socket (8 px, 40 ms down / 90 ms up), no bounce.
- [ ] Every clickable tile is square with a voxel-render icon that contrasts with its plate.
- [ ] Hidden buttons are hidden in `Spec.BUTTONS`, not deleted.
- [ ] The luck meter has no plate and reads at 844×390 (≥ 28 px digits after scaling).
- [ ] Mockup sits on a real capture with the old HUD painted out.
- [ ] Motion matches the table; at rest only the Daily badge and selected slot move.
- [ ] `lune run` on both tests passes; Studio play test done on PC and phone emulator (say so if not).
