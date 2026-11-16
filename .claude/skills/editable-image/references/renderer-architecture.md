# A full-screen pixel renderer, layer by layer

How a whole 2D game is drawn into one EditableImage at a steady frame rate on phones. This is the architecture of our shipped survivors-style renderer, kept generic.

## Frame shape

- **Resolution:** one knob. 320×180 for a spike, 480×270 for the game (2 world px per screen px, sprites authored at the 320 size and upscaled 1.5× **at load**, never per frame). Draw full-bleed on every aspect (16:9, 4:3, phone-wide); don't letterbox.
- **Buffers, allocated once:** colour RGBA8 (`W·H·4`), owner u8 (`W·H`), a half-resolution protect grid, light map, heat buffer. The owner fill is ~0.001 ms.
- **Upload:** exactly one `WritePixelsBuffer` per frame (0.02–0.16 ms measured at 480×270).
- **Gameplay is independent:** the sim never reads the frame. Rendering off, the game must play identically (this is also what makes headless tests possible).

## Layer order and what each costs

ground → props → pickups → actors → glyphs → fx → heat → light → numbers → polish/post → hud → upload.

| Layer | How it's built | Cost driver |
|---|---|---|
| Ground | Baked tile (512², ~1 MB, ~210 ms bake at load) copied per row with `buffer.copy`; band-tinted variants baked per light band | Per-pixel work inside "history blocks" (below). A copy fast path for untouched rows halves it. |
| Props | Pre-shaded stamps with opaque row spans; depth occlusion via per-row footline spans | Span count; occlusion clipping (the most expensive feature we added, ~+0.8 ms heavy scene) |
| Pickups / actors | Span blits; hit flash, squash, dissolve and rims as stamp variants | Body count × variants. Full-quality rims/outlines per body cost 7 ms on a desktop live client; tier them. |
| Glyphs | Crowd LOD: far cells collapse to density glyphs `. : * # @` with exact counts and hysteresis | Cell count |
| FX | Pooled effect structs, drawn as spans/strips into the frame | Coverage; an attention budget caps how much FX may cover |
| Heat / light | Per-pixel passes (heat composite, banded light) | **The most interpreter-sensitive layers.** Run at half res (light map 160×90 or 120×68, upsampled), half rate, or only on rows/tiles that changed. |
| Numbers / HUD | Bitmap font blits | Small |

## Pixel ownership

Every write passes `CAN[writer][dest]` against the owner buffer (tiers 0 background … 7 ceremony). This is how "friendly FX never hide a threat" and "the selection ring stays on top" become guarantees instead of hopes. Measured cost of tagging: +0.04 ms for 500 bodies. Example: [`PixelFrame.luau`](../examples/PixelFrame.luau).

## Pre-shading and palettes

- Bake each sprite per palette/light band at load (8 bands); draw time is a copy.
- A grade or "calm" pass is a palette/LUT swap at bake time (~0 ms per frame), never a per-pixel remap.
- Palette cycling (water, magic, rarity rims): store region pixels as indices with a span list; rotate an 8-colour ramp and re-resolve only tagged spans every 3rd frame (~0.1 ms). `lib/frontier` `IndexedFrame` does this with dirty tiles.

## History that costs nothing until it exists

Scorch marks, footprints and stains live in 16×16 "history blocks" allocated only where something happened. Untouched blocks take the plain copy path, so cost stays flat until the ground fills up.

## Menus and static screens

Bake each screen's static layers once into buffers. Per frame, redraw only dirty rects (focus plate, springs, embers) and upload only the changed row band. Estimated 6–8 ms → under 1.5 ms on a heavy map screen; the single biggest phone win for menus.

UI drawing order is plate → text → focus. Drawing a hover fill after the text knocks the glyphs out into blocks (a bug we shipped once).

## Device tiers and fallbacks

- **Tiers chosen at startup** from device class (phone, not-top-tier, full) and threaded through every effect: phones get the cheap path of spectacle moments, no lantern floor tint, a lite HUD, no live material shading. An FX budget module owns the lowest tier switch.
- **Zoom:** presentation-only integer 2× on phones/portrait, 1× on PC/landscape, as a setting.
- **No-image fallback:** if `CreateEditableImage` returns nil, show a readable message ("This device can't create the game's pixel frame right now. Try rejoining.") instead of a black screen.
- **Accessibility:** flashing-reduction turns impact frames off; offer "skip ceremonies".

## Hard-pixel rules that got broken (and how we noticed)

- A portrait upscaled ~12× through dithered sampling went soft: integer-scale sprites (×6 with a 1 px outline) or render a dedicated portrait.
- A low-res fire drawn at chunky blocks with a ruler-straight bottom read as a placeholder texture: give it a per-column height field and a falloff.
- Halftone transition frames must not hold longer than ~4 frames.
