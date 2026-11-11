# surfacebake

Bakes **algorithm textures onto real model assets**. It rasterises a mesh into its own UV layout, finds the 3D surface point behind every texel, and evaluates noise, Voronoi, edge distance, ambient occlusion or any 2D algorithm render (triplanar) there. The output is colour, normal (OpenGL), roughness and metalness maps, ready for `EditableImage:WritePixelsBuffer` and a `SurfaceAppearance`.

Pure Luau except `Apply.luau`. Tested headless in lune. The process is in the [procedural textures playbook](../../docs/playbooks/procedural-textures.md); [`examples/web/surface-bake.html`](../../examples/web/surface-bake.html) is the same pipeline in a browser with a lit 3D preview.

| Module | What it does |
|---|---|
| `Mesh` | The plain triangle layout (welded positions; per-corner UVs and normals, like `EditableMesh`), plus test meshes: box with a 3×2 atlas, UV sphere, torus |
| `Raster` | UV-space G-buffer: per texel the triangle, barycentrics, object-space position, normal, tangent (+u) and bitangent (+v). `dilate(px)` pads islands so mipmaps never bleed |
| `Surface` | Per-vertex mean curvature and AO (hemisphere rays with a grid), sharp-edge extraction, and **edge distance in studs** (wear width independent of tessellation) |
| `Noise` | fBm, ridged, domain-warped (on `math.noise`), 3D Voronoi F1/F2/id, triplanar sampling of any RGBA8 tile |
| `Recipe` | A material as data: base plus masked layers (noise, ridged, voronoi, curvature, ao, edge, up, y, image). Layers mix colour, roughness, metalness and height |
| `Bake` | Mesh + recipe → `albedo`, `normal`, `roughness`, `metalness`, plus `edge` and `ao` maps; normals from 3D height differences (seamless) |
| `Presets` | `paintedMetal`, `rustedIron`, `mossyStone`, `lavaRock`, `ice` |
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

## Tests and timings

```sh
cd lib/surfacebake/qa && lune run test_surfacebake.luau | grep -a '^@@'   # 28 checks
python3 lib/surfacebake/qa/sheet.py                                          # qa/out/sheet.png of every map
```

Headless lune timings (this container, single thread): 256² painted-metal box, 432 triangles: raster 22 ms, surface (curvature, AO, edge distance) 78 ms, shade 122 ms (about 220 ms total). 128² rusted-iron sphere with warped noise and Voronoi pitting: about 250 ms. Shade time grows with texels × layers × noise octaves; 512² is about 4× the 256² time. Roblox client timings: **not measured yet**. Run it in Studio before committing to runtime bakes; `opts.yield = task.wait` spreads the work over frames.

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
