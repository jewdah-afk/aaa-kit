# Icon pipeline

How we made consistent, glossy, painted icons, hundreds of them, all with the same outline. Tools: [tools/icons](../../tools/icons/README.md).

## Style

- **Glossy painted 3D look.** Flat or vector icons were rejected every time.
- Chunky, front-facing, soft top-left key light.
- Three cel bands: a cool shadow, the base and a highlight, plus a glossy specular and a thin rim light.
- Saturated colours, no muddy darks. Dark subjects get a lighter base and a stronger rim.
- **One uniform ink outline** (`#0B0C10`), the same weight on every icon: 6 px at 256 px.
- About 8 % padding. 256×256 transparent PNG.
- Tiers must look visibly better at each step (bamboo rod → divine rod), and size tiers must grow (tank 1 → 5).
- Kid-safe: no blood, gore or skulls. Every image prompt says so. (One upload of the wrong kind got the account warned.)

## Generate → cut → QA

1. **Generate a sheet**: a 4×4 grid on a **black** background (or white for sprites), one subject per cell, using Figma AI image generation or another image model. Build prompts from the game data so every item gets one (e.g. a prompt per fish from the species table).
2. **Cut it:** `python3 cut_grid.py sheet.png 4 4 name1 name2 …` (`-` skips a cell, `name!` keeps the drawn size). Per cell the cutter:
   1. takes the coloured interior, filling holes so pupils and stripes stay
   2. assigns interior pieces to their cell
   3. redraws the outline as a fixed-width anti-aliased ring (distance transform), which also repairs edges where icons touched on the sheet
3. **Fix outliers:** `clean_ring.py` (soft halos), `dehalo.py` (baked dark auras), `bolden.py` (match an older set's weight).
4. **QA every icon** on dark and light with `qa.py`. Check: outline closed all round, no floating parts, nothing clipped, reads at 48 px.
5. **Keep a manifest** (`final/manifest.json`) listing every icon and anything in the game data that still has none.

## Upload

- **To Figma:** `upload_assets` onto 72×72 `src/<name>` rectangles (FIT), then POST the PNGs to the returned URLs. One shared icon strip frame holds them all; the Figma kit reads it by name.
- **To Roblox:** Studio MCP `upload_image` or Open Cloud, **one image at a time**, inspecting each. Roblox downscales anything over 1024 px. Keep the resulting ids in one `Icons` module (`{ name = "rbxassetid://…" }`); every `ico/<name>` layer must resolve to it.

## Blender source (for 3D icons and drops)

`lib.py` and a per-game `icons.py` model each icon in Blender, running headless as the `bpy` module (`pip install bpy`):

- Each icon is its own collection `icon/<name>`, centred on the origin, facing −Y (the camera), fitting about a 2-unit box. A `pivot` empty holds any display tilt.
- Modifiers stay live: bevel, subsurf, displace, and an outline `SOLIDIFY` with an `ink_*` material.
- Materials are emission-only cel shaders: a 3-band constant ramp from dot(normal, light), plus a rim from Layer Weight.
- **Exporting to Roblox:** apply bevel, subsurf and displace; **drop the outline solidify and ink material** (Roblox draws outlines with `Highlight` or its own inverted hull). Bake each material to a small texture or vertex-colour ramp, or use a flat colour + `SurfaceAppearance` with toon lighting. FBX per collection, origin at the base, root named `icon_<name>`, under 2k triangles.
- **3D icons in UI:** a ViewportFrame with the same front camera, a narrow FOV, and a slow ±8° idle sway.

## Algorithmic polish (pixel games)

For pixel-art games the painted icons stayed as they were, but an algorithmic pass added re-light, rim and glints at runtime. Baked FX were cut out so they could be drawn live. Painted art is never replaced by generated art without the owner's approval.
