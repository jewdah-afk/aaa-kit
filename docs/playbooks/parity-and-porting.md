# Parity and porting

How we rebuilt a game (our own web prototype, or a design reference) in Roblox with exact numbers. This covers method only; never copy another studio's art, names or text into a public game.

## 1. Build a parity harness before the port

1. **Pull the rules out as data.** Extract formulas, tables and constants into JSON and docs (`CORE_FORMULAS.md`, `SYSTEMS.md`, `UPGRADES.md`, `data/*.json`), each with a source note.
2. **Port the maths to pure Luau** (formulas, systems, a big-number type) and **verify it against the original functions**, value by value. For example, every upgrade cost at levels 0–30 came to 4,960 values, all exact; the systems check was 3,347 values. A JS harness (`node`) runs the original functions; lune runs the port; a script diffs them.
3. **An HTML parity build** reproduces every screen's layout, sections, data and flow in one page, with a phase table and a `DIFFERENCES.md`. It becomes the layout reference for the Figma work and the target for a numbers check (e.g. 80,461 of 80,461 values matching).

## 2. Inventory and plan

- List every screen and system and mark each **E** (exists and matches), **D** (differs) or **M** (missing).
- Keep a **parity checklist** per area: ✅ built and Studio-checked · 🟡 built, not Studio-checked · 🔧 buildable now · ⛔ blocked (with the reason, usually "needs approved art").
- Put deliberate deviations in a "Deviations" section with the reason. Everything else is 1:1.
- Remakes take only layout, sections, data and flow; art, names and text are our own.

## 3. Port in order

1. **Skeleton first:** every system, screen and content type playable end to end with placeholder visuals.
2. Then raise each module to full quality one at a time, each as a look-dev pass ([look-dev loop](look-dev-loop.md)).
3. Headless tests guard each system as it lands (spawner, progression, economy, unlock routes). One test fails if any unlock waits on an event nothing reports.

## 4. Porting to another engine

The same method moves a Roblox game elsewhere (a Unity port harness was drafted on the same pattern):
- pure-logic modules ported first and diffed against the Luau originals
- a templates folder for the engine's project layout
- skills per engine
- one copy-paste kickoff prompt

## 5. Big numbers

The original's numbers went past 1e308, so the port needed a big-number type with identical maths (see [examples/bignum](../../examples/bignum/README.md)). Only balances and payouts needed it; costs stayed plain numbers capped at 1.8e308, matching the original.
