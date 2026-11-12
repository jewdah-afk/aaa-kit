--!strict
-- EditableMeshAdapter: the ONLY Roblox-facing file in lib/celestialrithm/geometry. Client-side.
-- Pushes VoxelModel chunk meshes into EditableMeshes shown by MeshParts, rebuilds dirty chunks in place, writes
-- jiggle positions, spawns debris Parts, and falls back to Parts when EditableMesh is unavailable.
--
-- ============================================ ALL OF THIS IS UNVERIFIED IN STUDIO ===================================
-- Compile-checked headless only. API names and limits are from docs/research/21 (EditableMesh.yaml / AssetService.yaml,
-- read 2026-09-17) and docs/research/20 (EditableImage). Specific assumptions, each to be confirmed by the Studio
-- test plan in docs/celestialrithm/frontier/editablemesh-voxel.md:
--   [UNVERIFIED] BatchAdd(Enum.MeshAttribute.Face, {{v0, v1, v2}, ...}) data shape and whether it creates default
--                per-corner attributes (we rebind every corner with BatchSetFaceAttributes, then RemoveUnused()).
--                The same pattern is used by lib/frontier/mesh/HeightfieldMesh.luau (also unverified).
--                `perElement = true` uses only AddVertex / AddTriangle / AddUV / AddColor / AddNormal + SetFace*.
--   [UNVERIFIED] MeshPart textures repeat when UVs leave [0, 1] (the stud grid relies on it).
--   [UNVERIFIED] vertex colours multiply TextureContent (doc 21 lists this as a documented-nowhere gap).
--   [UNVERIFIED] AddColor alpha 1 = opaque; UV V origin (we pass 1 - v; studs are symmetric so it barely matters).
--   [UNVERIFIED] CreateMeshPartAsync re-centres geometry: we place the part at cframe * (em:GetCenter()).
--   [UNVERIFIED] after Clear() + re-adding faces on the same EditableMesh the MeshPart shows the new geometry with no
--                CreateMeshPartAsync (doc: "visual changes ... immediately reflected"), but MeshSize/bounds stay stale
--                until ApplyMesh, so `settle()` re-bakes once a burst of edits has stopped.
--   [UNVERIFIED] Highlight outline on a Model of MeshParts; Highlights have a reported concurrent-instance limit.
--   [UNVERIFIED] SurfaceType.Studs still renders studs on Plastic Parts (Part fallback / debris look).
-- Documented facts relied on: 20,000 triangles / 60,000 vertices per EditableMesh (errors past them);
-- CreateEditableMesh returns nil when the client editable memory budget is exhausted; Content.fromObject does not
-- replicate (so build on each client from the shared seed); Clear() only on non-FixedSize meshes (blank meshes are).
-- =====================================================================================================================

local GreedyMesher = require("./GreedyMesher")
local VoxelModel = require("./VoxelModel")
local StudTexture = require("./StudTexture")
local Jiggle = require("./Jiggle")

local Adapter = {}

local MAX_TRIS, MAX_VERTS = 20000, 60000

export type PartView = {
	em: any, -- EditableMesh (nil in Part fallback)
	part: any, -- MeshPart or Model of Parts
	vids: { number }, -- vertex IDs in mesh vertex order (for jiggle pushes)
	vals: { Vector3 }, -- reused scratch for BatchSetValues
	binding: Jiggle.Binding?,
}

export type ChunkView = { version: number, parts: { PartView } }

export type View = {
	model: VoxelModel.Model,
	root: any, -- Model instance
	cframe: CFrame,
	mode: string, -- "mesh" | "parts"
	chunks: { [number]: ChunkView },
	texture: any, -- EditableImage or nil
	studsPerTile: number,
	perElement: boolean,
	settlePending: boolean,
	collision: boolean,
}

export type ViewOptions = {
	parent: any,
	cframe: CFrame?,
	name: string?,
	texture: boolean?, -- procedural stud tile on every MeshPart (default true)
	studsPerTile: number?, -- default 4
	outline: boolean?, -- black Highlight outline (default true)
	perElement: boolean?, -- use only per-element add calls (default false: batched)
	collision: boolean?, -- bake collision on settle (default false: use simple Part hitboxes instead)
	forceParts: boolean?, -- test the fallback
}

local function rgbOf(rgba: number): Color3
	return Color3.fromRGB(bit32.band(rgba, 255), bit32.band(bit32.rshift(rgba, 8), 255), bit32.band(bit32.rshift(rgba, 16), 255))
end

-- Fills an empty EditableMesh from one GreedyMesher mesh. Each quad shares one normal ID and one colour ID across
-- its two triangles (flat-shaded, per-quad colour). Returns vertex IDs in mesh order.
function Adapter.fillEditableMesh(em: any, m: GreedyMesher.Mesh, studsPerTile: number, perElement: boolean): { number }
	assert(m.tcount <= MAX_TRIS and m.vcount <= MAX_VERTS, "EditableMeshAdapter: mesh over the EditableMesh caps; split it first")
	local vc, qc = m.vcount, m.quads
	local inv = 1 / studsPerTile
	if perElement then
		local vids = table.create(vc)
		for q = 0, qc - 1 do
			local vb = q * 4
			local o = vb * 12
			local n = em:AddNormal(Vector3.new(buffer.readf32(m.nrm, o), buffer.readf32(m.nrm, o + 4), buffer.readf32(m.nrm, o + 8)))
			local c = em:AddColor(rgbOf(buffer.readu32(m.col, vb * 4)), 1)
			local v, u = table.create(4), table.create(4)
			for k = 0, 3 do
				local vi = vb + k
				v[k + 1] = em:AddVertex(Vector3.new(buffer.readf32(m.pos, vi * 12), buffer.readf32(m.pos, vi * 12 + 4), buffer.readf32(m.pos, vi * 12 + 8)))
				u[k + 1] = em:AddUV(Vector2.new(buffer.readf32(m.uv, vi * 8) * inv, 1 - buffer.readf32(m.uv, vi * 8 + 4) * inv))
				vids[vi + 1] = v[k + 1]
			end
			for _, tri in { { 1, 2, 3 }, { 1, 3, 4 } } do
				local f = em:AddTriangle(v[tri[1]], v[tri[2]], v[tri[3]])
				em:SetFaceNormals(f, { n, n, n })
				em:SetFaceColors(f, { c, c, c })
				em:SetFaceUVs(f, { u[tri[1]], u[tri[2]], u[tri[3]] })
			end
		end
		em:RemoveUnused()
		return vids
	end
	local P, U = table.create(vc), table.create(vc)
	local N, C, A = table.create(qc), table.create(qc), table.create(qc, 1)
	for v = 0, vc - 1 do
		P[v + 1] = Vector3.new(buffer.readf32(m.pos, v * 12), buffer.readf32(m.pos, v * 12 + 4), buffer.readf32(m.pos, v * 12 + 8))
		U[v + 1] = Vector2.new(buffer.readf32(m.uv, v * 8) * inv, 1 - buffer.readf32(m.uv, v * 8 + 4) * inv)
	end
	for q = 0, qc - 1 do
		local o = q * 48
		N[q + 1] = Vector3.new(buffer.readf32(m.nrm, o), buffer.readf32(m.nrm, o + 4), buffer.readf32(m.nrm, o + 8))
		C[q + 1] = rgbOf(buffer.readu32(m.col, q * 16))
	end
	local vids = em:BatchAdd(Enum.MeshAttribute.Vertex, P)
	local uids = em:BatchAdd(Enum.MeshAttribute.UV, U)
	local nids = em:BatchAdd(Enum.MeshAttribute.Normal, N)
	local cids = em:BatchAdd(Enum.MeshAttribute.Color, C, A)
	local tc = m.tcount
	local F, FN, FU, FC = table.create(tc), table.create(tc), table.create(tc), table.create(tc)
	for t = 0, tc - 1 do
		local a = buffer.readu32(m.idx, t * 12) + 1
		local b = buffer.readu32(m.idx, t * 12 + 4) + 1
		local c = buffer.readu32(m.idx, t * 12 + 8) + 1
		local q = t // 2 + 1
		F[t + 1] = { vids[a], vids[b], vids[c] }
		FN[t + 1] = { nids[q], nids[q], nids[q] }
		FC[t + 1] = { cids[q], cids[q], cids[q] }
		FU[t + 1] = { uids[a], uids[b], uids[c] }
	end
	local fids = em:BatchAdd(Enum.MeshAttribute.Face, F)
	em:BatchSetFaceAttributes(fids, FN)
	em:BatchSetFaceAttributes(fids, FU)
	em:BatchSetFaceAttributes(fids, FC)
	em:RemoveUnused()
	return vids
end

local function makeTexture(studsPerTile: number): any
	local AssetService = game:GetService("AssetService")
	local tile = StudTexture.generate(32, studsPerTile)
	local ok, img = pcall(function()
		return AssetService:CreateEditableImage({ Size = Vector2.new(tile.w, tile.h) })
	end)
	if not ok or img == nil then
		return nil -- budget exhausted: meshes still render with vertex colours only
	end
	img:WritePixelsBuffer(Vector2.zero, Vector2.new(tile.w, tile.h), tile.pixels)
	return img
end

local function newMeshPart(view: View, em: any): any?
	local AssetService = game:GetService("AssetService")
	local ok, part = pcall(function()
		return AssetService:CreateMeshPartAsync(Content.fromObject(em), {
			CollisionFidelity = Enum.CollisionFidelity.Box,
			RenderFidelity = Enum.RenderFidelity.Precise,
		})
	end)
	if not ok or part == nil then
		return nil
	end
	part.Anchored = true
	part.CanCollide = view.collision
	part.CanQuery = false
	part.CanTouch = false
	part.CFrame = view.cframe * CFrame.new(em:GetCenter())
	if view.texture then
		part.TextureContent = Content.fromObject(view.texture)
	end
	part.Parent = view.root
	return part
end

local function destroyChunk(cv: ChunkView)
	for _, pv in cv.parts do
		if pv.part then
			pv.part:Destroy()
		end
		if pv.em then
			pv.em:Destroy()
		end
	end
	table.clear(cv.parts)
end

-- Part fallback: one Part per 3D greedy box of the chunk. Slower to build and heavier per instance, but it works
-- without EditableMesh (no verification gate, no editable memory budget).
local function buildChunkParts(view: View, chunkIndex: number): ChunkView
	local model = view.model
	local c = model.chunks[chunkIndex]
	local g = model.grid
	local folder = Instance.new("Model")
	folder.Name = `Chunk{chunkIndex}`
	local vs = model.meshOpts.voxelSize :: number
	local boxes = GreedyMesher.boxes(g, { x0 = c.x0, y0 = c.y0, z0 = c.z0, x1 = c.x1, y1 = c.y1, z1 = c.z1 })
	for i = 1, #boxes, 7 do
		local x, y, z, w, h, d, col = boxes[i], boxes[i + 1], boxes[i + 2], boxes[i + 3], boxes[i + 4], boxes[i + 5], boxes[i + 6]
		local px, py, pz = VoxelModel.toStuds(model, x + w / 2, y + h / 2, z + d / 2)
		local p = Instance.new("Part")
		p.Anchored = true
		p.CanCollide = false
		p.CanQuery = false
		p.CanTouch = false
		p.Size = Vector3.new(w * vs, h * vs, d * vs)
		p.CFrame = view.cframe * CFrame.new(px, py, pz)
		local rgb = g.palette.colors[col]
		p.Color = Color3.fromRGB(bit32.rshift(rgb, 16), bit32.band(bit32.rshift(rgb, 8), 255), bit32.band(rgb, 255))
		if g.palette.flat[col] then
			p.Material = Enum.Material.SmoothPlastic
		else
			p.Material = Enum.Material.Plastic
			p.TopSurface = Enum.SurfaceType.Studs
		end
		p.Parent = folder
	end
	folder.Parent = view.root
	return { version = c.version, parts = { { em = nil, part = folder, vids = {}, vals = {}, binding = nil } } }
end

local function buildChunk(view: View, chunkIndex: number): ChunkView
	local c = view.model.chunks[chunkIndex]
	if view.mode == "parts" then
		return buildChunkParts(view, chunkIndex)
	end
	local AssetService = game:GetService("AssetService")
	local cv: ChunkView = { version = c.version, parts = {} }
	for _, m in c.parts do
		if m.tcount == 0 then
			continue
		end
		local em = AssetService:CreateEditableMesh()
		if em == nil then
			-- editable memory budget exhausted: this chunk (and later ones) fall back to Parts
			destroyChunk(cv)
			view.mode = "parts"
			return buildChunkParts(view, chunkIndex)
		end
		local vids = Adapter.fillEditableMesh(em, m, view.studsPerTile, view.perElement)
		local part = newMeshPart(view, em)
		if part == nil then
			em:Destroy()
			destroyChunk(cv)
			view.mode = "parts"
			return buildChunkParts(view, chunkIndex)
		end
		table.insert(cv.parts, { em = em, part = part, vids = vids, vals = table.create(#vids), binding = nil })
	end
	return cv
end

function Adapter.available(): boolean
	local ok, AssetService = pcall(game.GetService, game, "AssetService")
	return ok and AssetService ~= nil and typeof((AssetService :: any).CreateEditableMesh) == "function"
end

-- Builds every non-empty chunk. Call VoxelModel.remeshAll / remeshDirty first.
function Adapter.new(model: VoxelModel.Model, opts: ViewOptions): View
	local root = Instance.new("Model")
	root.Name = opts.name or "VoxelModel"
	local view: View = {
		model = model,
		root = root,
		cframe = opts.cframe or CFrame.identity,
		mode = if opts.forceParts or not Adapter.available() then "parts" else "mesh",
		chunks = {},
		texture = nil,
		studsPerTile = opts.studsPerTile or 4,
		perElement = opts.perElement == true,
		settlePending = false,
		collision = opts.collision == true,
	}
	if view.mode == "mesh" and opts.texture ~= false then
		view.texture = makeTexture(view.studsPerTile)
	end
	for _, c in model.chunks do
		if c.mesh.tcount > 0 then
			view.chunks[c.index] = buildChunk(view, c.index)
		end
	end
	if opts.outline ~= false then
		local hl = Instance.new("Highlight")
		hl.FillTransparency = 1
		hl.OutlineColor = Color3.new(0, 0, 0)
		hl.OutlineTransparency = 0
		hl.DepthMode = Enum.HighlightDepthMode.Occluded
		hl.Adornee = root
		hl.Parent = root
	end
	root.Parent = opts.parent
	return view
end

-- Re-bakes MeshSize / bounds (and collision if enabled) once edits stop. One CreateMeshPartAsync per part
-- (~22 ms + 0.27 ms/1k tris reported [secondary]), so it is deferred and never per frame.
function Adapter.settle(view: View)
	if view.settlePending or view.mode ~= "mesh" then
		return
	end
	view.settlePending = true
	task.delay(0.25, function()
		view.settlePending = false
		local AssetService = game:GetService("AssetService")
		for _, cv in view.chunks do
			for _, pv in cv.parts do
				if pv.em and pv.part then
					local ok, rebuilt = pcall(function()
						return AssetService:CreateMeshPartAsync(Content.fromObject(pv.em), {
							CollisionFidelity = if view.collision then Enum.CollisionFidelity.Default else Enum.CollisionFidelity.Box,
						})
					end)
					if ok and rebuilt then
						pv.part:ApplyMesh(rebuilt)
						pv.part.Size = rebuilt.Size
						pv.part.CFrame = view.cframe * CFrame.new(pv.em:GetCenter())
						rebuilt:Destroy()
					end
				end
			end
		end
	end)
end

-- Rebuilds every chunk whose VoxelModel version moved (after remeshDirty). Reuses each chunk's EditableMesh when the
-- part count is unchanged (Clear + refill: live visual update, no CreateMeshPartAsync), otherwise recreates it.
function Adapter.sync(view: View, chunks: { VoxelModel.Chunk }?)
	local model = view.model
	local list = chunks or model.chunks
	local changed = false
	for _, c in list do
		local cv = view.chunks[c.index]
		if cv and cv.version == c.version then
			continue
		end
		changed = true
		local nonEmpty = 0
		for _, m in c.parts do
			if m.tcount > 0 then
				nonEmpty += 1
			end
		end
		if nonEmpty == 0 then
			if cv then
				destroyChunk(cv)
				view.chunks[c.index] = nil
			end
			continue
		end
		if cv and view.mode == "mesh" and #cv.parts == nonEmpty then
			local k = 0
			for _, m in c.parts do
				if m.tcount == 0 then
					continue
				end
				k += 1
				local pv = cv.parts[k]
				pv.em:Clear()
				pv.vids = Adapter.fillEditableMesh(pv.em, m, view.studsPerTile, view.perElement)
				pv.vals = table.create(#pv.vids)
				pv.binding = nil
			end
			cv.version = c.version
		else
			if cv then
				destroyChunk(cv)
			end
			view.chunks[c.index] = buildChunk(view, c.index)
		end
	end
	if changed then
		Adapter.settle(view)
	end
end

-- Binds every mesh part to a jiggle rig (call again after a sync that changed topology).
function Adapter.bindJiggle(view: View, rig: Jiggle.Rig)
	for ci, cv in view.chunks do
		local c = view.model.chunks[ci]
		local k = 0
		for _, m in c.parts do
			if m.tcount == 0 then
				continue
			end
			k += 1
			local pv = cv.parts[k]
			if pv and pv.em then
				pv.binding = Jiggle.bind(rig, m.pos, m.vcount)
			end
		end
	end
end

-- Per frame while the rig has energy: Jiggle.step, then this. Positions only; topology and IDs are unchanged.
-- Allocation: none in Luau (Vector3 is a value type; vals tables are reused). Each pushed part re-uploads its whole
-- vertex set [secondary: transcode cost scales with the mesh], so keep jiggling models small or chunked.
function Adapter.pushJiggle(view: View, rig: Jiggle.Rig)
	for _, cv in view.chunks do
		for _, pv in cv.parts do
			local b = pv.binding
			if not b or not pv.em then
				continue
			end
			Jiggle.apply(rig, b)
			local out, vals = b.out, pv.vals
			-- mesh positions are model-local; the part was centred on em:GetCenter() at creation, and SetPosition
			-- works in the mesh's own space, so local positions are written as-is
			for v = 0, b.count - 1 do
				vals[v + 1] = Vector3.new(buffer.readf32(out, v * 12), buffer.readf32(out, v * 12 + 4), buffer.readf32(out, v * 12 + 8))
			end
			pv.em:BatchSetValues(pv.vids, vals)
		end
	end
end

-- Spawns a carve's debris as unanchored Parts (one per 3D greedy box of each fragment), flung away from the hit.
-- maxParts caps the total; the rest are skipped (they were tiny).
function Adapter.spawnDebris(view: View, fragments: { VoxelModel.Fragment }, hitStuds: Vector3, opts: { maxParts: number?, lifetime: number?, speed: number? }?): { any }
	local o = opts or {}
	local maxParts, lifetime, speed = o.maxParts or 48, o.lifetime or 4, o.speed or 18
	local model = view.model
	local vs = model.meshOpts.voxelSize :: number
	local DebrisService = game:GetService("Debris")
	local out = {}
	for _, frag in fragments do
		local fg, gx, gy, gz = VoxelModel.fragmentGrid(model, frag)
		local boxes = GreedyMesher.boxes(fg)
		for i = 1, #boxes, 7 do
			if #out >= maxParts then
				return out
			end
			local x, y, z, w, h, d, col = boxes[i] + gx, boxes[i + 1] + gy, boxes[i + 2] + gz, boxes[i + 3], boxes[i + 4], boxes[i + 5], boxes[i + 6]
			local px, py, pz = VoxelModel.toStuds(model, x + w / 2, y + h / 2, z + d / 2)
			local p = Instance.new("Part")
			p.Size = Vector3.new(w * vs, h * vs, d * vs)
			p.CFrame = view.cframe * CFrame.new(px, py, pz)
			local rgb = model.grid.palette.colors[col]
			p.Color = Color3.fromRGB(bit32.rshift(rgb, 16), bit32.band(bit32.rshift(rgb, 8), 255), bit32.band(rgb, 255))
			p.Material = Enum.Material.Plastic
			p.TopSurface = Enum.SurfaceType.Studs
			p.CanQuery = false
			p.CanTouch = false
			local dir = (p.Position - view.cframe:PointToWorldSpace(hitStuds))
			dir = if dir.Magnitude > 1e-3 then dir.Unit else Vector3.yAxis
			p.AssemblyLinearVelocity = (dir + Vector3.new(0, 0.8, 0)) * speed
			p.Parent = workspace
			DebrisService:AddItem(p, lifetime)
			table.insert(out, p)
		end
	end
	return out
end

function Adapter.destroy(view: View)
	for _, cv in view.chunks do
		destroyChunk(cv)
	end
	table.clear(view.chunks)
	if view.texture then
		view.texture:Destroy()
	end
	view.root:Destroy()
end

return Adapter
