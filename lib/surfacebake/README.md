# surfacebake

Bakes **algorithm textures onto real model assets**. It rasterises a mesh into its own UV layout, finds the 3D surface point behind every texel, and evaluates noise, Voronoi, edge distance, ambient occlusion or any 2D algorithm render (triplanar) there. The output is colour, normal (OpenGL), roughness and metalness maps, ready for `EditableImage:WritePixelsBuffer` and a `SurfaceAppearance`.

Pure Luau except `Apply.luau`. Tested headless in lune. The process is in the [procedural textures playbook](../../docs/playbooks/procedural-textures.md); [`examples/web/surface-bake.html`](../../examples/web/surface-bake.html) is the same pipeline in a browser with a lit 3D preview.

| Module | What it does |
|---|---|
| `Mesh` | The plain triangle layout (welded positions; per-corner UVs and normals, like `EditableMesh`), plus test meshes: box with a 3×2 atlas, UV sphere, torus |
| `Raster` | UV-space G-buffer: per texel the triangle, barycentrics, object-space position, normal, tangent (+u) and bitangent (+v). `dilate(px)` pads islands so mipmaps never bleed |
| `Surface` | Per-vertex mean curvature and AO (hemisphere rays with a grid), sharp-edge extraction, and **edge distance in studs** (wear width independent of tessellation) |
| `Noise` | fBm, ridged, domain-warped (on `math.noise`), 3D Voronoi F1/F2/id, triplanar sampling of any RGBA8 tile |
| `Recipe` | A material as data: base plus masked layers (noise, ridged, voronoi, wave, rings, grid, curvature, ao, edge, up, y, image). Layers mix colour, roughness, metalness and height |
| `Bake` | Mesh + recipe → `albedo`, `normal`, `roughness`, `metalness`, plus `edge` and `ao` maps; normals from 3D height differences (seamless) |
| `Presets` | 15 recipes: `paintedMetal`, `rustedIron`, `mossyStone`, `lavaRock`, `ice`, `wood`, `gold`, `marble`, `sciFiPanel`, `camo`, `snowRock`, `slime`, `runeStone`, `carbonFiber`, `copperPatina` |
| `Animate` | Realtime moving surfaces from pre-baked per-texel fields: `pulse`, `flow`, `dissolve`, `scan`, `spread`. A texel budget per frame with round-robin rows, and a reused upload slice (no per-frame allocation) |
| `React` | Reactive surfaces: `hit()` adds heat (glows red → white, cools) and ripples that travel in 3D; frost grows from seeds and melts under heat; a lava flow freezes under frost; a shield shimmers with spin speed; `spring()` makes fur, cloth and jelly lag behind the body's motion |
| `Parallax` | Depth without shaders: parallax occlusion mapping, interior mapping (rooms behind windows), layered 2D parallax, infinite zoom (octave blend, optional spiral) and shell texturing (fur/grass meshes and masks) |
| `Apply` | Roblox only: read a `MeshPart` through `EditableMesh`, bake over several frames, and apply as `TextureContent` or a `SurfaceAppearance` |

```lua
-- client (LocalScript): bake a rusted look onto a MeshPart you own
local SurfaceBake = ReplicatedStorage.Shared.surfacebake
local Apply = require(SurfaceBake.Apply)
local Presets = require(SurfaceBake.Presets)
local ok, msg = Apply.bakeMeshPart(workspace.Barrel, Presets.rustedIron, { size = 512 })
if not ok then warn(msg) end   -- keeps the authored texture on failure
```

```lua
-- your own recipe: copy a preset, change numbers only
local moldyCrate = table.clone(Presets.paintedMetal)
moldyCrate.base = { color = { 0.42, 0.3, 0.18 }, rough = 0.8 }
```

## Moving and depth

```lua
-- realtime rune glow on a baked crate: prepare once, then a fixed texel budget per frame
local maps = Bake.run(mesh, Presets.runeStone, { size = 256 })
local img = Apply.toEditableImage(maps.albedo, 256, 256)
part.TextureContent = Content.fromObject(img)
local anim = Animate.prepare(maps, { effect = "pulse", color = { 0.35, 1, 1 }, phase = { "y", scale = 1 },
	mask = Presets.runeStone.layers[2].mask })
RunService.RenderStepped:Connect(function()
	local y0, rows = Animate.step(anim, os.clock(), 256 * 32)          -- ~0.7 ms headless
	img:WritePixelsBuffer(Vector2.new(0, y0), Vector2.new(256, rows), Animate.rows(anim, y0, rows))
end)
```

Reactive: `local st = React.prepare(maps, profile)`; on a raycast hit call `React.hit(st, p.X, p.Y, p.Z, 1)` with the hit in mesh space; each frame `React.step(st, dt, angularSpeed)` and upload `st.out`.

GIFs of all of it, on different surfaces: [media/gifs/surfaces](../../media/gifs/surfaces/index.html) (record with `node tools/capture_surface_gifs.mjs`).

`Parallax.pom`, `Parallax.interior` and `Parallax.zoom` write into an RGBA8 buffer you upload the same way: a portal, a facade or a screen on a `SurfaceGui`. `Parallax.shells` returns offset meshes and alpha masks for fur and grass. The [depth lab](../../examples/web/depth-lab.html) runs all of them live.

## Tests and timings

```sh
cd lib/surfacebake/qa && lune run test_surfacebake.luau | grep -a '^@@'   # 28 checks: bake
cd lib/surfacebake/qa && lune run test_motion.luau | grep -a '^@@'        # 26 checks: Animate + Parallax
cd lib/surfacebake/qa && lune run test_react.luau | grep -a '^@@'         # 11 checks: React
cd lib/surfacebake/qa && lune run bench.luau                              # latency tables (BENCH.md)
python3 lib/surfacebake/qa/sheet.py                                       # qa/out/sheet.png of every map
```

Full numbers are in [BENCH.md](BENCH.md). Headless lune, one thread:

| Work | Cost |
|---|---|
| Bake 256², most presets (one-off) | 180–380 ms |
| Bake 256², Voronoi-heavy presets (moss, lava, rune, slime, ice, rust) | 570–690 ms |
| Bake 1024² (one-off) | about 3.3 s |
| Animate, full 128² frame | 1.0–1.6 ms |
| Animate, full 256² frame | 3.6–6.5 ms |
| Animate, 256² budgeted to 32 rows/frame | 0.7 ms |
| React, 128² (heat + ripple / flow + frost / shield) | 2.5–3.4 ms |
| React, 256² | 10–23 ms (too much per frame: use 128² for reactive surfaces) |
| POM 128², 16 steps | 4.5 ms |
| Interior mapping 128² | 2.4 ms |
| Infinite zoom 128², 5 octaves | 1.6 ms |
| Shells, 16 × 256² masks (one-off) | 137 ms |

**Frame budget rule (kit default: phones about 4–5× slower, not measured).** Per-frame work on a client should stay under about 2 ms headless:
- Animate at 128² full, or 256² budgeted
- infinite zoom at 128²
- POM and interiors at 96–128², updated only when the camera moves (or every 2nd–3rd frame)

Bakes are one-offs: do them at load with `opts.yield`, or in Studio (route A). Native codegen (`--!native`) may speed up the per-texel loops; **not measured here**.

Verified headless:
- texel positions lie on the surface
- tangent frames are orthonormal
- shared edges leave no cracks
- dilation pads without overwriting
- box corners are convex and face interiors flat
- the torus's outer ring is more convex and less occluded than its inner ring
- edge-band width is the same on a 1× and an 8× subdivided box
- the sphere's UV seam is no harsher than its neighbouring columns
- a flat recipe gives `(128,128,255)`
- the green channel follows image-up (OpenGL)

**Not verified in Studio:**
- the UV v direction of imported meshes (`Apply.fromEditableMesh(em, flipV)` flips it if a test texture shows upside down)
- that normal maps light correctly on a real `SurfaceAppearance` (bake a single bump and look before trusting a recipe)
