# EditableMesh: limits, data model and gotchas

Full sourcing: [research chapter 21](../../../../docs/research/21-roblox-editablemesh-api.md). Measured library numbers: [`lib/frontier`](../../../../lib/frontier/README.md).

## Hard limits and gates

| Limit | Value | Failure |
|---|---|---|
| Per mesh | **60,000 vertices, 20,000 triangles** | Throws. Chunk large surfaces. |
| Memory | Client budget, device-specific, unpublished, **shared with EditableImage** | `CreateEditableMesh*` returns **nil** |
| Published games | Creator 13+ age + ID verified, **Enable Mesh / Image APIs** on | Works in Studio, fails live |
| Loading an asset | Owned by / shared with the owner, Studio user, or (client only) the player | `CreateEditableMeshAsync` throws |
| `CreateMeshPartAsync` | ~22 ms per call (measured order); throws on failure | Never per frame |
| Replication | `Content.fromObject` doesn't replicate | Cyan/magenta checkerboard on clients |
| Uploading | No documented API saves a generated mesh as an asset | Regenerate from a seed, or export at edit time |

## Data model

- IDs are **stable int64 handles**, not indices. Removing leaves holes; iterate `GetVertices()` / `GetFaces()`.
- Positions are per vertex; normals, UVs and colours are **per face corner** in their own ID spaces. `AddTriangle` reuses a vertex's existing attributes (smooth) unless you add new ones (seams, hard edges).
- New vertices get UV (0,0): an untextured-looking mesh is usually unset UVs, not a broken texture. V origin is unverified; test with an asymmetric texture.
- `FixedSize` defaults to **true** for meshes loaded from an asset (cheaper, no topology changes, `Clear()` throws). Pass `{ FixedSize = false }` to edit topology.
- Batch APIs (`BatchAdd`, `BatchSetValues`, `BatchGetValues`, `BatchRemove`) are the fast path. They are not atomic: they stop at the first bad ID.

## Live vs baked

- **Visual edits are live** on a linked MeshPart. **Collision, `MeshSize` and fluid geometry are baked** and only update through `CreateMeshPartAsync` + `ApplyMesh`.
- So: deform visuals every frame if needed; rebuild collision rarely, per tile, debounced (`ContourMesh` rebuilds one tile per carve, 0.44 ms interp + the part call).
- Use simple Parts as hitboxes for anything that moves.

## Performance (headless desktop, ms; use Interp for live clients)

| Work | Interp | Native |
|---|---|---|
| Heightfield chunk build (8.7k tris) | 4.3 | 2.3 |
| 8×8 brush incremental vertex update | 0.12 | 0.05 |
| Morph 64 chunks | 7.5 | 1.6 |
| Contour carve + rebuild one tile | 0.44 | 0.14 |
| Fracture: crack growth per frame / full fracture into 29 meshes | 0.40 / 74 | 0.11 / 25 |

Build big things over several frames (fracture labels in one frame, builds 2 meshes per frame after).

## Threads

Mutators are parallel-**Unsafe**; getters and spatial queries are **Safe**. Raycast and compute in Actors, write after `task.synchronize()`.

## Gotchas

| Symptom | Cause | Fix |
|---|---|---|
| Faces invisible from outside | Clockwise winding | Counter-clockwise seen from the front; `DoubleSided` doubles raster cost |
| Cube looks like a blob | Shared normals | One normal ID per face for hard edges |
| Mesh drifts toward the cap | `RemoveFace` leaves vertices and attributes | `RemoveUnused()` on a cadence |
| Raycast misses the animated pose | Queries use the bind pose on skinned meshes | Query your own data, or a proxy |
| Hits land where the mesh used to be | Collision not rebuilt | `CreateMeshPartAsync` + `ApplyMesh` after edits |
| Wrong values from queries | `RaycastLocal` returns `(point, face, bary)`, `FindClosestPointOnSurface` returns `(face, point, bary)` | Wrap both once |
| Budget runs out with many copies | Every instance holds its own editable mesh | For many repeated objects (pets, crowd props, 20+ per player), use **uploaded meshes + colour tints**, and keep EditableMesh for few, unique, changing shapes |
