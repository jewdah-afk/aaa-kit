---
name: editable-image
description: Use when drawing pixels yourself in Roblox with EditableImage - pixel-art renderers, owner buffers, layered compositing, procedural textures, minimaps, pixel HUDs, dynamic decals, buffer-based drawing, WritePixelsBuffer performance and pooling. Triggers on "EditableImage", "pixel renderer", "WritePixelsBuffer", "draw pixels", "pixel art in Roblox", "procedural texture", "owner buffer".
---

# editable-image

An EditableImage renderer draws the whole frame into your own pixel buffers and uploads it once. We shipped a full 2D game this way: 480×270 hard pixels, an owner buffer, ~300 enemies on screen, **11.5–13.5 ms of script on an iPhone 12** at 60 fps after a cut pass (it started at 20.6 ms). This skill is the procedure; the detail lives in `references/`.

| Need | Read |
|---|---|
| Limits, gates, sinks, pixel format, threads, saving | [references/api-and-limits.md](references/api-and-limits.md) |
| How a whole-game renderer is laid out (layers, ownership, tiers, fallbacks) | [references/renderer-architecture.md](references/renderer-architecture.md) |
| Measured ms: Studio vs desktop app vs phone, interpreter rules, what to cut | [references/performance.md](references/performance.md) |
| Effect recipes with costs and phone paths | [references/recipes.md](references/recipes.md) |
| Which algorithms suit pixels (families, top picks, Godrithm chains) | [references/algorithms.md](references/algorithms.md) |
| Golden frames, paired A/B timing, bench places | [references/testing.md](references/testing.md) |
| Symptoms → cause → fix | [references/gotchas.md](references/gotchas.md) |

## When to use

- A 2D game or HUD drawn as hard pixels
- Procedural textures, minimaps, fog-of-war, painted decals, live texture effects on a MeshPart
- Anything needing per-pixel ownership or effects that instances can't do

**Not for:** standard UI (use instances, see `ui-hud`), 3D geometry (`editable-mesh`), or a texture that never changes at runtime (bake it at edit time and upload it as an asset).

## Method

1. **Check the gates before designing.** Published games need the creator 13+ age + ID verified and **Enable Mesh / Image APIs** on. Limits: 1024×1024 max, `Size` read-only, **one displayed image refreshes per frame**, a small unpublished client memory budget (~32 MB reported, shared with EditableMesh). `Content.fromObject` doesn't replicate: generate on the client.
2. **Choose the resolution once.** One knob (`W`, `H`). 320×180 or 480×270 for a pixel game; author sprites at the base size and upscale **at load**. `ResampleMode = Pixelated`, integer scale, full-bleed on every aspect.
3. **Create safely.** `CreateEditableImage` returns **nil** on a full budget; `CreateEditableImageAsync` **throws** on permissions. Nil-check, `pcall`, clear the image, and show a readable fallback (never a black screen). Pool images under your own byte cap (`lib/frontier` `ImagePool`).
4. **Allocate buffers once.** Colour `buffer.create(W*H*4)` (RGBA8, straight alpha), owner `buffer.create(W*H)`. Nothing in the render loop allocates.
5. **Clear cheaply.** `buffer.fill` for the owner; a pre-baked background copied row by row with `buffer.copy`.
6. **Draw in layer order:** ground → props → pickups → actors → glyphs → FX → heat/light → numbers → post → UI. Every write goes through the owner rule (`CAN[writer][dest]`).
7. **Pre-bake everything static.** Sprites per palette/light band, opaque row spans, palette LUTs and grades. Draw time is copies, not maths.
8. **Blit with spans.** Long runs with `buffer.copy`, runs of ≤ 7 px with direct `writeu32` (calls cost ~50 ns vs ~5–10 ns per write in the interpreter). Integer coordinates only.
9. **Upload once per frame.** One `WritePixelsBuffer`; for static screens, only the dirty row band. More than one live canvas → composite or atlas (`Atlas` + `Uploader`).
10. **Tier for devices at startup.** Phone / mid / full. Per-pixel full-frame passes go half-res or half-rate first; per-body extras (rims, outlines, foil) are full-tier only.
11. **Measure on live clients.** Per-layer `os.clock()` EMA in a debug overlay, then a bench place on the desktop app and a real phone. Studio compiles `--!native`; live clients don't, so live is ~2.2× Studio overall and up to **7×** for per-pixel loops.
12. Run the self-check.

### Measured budget (480×270, worst endgame scene, ms)

| | Studio | Desktop app | iPhone 12 |
|---|---|---|---|
| Renderer before cuts | ~9.1 | 20.2 | 19.6 |
| Our code after cuts (phone tier) | – | 9.4 | **11.5** |
| After a look overhaul | – | 12.2 | 13.5 |
| Full tier on desktop / phone tier | – | 22.5 (actors 7.3) | 12.9 |

Target: **our code ≤ 12 ms on an iPhone 12** in the worst scene. Upload itself is 0.02–0.16 ms; the cost is always the drawing. Re-measure after every look change.

## Hierarchy rules it obeys

- §3: the owner buffer *is* pixel ownership (0 background … 7 ceremony).
- §8: friendly FX can't hide a threat (`CAN[HERO][THREAT] = false`).
- §10: protected masks read from a half-resolution protect grid.
- §11: the hero's thin ring darkens what's under it by 2 bands.
- §12: crowd LOD switches cells to aggregate glyphs with hysteresis.

## Engine notes

**Roblox.**

- Create with `AssetService:CreateEditableImage({ Size = Vector2.new(W, H) })`; show with `label.ImageContent = Content.fromObject(img)`. It's an `Object`: no `Parent`. Tear down with `Content.none` then `Destroy()`.
- Sinks: `ImageLabel/ImageButton.ImageContent`, `Decal.ColorMapContent`, `MeshPart.TextureContent`, `SpecialMesh.TextureContent`, `SurfaceAppearance` (only via `CreateSurfaceAppearanceAsync`). `HoverImageContent`/`PressedImageContent`, clothing and `ViewportFrame` don't take it.
- Buffers use alpha (255 opaque); `Draw*` uses transparency (0 opaque). `WritePixelsBuffer` reads from byte 0. `ReadPixelsBuffer` allocates every call; never read back per frame.
- Parallel: only `ReadPixelsBuffer` and `Size` are legal desynchronized. Compute in Actors, write after `task.synchronize()`.
- Optimise for the interpreter: hoist locals, no closures or `{}` in inner loops, whole-pixel `writeu32`, prefer engine `Draw*` calls for anything that's a rect, line or blit.
- Persist with `CreateAssetAsync` (plugins / Open Cloud only); in-game, save a compact codec (`Snapshot`).

**Web equivalent.** `ImageData` plus `Uint32Array` views, `putImageData` once per frame, and `imageSmoothingEnabled = false`.

## Library and research

- [`lib/frontier`](../../../lib/README.md): `ImagePool`, `Atlas` + `Uploader`, `IndexedFrame` (palette cycling, dirty tiles), `Snapshot`, falling sand, radiance-cascade GI, Voxel Space, sprite stacking, and `studio/Bench.client.luau` for live-client numbers.
- [`lib/pixelfx`](../../../lib/pixelfx/README.md): 15 ready effects writing `WritePixelsBuffer`-ready RGBA8.
- [`lib/surfacebake`](../../../lib/surfacebake/README.md): procedural textures baked onto mesh UVs (`Apply.bakeMeshPart`).
- Research: [EditableImage API](../../../docs/research/20-roblox-editableimage-api.md), [technique cookbook](../../../docs/research/40-editableimage-technique-cookbook.md), [Luau performance](../../../docs/research/22-luau-performance-engineering.md). Playbooks: [procedural textures](../../../docs/playbooks/procedural-textures.md), [look-dev loop](../../../docs/playbooks/look-dev-loop.md).

## Example

- `examples/PixelFrame.luau`: colour and owner buffers, the `CAN` table, snapping, clipped rects and coverage. Tested in `PixelFrame.test.luau`.
- `examples/SpanBlit.luau`: sprites as precomputed opaque row spans with the short-run rule, plus a dirty-row tracker that packs the band for a partial upload. Tested in `SpanBlit.test.luau`.

```lua
local PixelFrame = require("./examples/PixelFrame")
local SpanBlit = require("./examples/SpanBlit")
local O = PixelFrame.OWNER
local W, H = 480, 270
local frame = PixelFrame.new(W, H)
local band = buffer.create(W * H * 4)
local dirty = SpanBlit.dirty()

-- Roblox setup (client):
-- local img = AssetService:CreateEditableImage({ Size = Vector2.new(W, H) })
-- if not img then NoImage.show(gui) return end
-- label.ImageContent = Content.fromObject(img); label.ResampleMode = Enum.ResamplerMode.Pixelated

local function render()
	frame:clear(12, 10, 20)
	frame:rect(0, 200, W, 70, 40, 52, 38, O.WORLD)        -- ground strip
	frame:rect(230, 120, 12, 16, 230, 220, 190, O.HERO)   -- hero
	frame:rect(300, 128, 8, 8, 255, 74, 74, O.THREAT)     -- enemy shot (wins over hero FX)
	SpanBlit.mark(dirty, 0, H, H)                         -- full-frame game: whole band
	local y0, rows = SpanBlit.band(dirty, frame.color, W, band)
	-- img:WritePixelsBuffer(Vector2.new(0, y0), Vector2.new(W, rows), band)
	return y0, rows
end
render()
```

## Make it insane

1. **Battle history in the ground:** scorch marks and footprints written into 16×16 history blocks that exist only where something happened, so cost stays flat until the ground fills up.
2. **Glyph LOD:** distant crowd cells collapse into density glyphs (`.` `:` `*` `#` `@`) that carry exact counts, with hysteresis, and turn back into sprites as you approach.
3. **Banded lantern light:** an 8-band lightness quantiser driven by a half-resolution light map, with a 1 px dither at band edges. A painterly cel look at a fixed cost.
4. **Radiance-cascade GI:** soft shadows and colour bleed from `lib/frontier`, amortized under a 3.5 ms budget per frame, on the full tier only.

## Self-check

- [ ] Gates handled: works in a published place; nil budget shows a fallback; `CreateEditableImageAsync` is `pcall`ed.
- [ ] No buffer or table is allocated per frame (grep the render loop for `buffer.create`, `{}` and `ReadPixelsBuffer`).
- [ ] Exactly one displayed canvas updates per frame; one `WritePixelsBuffer` (or one dirty band).
- [ ] Every write goes through the owner rule; a test proves hero FX can't cover a threat.
- [ ] Integer coordinates; `Pixelated`; integer scale; no filtered upscales of pixel art.
- [ ] Per-layer timings recorded **on a real phone and the desktop app**, with device, client version and commit; phone tier ≤ 12 ms of script on an iPhone-12-class phone.
- [ ] Device tiers exist; per-pixel full-frame passes have a half-res or half-rate path.
- [ ] Gameplay runs identically with rendering disabled.
- [ ] A golden frame chain catches unintended pixel changes; optimisations are pixel-identical.
