# The look-dev loop

How cursed-survivors pushed its look forward pass by pass without breaking anything: 90 passes, each with evidence. The loop works for any game with a headless renderer or a scriptable capture.

## One pass

```
question → change → headless capture (before | after) → measure → NOTES.md → tests + golden → owner review
```

1. **Name the pass** after the question it answers: `docs/look/<pass>/` (e.g. `vfx`, `hud2`, `death-fx`, `ui-motion`, `perf3`).
2. **Change one thing**, visual only, unless the pass says otherwise. Gameplay contracts (hitboxes, timing, counts, paths) don't move.
3. **Capture before and after** from the same seed and frame through the real code path:
   - `lune run tools/devmode.luau -- --stage … --weapons … --enemies 160 --time 10:00 --seed 7 --frames 480 --out run.rgb`
   - `tools/capture.sh` replays a fixed set of scripted fights (early game, mid game, an evolution, the max horde, a boss, ranged enemies)
4. **Build evidence**, saved in the pass folder:
   - before | after sheets of the busiest frame (`*_before_after.png`)
   - ×4 zoomed crops for detail
   - GIFs of the motion
   - stress tables (`stress_before.txt` / `stress_after.txt`)
5. **Measure the cost** in ms per layer on the same machine, interpreted (live clients may not run native codegen), and log it in `docs/budgets.md`.
6. **Write `NOTES.md`** with the same headings every time:
   - **Done:** what changed, with the numbers (sizes, durations, counts)
   - **Rules:** any new rule the pass created (tiers, caps, budgets)
   - **Evidence:** files and the exact command that made each
   - **Where I stopped:** pushed? merged? tests green?
   - **Questions for the user**
7. **Lock it in with tests:**
   - a unit test for the new behaviour (`tests/render/<pass>.luau`)
   - the **golden frame** checksum, unchanged or updated on purpose with the pixel count and region that moved
   - `tests/all.sh` must exit 0
8. **Owner reviews screenshots, not descriptions.** Every visual change ships with before/after images.

## Stress testing VFX

Run every weapon and evolution at level 1, level 8, and level 8 + max passives (amount +3, area ×1.6, duration ×1.8, speed ×1.6, cooldown ×0.55) through the real fire path, on the golden scene plus 120 enemies and 80 pickups. Measure, per configuration:

- % of enemy pixels and hero pixels covered by FX (must be 0 for hostile shots and near the hero)
- % of the screen washed by glow
- fx ms and its p95

The first stress run found the bugs no screenshot showed:
- a fallback FX path writing raw pixels over the hero (up to 16 %)
- one weapon stacking rings across the whole screen (3.6 ms)
- the glow composite painting over enemies and pickups

The fix became the rules in [HIERARCHY.md §8–10](../../HIERARCHY.md#8-urgency-beats-rarity):
- tiers per effect (signature / base / ambient)
- LOD per copy, newest first (FULL → LOW → FAR)
- a global budget of 18 FULL copies
- glow pooling capped below the white step
- juice that scales with damage, not with count

## Benches and budgets

- One bench per hot system (`render_bench`, `hud_bench`, `endgame_bench`, `crowd`, `perfbench`), each printing ms per call.
- A 720-frame checksum chain (colour, owner and heat buffers) proves an optimisation pass changed **no pixels**.
- The budget table records the device and conditions for every number. "Not measured on a phone" is written down, never implied.

## Review lenses

Recorded play sessions get reviewed through named lenses (readability, threat, reward, HUD, motion, sound). Each lens produces a numbered findings list; findings become the next passes.
