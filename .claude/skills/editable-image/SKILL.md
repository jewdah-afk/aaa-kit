---
name: editable-image
description: Use when drawing pixels yourself in Roblox with EditableImage - pixel-art renderers, owner buffers, layered compositing, procedural textures, minimaps, pixel HUDs, dynamic decals, buffer-based drawing, WritePixelsBuffer performance and pooling. Triggers on "EditableImage", "pixel renderer", "WritePixelsBuffer", "draw pixels", "pixel art in Roblox", "procedural texture", "owner buffer".
---

# editable-image

An EditableImage renderer draws the whole frame into a pixel buffer and uploads it once. The reference implementation is the cursed-survivors renderer: 480×270 hard pixels, an owner buffer and a measured cost of about 3.4 ms light and 7.0 ms at the endgame on desktop.

## When to use

- A 2D game or HUD drawn as hard pixels
- Procedural textures, minimaps, fog-of-war, painted decals
- Anything needing per-pixel ownership or effects that instances can't do

**Not for:** standard UI (use instances, see `ui-hud`) or 3D meshes (`editable-mesh`).

## Method

1. **Choose the resolution once.** Make it one knob (`W`, `H`, `SCALE`). 320×180 or 480×270 for a pixel game. Set the ImageLabel's `ResampleMode = Pixelated` and integer-scale it.
2. **Allocate buffers once.** Colour is `buffer.create(W*H*4)` (RGBA8) and owner is `buffer.create(W*H)` (u8). Never allocate per frame.
3. **Clear cheaply.** `buffer.fill` for the owner, and a pre-baked background copied with `buffer.copy` for colour.
4. **Draw in layer order:** ground → props → pickups → actors → FX → heat/light → numbers → UI. Every write goes through the owner rule (`CAN[writer][dest]`).
5. **Snap to whole pixels.** Integer coordinates only (`x // 1`), and sprites authored at the base size.
6. **Upload once per frame.** `editableImage:WritePixelsBuffer(Vector2.zero, size, colour)`.
7. **Pre-shade sprites.** Bake each sprite per palette band at load. At draw time it's a copy, not maths.
8. **Measure every layer** with `os.clock()` deltas into a rolling average, shown in a debug overlay, and keep a budget table (see below).
9. **Keep gameplay independent.** The sim never reads the frame. FX never move gameplay pixels.
10. Run the self-check.

### Measured budget (desktop Studio, 480×270, from the reference renderer)

| Layer | Quiet | Endgame (~300 enemies) |
|---|---|---|
| Light | 0.9 ms | 0.7 ms |
| Ground (band-stretch copies) | 0.85 ms | 1.0 ms |
| Props | 1.1 ms | 1.0 ms |
| Actors | 0.2 ms | 1.2 ms |
| FX | 0.03 ms | 1.4 ms |
| Upload | 0.09 ms | 0.09 ms |
| **Total** | **~3.9 ms** | **~7.0 ms** |

A phone is roughly 4–5× slower and hasn't been measured. Plan the first cuts in advance: half-resolution light, every-other-frame world passes, and glyph LOD for crowds.

## Hierarchy rules it obeys

- §3: the owner buffer *is* pixel ownership (0 background … 7 ceremony).
- §8: friendly FX can't hide a threat (`CAN[HERO][THREAT] = false`).
- §10: protected masks read from a half-resolution protect grid.
- §11: the hero's thin ring darkens what's under it by 2 bands.
- §12: crowd LOD switches cells to aggregate glyphs with hysteresis.

## Engine notes

**Roblox.**

- Create with `AssetService:CreateEditableImage({ Size = Vector2.new(W, H) })` and show it with `imageLabel.ImageContent = Content.fromObject(img)`.
- EditableImage counts against a per-device memory budget. Creation can fail on low memory, so check for `nil` and fall back.
- Read back only when you must (`ReadPixelsBuffer` is slow). Keep your own buffers as the truth.
- Live clients usually run without native codegen, so optimise for the interpreter: hoist locals, avoid closures in inner loops, use `buffer.writeu32` for whole pixels, and copy whole same-colour runs.

**Web equivalent.** `ImageData` plus `Uint32Array` views, `putImageData` once per frame, and `imageSmoothingEnabled = false`.

## Library and research

- [`lib/frontier`](../../../lib/README.md): `ImagePool` (byte budget, evict-and-retry on nil), `Atlas` + `Uploader` (many surfaces through one refresh per frame), `IndexedFrame` (1 byte per pixel, dirty tiles, palette cycling), `Snapshot` (save and replicate canvases), plus falling sand, radiance-cascade GI, Voxel Space and sprite stacking.
- [`lib/pixelfx`](../../../lib/pixelfx/README.md): 15 ready effects (lightning, dissolve, bloom, outlines, crowd) writing `WritePixelsBuffer`-ready RGBA8.
- Research: [EditableImage API](../../../docs/research/20-roblox-editableimage-api.md), [technique cookbook](../../../docs/research/40-editableimage-technique-cookbook.md), [Luau performance](../../../docs/research/22-luau-performance-engineering.md).

## Example

`examples/PixelFrame.luau` holds the colour and owner buffers, the `CAN` table, pixel snapping, clipped rects and coverage (for FX budgets). It's tested in `examples/PixelFrame.test.luau`.

```lua
local PixelFrame = require("./examples/PixelFrame")
local O = PixelFrame.OWNER
local W, H = 480, 270
local frame = PixelFrame.new(W, H)

-- Roblox setup (client):
-- local img = AssetService:CreateEditableImage({ Size = Vector2.new(W, H) })
-- label.ImageContent = Content.fromObject(img); label.ResampleMode = Enum.ResamplerMode.Pixelated

local function render()
	frame:clear(12, 10, 20)
	frame:rect(0, 200, W, 70, 40, 52, 38, O.WORLD)        -- ground strip
	frame:rect(230, 120, 12, 16, 230, 220, 190, O.HERO)   -- hero
	frame:rect(300, 128, 8, 8, 255, 74, 74, O.THREAT)     -- enemy shot (wins over hero FX)
	-- img:WritePixelsBuffer(Vector2.zero, Vector2.new(W, H), frame.color)
end
render()
```

## Make it insane

1. **Battle history in the ground:** scorch marks, blood and footprints written into 16×16 "history blocks" that only exist where something happened, so cost stays flat until the ground fills up.
2. **Glyph LOD:** distant crowd cells collapse into ASCII density glyphs (`.` `:` `*` `#` `@`) that carry exact counts, with hysteresis, and turn back into sprites as you approach.
3. **Banded lantern light:** an 8-band lightness quantiser driven by a half-resolution light map, with a 1 px dither at band edges. It gives a painterly cel look at a fixed cost.

## Self-check

- [ ] No buffer is allocated per frame (grep the render loop for `buffer.create` and `{}`).
- [ ] Exactly one `WritePixelsBuffer` per frame.
- [ ] Every write goes through the owner rule; a test proves hero FX can't cover a threat.
- [ ] Integer coordinates only; ImageLabel set to Pixelated with integer scale.
- [ ] Per-layer timings recorded; worst case written down with the device.
- [ ] Gameplay runs identically with rendering disabled.
- [ ] A golden frame or checksum catches unintended pixel changes.
