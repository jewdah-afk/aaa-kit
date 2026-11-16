# Gotchas and failures we hit

| Symptom | Cause | Fix |
|---|---|---|
| Works in Studio, blank or erroring live | Creator verification + **Enable Mesh / Image APIs** toggle off | Toggle on the Creator Dashboard; test a published place |
| Cyan/magenta checkerboard on clients | Server put an EditableImage on a replicating instance | Generate on the client from replicated parameters |
| Black screen on some phones | `CreateEditableImage` returned nil (budget) | Nil-check, pool with a byte cap (`ImagePool`), show a fallback message |
| Layers appear on different frames, animated panels stutter | One displayed image updates per frame | Composite into one canvas or one atlas page |
| Image black/white after porting a tutorial | Old float 0..1 table API vs u8 buffers | `WritePixelsBuffer` with bytes 0..255 |
| Shape invisible or inverted alpha | Buffers use alpha, `Draw*` uses transparency | Convert: `alpha = (1 - t) * 255` |
| Dark halos around scaled sprites | Straight alpha + bilinear filtering | Bleed colour into transparent pixels; use `Pixelated` |
| Pixel art soft or shimmering | Bilinear default, fractional positions, non-integer scale | `ResampleMode = Pixelated`, integer coords, integer scale |
| Sprite offset by half its size | `DrawImageTransformed` positions the pivot | Offset by size/2, or use `DrawImage` |
| Hover image doesn't show | `HoverImageContent`/`PressedImageContent` reject EditableImage | Redraw the one `ImageContent` canvas |
| Memory climbs across rounds | Not calling `Destroy`, or still referenced | `Content.none` then `Destroy()` |
| GC spikes | `ReadPixelsBuffer` per frame; per-frame tables/caches | Keep your own buffers; preallocate; no global caches |
| Great in Studio, slow live | Native codegen doesn't run on live clients | Measure live; cut per-pixel loops first |
| Layer ranking flips on phone | Interpreter penalty differs per layer (1.3×–7×) | Profile per layer on the phone before choosing what to cut |
| Upload shows the wrong rows | `WritePixelsBuffer` reads from byte 0 | Copy the band into its own buffer |
| Text knocked out into blocks | Hover fill drawn after text | Plate → text → focus |
| Upscaled portrait looks mushy | Dithered/filtered upscaling of a tiny sprite | Integer scale + outline, or a dedicated portrait |
| Parallel script errors | Draw/Write calls while desynchronized | Compute in parallel, write after `task.synchronize()` |
| Two systems scribble on one canvas | Multi-referenced image, no locking | One writer per canvas |
