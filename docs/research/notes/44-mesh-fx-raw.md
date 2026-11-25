# E. Geometry VFX on Roblox: making mesh, beam, trail and bone effects cheaper and stronger

Research date 2026-11-24. Scope: EditableMesh (EM), MeshPart, Beam, Trail, Bone/skinning, Decal/SurfaceAppearance/material tricks, mapped from AAA mesh-VFX practice.

The kit already has `docs/research/21-roblox-editablemesh-api.md` and `41-editablemesh-technique-cookbook.md`, which restate the API. These notes cover **deltas and depth**: facts that are new, corrected, measured, or resolve items those chapters mark `[UNVERIFIED]`. Section 0 lists what changes for the kit.

## Confidence tags

- **[DOCUMENTED]**: Roblox creator-docs YAML or guide (raw.githubusercontent.com/Roblox/creator-docs/main, cloned 2026-11-24), or a Roblox staff post in an official DevForum announcement thread.
- **[API-DUMP]**: read from the reference YAML's security, thread-safety and tag fields (generated from the engine API dump).
- **[COMMUNITY, SECOND-HAND]**: DevForum replies by non-staff, community resources, or public GitHub code. Numbers are someone else's measurement on their own hardware.
- **[UNVERIFIED]**: my inference, or a claim no source confirms. These are worth a Studio test.

Staff names seen in the threads: FGmm_r2, L3Norm, TheMeshBoy (EditableMesh/geometry team), zeuxcg (former rendering lead, 2018 posts), RobieTheCat (skinned-mesh engineer, 2020), vrtblox (ForceField material, 2019). Penpen0u0's role is unknown.

### Sources (fetched for these notes)

Primary docs (creator-docs `main`, `content/en-us/`):
- `reference/engine/classes/EditableMesh.yaml`, `AssetService.yaml`, `MeshPart.yaml`, `Bone.yaml`, `WrapDeformer.yaml`, `FaceControls.yaml`, `EditableImage.yaml`, `Decal.yaml`, `SurfaceAppearance.yaml`, `Highlight.yaml`, `Beam.yaml`, `Trail.yaml`; `datatypes/Content.yaml`; `enums/ContentSourceType.yaml`, `Material.yaml`, `AlphaMode.yaml`
- `performance-optimization/improve.md` and `design.md`, `effects/beams.md`, `trails.md` and `highlighting.md`, `parts/textures-decals.md`, `parts/procedural-models.md`, `art/modeling/rigging.md`
- The `art/modeling/editable-mesh*` guides **no longer exist** (404 on raw; not in the tree). The reference YAML is now the only primary doc.

DevForum (read through the `/raw/<topic-id>` endpoint):
- [Full Release] EditableMesh Batching APIs & Parallel Queries, 4779401 (staff: FGmm_r2, L3Norm; full release 2026-09-15)
- [Full Release] Introducing CreateDataModelContent, 4541898 (staff, 2026-03 to 05)
- [Studio Beta] Skinning and FACS data support for EditableMesh, 3731147 (staff, 2025-06)
- [Studio Beta] Major updates to in-experience Mesh & Image APIs, 3225681 (staff, memory-management section)
- EditableMesh and EditableImage Improvements, 3818624 (staff, 2025-07)
- Part Instancing pre-release announcement, 130333 (zeuxcg, 2018: the only detailed public description of Roblox batching)
- Real world building and scripting optimization, 3127146 (Roblox-published guest article by MrChickenRocket, 2024)
- Low FPS due to transcodeVerticesAndCalculateBounds, 3904722; EditableMeshes cause extreme FPS drop on PC, 3904168; SetPosition black flicker on macOS Metal, 4635427; Bulk API operations request, 4643551
- Skinned MeshParts are live, 831011 (RobieTheCat); SkinnedGrass resource, 3364812; Bone.ShouldUpdate request, 954296; UpdateGeometryWithSkinning bug, 3629660
- Solid modeling on meshes: Fragment and Sweep, 4515374 (staff; live 2026-07-07)
- New material ForceField v2.0, 297785 (vrtblox); How ForceField texture animation works, 3041374
- Beams: Bypassing forced beam LOD 2426888, Light beam limits 254668, Force segments request 82214

GitHub (public; read raw):
- `vfx-forge/module`: `docs/lightning-measured.md` (Studio measurements, 2026-10-24) and `src/mod/lightning/mesh.luau`
- `nightcycle/imposter-baker`: `README.md`, `imposter-render/src/init.luau`
- `turtlesoupy/robloquake`: `src/client/render/entrender.luau`
- `MrChickenRocket/sdf-procedural-toolkit`: `docs/02-editablemesh-and-baking.md`
- Code search hits are listed in §6

AAA background:
- GDC 2013 "Technical Artist Bootcamp: The VFX of Diablo" (Julian Love), https://gdcvault.com/play/1017660; JangaFX teardown https://jangafx.com/insights/diablo-3-vfx-experiments; Simon Schreibt on Diablo 3 resource bubbles https://simonschreibt.de/gat/diablo-3-resource-bubbles
- RealtimeVFX "LoL FX + Knowledge Share" (Shannon Berke/McSheehan), https://realtimevfx.com/t/shannon-berke-lol-fx-knowledge-share/1133; "VFX Basics - Mesh Soulercoasters", https://realtimevfx.com/t/vfx-basics-mesh-soulercoasters/1987
- Octahedral impostors (Ryan Brucks, shaderbits 2018), summarised at https://smailikhappy.github.io/posts/Octahedral_imposters/; SideFX Labs octahedron impostor, https://www.sidefx.com/docs/houdini/nodes/shop/labs--octahedron_impostor_lens.html
- EA SEED "Dem Bones" (skinning decomposition), https://www.ea.com/seed/news/open-source-dem-bones (named by L3Norm as the shape-key-to-bones route)

---

## 0. What changes for the kit (deltas against chapters 21/41)

1. **Bone instances drive EditableMesh bones by name: resolved [DOCUMENTED].** Chapter 21 §? marks this `[UNVERIFIED]`. Staff (FGmm_r2, 3731147 #1): *"Internal bones and Bone instances are bound to each other by their unique names. For example: The `MeshPart.Neck` instance will drive the runtime transformation of the `EditableMesh:GetBoneByName("Neck")` internal bone."* So a skinned EM is deformed by the engine. Per-frame deformation costs a handful of `Bone.Transform` writes, with no per-vertex Luau and no re-transcode.
2. **Server-made DataModelContent replicates to clients: resolved [DOCUMENTED].** Chapter 21 §9 marks this `[UNVERIFIED]`. Staff (FGmm_r2, 4541898 #73): server-created DataModelContent *"will also be available on all clients through replication"*; client-created content does not replicate. It *"pages the Mesh / Image content to local disk"*, with no CDN involved. Content is reference-counted and the file is deleted when the last reference goes (L3Norm #44).
3. **Why "8 dynamic EMs" happens [DOCUMENTED].** L3Norm (4779401 #117, 2026-10-19): *"every time you create an empty EditableMesh, it adds 20,000 triangles to the budget"*, so about 8 at a time. The budget is not exposed to scripts (4541898 #70).
4. **The CreateMeshPartAsync cost depends on CollisionFidelity [COMMUNITY, measured 2026-10-23].** vfx-forge: *"Box fidelity made a 330 vertex bolt's part in 0.22 ms, the default fidelity in 21.7 ms."* This conflicts with cookbook 41's "~22 ms even with Box". Separately, staff acknowledged a ~20 ms main-thread lockup in CreateMeshPartAsync that did not depend on mesh size. L3Norm, 4779401 #115 (2026-10-01): *"I believe I have a fix."* **Re-measure on the current client** (see Q9).
5. **Re-transcode cost does not depend on how many vertices changed [COMMUNITY].** DevVexus, 4779401 #85: *"(TranscodeVerticies) Currently the same for updating one vertex of a mesh to updating all of them."* Batching removes the Luau-to-C++ call overhead, not the transcode. Split meshes by update rate.
6. **Writing vertices on an animating skinned EM is the worst case [COMMUNITY, reverse-engineered].** tabby0x (3731147 #15): any vertex edit on a skinned EM while it animates is treated as a bind-pose change. That means a FastCluster rebuild, a full re-upload and a full skinning pass every frame: 240 to 60 fps on a 7800X3D, under 10 fps on mobile. **Pick bones or vertex writes per mesh, never both.**
7. **New scriptable render knobs that need no EditableMesh [API-DUMP]:**
   - `MeshPart.DoubleSided` (write: None)
   - `Decal.UVOffset`, `Decal.UVScale`, `Decal.Rotation` (all write: None)
   - `Decal.EmissiveMaskContent`, `Decal.EmissiveStrength` and `Decal.EmissiveTint`
   - `SurfaceAppearance.Color`, `EmissiveStrength` and `EmissiveTint` (write: None)

   They give UV-scrolled and pulsing surfaces on any part, with no transcode.
8. **The Highlight cap is now 255, not 31 [DOCUMENTED, highlighting.md].** The first visible Highlight costs *"up to 1 millisecond of GPU time on mobile"*; extra ones cost little. Adding or removing a Highlight triggers a geometry rebuild, so toggle `Enabled` instead.
9. **Beam segment counts no longer drop with quality level [DOCUMENTED, design.md 2026]:** *"beams keep their segment count at all quality levels."* This contradicts 2018–2023 community reports (see §5). Verify with Q11.
10. **Only one displayed EditableImage updates per frame [DOCUMENTED, EditableImage.yaml].** *"if you update three EditableImage objects which are currently being displayed, it will take three frames."* Never animate several EditableImage textures at once for VFX; animate UVs or geometry instead.
11. **The editable-mesh guides were removed** from creator-docs. Links to `art/modeling/editable-mesh` are dead.

---

## 1. Primary-doc facts, with the mechanism of each saving

### 1.1 Limits

- **60,000 vertices and 20,000 triangles per EM.** Quads are now allowed (`AddFace` with 4 IDs) and count as 2 triangles. Going over throws [DOCUMENTED, EditableMesh.yaml "Limitations"]. Staff: the limits *"are based on the limits that are enforced when you upload a mesh"*. There are talks about raising them but *"nothing imminent"* (L3Norm, 4779401 #63).
- **4 bones per vertex** [DOCUMENTED, GetVertexBones]. The maximum bones per mesh is **not documented**; AddBone errors *"if … the mesh already contains the maximum number of bones."* See Q4.
- **Bone names are unique** and at most 100 characters [DOCUMENTED].
- **MeshPart size cap is 2048 studs per axis** [COMMUNITY, 4541898 #24/#59]. A script-created runtime MeshId can be put on a SpecialMesh to scale past it, but staff warn the internal ID will become opaque and refcount-unsafe (#54). Don't build on that.

### 1.2 Memory budget wording, and how to stay under it

- Docs: *"Editable assets are currently expensive for memory usage. … `EditableMesh` has strict client-side memory budgets, although the server, Studio, and plugins operate with unlimited memory. Using `FixedSize` may help … linking one `EditableMesh` to multiple `MeshParts` (multi-referencing) can help with memory optimization. If an `EditableMesh` no longer changes, you can save a significant amount of memory budget by converting it to `Opaque` content with `CreateDataModelContentAsync()`."* [DOCUMENTED, EditableMesh.yaml "Memory limits"]
- `CreateEditableMesh()` / `CreateEditableMeshAsync()` return **nil** when the device budget is spent [DOCUMENTED, AssetService.yaml].
- Staff decision table (L3Norm, 4779401 #117) [DOCUMENTED]:
  - *"Need 20,000 triangles per EditableMesh and still dynamic? Effective limit is still 8."*
  - *"Want fewer triangles and still dynamic? Convert EditableMeshes to fixed-size"*: `AssetService:CreateEditableMeshAsync(Content.fromObject(dynamicEm))` returns fixed-size by default, and you can still set positions, colours and UVs.
  - *"Just want procedural geometry that is static? DataModel Content is the way to go."*
- **Mechanism.** A blank EM reserves worst-case capacity. A fixed-size clone reserves only its real element count. DataModelContent leaves the editable pool entirely and gets mesh streaming and LODs.
- Real code doing this: robloquake `entrender.luau`: *"fixed-size copy: a dynamic EditableMesh reserves the 60k-vertex max against the memory budget; the copy reserves only its actual size and still allows SetPosition (frame animation)"*. A shipped kit-cited project holds 81 live fixed-size EMs (chapter 41) [COMMUNITY].

### 1.3 FixedSize: what it does, and whether it is faster

- *"Fixed-size meshes are more efficient in terms of memory but you cannot change the number of vertices, faces, or attributes. Only the values of vertex attributes and positions can be edited."* `Clear()` throws on a fixed-size mesh [DOCUMENTED]. The `FixedSize` property is read-only (write: RobloxEngineSecurity) [API-DUMP].
- **Speed: no source claims fixed-size updates or transcodes faster.** All documented and staff wording is about memory. Treat it as a memory lever [UNVERIFIED for speed; Q7].

### 1.4 What updates the render live, and what needs a rebuild

| Change | Render updates | Physics/collision | Cost driver | Source |
|---|---|---|---|---|
| Positions, UVs, colours, alpha, normals (`Set*`, `BatchSetValues`) | Live, next frame | Not updated | Luau calls plus a **whole-mesh** re-transcode and GPU re-upload | [DOCUMENTED] *"Visual changes to the mesh will always be immediately reflected"*; [COMMUNITY] transcode is the same for 1 or all vertices |
| Topology (`AddFace`, `RemoveFace`, `BatchAdd`, `BatchRemove`) on a non-fixed EM | Live | Not updated | As above | [DOCUMENTED] |
| Collision or fluid geometry | n/a | Only `CreateMeshPartAsync` then `MeshPart:ApplyMesh` | Hull build: fidelity dependent (0.22 ms Box vs 21.7 ms Default, ~330 verts) | [DOCUMENTED] + [COMMUNITY measured] |
| `Bone.Transform` on bones bound to a skinned EM | Live; engine skinning | Not updated (bones are visual only) | Per-bone engine update; no Luau per vertex | [DOCUMENTED] binding by name; [COMMUNITY] costs §1.6 |
| `SetBoneCFrame` (bind pose) or vertex edits on a skinned EM | Live | n/a | **Full bind-pose rebuild, FastCluster rebuild, full skin** | [COMMUNITY RE] tabby0x |
| `EditableMesh` queries (`RaycastLocal`, `FindClosest*`, `Get*`, `BatchGet*`) | n/a | n/a | Parallel-safe (Actors after `task.desynchronize()`) | [DOCUMENTED] 4779401; YAML `thread_safety: Safe` |
| Skinned EM queries | Run against the **bind pose**, not the deformed mesh | | | [DOCUMENTED] RaycastLocal/FindClosest descriptions; L3Norm 3731147 #41: no API returns skinned positions |

### 1.5 Bone and skinning API, the GPU-deformation path

**Answer to the brief: yes.** Moving Bone instances deforms a skinned EditableMesh with no per-vertex Luau [DOCUMENTED binding; COMMUNITY recipe details].

**Recipe** (MrChickenRocket `02-editablemesh-and-baking.md`, written against the 2026 API) [COMMUNITY]:
1. `em:AddBone({ Name = "B1", CFrame = bindCFrame, ParentId = parentId })`. Add parents before children.
2. For each skinned vertex, `em:SetVertexBones(vid, {ids})` **then** `em:SetVertexBoneWeights(vid, {ws})`. Use at most 4 bones. Leave out zero weights together with their IDs (the engine trims them and warns). Weights should sum to about 1. The arrays must be the same length.
3. Build the part **single-step**: `AssetService:CreateMeshPartAsync(Content.fromObject(em), {CollisionFidelity = Enum.CollisionFidelity.Box})`. MCR reports the two-step path (`CreateDataModelContentAsync`, then `CreateMeshPartAsync`) gives `HasSkinnedMesh = false` (*"a Roblox regression"*). That contradicts staff: L3Norm (4541898 #44) says a skinned EM baked to DataModelContent *"should animate like any other MeshPart"*. Test it (Q15).
4. `AddBone` does **not** create Bone instances. Create `Instance.new("Bone")` with the **exact** name and `CFrame = bindCFrame`, parented to the MeshPart (flat) or to a parent Bone (nested).
5. Animate with **`bone.Transform`**, never `bone.CFrame` (that is the bind pose). `Transform` is NotReplicated [API-DUMP], so drive it on the client.

```lua
-- Skinned EM ring: 2 rings x 8 bones, deformed by Bone.Transform only.
local AssetService = game:GetService("AssetService")

local function buildSkinnedRing(radius: number, width: number, segments: number)
	local em = AssetService:CreateEditableMesh()
	if not em then return nil end
	local inner, outer = {}, {}
	local boneIds = {}
	for b = 1, 8 do
		local a = (b - 1) / 8 * math.pi * 2
		boneIds[b] = em:AddBone({ Name = "R" .. b, CFrame = CFrame.new(math.cos(a) * radius, 0, math.sin(a) * radius) })
	end
	for s = 0, segments - 1 do
		local a = s / segments * math.pi * 2
		local dir = Vector3.new(math.cos(a), 0, math.sin(a))
		inner[s] = em:AddVertex(dir * (radius - width * 0.5))
		outer[s] = em:AddVertex(dir * (radius + width * 0.5))
		-- weight to the two nearest bones
		local f = s / segments * 8
		local b0 = math.floor(f) % 8 + 1
		local b1 = b0 % 8 + 1
		local w1 = f - math.floor(f)
		for _, v in { inner[s], outer[s] } do
			if w1 < 1e-3 then
				em:SetVertexBones(v, { boneIds[b0] })
				em:SetVertexBoneWeights(v, { 1 })
			else
				em:SetVertexBones(v, { boneIds[b0], boneIds[b1] })
				em:SetVertexBoneWeights(v, { 1 - w1, w1 })
			end
		end
	end
	for s = 0, segments - 1 do
		local n = (s + 1) % segments
		em:AddFace(inner[s], outer[s], outer[n], inner[n]) -- quad = 2 tris
	end
	local part = AssetService:CreateMeshPartAsync(Content.fromObject(em), { CollisionFidelity = Enum.CollisionFidelity.Box })
	local bones = {}
	for b = 1, 8 do
		local bone = Instance.new("Bone")
		bone.Name = "R" .. b
		bone.CFrame = em:GetBoneCFrame(boneIds[b])
		bone.Parent = part
		bones[b] = bone
	end
	return part, bones, em
end
-- per frame: expand the ring with 8 writes, no vertex edits
-- bones[b].Transform = CFrame.new(radialDir[b] * grow)
```

Engine-side costs [COMMUNITY unless marked]:
- GPU skinning cost is *"an extra 10-15% depending on platform. CPU cost is less than that, and depends on how much is skinned to Bones vs Parts"* (RobieTheCat, staff, 831011 #38, 2020) [DOCUMENTED-ish, dated]. This implies GPU skinning on most platforms. Whether there is a CPU fallback on old GLES devices is unknown.
- Measured (SkinnedGrass, 3364812, 2026-01): *"bulkmoveto on 2000 meshparts averages 3.426 ms; transform on 2000 bones in 20 skinned meshes … .987 ms"*. Reparenting 2000 MeshParts took 18.5 ms against under 0.5 ms for 20 skinned meshes with 2000 bones. Static MeshParts are *slightly* cheaper than static skinned ones, and shadows cost more on skinned meshes.
- Idle bones still cost (tyridge77, 954296, **2020**): `updateSkinningIslands` scales with bone count and `performUpdateCoordinateFrame` with bones and vertices, *"whether or not they're actually updating"*. It may have improved since. Mitigation: parent bone-heavy VFX into Workspace only while playing.
- **Moving skinned MeshParts** in a Model without a Humanoid sit in spatial FastClusters, and moving them forces cluster rebuilds. Docs [DOCUMENTED, improve.md]: *"A highly effective workaround is to embed a Humanoid within the Model … position updates no longer necessitate cluster rebuilds."* Use this only for skinned VFX that travel, such as a skinned projectile or slash.
- `Size` and scale changes also rebuild FastClusters [DOCUMENTED, improve.md]. One report has Size tweening on a character-held MeshPart costing about 5 ms in `UpdateGeometryWithSkinning` (3629660).
- Bone-heavy meshes add draw calls: *"Using extreme amounts of bones on skinned meshes can cause extra drawcalls"* (MrChickenRocket guest article 3127146). The likely cause is a per-draw bone-palette limit [UNVERIFIED].

### 1.6 Vertex colour and alpha

- Colour and alpha are stored **per face corner** through colour IDs. `AddColor(color, alpha)`, `SetColor`, `SetColorAlpha` and `BatchSetValues(colorIds, {Color3})` or `(colorIds, {number})` are documented. `alpha` runs 0 (transparent) to 1 (opaque) [DOCUMENTED].
- **Per-vertex alpha only renders when the part is in the transparent pass.**
  - Staff (L3Norm, 4541898 #44) [DOCUMENTED]: *"per-vertex transparency rendering doesn't kick in unless the part itself has a slight transparency."*
  - vfx-forge measured that the threshold is **0.02** (0.01 drew opaque, 2026-10-23) [COMMUNITY]. Another user said 0.011. Use **`part.Transparency = 0.02`**.
  - The same 0.02 threshold appears in `SurfaceAppearance.AlphaMode` docs: Transparency ≥ 0.02 switches to *"a different blending method … smooth transparency gradients and soft edges"* [DOCUMENTED].
- `MeshPart.Color` multiplies vertex colour. Keep it `Color3.new(1, 1, 1)` [COMMUNITY, MCR].
- **Cost implication.** A transparent MeshPart is drawn alone (§2). One transparent EM holding 50 quads is **one** draw call; 50 transparent MeshParts are 50.

### 1.7 Normals

- `AddNormal()` with no argument gives an **auto-computed** normal. `SetNormal` overrides it; `ResetNormal(id)` and `BatchSetValues(normalIds, nil)` revert to auto [DOCUMENTED].
- **There is no `ComputeNormals` method any more** [DOCUMENTED, method list]. Auto normals are recomputed by the engine.
- **Cost unknown** [UNVERIFIED]: whether auto normals add to the per-frame transcode once positions move. For unlit VFX (Neon, or `LightInfluence`-style looks) normals barely matter. Give every face one fixed explicit normal ID and test whether transcode time drops (Q16).
- Flat shading: give each face its own normal ID (`SetFaceNormals(fid, {n, n, n})`). Smooth shading: share IDs. This is the default when faces share vertices [DOCUMENTED].

### 1.8 Faces, UV IDs and stable IDs

- IDs are stable, with holes, and encode their own type. `IdDebugString` decodes them [DOCUMENTED].
- New: `AddFace` takes 3 or 4 IDs; `Triangulate()` splits quads; `MergeVertices(tol)` welds vertices and keeps attribute IDs; `GetVertexFaceUV/Color/Normal` and the setters work per corner [DOCUMENTED].
- **Change UV values in place** (`GetVertexFaceUV` then `SetUV`) rather than adding IDs. Docs: *"more performant and avoids leaving unused IDs"* [DOCUMENTED]. For UV scrolling, keep the UV ID array and call `BatchSetValues(uvIds, uvs)` each frame.

### 1.9 Multi-referencing one EM from many MeshParts

- [DOCUMENTED]: *"You can create more MeshPart instances that reference the same EditableMesh Content"* (`CreateMeshPartAsync(Content.fromObject(em))` repeatedly, or `ApplyMesh`). This is documented as a **memory** optimisation.
- **Instancing (one draw call) for parts sharing one EM is not documented.** Community evidence suggests geometry is shared. chkfla2 (4779401 #18): one animated grass-patch EM copied across many MeshParts gave *"640,000 total moving blades of grass covering 400 studs (~105 FPS)"*, and the work is computed once per patch [COMMUNITY]. Test the draw-call count (Q1).
- **VFX use:** one deforming EM can feed *N* simultaneous copies of an effect (8 identical shockwaves, a field of flames) for **one** set of Luau writes and one transcode.

### 1.10 CreateMeshPartAsync and collision fidelity

- Options: `CollisionFidelity`, `RenderFidelity` and `FluidFidelity` [DOCUMENTED].
- Measured: **Box 0.22 ms against Default 21.7 ms** for a 330-vertex mesh (vfx-forge, 2026-10-23) [COMMUNITY].
- Older reports of 15–21 ms per call regardless of size: 4779401 #102 (2026-09) and #114. Staff are fixing it (#115, 2026-10-01). Pavalineox measured CreateDataModelContentAsync as async but CreateMeshPartAsync blocking the main thread for about 20 ms.
- **Recipe for every VFX part:** `{CollisionFidelity = Enum.CollisionFidelity.Box}`, then `CanCollide = false`, `CanQuery = false`, `CanTouch = false`, `CastShadow = false`, `Anchored = true`. Create parts at load and pool them; never create them mid-combat.

### 1.11 DataModelContent (bake once, replicate, LOD) [DOCUMENTED, 4541898]

- `local res, content = AssetService:CreateDataModelContentAsync(Content.fromObject(em))` returns `Enum.CreateContentResult` plus Opaque `Content`. On server storage exhaustion it returns `StorageLimitExceeded` [DOCUMENTED, AssetService.yaml].
- Staff list: it can drive MeshContent and TextureContent; it **replicates** server to client; it is *"transcoded into various Levels of Detail (Meshes) and Mips (Images)"*; it does **not** use the Editable budget; it can be turned back into an EM. It lives for the session, needs no moderation queue and no upload. Studio Assistant and GenerationService outputs use it too.
- Cost measured by community: about 85–100 ms for `CreateDataModelContentAsync` plus 40–60 ms for the part, with spikes into the 200s (4541898 #74). One voxel user measured 20–30 ms per bake (4779401 #89). **Bake at load, never per hit.**
- Discarding the returned `Content` deletes the data. Keep the Content (or a MeshPart using it) alive, and don't copy its internal MeshId string (L3Norm #54).
- MCR recommends passing the fidelity options to **both** calls in the two-step path [COMMUNITY].

### 1.12 Bounds, origin and culling

- vfx-forge (2026-10-23) [COMMUNITY]: *"a mesh part keeps its mesh's origin instead of recentering on its bounds, so world space vertices sit at identity, and vertices moved past the bounds it was made with still draw"*. Their bolt sets `part.CFrame = CFrame.identity` and writes world-space vertices.
- nightcycle impostor renderer [COMMUNITY]: *"Degenerate, invisible triangles keep a fixed local-space mesh bound. All dynamic quads must stay inside this extent for reliable culling."* It adds two zero-area triangles at ±`WorldExtent`. An older community report says culling used the MeshPart size rather than the EM's live extent.
- **Recipe:** for any EM whose vertices travel (ribbons, pooled quads), pin the bounds with 2 degenerate triangles at the corners of the largest extent you will use, then call `CreateMeshPartAsync`. The cost is 6 vertices; the gain is no popping when the original small bounds leave the frustum. Whether `transcodeVerticesAndCalculateBounds` already refreshes culling bounds is not confirmed (Q8).

### 1.13 Platform bug to design around

- macOS Metal: a loop of `SetPosition` over 500+ vertices in the serial phase causes single-frame black flickers. It shows only at graphics quality ≥ 5 (4635427, 2026-05; staff could not reproduce) [COMMUNITY]. **Use one `BatchSetValues` per frame instead of loops.** It is likely, not proven, to give an atomic update [UNVERIFIED; Q17].

---

## 2. Instancing and draw calls on Roblox

### Rules (zeuxcg 2018, still the only detailed public statement) [DOCUMENTED, dated]

- Meshes with the same asset ID share **one vertex buffer**. Parts *"similar"* in geometry, material/shader and texture are batched: up to about **512 instances per draw call**, within one cluster (chunks of 128×64×128 studs; *"may change"*).
- **No batch cost:** CFrame, Size (mostly), Color/BrickColor, UsePartColor, Reflectance; SpecialMesh Offset, Scale and VertexColor; Decal Color3, Transparency and StudsPerTile.
- **"Batch Wreckers":** MeshId, TextureId, Material, and **Transparency, *"the worst … we have to force a single instance per draw call for each transparent part"*** (OIT too expensive). Decal transparency is exempt.
- **Update cost, cheapest to most expensive:**
  - (0) static
  - (1) **CFrame of meshes: "the fast path … as cheap as patching a few floats"**
  - (2) Color, Size, Reflectance: full part update plus cluster bbox update
  - (3) SpecialMeshes: about **10× slower** than basic parts, no fast path
  - (3) CFrame across a cluster boundary
  - (4) Transparency: nonzero to nonzero is like Color; **0 to nonzero creates and destroys graphics objects**
  - (5) anything else rebuilds graphics objects
- Hiding: Transparency = 1 is cheap after a 2018 fix. Toggling 0↔1 is *"noticeably faster than unparenting/reparenting"*.

### Current official wording [DOCUMENTED, improve.md 2026]

- *"multiple meshes with the same `MeshContent` are handled in a single draw call when: SurfaceAppearances are identical if present, otherwise when TextureContents are identical. Materials are identical when both SurfaceAppearance and TextureID don't exist."*
- *"Objects like decals, textures, and particles don't batch well … property changes to ParticleEmitters can have a dramatic impact on performance."*
- *"High transparency overdraw"* is listed as a problem.
- Baseline example budget: *"stay below 1,000 draw calls and 1,000,000 triangles"* on your baseline device (design.md). This is an example, not a rule.

### Roblox-published guest article (MrChickenRocket 2024, 3127146) [COMMUNITY, Roblox-published]

- Scene budget 500 draw calls / 500k triangles; a flexible budget of 200 draw calls / 200k triangles for players, pets and effects.
- *"all particle emitters take one drawcall each"*; *"Beams and particle effects all cost 1 drawcall each"*; *"Transparent objects via Part.Transparency can cause unexpected extra drawcalls"*; unique Decal/Texture IDs each add draw calls.
- A reply notes semi-transparent parts with decals don't batch.

### What this means for geometry VFX

| Approach | Draw calls | Per-frame CPU | Notes |
|---|---|---|---|
| *N* opaque pooled MeshParts, same MeshId and material (debris, shards, rocks) | ~1 per cluster | `workspace:BulkMoveTo` (fast path) | Fade by **shrinking**, not Transparency; don't vary TextureID |
| *N* transparent MeshParts (glows, slashes) | **N** | — | The biggest hidden cost in Roblox VFX |
| One EM holding *N* transparent pieces | **1** (plus one transparency sort for the whole mesh) | One BatchSetValues plus a whole-mesh transcode | No per-triangle sort, so overlapping alpha can mis-order. Additive Neon looks hide this |
| *N* Beams or *N* Trails | **N** | Engine; zero Luau when static or TextureSpeed only | Per-frame update cap (§5) |
| One ParticleEmitter | 1 | Engine | Prefer it for sprite clouds |
| Distinct EMs (each its own content) | 1 each | — | Procedural chunks never batch with each other (3818624 #5) |
| Many MeshParts sharing one EM | Probably 1 per cluster [UNVERIFIED, Q1] | One update feeds all copies | Community grass evidence |

---

## 3. AAA mesh-VFX techniques, mapped to Roblox

Each entry: what it is, how it saves, the Roblox recipe, cost, sources and confidence.

### 3.1 Slash / crescent ("anime slash")

**AAA.** A crescent mesh, UV U along the arc and V across, a scrolling or eroding texture (often a panner plus an alpha-erode threshold driven by particle age), plus vertex-colour alpha feathering at the tips. One mesh can serve hundreds of slashes. Sources: Diablo 3 talk, LoL knowledge-share thread, Soulercoasters.

**Roblox recipes, cheapest first:**

1. **Beam arc (zero Luau per frame) [DOCUMENTED properties, recipe mine].** A Beam is a cubic Bézier. P1 sits `CurveSize0` studs from Attachment0 along its **+X** axis; P2 sits `CurveSize1` studs from Attachment1 along its **−X** axis (beams.md). For a circular arc of radius *r* and sweep θ, set both CurveSizes to **k = (4/3)·tan(θ/4)·r**: 90° gives 0.5523r, 120° gives 0.7698r, 180° gives 1.3333r (about 2% radius error). Use two beams for more than 180°. Point each attachment's X axis (`Attachment.Axis`) along the direction of travel at that end.
   - Texture: a slash strip with alpha falloff at the edges; `TextureMode = Stretch`, `TextureLength = 1`; `LightEmission = 1` (additive); `LightInfluence = 0`; `Segments` about 12–20 (each segment is 2 triangles, beams.md).
   - Width taper: `Width0` large, `Width1` small, or the reverse.
   - **Wipe-in:** a texture whose alpha ramps along U, scrubbed with `beam:SetTextureOffset(t)` each frame (one method call), or animated continuously with `TextureSpeed`.
   - Core plus glow is 2 beams on the same attachments; use `ZOffset` against z-fighting.
   - Cost: 1 draw call per beam, engine work only. vfx-forge measured 40 beams per bolt × 10 bolts at about +0.4 ms render CPU on desktop.
   - Which attachment axis sets the ribbon plane when `FaceCamera = false` is not stated in the docs. Check in Studio (Q19).
2. **Asset crescent MeshPart plus Decal UV animation (no EM) [API-DUMP for properties; UNVERIFIED as a slash look].** Decals project per face (`Decal.Face`), so a **flat** crescent lying in its local XZ plane with a Top-face Decal gets planar mapping. `Decal.UVOffset` and `UVScale` (new) slide or zoom the texture across the face. This scrolls in plane space, not along the arc, so use radial/sweep textures. VFX Forge's `forge_mesh.luau` animates `Decal.UVOffset`/`UVScale` with write-skipping (`UV_STEP = 1/1024`).
3. **EditableMesh crescent (full control) [DOCUMENTED API].**
   - About 32×2 vertices along the arc. Keep `uvIds` and `colorIds`.
   - **UV scroll:** each frame `uvs[i] = baseUV[i] + Vector2.new(t, 0)`, then `em:BatchSetValues(uvIds, uvs)`.
   - **Erode:** `alphas[i] = math.clamp((u_i - t) * sharp, 0, 1)`, then `em:BatchSetValues(colorIds, alphas)`. Erosion resolution equals the vertex columns, so use 32–64 columns.
   - `part.Transparency = 0.02`, Neon, `DoubleSided = true`.
   - Cost per frame: 2 batch calls plus one transcode of about 128 vertices, which is trivial. **Put all active slashes in one EM** so 10 slashes are 1 draw call. Pin the bounds (§1.12).
4. **Skinned crescent (grow and bend on GPU).** 6–8 bones along the arc. `Bone.Transform` per frame sweeps the arc open, bends it and adds lag. Pair with recipe 3's colour data, which is set once and never rewritten per frame (see the §0 warning about mixing).
5. **ForceField material crescent** for a built-in shimmer (§3.4).

### 3.2 Shockwave ring

**AAA.** A flat or slightly conical ring mesh scaled up over 0.2–0.5 s, UV-scrolling outward, alpha fading by age. Often 2–3 stacked rings plus a ground decal.

**Roblox recipes:**
1. **Rigid asset ring plus Size and CFrame tween.** Size is a tier-2 update [DOCUMENTED 2018]. That's fine for a few rings in the open world. Avoid it on character-attached or skinned parts (FastCluster rebuild, ~5 ms reported). Fade via `Transparency` nonzero to nonzero (tier 2); start at 0.02, not 0.
2. **Decal-zoom ring (no geometry change) [UNVERIFIED trick].** A thin disc Part or MeshPart at final size with a radial-ring texture as a Top Decal. Animate `Decal.UVScale` from large to 1 so the ring appears to expand. Keep it centred by adjusting `UVOffset` (offset = 0.5 − 0.5·scale under a scale-then-offset convention; **the docs don't state the operation order**, Q3). Fade with `Decal.Transparency`. Decal Color3 and Transparency don't break batching (2018).
3. **Skinned ring** (code in §1.5): 8–16 bones on 2 rings. Expansion and thickness are Transform translations. Cost is 16 writes per frame and no part Size change. One ring EM can be **multi-referenced** for simultaneous identical shockwaves (§1.9).
4. **EM ring with vertex-alpha fade:** one `BatchSetValues(colorIds, alphas)` per frame. Several rings in one EM give 1 draw call.

### 3.3 Tornado / vortex / cylinder

**AAA.** 2–3 nested cylinders or cones with twisted UVs, counter-scrolling, a vertex-colour alpha gradient top and bottom, and a sway deformation (vertex shader sine on height).

**Roblox:**
- Author the cylinders with **twisted UVs and baked vertex-alpha gradients** in the asset. Imported vertex colours render [COMMUNITY, MCR guest article].
- Spin each with **CFrame** every frame, the fast path [DOCUMENTED 2018]. Counter-rotating shells read as UV counter-scroll.
- **Sway:** a 4–6 bone vertical chain (asset-skinned or EM-skinned), `Bone.Transform = CFrame.Angles(...)` with a sine phase per bone. That's about 6 writes per frame, deformed on GPU. This is pivot-painter-lite.
- **Shimmer:** ForceField material (§3.4).
- **Avoid:** per-frame EM vertex rewrites for sway; it costs a whole-mesh transcode for what bones do almost free.

### 3.4 Dome / shield / force field with a fresnel rim (no custom shaders)

1. **ForceField material, the only built-in fresnel shader [DOCUMENTED + staff 2019].** vrtblox (297785) lists what the material does:
   - *"Fresnel (and optionally depth where its supported) driven transparency which makes the force field visible near edges"*
   - *"Vertex alpha driven outlines … 1 is no forced color and 0 is fully forced color"*
   - vertex RGB tint
   - *"Animation for mesh based parts with custom textures. The 'r' channel of texture is used to calculate visibility … over time (there's a sliding window …). The alpha channel controls how visible the texture pattern is."*

   Material docs: the mesh must have UVs covering much of 0–1, and a `TextureID` with a wide value range. Community (Zomebody, 3041374): the animation speed and window width (~10% visible at a time) **can't be controlled**; Texture instances don't work, so use the MeshPart's TextureID.

   **Recipe:** dome MeshPart, `Material = ForceField`, `TextureContent` = a red-channel gradient or noise (black to red), colour via `part.Color` or vertex colour, and per-vertex alpha 0 where you want a forced rim. Cost is one material draw with engine-side animation and **zero Luau**. Caveat: one report says other meshes sharing that texture and having any transparency pick up the ForceField look [COMMUNITY].
2. **Camera-facing rim disc (exact fake fresnel for spheres) [recipe mine; standard AAA billboard trick].** A sphere's silhouette is always a circle facing the camera. Place a flat disc MeshPart with a **ring-gradient texture** (bright edge, clear centre) at the shield centre and set `CFrame.lookAt(center, camPos)` every frame (fast path). Combine with a faint inner sphere. Cost: 1 draw call and 1 CFrame write per frame.
3. **Highlight outline:** `Highlight.FillTransparency = 1`, `OutlineTransparency = 0`. This gives a crisp silhouette rim. The first Highlight costs up to 1 ms GPU on mobile; the cap is 255; add or remove = geometry rebuild, so toggle `Enabled` [DOCUMENTED].
4. **CPU facing-ratio alpha:** an EM icosphere (642 vertices). When the camera moves, `alpha_i = (1 - |n_i · v_i|)^p`, then `BatchSetValues(colorIds, alphas)`. Cost is 642 dot products plus a transcode, only on camera moves. Use it when you need a non-spherical shape with a true rim.
5. **Baked rim texture** only works for one view direction; skip it except for HUD-like viewmodels.

### 3.5 Vertex animation textures (VAT) and substitutes

**AAA.** Bake a simulation (destruction, cloth, fluid) to textures; the vertex shader fetches the position per frame, so CPU cost is zero. **Roblox has no vertex texture fetch.** Substitutes, ranked:

1. **Bone-baked animation plus Animator: the real VAT substitute.** Bake the sim to a skinned mesh offline (Houdini or Blender; "skinning decomposition" via Dem Bones, which L3Norm cited). Import with the animation, or rebuild the skin at runtime with EM bone APIs. Play with `AnimationController` + `Animator` (client-side), or drive `Bone.Transform` from a keyframe table. Evaluation and skinning are engine-side; Luau per frame is zero (Animator) or one write per bone [DOCUMENTED binding; COMMUNITY costs].
2. **FACS poses as 50 engine-blended morph targets [DOCUMENTED API; UNVERIFIED on non-head parts].**
   - EM `SetFacsPose(actionUnit, boneIds, cframes)` stores up to about 50 base poses (plus 2- and 3-way correctives) on virtual bones.
   - A `FaceControls` child exposes 50 scriptable 0–1 float properties (write: None, NotReplicated). Changing them *"deforms the MeshPart's geometry"* [DOCUMENTED FaceControls.yaml].
   - L3Norm (3731147 #33) suggested exactly this non-facial use: *"if you're implementing car damage, raising the left eyebrow could map to damage on the back left bumper … you can combine up to 50 different poses per mesh."*
   - VFX: "expand", "twist", "flatten" and "flare" poses on a single shockwave or tornado mesh, blended by property writes. Test it (Q13).
3. **Keyframed EM positions (CPU VAT).** robloquake plays Quake vertex-frame models this way: per changed frame, a `SetPosition` loop (use `BatchSetValues(vertexIds, frames[k])`). It re-poses *"only when the time-resolved subframe actually changed"*. Store frames as `{vector}` arrays built at load. Blending two frames costs N lerps in Luau, with `--!native`. Cost: one transcode per changed frame. Fine for ≤ 2–5k vertices on a few objects.
4. **Flipbook of pre-baked meshes:** bake each keyframe once to DataModelContent at load, create one MeshPart per frame (pooled), and **swap by CFrame**. Park the hidden frames far away or inside the visible one; CFrame is the fast path and moving far away matches unparenting for draw calls (3127146 #?). Toggling Transparency 0↔1 also works but creates and destroys graphics objects (2018). Memory: K frames × the mesh. This is best for short, chunky 6–12-frame stylised effects.

### 3.6 Morph targets / shape keys

There is no native support. Staff call it *"a much bigger lift"* (3731147 #30). Use FACS poses (3.5.2), bones, or CPU blending with BatchSetValues. **Never** CPU-morph a skinned mesh that is also animating (§0.6).

### 3.7 Pivot painter

**AAA.** Per-element pivot and axis stored in UVs or textures; the shader rotates each leaf or chunk around its pivot.

**Roblox:** give **one bone per element** with rigid weight 1, bone CFrame at the element's pivot. `Bone.Transform` rotations swing each element independently, GPU-skinned. That's exactly pivot painter, at about 3.4× cheaper CPU than BulkMoveTo-ing separate parts (SkinnedGrass numbers) and one draw call. Watch the unknown per-mesh bone cap (Q4) and the extra draw calls with *"extreme amounts of bones"*.

### 3.8 Procedural ribbons and trails: Trail vs Beam vs EM

| | Trail | Beam chain | EM ribbon |
|---|---|---|---|
| Draw calls | 1 each | 1 per beam | **1 for all ribbons in the mesh** |
| Luau per frame | 0 | Attachment moves | Write the head segment (2 vertices) plus the alpha array |
| Shape control | Attachment pair over time; `Lifetime` 0.01–20 s, `MinLength`, `MaxLength`, `WidthScale` sequence | Bézier per segment | Anything |
| Risks | Per-frame update cap shared with Beams (§5); lifetime reported FPS-dependent (old) | Same cap | Whole-mesh transcode; manual fade |

**EM ribbon recipe:** a ring buffer of K cross-sections (2 vertices each), all ribbons of a weapon set in **one EM**. Per frame, write only the newest cross-section's positions: `BatchSetValues({v1, v2}, {p1, p2})`. Then write alphas for all K (age fade) in one call, or put the fade in the texture and rewrite UVs instead. Collapse dead cross-sections to the head position (degenerate triangles aren't rasterised). Pin the bounds. Transparency 0.02, Neon.

### 3.9 Tight particle meshes / mesh particles

- **Opaque mesh particles** (rocks, shards, sparks with geometry): pool MeshParts with the same MeshId and material and **no TextureID differences**, so they batch. Animate with `workspace:BulkMoveTo(parts, cframes, Enum.BulkMoveMode.FireCFrameChanged)`. Fade by **scaling** (Size, tier 2), never Transparency, which de-batches. Draw calls stay near one per cluster [DOCUMENTED rules].
- **Transparent sprite particles with custom motion:** one EM holding N quads (nightcycle-style pool), CPU-billboarded per frame. That's 1 draw call for N particles, against ParticleEmitter's 1 draw call per emitter. Use it when you need several emitter behaviours (boids, curl noise, attraction to bones) in one draw call. Cost: 4N vertex writes plus one transcode per frame. Keep N ≤ about 500 on phones [UNVERIFIED budget]. Otherwise use ParticleEmitter (`FlipbookLayout`, `FlipbookMode`, `Orientation`, `Squash`, `Shape*`).

### 3.10 Mesh decals

- **Planar Decal on parts:** new UV, emissive and PBR properties. An emissive mask plus `EmissiveStrength` gives glowing runes and impact marks that **pulse with one property write** [DOCUMENTED Decal.yaml].
- **Baked mesh decals:** `EditableImage:DrawImageProjected(mesh or WrapTextureTransfer, projection, brush)` projects a decal into an EM's **UV texture**, and `SampleImageProjected` is the inverse [DOCUMENTED]. Bake scorch marks once per hit into a pooled EditableImage. Respect the one-displayed-EditableImage-update-per-frame rule [DOCUMENTED].
- **Ground decals for VFX:** a flat MeshPart with a SurfaceAppearance (`AlphaMode = Transparency`, Transparency ≥ 0.02 for soft edges) or a Decal. Prefer one shared texture across all instances so they batch (unique DecalIds add draw calls).

### 3.11 Shells and fins (fur, force fields, energy layers)

**AAA.** N concentric offset copies, each alpha-tested against noise at increasing thresholds.

**Roblox:**
- (a) N MeshParts with the same MeshId at growing Size. Transparency breaks batching, so it's N draw calls; fine for N ≤ 8 on hero objects. Use a SurfaceAppearance noise texture with `AlphaMode = Transparency`.
- (b) **One EM with all shells baked** (normal offset per shell; shells × triangles ≤ 20,000), alpha per shell via vertex alpha. That's 1 draw call. Wind via bones.
- ForceField material on the outer shell gives the energy edge.
- Fins (silhouette quads) need per-frame CPU silhouette detection; skip them.

### 3.12 Impostors / octahedral impostors

- **There is no runtime 3D-to-image path on Roblox.** EditableImage has no render-from-camera API. Staff asked for use cases for "baking a ViewportFrame" but nothing shipped (4541898 #48/#55). `DrawImageProjected` projects textures onto meshes; it doesn't rasterise scenes.
- **Workable pipeline [COMMUNITY]:** nightcycle `imposter-baker`, a Rust CLI that rasterises an `.rbxm` offline into a pan × tilt sprite atlas with matching SurfaceAppearance maps. The runtime `imposter-render` package keeps **one EM of N quads** with one shared SurfaceAppearance (`AlphaMode = Transparency`, emissive). Per instance it picks the atlas cell by view direction (`Util.SelectShot`) and rewrites 4 UVs and 4 positions. The demo shows *"4,100 imposters sharing one mesh and five texture maps"*.
- **For VFX:** pre-rendered volumetric explosions and smoke are already handled by ParticleEmitter flipbooks. Use impostor quads for large distant set-piece effects (a far-off tornado or meteor) that would otherwise cost thousands of triangles.
- Octahedral 3-view blending would need two overlapping quads with an alpha cross-fade per instance. That's possible in one EM but costs 2× the quads.

### 3.13 LOD, decimation and mobile triangle budgets

- `MeshPart.RenderFidelity = Automatic` switches LOD at **<250 / 250–500 / ≥500 studs** [DOCUMENTED]. `Performance` forces lower detail.
- DataModelContent gets LODs [DOCUMENTED staff]. **Live EMs probably don't** [UNVERIFIED, Q14]. Hand-roll it: keep 2–3 density variants (DataModelContent bakes or fixed-size EMs) and **swap by CFrame** by distance.
- No decimation API: use `MergeVertices` for welding only.
- Budgets:
  - Docs example: 1,000 draws / 1M triangles for the baseline device.
  - Guest article: 500 draws / 500k triangles for the scene, 200 / 200k flexible.
  - **Suggested** VFX slice on phones: ≤ 60 draw calls and ≤ 60k triangles for all simultaneous effects. A single hero effect gets ≤ 8 draw calls and ≤ 6k triangles at the top intensity rung, and drops by rung first [UNVERIFIED, my numbers; measure with Shift+F2 "Draw (scene)"].

### 3.14 Destruction (bake once)

- `GeometryService:GenerateFragmentSites(part, ...)` plus `GeometryService:FragmentAsync(part, sites)` (3D Voronoi). This is **live in published games since 2026-07-07** and works on watertight MeshParts. `SweepPartAsync` handles smooth cuts [DOCUMENTED staff, 4515374].
- Results are not saved across sessions [DOCUMENTED].
- **Recipe:** fracture each breakable prop type **once at load** (or in Studio with a plugin, then weld). Pool the shards. On break, unanchor and `BulkMoveTo`. Fade by scale. Shards from one source share material, so they batch well when opaque.

### 3.15 Cage deformation (WrapDeformer)

- `WrapDeformer:SetCageMeshContent(Content.fromObject(cageEm), cageOrigin?)` deforms a high-resolution MeshPart from a low-resolution cage EM [DOCUMENTED].
- The algorithm cost *"grows super-linearly with the number of vertices"* and it is designed to run once or on change (announcement 3294953, via search summary) [DOCUMENTED-ish].
- **Not a per-frame lever.** Use it to **bake variants**: deform, then `WrapDeformer:CreateEditableMeshAsync()` (returns a fixed-size EM), then DataModelContent. For example, 6 bent versions of a slash mesh for a flipbook.

---

## 4. Bake-once strategies

1. **Generate at load, bake, pool.**
   - Build each procedural VFX mesh once with `BatchAdd`, then `CreateDataModelContentAsync`, then destroy the EM.
   - Then `CreateMeshPartAsync(content, {CollisionFidelity = Box})` × pool size. Every pooled part references the **same Content**: one geometry, expected to instance (Q1).
   - Server-baked content replicates to all clients [DOCUMENTED], so you can bake on the server once per session and clients pay no generation cost.
   - The mesh/image caps no longer apply after baking; only the server storage budget does.
2. **Keyframe a deformation into N preset meshes and swap.**
   - Swap by CFrame (fast path), not by editing vertices (a whole transcode per frame) and not by ApplyMesh (re-cook).
   - Memory is N × the mesh, but per-frame cost is about one CFrame write.
   - Best for ≤ 12-frame stylised bursts and anything that must run on many simultaneous instances.
3. **Rigid MeshPart transforms are nearly free; vertex edits are not.**
   - `CFrame` is the fast path. `BulkMoveTo` many at once.
   - `Size` is tier 2 and rebuilds FastClusters near characters.
   - **Transparency** per frame on many parts is expensive. vfx-forge: 80 part Transparency changes per bolt per frame × 10 bolts = **7.5 ms render CPU** (114 fps from 360). The same fade via one vertex-alpha `BatchSetValues` per mesh bolt cost about 0.1 ms render CPU per bolt.
   - SpecialMesh.Scale is about 10× slower than a basic part update (2018).
4. **Write-skipping.**
   - Quantise animated values and write only when they change past a step. VFX Forge uses `UV_STEP = 1/1024` and `SIZE_STEP`; robloquake writes only on subframe change; vfx-forge's held bolt *"only compares the state it drew"*.
   - Each skipped write saves a property change or a whole-mesh transcode.
5. **Partition by update rate.** The transcode is whole-mesh, so split static, rarely-changing and every-frame geometry into **separate** EMs and parts. Keep the per-frame mesh small (hundreds of vertices).
6. **Fixed-size clone for dynamic EMs** (§1.2). Build dynamic, clone fixed, destroy the dynamic one. Then the budget allows dozens of EMs, not 8.
7. **Bake once per player, not once per cast.** For player-tinted effects, bake the variant on first use and cache the Content keyed by tint, instead of rewriting vertex colours every cast.

---

## 5. Beam and Trail as cheap geometry

### Facts [DOCUMENTED unless marked]

- **Beam:**
  - A cubic Bézier between Attachment0 and Attachment1. `CurveSize0` runs along Attachment0's **+X**; `CurveSize1` runs along Attachment1's **−X** (beams.md).
  - `Segments` (default 10): straight segments, *"two triangles drawn between Segments"*. Colour and Transparency sequences need at least n − 1 segments to show n keypoints.
  - `Width0`/`Width1`: linear taper.
  - `TextureSpeed`: cycles per second; negative reverses; 0 is static.
  - `SetTextureOffset(0..1)`: sets the cycle phase; the cycle wraps.
  - `TextureMode` Wrap/Static/Stretch with `TextureLength`.
  - `FaceCamera`: always faces the camera.
  - `LightEmission`: 0 normal to 1 additive.
  - `LightInfluence`: 0 ignores scene light.
  - `Brightness`: 0–10000 when `LightInfluence < 1`.
  - `ZOffset`: camera-relative offset against z-fighting.
  - `LocalTransparencyModifier`.
- **Trail:**
  - `Lifetime` 0.01–20 s. Changing it retroactively kills older segments.
  - `MinLength`: no new segment until the attachments move this far.
  - `MaxLength` (0 = unlimited): oldest segments are erased past it.
  - `WidthScale` NumberSequence (0–1 × attachment distance).
  - `FaceCamera`: changing it affects existing segments.
  - `Clear()`: clear and also disable for a clean reset.
- **Quality scaling:** *"beams keep their segment count at all quality levels"* (design.md, 2026). Older community reports (2018–2023, 82214, 2426888) say quality and distance multiply segment counts down. A community script reverse-scales `Segments` by `(1 - (dist - 200)/800) * quality/10`. **The docs are newer; verify (Q11).**
- **Draw calls:** each Beam costs 1 draw call [COMMUNITY, Roblox-published guest article]. vfx-forge measured on desktop: 10 bolts × 40 beams added about 0.36 ms render CPU, and rewriting each beam's Transparency NumberSequence every frame added about 0.034 ms Lua and 0.067 ms render CPU per 40 beams.
- **Per-frame update cap [COMMUNITY, 2019, unverified]:** *"There is a hard cap on how many Beams and Trails (combined) can be updated per renderstep, and updating too many can cause some to disappear. IIRC it was 64 on desktop and 16 on mobile"* (EmilyBendsSpace, 254668 #8). Tracers flickered past about 40 at once. **This decides whether beams or trails are safe for bullet-hell or ability spam on phones. Measure it (Q10).**

### Recipes

- **Arc / slash / whip:** the §3.1 Beam arc with k = (4/3)·tan(θ/4)·r. Wipe with `SetTextureOffset`; core and glow beams; LightEmission 1.
- **Lightning:** chains of 1-segment beams between jittered attachments (vfx-forge "Segments" style), or one EM tube (vfx-forge "Tube/Rim": 228–500 vertices per bolt). The mesh bolt fades with one BatchSetValues; part-based segments fade expensively (§4.3).
- **Scrolling energy pipe or laser:** 1 beam, `TextureSpeed` 2–4, Wrap mode, `FaceCamera = true`. Zero Luau.
- **Ground cracks or decal lines:** beams with `FaceCamera = false`, attachments oriented flat.
- **Swing trails:** Trail with `Lifetime` 0.15–0.3, `MinLength` about 0.1, `WidthScale` from 1 to 0, `LightEmission` 1. For more than about 10 simultaneous swingers on phones, switch to one EM ribbon (§3.8) to dodge the update cap and the draw-call count.

---

## 6. Open-source projects and measured numbers

| Project | What it does with geometry | Numbers / lessons | Tag |
|---|---|---|---|
| `vfx-forge/module` (VFX Forge plugin's emit module), `docs/lightning-measured.md`, `src/mod/lightning/mesh.luau` | Lightning as EM tubes (core 5 sides, rim 6 sides; 500 vertices / 968 triangles per default bolt), `BatchAdd` build, per-frame `BatchSetValues` for positions (Flow) and alphas (Fade); Neon; Transparency 0.02; `CFrame.identity` with world-space vertices | Box 0.22 ms vs Default 21.7 ms CreateMeshPartAsync; 1 held bolt +0.03 ms render CPU, 10 bolts +0.1 ms; Flow (all vertices every frame) about 0.05 ms Lua + 0.17 ms render CPU per bolt; part-segment fade 10 bolts = 7.5 ms render CPU; setup about 1 ms per bolt (10 bolts in one emit ≈ 10 ms in one frame, so stagger spawns) | COMMUNITY, measured in Studio at 360 fps, 2026-10-24 |
| `nightcycle/imposter-baker` | Offline Rust impostor baker plus a runtime single-EM quad pool with a shared SurfaceAppearance atlas | 4,100 impostors on one mesh; bounds pinned with degenerate triangles; budgets EditableImage pixels explicitly | COMMUNITY |
| `turtlesoupy/robloquake` | Quake MDL vertex-frame animation on fixed-size EM clones; ViewportFrame viewmodel | Fixed-size clone to escape the 60k reservation; re-pose only on subframe change; falls back to parts when the budget is exhausted | COMMUNITY |
| `MrChickenRocket/sdf-procedural-toolkit` | SDF to mesh, bake paths, skinning pipeline | Bone rules (≤4, no zeros, equal lengths, sum to 1); single-step bake for skinned; Bone instances by exact name and bind CFrame; Transform not CFrame | COMMUNITY (expert) |
| SkinnedGrass (DevForum 3364812, Creator Store) | Grass via bone transforms | 2000 bones 0.99 ms vs BulkMoveTo 2000 parts 3.43 ms; reparent 0.5 ms vs 18.5 ms | COMMUNITY |
| chkfla2 grass (4779401 #7/#18) | One EM grass patch multi-referenced | 10k blades 65 to 110 fps with batching; 640k blades about 105 fps via shared EM | COMMUNITY |
| DevVexus FFT ocean (4779401 #39/#85) | Ocean EM | 140 to 280 fps from batching alone; transcode cost flat in changed-vertex count | COMMUNITY |
| Dev_Harp (4779401 #57/#59) | 1,000 low-poly NPCs in 8 EMs (106 triangles each) | 80 to 120 fps from flat buffers, LUTs, `--!native` | COMMUNITY |
| Other EM-VFX code found by code search | `chaitnaya0711/roblox-blackhole` (photon ring, star field, disk via BatchSetValues colours); `andypeng1/The-Reactor-Game-Continuation/_tools/shock_ripple_client.luau` (single-EM shock disc, raised-cosine envelope); `aidan-epperly/citrate` (cloth, drum demos); `plirt/Softbody-physics`; `KashTheKing/library` (Ocean/Spectral/Clipmap); `EgoMoose/rbx-csg-to-mesh-plugin` (StaticContent.luau, the DataModelContent path) | No published timings | COMMUNITY |

`gh api search/code` works through the session proxy (68 hits for `EditableMesh SetPosition language:Luau`; 16 for `BatchSetValues language:Luau`). Many "VFX skill" markdown hits are AI-written knowledge dumps; I ignored them.

---

## 7. Top 12 mesh-VFX levers, ranked by impact over cost

1. **Merge transparent VFX pieces into one EditableMesh per effect family.**
   - Why: N transparent MeshParts are N draw calls (2018 zeuxcg, 2024 guest article). One EM is 1 draw call and 1 sort.
   - How: vertex alpha with part `Transparency = 0.02`; pool quads or strips in one mesh, collapse unused ones to degenerate triangles, pin the bounds.
   - Cost: one BatchSetValues and one small transcode per frame.
   - Impact: on a phone, often the difference between 40 and 4 draw calls for an ability.
2. **Deform with bones, not vertices.**
   - How: skinned asset or EM-skinned mesh, Bone instances named to match, animate `Bone.Transform` or play an Animator clip.
   - Why: engine/GPU skinning, a few writes per frame, no transcode. About 3.4× cheaper than BulkMoveTo-ing parts. Never mix with vertex writes on the same mesh.
3. **CollisionFidelity Box on every CreateMeshPartAsync, plus pooling.** 0.22 ms vs 21.7 ms measured. Create at load; never create mid-fight.
4. **Bake static or procedural VFX geometry once to DataModelContent.**
   - Benefits: no editable budget; server-to-client replication; LODs and streaming.
   - Reuse one Content across every pooled MeshPart (expected to instance, Q1).
   - Bake cost about 100 ms, so only at load.
5. **Beams for arcs, slashes, lasers and lightning segments.**
   - Zero Luau, with engine scroll via `TextureSpeed` and `SetTextureOffset`.
   - Circular arc via CurveSize = (4/3)·tan(θ/4)·r.
   - Keep simultaneous beams and trails under the (to-be-measured) mobile update cap.
6. **The CFrame fast path for rigid motion; avoid per-frame Transparency or Size on many parts.**
   - BulkMoveTo for debris and spinning shells.
   - Fade by scaling or vertex alpha; part Transparency fades scale badly (7.5 ms for 10 part-bolts).
7. **Fixed-size clones for every dynamic EM.** Each blank EM bills 20k triangles (about 8 per client); a fixed clone bills its real size, so dozens fit.
8. **Batch, write-skip and partition by update rate.**
   - One `BatchSetValues` per attribute per frame (10–30× less call overhead).
   - Quantise and skip unchanged writes.
   - Split meshes so only small ones re-transcode, since the transcode is whole-mesh.
9. **ForceField material for shields, auras and tornado shells.** Engine fresnel, depth fade, vertex-alpha outlines and red-channel animation, with zero Luau. Use it for every "energy surface" before writing CPU fresnel.
10. **Multi-reference one deforming EM across many MeshParts.** One Luau update and one transcode animates every identical copy (grass-patch evidence). Use it for N simultaneous identical shockwaves, flame tongues or water rings.
11. **Decal and SurfaceAppearance property animation** (`Decal.UVOffset/UVScale/Rotation`, `Decal/SurfaceAppearance.EmissiveStrength/EmissiveTint`, `SurfaceAppearance.Color`). Scrolling, zooming and pulsing surfaces with **no EditableMesh, budget or transcode**. Also try the camera-facing rim disc as fake fresnel for spherical shields.
12. **FACS poses as up to 50 engine-blended morph targets on one EM**, driven by FaceControls float properties. "Expand", "twist" and "flare" shapes blended by property writes. Needs a Studio check on non-head parts (Q13). If it works, it replaces CPU morphing outright.

Honourable mentions: pre-fracture with `FragmentAsync` at load; impostor quads for distant set-piece effects; a Humanoid inside Models with moving skinned VFX (FastCluster); Highlight outline for silhouette rims (first one ≈ 1 ms GPU on mobile).

---

## 8. Open questions only a Studio test can answer (each with the exact test)

Measure render cost with `Stats.RenderCPUFrameTime` / `Stats.RenderGPUFrameTime` averaged over `RenderStepped` for 2 s. Count draw calls with Shift+F2 → Render → "Draw (scene)". Read batching from the Ctrl+Shift+F2 clusters line `inst Nc Ne Ni` (entities ≈ draw calls). Use the MicroProfiler for named tags. Run on PC **and** a real phone at graphics quality 1, 5 and 10.

**Q1. Do MeshParts sharing one EditableMesh instance?**
- Setup: build a 200-triangle EM. Make 200 MeshParts with `CreateMeshPartAsync(Content.fromObject(em), {CollisionFidelity = Box})`, all SmoothPlastic, white, opaque, within one 128-stud chunk.
- Compare against (b) 200 parts from one DataModelContent bake, (c) 200 clones of an uploaded asset MeshPart, and (d) 200 *separate* EMs.
- Record "Draw (scene)" and the `inst` line. If (a) ≈ (c), multi-reference instancing works.
- Repeat while deforming the shared EM every frame.

**Q2. Is every transparent MeshPart still its own draw call in 2026?**
- Setup: 200 same-MeshId MeshParts at Transparency 0, then 0.02, then 0.5, then Neon at 0.5.
- Record draw calls. Then the same 200 quads merged into one EM at Transparency 0.02.

**Q3. Decal UV animation cost and convention.**
- Convention: one Top Decal with a checker texture; set `UVScale = (2, 2)` and `UVOffset = (0.25, 0)`; screenshot to learn whether scale or offset applies first and the pivot.
- Cost: 500 decals on 500 parts, per frame write `UVOffset` vs `Color3` vs `Transparency`. Compare render CPU and check for `updateInvalidatedFastClusters` spikes.

**Q4. Skinning cost model and bone cap.**
- Cap: EM `AddBone` in a loop until it errors; log the count.
- Cost: a 10k-triangle EM ring skinned to 8, 64 and 255 bones. Animate all Transforms per frame and read `updateSkinningIslands`, `performUpdateCoordinateFrame`, render CPU and GPU, and draw calls (bone-palette splits).
- Repeat with the bones idle (Transform constant) to see whether idle bones still cost (the 2020 claim).

**Q5. Can Bone.Transform scale?**
- Set `bone.Transform = CFrame.new(0, 0, 0, 2, 0, 0, 0, 2, 0, 0, 0, 2)` on a skinned quad. Does it scale, get orthonormalised, or error? If it scales, skinned shockwaves need no radial bone ring.

**Q6. Transcode cost against size.**
- EMs of 1k, 5k, 20k and 60k vertices (fixed-size clones).
- Per frame, `BatchSetValues` on 1 vertex vs all vertices vs only UVs vs only alphas.
- Read `transcodeVerticesAndCalculateBounds` ms on PC and phone. This gives the per-vertex transcode slope for budgeting.

**Q7. Is a FixedSize mesh faster to update?**
- Same as Q6, with a non-fixed EM vs its fixed clone, same data.

**Q8. Culling after vertices leave the creation bounds.**
- Create an EM with a 1-stud quad and its MeshPart, then move the quad's vertices 60 studs away.
- Orbit the camera so the original 1-stud bounds leave the frustum while the moved quad stays in view. Does it pop?
- Repeat with degenerate pin triangles at ±80 studs added before `CreateMeshPartAsync`.

**Q9. CreateMeshPartAsync cost today.**
- 300-, 3k- and 20k-triangle EMs × Box, Default, PreciseConvexDecomposition.
- Time `os.clock()` around the call **and** watch frame time for main-thread stalls (the ~20 ms lockup staff were fixing).
- Also time `CreateDataModelContentAsync` for each size.

**Q10. Beam/Trail per-frame update cap.**
- Spawn 8, 16, 32, 64 and 128 beams whose attachments move every frame (and 128 static beams with `TextureSpeed` 1), plus the same counts of moving Trails.
- On a phone at quality 1/5/10 and on PC, count visible beams (screenshot plus script tally). Find where they start disappearing, and whether static `TextureSpeed` beams count against the cap.

**Q11. Beam segment LOD in 2026.**
- A 3-segment curved beam and a 20-segment beam, at quality 1, 5 and 10, at 50, 300 and 900 studs. Screenshot and compare with the docs' "keep their segment count at all quality levels".

**Q12. Vertex-alpha threshold.**
- An EM quad with a vertex-alpha gradient; sweep part Transparency over 0, 0.005, 0.01, 0.011, 0.015, 0.02 and 0.05.
- Note the first value that shows the gradient, on PC and phone, for SmoothPlastic and for Neon.

**Q13. FACS morph targets on a non-head EM.**
- An EM plane grid with 2 virtual bones (`AddBone{Virtual = true}`).
- `SetFacsPose(Enum.FacsActionUnit.JawDrop, {boneId}, {CFrame.new(0, 2, 0)})`, then `CreateMeshPartAsync`, then parent a `FaceControls` to the part, then set `FaceControls.JawDrop = 1`.
- Does the grid deform? Measure the cost of writing all 50 properties per frame.

**Q14. LOD on EM-backed and DataModelContent meshes.**
- A 20k-triangle sphere as (a) a live EM part and (b) a DataModelContent part, `RenderFidelity = Automatic`.
- Record "Draw (scene)" triangle counts at 100, 300 and 600 studs.

**Q15. Do bones survive the DataModelContent bake?**
- A skinned EM baked two-step vs single-step. Check `MeshPart.HasSkinnedMesh` and whether Bone.Transform deforms each.

**Q16. Auto normals vs explicit normals.**
- A 10k-vertex EM animated every frame: (a) all auto normals, (b) every face corner pointing at one fixed explicit normal ID.
- Compare transcode ms.

**Q17. Metal flicker.**
- On an Apple Silicon Mac at quality ≥ 5, run a 2k-vertex wave with a `SetPosition` loop vs a single `BatchSetValues`. Count black flashes in a 30 s screen recording.

**Q18. Animator on an EM-skinned part.**
- Build an EM-skinned mesh with Bone instances named for an uploaded animation's bones. Add an AnimationController + Animator; play a clip locally.
- Does it animate, and what is `stepAnimation` cost against hand-written Transform writes?

**Q19. Beam ribbon plane.**
- One beam with `FaceCamera = false` between two attachments. Rotate each attachment 90° about X, then Y, then Z; record which axis sets the ribbon's width direction. That pins down the slash-plane recipe in §3.1.
