# UI motion and sound

The motion and sound language our UI used. Implemented in [`lib/figma-ui/Motion.luau`](../../lib/figma-ui/Motion.luau). Numbers are the values that shipped in the prototype.

## Keys: press in, never bounce

- **One function gives every key its feedback** (`Motion.key(target, kind)`). Keycaps (ink body, lip, face) drop body and face by the lip depth with the lip hidden in **40 ms** and rise in **90 ms**. Flat buttons (tabs, rows, cells, plates) drop 2 px.
- **Hover:** +6 % light veil and a 2 px lift (keycap) or 1 px (flat).
- **No squash or overshoot on any key.** Outcomes carry the juice, not clicks. A window's hero key may settle 3 % on success.
- **Sounds:** `press_down`, `press_up`, `hover_tick` on every key.

## Windows

| Moment | Motion |
|---|---|
| Open | Scale 0.86 → 1.04 (0.2 s) → 1 (0.12 s) out of the button that opened it; rows cascade in 40 ms apart |
| Close | Rows collapse in reverse, then the window shrinks (0.22 s) into its button with a sparkle burst. No fade, no CanvasGroup |
| Tab switch | The pill glides (0.2 s Quint); content crossfades 0.12 s with an 8 px slide; no re-pop, no rebuild |
| Idle (open window only) | Header gloss sweep every 4.5 s, glow breathes over 2.8 s, sparkles twinkle, up to 2 big icons bob ±3 px; the one primary key catches a light sweep every ~3.5 s |
| Can't afford | Shake ±6 px × 3, red cost flash, wallet wiggle |
| Maxed | Gold pop + sparkles + shimmer, then the row folds |
| Reset moments | Hold to confirm, then a flash in the reset colour; currency flies to its counter; rows dissolve |

CanvasGroups only during a transition; everything else is TweenService and event-driven (no per-frame Lua).

## HUD feedback

- Counters roll (odometer). A gain shows a "+N" floater and icons flying into the chip.
- **One** breathing attention key on screen (usually the primary BUY). A "recommended" sparkle on the cheapest affordable row.
- Unaffordable rows: desaturated icon and a red cost.
- At most 2 badges, in priority order.
- Hold to buy accelerates; Shift or long press = MAX.
- Lists: thin scrollbar, edge fades, row hover, a very quiet scroll tick.
- Tooltips hide on press, when any window opens, and on leave. A HUD tooltip never shows while a window is open.

## Pull-down board (a worked example)

A companion list that drops like a classroom map shows how far tuning went:

- **Drop:** height 0 → H + 6 in 0.34 s Quad Out (gravity), then H − 2 (0.12 s Sine InOut), then H (0.10 s Sine Out). The sheet stretches 1.05 → 1 over the first 0.2 s.
- **Rows** uncover as the roller passes their middle (delay = T(1 − √(1 − y/H))).
- **Pull ring** swings +14 / −9 / +4 / 0° over 0.12 / 0.18 / 0.14 / 0.12 s.
- **Roll up:** H → 0 in 0.26 s Quad In, overshoot 5 px into the header (0.06 s), settle (0.16 s Back Out).
- **Sounds:** roll down, roll up, a clack on the snap.
- One tweened size drives clip, sheet and roller. Every height change is announced, so dependent HUD groups tween with the **same TweenInfo on the same frame**.

## Sound system

- **One function per event:** press_down/up, hover_tick, tab_switch, window_open/close, row_select, dropdown_open/close, toggle_on/off, slider_tick, scroll_tick, buy_ok, purchase_big, cant_afford, denied, maxed, level_up, collect, coin_land, toast, unlock, error, …
- **Length caps per category** with a fade-out: UI 0.35 s, rewards 1.2 s, messages 3 s. Optional start offset per sound; every id preloaded.
- **±5 % random pitch** on every play.
- **SoundGroups:** UI 0.8, rewards 1, messages 1, music 0.6. Music ducks under big moments.
- **Layered events:** a pickup = a short tap (first 0.12 s, speed 1.1–1.25, vol 0.3) plus a soft pop 7 ms later (0.25 s, vol 0.4), both EQ'd warm (High −9 / Mid −2 / Low +3 dB). Pitch ±4 % per pickup plus a combo climb; a rare variant pitches the pop up 1.12 with a sparkle tail.
- **Dev sound board:** one row per event (one per layer for layered ones). Audition A–D candidates through the real playback path, USE applies a pick live and saves it (dev DataStore), COPY TABLE prints the final id table. Picking sounds becomes a 10-minute listening session instead of code edits.
- **Candidates** come from licensed packs; keep the candidate list next to the chosen ids.
