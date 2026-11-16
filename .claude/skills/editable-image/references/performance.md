# Performance: what we measured

## The headline: Studio lies about phones

Live Roblox clients run `--!native` code **interpreted**; only Studio compiles it. Every Studio playtest number understates live cost, and gets the **ranking** of layers wrong.

Same renderer, same endgame scene (minute 29, ~300 enemies, 6 evolved weapons), 480×270:

| Layer | Studio (native) | Desktop app | iPhone 12 | iPhone ÷ Studio |
|---|---|---|---|---|
| heat (full-frame per-pixel) | 0.67 | 2.96 | **4.79** | **7.1×** |
| fx | 1.24 | 2.92 | 3.07 | 2.5× |
| light (per-pixel map) | 0.79 | 2.63 | 2.79 | 3.6× |
| ground | 1.22 | 2.44 | 2.71 | 2.2× |
| actors | 1.93 | 3.35 | 2.53 | 1.3× |
| props | 1.12 | 2.30 | 1.81 | 1.6× |
| upload (`WritePixelsBuffer`) | 0.15 | 0.09 | 0.02 | |
| **renderer total** | **~9.1** | **20.2** | **19.6** | **2.2×** |

- Whole renderer: live ≈ **2.1–2.3× Studio**. Code that is mostly `buffer.copy`/`buffer.fill`/engine calls runs at C speed either way.
- Pure per-pixel Luau loops blow up **3.6–7×**. Those are the first layers to cut.
- On the iPhone our Luau was ~96% of the frame: the script sets the frame rate, not the GPU.
- Studio's device emulator changes resolution, not CPU speed. It can't prove a phone target.

## How the cuts went (same scene, iPhone 12)

| Build | Our code | Frame | Notes |
|---|---|---|---|
| Before | 20.6 ms | 21.5 ms (47 fps) | heat 4.8, fx 3.1, light 2.8 |
| After the cut pass | **11.5 ms** | 16.8 ms (60 fps cap) | heat 1.2, light 0.65: half-res/half-rate light, heat only on touched rows, copy fast paths, span blits |
| After a look overhaul | 13.5 ms | 60 fps | regressions: ground +1.3 (seam dither), actors +0.8 (threat FX), glyphs +0.7 |
| Phone tier on, desktop full tier | 12.9 / 22.5 ms | 58 / 39 fps | desktop full tier (rims/outlines/foil per body) became the problem: actors 7.3 ms |

Target that worked: **our code ≤ 12 ms on an iPhone 12 in the worst scene.** That leaves ~25 ms on a phone 2× slower, so it still holds 30 fps. Cheaper Androids are an estimated 2–3× slower than an iPhone 12 (not measured).

Lesson: **every look change needs a re-measure on the phone**, and the "full" tier needs a budget too.

## Interpreter rules (measured)

- `buffer.copy` / `buffer.fill`: ~50 ns per call. `readu32`/`writeu32`/`writeu8`: ~5–10 ns. **Runs of ≤ 7 px are cheaper written pixel by pixel**; longer runs use `buffer.copy`. Applying this to strips and halos took one effect from 0.175 to 0.105 ms. See [`SpanBlit.luau`](../examples/SpanBlit.luau).
- In-game costs run **2–3× the hot micro-bench** (cache and call-chain effects). Bench in situ.
- Hoist locals (`local writeu32 = buffer.writeu32`), cache `img.Size`, no closures or `{}` in inner loops, whole-pixel `writeu32`.
- Global caches that allocate (per-frame tables, LRU programs) made things **worse** through GC. Per-body caches keyed on last frame hit ~50%; that's the ceiling when keys are new or last-frame.
- Row-wise rewrites and "whole row hidden" fast paths were both slower in our occlusion code. Measure before keeping a "clever" path.

## Library timings (headless, desktop CPU, ms)

| Work | Interp | Native |
|---|---|---|
| IndexedFrame full resolve 256×144 / 8 dirty tiles | 0.91 / 0.06 | 0.13 / 0.013 |
| Atlas: write 64 × 64² surfaces + pack upload | 0.78 | 0.37 |
| Falling sand 320×180 active / settled | 2.3 / 0.02 | 0.82 / 0.009 |
| Voxel Space 320×180 full / checkerboard | 8.4 / 4.3 | 1.6 / 0.9 |
| Radiance cascades 256², amortized (moving light) | 2.9–4.0 | 3.5 |
| Snapshot encode / decode 512² | 1.8 / 0.17 | 0.57 / 0.06 |
| surfacebake bake 256² (per preset) | 179–729 | – |
| surfacebake animate full frame 128² / 256² | 0.9–1.6 / 3.6–6.5 | – |

Use the **Interp** column for live clients. Bakes are load-time only; amortize anything over ~5 ms across frames.

## Per-pixel loop ceiling (interpreted, per frame)

64² and 128²: fine. 256²: tight. 512²: update on change or a sub-region. 1024²: generate once or amortize. Shift one row down for phones.

## Where to cut first (in order)

1. Per-pixel full-frame passes → half resolution, half rate, or only dirty rows/tiles.
2. Short runs → direct writes; long runs → `buffer.copy`; opaque spans precomputed.
3. Per-body extras (rims, outlines, foil) → tiered off on weaker devices.
4. Static screens → baked layers + dirty-row uploads.
5. Crowds → glyph LOD.
