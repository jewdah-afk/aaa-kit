# vfxbench: what an EditableImage effect costs, measured

Twenty-four groups of pixel kernels. Each group times the naive way against the fast way of doing the same job, and checks that every variant gives the same pixels (a checksum, or the mean byte for the variants that change rounding or resolution). Results and what they mean: [docs/research/44-vfx-optimisation-frontier.md](../../docs/research/44-vfx-optimisation-frontier.md) §2.

```sh
# Luau CLI 0.740 (the version cursed-survivors pins). `luau` must be on PATH or set LUAU.
LUAU=luau bash tools/vfxbench/run.sh 3      # 3 runs x (interpreter -O2, native -O2, interpreter -O1) -> results/RESULTS.md
luau -O2 tools/vfxbench/bench.luau -a quick # one quick pass, prints a Markdown table
```

The last line of every run is `@@DONE <n>`. A non-zero `n` means a fast variant drew different pixels, so its time doesn't count.

## What it can and can't tell you
- **It can:** the cost of Luau inner loops in the same VM the Roblox client runs: interpreter, and native codegen (`--!native`, which Roblox runs on the server; client support is in §1 of the chapter).
- **It can't:** engine calls (`WritePixelsBuffer`, `DrawImage`, the one-update-per-frame display limit), the GPU, or a phone. For those, run [lib/frontier/studio/Bench.client.luau](../../lib/frontier/studio/Bench.client.luau) in Studio and on a device.
- **Phones:** the kit plans for a phone about 4–5× slower than this desktop-class CPU. Multiply the ms column before deciding something fits.

## Groups
| # | Kernel | Compares |
|---|---|---|
| 01–02 | Clear a 480×270 canvas | per-pixel writes vs doubling `buffer.copy`, prebuilt template copy, `buffer.fill` |
| 03 | Write a computed pixel | 4× `writeu8` vs one `writeu32` (arithmetic or `bit32` pack) |
| 04 | Additive blend (saturating) | per channel with `math.min` or a LUT vs SWAR (two channels per add) |
| 05 | Alpha blend at one opacity | per channel vs SWAR (two channels per multiply) |
| 06 | Palette-indexed resolve | per-pixel colour maths vs palette in a table/buffer vs 4 indices per read |
| 07 | Box blur r=8 | naive 2D vs separable vs running sum |
| 08 | 400 soft splats | `exp()` per pixel vs a precomputed stamp |
| 09 | Tunnel effect | `atan2`+`sqrt` per pixel vs a precomputed (u,v) table |
| 10 | Plasma | `math.sin` per pixel vs per-row/column sine tables |
| 11 | Rotozoom feedback | multiply per pixel vs incremental stepping |
| 12 | Swirl warp | per-pixel trig vs a coarse 8 px grid with interpolation (the Milkdrop mesh) |
| 13 | Shading function | call per pixel vs indirect call vs inline (shows `-O2` inlining) |
| 14 | Unpack RGBA | 4× `readu8` vs `readu32` + `bit32` vs `readu32` + `//`/`%` |
| 15 | 20k particles | array of tables vs parallel arrays vs one f32 buffer vs `vector` |
| 16 | Dirty-rect pack | per pixel vs one `buffer.copy` per row |
| 17 | 2× nearest upscale | per output pixel vs write once + copy the twin row |
| 18 | Expensive field (warped fBm) | full res vs checkerboard vs interlaced vs half and quarter res |
| 19 | Type annotations | untyped vs `buffer`/`number` params (codegen only) |
| 20 | Sparse glow composite | every pixel vs skip empty pixels vs lit 16×16 tiles |
| 21 | 50% overlay | true blend vs checker dither (write-or-skip) |
| 22 | 300 sprite blits | alpha test per pixel vs precomputed opaque runs |
| 23 | 200 filled discs | distance test per pixel vs row spans |
| 24 | Resample 128²→256² | bilinear vs nearest in Luau (the GPU does it for free) |
