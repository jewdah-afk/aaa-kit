# Procedural textures on model assets

How to take an algorithm render (noise, Voronoi, reaction-diffusion, cellular automata, edge wear, grime) and put it **on a real model** in Roblox, so it looks painted for that mesh rather than slapped on. Library: [`lib/surfacebake`](../../lib/surfacebake/README.md). Live demo: [`examples/web/surface-bake.html`](../../examples/web/surface-bake.html). API facts: [EditableImage research §1, §8.6](../research/20-roblox-editableimage-api.md), [EditableMesh research](../research/21-roblox-editablemesh-api.md).

## 1. The core idea: evaluate in 3D, store in UV

A texture is a 2D image, but the model is 3D. Running a 2D algorithm straight in UV space gives seams at every UV island border, stretching wherever texel density changes, and wear in the wrong places. So:

1. **Rasterise the mesh into its own UV layout** (a G-buffer). Each covered texel learns which triangle it belongs to, its barycentrics, and from those the object-space **position**, **normal** and **tangent frame**.
2. **Run the algorithm on the 3D position** of each texel. Two texels on either side of a seam sit next to each other in 3D, so they get the same value. No seams.
3. **Use the geometry as masks:**
   - **edge distance** (studs to the nearest sharp edge) for chipped paint and polished rims
   - **AO** for grime in crevices
   - **normal · up** for dust, moss and snow on top faces
   - **height** for water lines
4. **Write height, then derive the normal map** by sampling height at ±1 texel along the tangent and bitangent in 3D. That's seamless too.
5. **Dilate** islands by 4+ texels so mipmapping never pulls in the background colour.

That is what `Bake.run(mesh, recipe, { size = 512 })` does.

## 2. Getting 2D algorithm renders onto the model

Some algorithms are naturally 2D: reaction-diffusion, cellular automata, Physarum, the `pixelfx` effects, a painted tile. Three ways to use them, best first:

| Route | How | When |
|---|---|---|
| **Triplanar** | Render the algorithm as a **tiling** RGBA8 tile, then use mask term `{ "image", img = buf, w = 96, h = 96, scale = 0.5 }` in a recipe. Three planar projections are blended by the normal | Organic patterns (coral, lichen, scales) on any mesh. Seams are hidden by the blend |
| **3D version of the algorithm** | Use the 3D equivalent: 3D noise, 3D Voronoi, or reaction-diffusion run on mesh vertices instead of a grid | When the pattern must flow continuously over the whole object |
| **Straight UV** | Run the 2D algorithm directly in the UV image, masked by `G.cover` | Only for meshes with one big, low-distortion island (a flag, a banner, a screen) |

## 3. Three ways to ship it in Roblox

| Route | API | Cost | Use for |
|---|---|---|---|
| **A. Bake in Studio, upload** | A plugin runs `Bake.run`, writes `EditableImage`s, then `AssetService:CreateAssetAsync(image, Enum.AssetType.Image)` and sets the uploaded IDs on a `SurfaceAppearance` | Zero runtime cost. Players download a normal texture | **Default for every static prop.** Thousands of variants at build time |
| **B. Bake on the client at load** | `Apply.bakeMeshPart(part, recipe, { size = 512 })`: `CreateEditableMeshAsync(part.MeshContent)` → bake with `task.wait` yields → `CreateSurfaceAppearanceAsync({ ColorMap, NormalMap, RoughnessMap, MetalnessMap })` | One bake per part per client; four 512² images is about 4 MB of editable memory | Per-player variation: a seeded rust pattern per pet, a weapon that wears down |
| **C. Live updates** | Bake once, then repaint a region of the colour map with `WritePixelsBuffer`, or stamp with `EditableImage:DrawImageProjected` | One image push per frame across all images (engine limit) | Damage decals, paint, scorch marks, growing moss |

**Rules that bite** (from the research):
1. **Bake on the client.** `Content.Object` doesn't replicate, and a server-made image shows as a checkerboard.
2. **Published games need the owner's 13+ and ID verification, plus "Enable Mesh / Image APIs".** Until then, route A is the only option that works for players.
3. **`CreateEditableMeshAsync` only opens meshes owned by or shared with the game owner** (or the player, client-side). It throws, so `pcall` it.
4. **Editable memory is budgeted per device**, and creation returns `nil` when it runs out. Always keep the authored texture as the fallback.
5. **`SurfaceAppearance` maps can't be swapped after creation.** A re-bake builds a new one. For colour-only updates, use `MeshPart.TextureContent`, which can be reassigned.
6. **The texture size limit is 1024².** For a hero prop use 1024; for crowd props, 256 is plenty.
7. **Roblox expects OpenGL normal maps**, which `Bake` writes. If a bump looks inverted, check the mesh's UV v direction (`Apply.fromEditableMesh(em, true)`) before flipping green.

## 4. Writing a recipe

Recipes are data. Copy a preset and change numbers only. Masks multiply, and each term goes through `smoothstep(lo, hi)` (set `lo > hi` to invert).

```lua
local recipe = {
	base = { color = { 0.36, 0.36, 0.38 }, rough = 0.35, metal = 1, vary = { scale = 5, amount = 0.08 } },
	detail = { { "noise", scale = 30, octaves = 3, amp = 0.01 } },        -- fine height everywhere
	layers = {
		{ name = "rust", color = { 0.45, 0.2, 0.08 }, rough = 0.92, metal = 0, height = 0.05,
			mask = { { "noise", scale = 2.5, octaves = 5, warp = 1.2, lo = -0.05, hi = 0.2 } } },
		{ name = "worn edge", color = { 0.62, 0.62, 0.64 }, rough = 0.2, metal = 1,
			mask = { { "edge", lo = 0.05, hi = 0.01 }, { "noise", scale = 12, octaves = 3, lo = -0.3, hi = 0.2 } } },
	},
	normalStrength = 1.2,
}
```

Craft rules:
1. **Wear follows geometry, then gets broken up by noise.** A clean edge mask looks like a stencil. Multiply it by a noise term so chips are irregular.
2. **Scale to the asset.** Scales are per stud. A 2-stud crate wants chip noise around 8–12; a 20-stud wall wants 1–2.
3. **The normal map does the selling.** A layer that changes colour but not height reads as a sticker. Give rust +height, chips −height and mortar −height.
4. **Roughness tells the material.** Rust 0.9, worn metal 0.2, paint 0.45, ice 0.1. The same colour at a different roughness is a different material.
5. **Keep it in its tier** ([HIERARCHY.md](../../HIERARCHY.md)). World props are tier 4: muted value range, no saturated accents brighter than threats or pickups. Run [`tools/hierarchy`](../../tools/hierarchy/README.md) on a capture of the scene.
6. **Emissive cracks (lava, runes)** are tier 2–4 depending on meaning. Bake the crack mask as a separate map and drive glow with a `SurfaceAppearance` emissive mask, or with a `PointLight` and `Highlight`, rather than a bright albedo alone.

## 5. Check before you ship

- [ ] `lune run lib/surfacebake/qa/test_surfacebake.luau` ends with `@@DONE 0`.
- [ ] Contact sheet (`qa/sheet.py`) reviewed: seams invisible, gutters padded, edges chipped where expected.
- [ ] In Studio, a test bump shows lit from the correct side (OpenGL convention, UV v direction).
- [ ] Route A (Studio bake and upload) for static props; route B only where per-player variation pays for itself.
- [ ] Fallback texture works when `CreateEditableMeshAsync` throws or memory is exhausted.
- [ ] Bake time measured on a phone-class device and logged in the repo's budgets doc.
