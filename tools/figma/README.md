# tools/figma

The Figma → Roblox UI pipeline. Windows and HUD pieces are designed in Figma, exported as layer trees, turned into Luau layout modules, and rebuilt node for node in game by [`lib/figma-ui`](../../lib/figma-ui/README.md). The game UI matches Figma by construction: change Figma, re-export, rebuild. Nobody redraws a frame by hand.

The full method, rules and gotchas are in the [Figma UI playbook](../../docs/playbooks/figma-to-roblox-ui.md).

| File | What it does |
|---|---|
| `kit.js` | Paste at the top of every `use_figma` script. Builds the house style: `WINDOW`, `TABS`, `STEEL` plates, `WELL`s, `KEY`/`BTN` keycaps, `PRESS` (pressed state), `CHIP`, `BAR`, `T`/`BODY` text, `ICO`, `GLYPH`, `SPEC` cards, `OUTLINE`, textures (`STRIPES`, `LATT`, `HALFTONE`), palettes (`PAL`, `THEME`) and `textW` for fit-checking text. |
| `exporter.js` | Read-only `use_figma` script. Replace `__PAGE__`, `__ROOT__` (a frame's node id) and `__PART__` (0, 1, 2…); each call returns one 19 KB slice of the frame's compact tree, prefixed `PWX|root|part|nparts|`. |
| `collect.py` | Reassembles the slices from the Claude session transcripts into `out/<root>.json`: `python collect.py <session dir>`. |
| `build_layouts.py` | Turns `out/*.json` into one Luau layout module per frame: `LAYOUT_DEST=<game>/src/client/UI/Figma/Layouts python build_layouts.py`. Needs `roots.json` (node id → module name and kind) and `hashes.json` (image hash → icon or texture name); see the `.example.json` files. |

## Set up for a new Figma file

1. In `kit.js`, set `CFG`: the UI page id, the icon strip frame, and three reference nodes it copies exact gradient transforms and the lattice texture from (a plate, a window, a header). Get ids with `get_metadata`.
2. In `exporter.js`, set `__PAGE__` to the same page id.
3. Copy `roots.example.json` → `roots.json` and `hashes.example.json` → `hashes.json`; add a row per frame and per image hash as you go.

## Export one frame

1. Run `exporter.js` with `__ROOT__` = the frame id and `__PART__` = 0. The prefix says how many parts; run 1…n−1 too.
2. `python collect.py ~/.claude/projects/<project>` → `out/<root>.json`.
3. `python build_layouts.py` → `Layouts/<Module>.luau` (the node id is in its header).
4. Sync to Studio and QA the window zoomed in ([studio workflow](../../docs/playbooks/studio-workflow.md)).
