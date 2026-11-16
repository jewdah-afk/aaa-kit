# EditableImage: API, limits and gates

The facts that decide whether a design is possible. Full sourcing: [research chapter 20](../../../../docs/research/20-roblox-editableimage-api.md).

## The three walls

| Wall | Number | Consequence |
|---|---|---|
| Size | Max **1024×1024**, default 512×512, `Size` read-only | No resize or crop. Make a new image, `DrawImageTransformed` into it, `Destroy` the old one. |
| Display refresh | **One displayed EditableImage updates per frame**, engine-wide | N animated canvases run at 60/N fps and tear between layers. Composite into one displayed canvas, or use an atlas + upload scheduler (`lib/frontier` `Atlas`, `Uploader`). Off-screen images are not throttled. |
| Memory | Client budget is **device-specific and unpublished**, shared with EditableMesh; ~32 MB is the community figure (5–6 large images). Server, Studio and plugins are unlimited | `CreateEditableImage` returns **nil** on a full budget. Studio never shows it. |

Bytes are `w·h·4` logical; plan for ~2× (GPU copy, possible mips). 320×180 = 225 KB, 480×270 = 506 KB, 512² = 1 MB, 1024² = 4 MB.

## Gates and failure shapes

| Gate | Applies to | Failure |
|---|---|---|
| Creator 13+ age **and** ID verified, then **Enable Mesh / Image APIs** on the Creator Dashboard | Every use in a **published** game | Works in Studio, fails live. Test a published place before launch. |
| Asset ownership / sharing | `CreateEditableImageAsync` only | **Throws.** `pcall` it. `rbxthumb://` URIs skip the check. A player's own assets load only on the client. |
| Editable memory budget | Both creators, clients only | Returns **nil**. Always nil-check and keep a fallback. |

Publishing note: a place published by the publish API, not Studio, may not carry the toggle; publish from Studio when in doubt.

## Creation and display

```lua
local img = AssetService:CreateEditableImage({ Size = Vector2.new(W, H) }) -- nil on low memory
if not img then return showFallback() end
img:DrawRectangle(Vector2.zero, img.Size, Color3.new(), 0, Enum.ImageCombineType.Overwrite) -- initial contents are undocumented
label.ImageContent = Content.fromObject(img)
label.ResampleMode = Enum.ResamplerMode.Pixelated
```

- `EditableImage` is an `Object`, not an Instance: no `Parent`, no `Instance.new`. Show it through a `*Content` property.
- **Sinks that accept it:** `ImageLabel.ImageContent`, `ImageButton.ImageContent`, `Decal.ColorMapContent` (and `Texture`), `MeshPart.TextureContent`, `SpecialMesh/FileMesh.TextureContent`, `SurfaceAppearance` maps (only via `AssetService:CreateSurfaceAppearanceAsync`; slots are PluginSecurity-write and can't be swapped later).
- **Sinks that silently reject it:** `ImageButton.HoverImageContent` / `PressedImageContent`, `Shirt`/`Pants`/`ShirtGraphic`, `ScrollingFrame` bar images. `ViewportFrame` has no image property. Draw hover/press states into the one `ImageContent` canvas.
- **Multi-referencing:** one image on many `Content` properties costs one image of budget. Give each shared canvas exactly one writer.
- **Teardown:** set the property to `Content.none`, then `img:Destroy()`. Destroy frees at once; the GC does not.

## Pixel I/O

- `WritePixelsBuffer(pos, size, buf)` / `ReadPixelsBuffer(pos, size)`: RGBA8, row-major, top-left origin, index `(y·W + x)·4`. Little-endian, so `writeu32` packs `r | g<<8 | b<<16 | a<<24`.
- `WritePixelsBuffer` reads the buffer **from byte 0** for a `size` region. To upload a band, copy it into its own buffer first (`SpanBlit.band`).
- `ReadPixelsBuffer` **allocates a new buffer every call**. Keep your own buffers as the truth; never read back per frame.
- Buffers use **alpha** (255 opaque); `Draw*` methods use **transparency** (0 opaque).
- Treat pixels as **straight alpha**. Bleed colour into transparent margins (colour with alpha 0, not black) or bilinear scaling shows dark halos.
- The old table APIs (`ReadPixels`/`WritePixels`, floats 0..1) and `image.Parent = label` are gone; most tutorials still use them.

## Draw methods (engine-side, native speed)

`DrawRectangle`, `DrawCircle`, `DrawLine` (1 px, no thickness), `DrawTriangle`, `DrawImage` (top-left, straight blit), `DrawImageTransformed` (pivot-positioned, degrees, defaults to bilinear + AlphaBlend; pass `Pixelated` and `Overwrite` explicitly), `DrawImageProjected` (most expensive; keep the volume brush-sized). `DrawRectangle` can't start outside the canvas; clamp. Anything expressible as rects, lines or blits is cheaper here than in a Luau loop.

## Threads and replication

- Only `ReadPixelsBuffer` (Safe) and `Size` (ReadSafe) are legal desynchronized. Do the maths in parallel into your own buffer, `task.synchronize()`, then one `WritePixelsBuffer`. Scale by giving each Actor a horizontal band.
- `Content.fromObject` does **not replicate**. A server-side image on a replicating instance shows a cyan/magenta checkerboard. Generate on the client from replicated parameters (seed, edit list, palette indices); persist with a compact codec (`lib/frontier` `Snapshot`).

## Saving

`CreateAssetAsync(img, Enum.AssetType.Image)` gives a permanent id from plugins / Open Cloud only. In-experience there is no image-publish path. The strongest pattern: generate at edit time, upload, ship the id; use runtime images only for what truly changes.
