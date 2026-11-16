# Testing and measuring an EditableImage renderer

## Headless first

Keep every pixel module pure Luau (buffers in, buffers out) with a thin Roblox adapter. Then:

- **Unit tests in lune** for owner rules, clipping, snapping and spans (see `examples/*.test.luau`).
- **Image dumps:** write the frame buffer to `.ppm` (a 15-line writer), upscale 2× to PNG for review; make GIFs from frame sequences without ffmpeg using a small PPM→GIF script.
- **Golden chains:** record a hash per frame over a fixed seed (e.g. 360 frames across golden, heavy and heavy+low-HP scenes). An optimisation must be **pixel-identical** on every frame (`--check`); a look change re-records the chain on purpose.

## Timing that survives noise

- **Paired A/B in one process:** render the same scene twice per frame with the feature on and off, interleaved, and take the median paired delta. Robust on a loaded machine where absolute ms are useless.
- **Machine-normalised gates:** time a fixed interpreted workload, divide by its time on the reference machine, clamp to [1, 3], and multiply every ms bar by that factor. Bars are never looser than on the reference machine.
- Per-layer `os.clock()` deltas into an EMA (0.9/0.1) on a debug overlay; remember EMA is smoothed, not a mean.
- Flaky timing gates near their limit usually mean the bar is within noise; re-run alone before "fixing" code.

## On real clients (the only numbers that count)

- A private **bench place** that mirrors the game's code tree plus one extra LocalScript: a button runs a scripted worst-case profile (fixed minute, held enemy count, fixed loadout, 3 s warm-up + 10 s capture) and shows frame avg/p95/max, per-section and per-layer ms on one screen. Run it on the desktop app and a real phone.
- `lib/frontier/studio/Bench.client.luau` measures what headless can't: `WritePixelsBuffer`/`ReadPixelsBuffer` MB/s from 64² to 1024², whether native codegen runs on the client, the real editable budget (create 256² images until nil, destroy, check it comes back).
- Record device, client version, commit and scene with every number.

## Before calling it done

- [ ] Works in a **published** place (verification toggle), not just Studio.
- [ ] Nil-path tested: force `CreateEditableImage` to fail and see the fallback.
- [ ] Phone tier measured on a phone, full tier on the desktop app.
- [ ] Golden chain unchanged, or re-recorded with a reason.
