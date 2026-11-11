---
name: editable-mesh
description: Use when generating or deforming 3D geometry at runtime in Roblox with EditableMesh - procedural terrain chunks, heightfields, ribbons and trails, destructible or squishy objects, morphs, procedural props, mesh LOD and vertex/triangle budgets. Triggers on "EditableMesh", "procedural mesh", "generate geometry", "deform mesh", "mesh LOD", "vertices", "triangles in Roblox".
---

# editable-mesh

EditableMesh lets a game build and change triangles at runtime. Use it when Parts, Terrain and pre-made MeshParts can't produce the shape.

## When to use

- Procedural terrain chunks, islands, caves and roads
- Ribbons, trails and banners shaped by code
- Deformation: dents, squash and stretch, wobbling slimes, morph targets
- Procedural props assembled from rules (rocks, crystals, plants)

**Not for:** flat pixel work (use `editable-image`) or plain shapes that a Part or MeshPart already handles cheaply.

## Method

1. **Separate data from engine.** Build positions, normals, UVs and triangles as plain arrays in a pure module, then push them through a small adapter. The pure half is testable in lune.
2. **Check the winding.** Counter-clockwise seen from outside; a wrong winding renders invisible from the front. Test it with a cross product.
3. **Smooth or faceted.** Shared vertices plus averaged normals look smooth; split vertices per face give crisp low-poly facets.
4. **UVs.** Planar for terrain (x/z ÷ size) and arc-length along ribbons. Keep the texel density constant across LODs.
5. **Chunk it.** Split big surfaces into chunks (e.g. 32×32 cells). Rebuild only dirty chunks.
6. **LOD rings.** Full cells near the camera, then ½ and ¼ further out. Stitch borders with skirts (a vertical strip hanging down) to hide cracks.
7. **Deform cheaply.** Keep the base positions and write `SetPosition` for moved vertices only. Recompute normals for the touched region.
8. **Collision.** Visual meshes don't need exact collision. Use simple Parts as hitboxes, or build a collision mesh only for static chunks.
9. Run the self-check.

## Hierarchy rules it obeys

- §2: generated world geometry is tier 4 (world): soft, calm, never brighter than the HUD.
- §11: the silhouettes of walkable edges and hazards pass the figure-ground gate.
- §15: generation code is a central system or a content-driven service, never inline in a component.

## Engine notes

**Roblox.**

- Create with `AssetService:CreateEditableMesh()`, then use `AddVertex`, `AddNormal`, `AddUV`, `AddTriangle`, `SetFaceNormals` and `SetFaceUVs`.
- Display with `AssetService:CreateMeshPartAsync(Content.fromObject(mesh))`, or apply it to an existing MeshPart's content.
- EditableMeshes have engine limits on vertex and triangle counts and a per-device memory budget. Creation can fail, so handle `nil` and keep chunks modest.
- Mesh edits replicate only if you build on the server and the API allows it; usually generate deterministically on each client from a shared seed.
- Use `SurfaceAppearance` or a texture for the look (see `materials`).

**Web.** Use three.js `BufferGeometry` with the same arrays: `position`, `normal`, `uv`, `index`.

## Library and research

- [`lib/frontier/mesh`](../../../lib/README.md): `HeightfieldMesh` (paint-to-terrain with LOD, geomorphing, skirts and incremental vertex updates) and `ContourMesh` (destructible 2D terrain: marching squares → simplify → earcut → extrude, one tile per carve), plus `combo/SandTable`, `combo/Lightmap` and `combo/Fracture`.
- Research: [EditableMesh API](../../../docs/research/21-roblox-editablemesh-api.md) (all methods, limits: 20k triangles / 60k vertices per mesh), [technique cookbook](../../../docs/research/41-editablemesh-technique-cookbook.md), [3D math toolkit](../../../docs/research/43-roblox-3d-math-toolkit.md).

## Process

Reading an asset's geometry to texture it: `Apply.fromEditableMesh` in [`lib/surfacebake`](../../../lib/surfacebake/README.md) turns an EditableMesh into positions, per-corner UVs and normals for UV-space baking ([procedural textures playbook](../../../docs/playbooks/procedural-textures.md)).

## Example

`examples/GridMesh.luau` builds a heightfield (positions, central-difference normals, UVs, CCW triangles), picks a LOD by distance, and includes a Roblox adapter that creates the EditableMesh and MeshPart. It's tested in `examples/GridMesh.test.luau`.

```lua
local GridMesh = require("./examples/GridMesh")
local data = GridMesh.build(64, 32, function(x, z)
	return 4 * math.noise(x / 20, z / 20)            -- any height function
end)
-- Roblox (client):
-- local part, mesh = GridMesh.toRoblox(data, workspace)
local cells = GridMesh.cellsForDistance(32, 120, 50)  -- 16 at 120 studs
```

## Make it insane

1. **Living terrain:** the heightfield breathes with a slow domain-warped noise near a boss arena, and its vertex colours pulse with the boss's attack telegraph so the floor itself warns the player.
2. **Squash-and-stretch pickups:** coins and pets are EditableMeshes whose vertices spring toward a target shape (mass-spring per vertex), wobbling on spawn and stretching toward the magnet when collected.
3. **Procedural crystals:** each rarity tier grows a different crystal (more facets, sharper angles, internal emissive core). The mesh is generated from a seed stored with the item, so every crystal is unique and still reads as its tier.

## Self-check

- [ ] Pure builder has a lune test (counts, winding, normals).
- [ ] Faces render from the intended side (no inverted triangles).
- [ ] Chunks rebuild only when dirty; nothing rebuilds per frame unless it's a deliberate deformation.
- [ ] LOD borders hide cracks (skirts or stitching).
- [ ] Creation failure is handled (fallback mesh or Part).
- [ ] Vertex and triangle counts per chunk are written down with the measured build time.
