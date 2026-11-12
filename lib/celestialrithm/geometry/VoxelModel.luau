--!strict
--!native
--!optimize 2
-- VoxelModel: a VoxelGrid split into cubic chunks, each with its own reusable mesh, rebuilt only when dirty.
--
-- Runtime edits and what they dirty:
--   * carveSphere: clears solid cells in a sphere. A chunk is dirty when it holds a changed cell, or when a changed
--     cell sits on its border (a 6-neighbour in the next chunk gains an exposed face). Nothing else is touched.
--   * Debris: after a carve, only solid cells 26-adjacent to the hole can have lost their connection. Each such
--     seed is flooded (26-connected) with a cap. A flood that reaches the anchor cell is attached; one that closes
--     below the cap without reaching it is a loose fragment, removed and returned for the caller to spawn as parts.
--     If any flood hits the cap undecided, one exact global labelling pass decides instead (rare: big splits).
--   * applyCells: replace the whole cell buffer (a morph frame); only chunks whose cells differ are dirtied.
-- remeshDirty(maxChunks) is the time-slice point: rebuild a few chunks per frame if a big edit dirtied many.
-- Each chunk's parts respect `triBudget` (EditableMesh caps at 20k triangles / 60k vertices per mesh).
-- Pure Luau, no Roblox API.

local VoxelGrid = require("./VoxelGrid")
local GreedyMesher = require("./GreedyMesher")

local VoxelModel = {}

export type Chunk = {
	index: number, -- 1-based
	cx: number,
	cy: number,
	cz: number,
	x0: number,
	y0: number,
	z0: number,
	x1: number,
	y1: number,
	z1: number,
	mesh: GreedyMesher.Mesh,
	parts: { GreedyMesher.Mesh }, -- mesh split under triBudget (usually { mesh })
	dirty: boolean,
	version: number, -- bumps on every remesh (adapters compare it)
}

export type Options = {
	chunkSize: number?, -- cells per chunk side, default 16
	voxelSize: number?, -- studs per voxel, default 1
	studsPerVoxel: number?, -- texture studs per voxel, default 1
	origin: { number }?, -- studs; default centres the grid in X/Z with the bottom at Y = 0
	splitEvery: number?, -- cut quads every K cells on Y (needed for crack-free Jiggle), default 0
	triBudget: number?, -- per part, default 18000 (headroom under the 20k cap)
	debrisMax: number?, -- flood cap for the local debris test, default 4096 cells
	piece: number?, -- mesh only this rigid piece
}

export type Fragment = {
	count: number,
	cells: { number }, -- flat x, y, z, colour per cell (grid coordinates)
	cx: number, -- centroid, studs (same space as mesh positions)
	cy: number,
	cz: number,
}

export type CarveResult = { removed: number, debris: { Fragment }, debrisCells: number, dirtied: number, globalPass: boolean }

export type Model = {
	grid: VoxelGrid.Grid,
	chunkSize: number,
	ncx: number,
	ncy: number,
	ncz: number,
	chunks: { Chunk },
	dirtyList: { number },
	meshOpts: GreedyMesher.MeshOptions,
	triBudget: number,
	debrisMax: number,
	anchor: number, -- padded cell index kept as "the body" for debris decisions
	stamp: buffer, -- u32 per cell: flood visit marks
	epoch: number,
	stack: buffer, -- u32 scratch
	carved: buffer, -- u32 scratch: cells cleared by the current carve
	off26: { number },
	remeshed: { Chunk }, -- reused result list of remeshDirty
}

local function chooseAnchor(g: VoxelGrid.Grid): number
	-- lowest solid cell nearest the X/Z centre: the "grounded root" of the model
	local cx, cz = (g.nx - 1) / 2, (g.nz - 1) / 2
	for y = 0, g.ny - 1 do
		local best, bestD = -1, math.huge
		for z = 0, g.nz - 1 do
			for x = 0, g.nx - 1 do
				local i = VoxelGrid.index(g, x, y, z)
				if buffer.readu8(g.cells, i) ~= 0 then
					local d = (x - cx) ^ 2 + (z - cz) ^ 2
					if d < bestD then
						best, bestD = i, d
					end
				end
			end
		end
		if best >= 0 then
			return best
		end
	end
	return -1
end

function VoxelModel.new(g: VoxelGrid.Grid, opts: Options?): Model
	local o: Options = opts or {}
	local cs = o.chunkSize or 16
	local vs = o.voxelSize or 1
	local origin = o.origin or { g.nx * vs / 2, 0, g.nz * vs / 2 }
	local ncx, ncy, ncz = math.ceil(g.nx / cs), math.ceil(g.ny / cs), math.ceil(g.nz / cs)
	local total = buffer.len(g.cells)
	local model: Model = {
		grid = g,
		chunkSize = cs,
		ncx = ncx,
		ncy = ncy,
		ncz = ncz,
		chunks = {},
		dirtyList = {},
		meshOpts = { voxelSize = vs, studsPerVoxel = o.studsPerVoxel or 1, origin = origin, splitAxis = 1, splitEvery = o.splitEvery or 0, piece = o.piece },
		triBudget = o.triBudget or 18000,
		debrisMax = o.debrisMax or 4096,
		anchor = chooseAnchor(g),
		stamp = buffer.create(total * 4),
		epoch = 0,
		stack = buffer.create(total * 4),
		carved = buffer.create(total * 4),
		off26 = VoxelGrid.offsets26(g),
		remeshed = {},
	}
	for cz = 0, ncz - 1 do
		for cy = 0, ncy - 1 do
			for cx = 0, ncx - 1 do
				local index = #model.chunks + 1
				local m = GreedyMesher.newMesh(64)
				model.chunks[index] = {
					index = index,
					cx = cx,
					cy = cy,
					cz = cz,
					x0 = cx * cs,
					y0 = cy * cs,
					z0 = cz * cs,
					x1 = math.min((cx + 1) * cs, g.nx),
					y1 = math.min((cy + 1) * cs, g.ny),
					z1 = math.min((cz + 1) * cs, g.nz),
					mesh = m,
					parts = { m },
					dirty = false,
					version = 0,
				}
			end
		end
	end
	for _, c in model.chunks do
		c.dirty = true
		table.insert(model.dirtyList, c.index)
	end
	return model
end

local function chunkAt(model: Model, cx: number, cy: number, cz: number): number
	if cx < 0 or cy < 0 or cz < 0 or cx >= model.ncx or cy >= model.ncy or cz >= model.ncz then
		return 0
	end
	return 1 + cx + model.ncx * (cy + model.ncy * cz)
end

local function markChunk(model: Model, ci: number)
	if ci == 0 then
		return
	end
	local c = model.chunks[ci]
	if not c.dirty then
		c.dirty = true
		table.insert(model.dirtyList, ci)
	end
end

-- Marks the chunks whose mesh can change when cell (x, y, z) changes: its own, plus the 6-neighbour chunk across
-- any border face the cell touches.
function VoxelModel.markCell(model: Model, x: number, y: number, z: number)
	local cs = model.chunkSize
	local cx, cy, cz = x // cs, y // cs, z // cs
	markChunk(model, chunkAt(model, cx, cy, cz))
	local lx, ly, lz = x - cx * cs, y - cy * cs, z - cz * cs
	if lx == 0 then
		markChunk(model, chunkAt(model, cx - 1, cy, cz))
	end
	if lx == cs - 1 then
		markChunk(model, chunkAt(model, cx + 1, cy, cz))
	end
	if ly == 0 then
		markChunk(model, chunkAt(model, cx, cy - 1, cz))
	end
	if ly == cs - 1 then
		markChunk(model, chunkAt(model, cx, cy + 1, cz))
	end
	if lz == 0 then
		markChunk(model, chunkAt(model, cx, cy, cz - 1))
	end
	if lz == cs - 1 then
		markChunk(model, chunkAt(model, cx, cy, cz + 1))
	end
end

function VoxelModel.remeshChunk(model: Model, c: Chunk)
	local o = model.meshOpts
	o.x0, o.y0, o.z0, o.x1, o.y1, o.z1 = c.x0, c.y0, c.z0, c.x1, c.y1, c.z1
	GreedyMesher.mesh(model.grid, o, c.mesh)
	c.parts = if c.mesh.tcount > model.triBudget then GreedyMesher.split(c.mesh, model.triBudget) else { c.mesh }
	c.dirty = false
	c.version += 1
end

-- Rebuilds up to maxChunks dirty chunks (all if nil). Returns the reused list of chunks rebuilt this call.
function VoxelModel.remeshDirty(model: Model, maxChunks: number?): { Chunk }
	local out = model.remeshed
	table.clear(out)
	local list = model.dirtyList
	local limit = maxChunks or #list
	local done = 0
	while done < limit and #list > 0 do
		local ci = table.remove(list) :: number
		local c = model.chunks[ci]
		if c.dirty then
			VoxelModel.remeshChunk(model, c)
			table.insert(out, c)
			done += 1
		end
	end
	return out
end

function VoxelModel.remeshAll(model: Model): { Chunk }
	for _, c in model.chunks do
		markChunk(model, c.index)
	end
	return VoxelModel.remeshDirty(model)
end

function VoxelModel.totals(model: Model): (number, number, number)
	local tris, verts, used = 0, 0, 0
	for _, c in model.chunks do
		tris += c.mesh.tcount
		verts += c.mesh.vcount
		if c.mesh.tcount > 0 then
			used += 1
		end
	end
	return tris, verts, used
end

-- Stud-space position of a grid coordinate (cell corner), matching mesh positions.
function VoxelModel.toStuds(model: Model, x: number, y: number, z: number): (number, number, number)
	local o = model.meshOpts
	local vs, org = o.voxelSize :: number, o.origin :: { number }
	return x * vs - org[1], y * vs - org[2], z * vs - org[3]
end

-- Debris ------------------------------------------------------------------------------------------------------

-- Floods from `seed` over solid cells not visited by this flood. Returns size, whether it is attached, and whether
-- the cap stopped it. A flood is attached when it reaches the anchor OR meets a cell stamped by an earlier flood of
-- the same carve: earlier loose floods are always fully closed (all their cells stamped), so any earlier stamp a new
-- flood can reach belongs to an attached component. Visited cells are left in model.stack[0 .. size-1].
local function flood(model: Model, seed: number, cap: number, base: number): (number, boolean, boolean)
	local cells, stamp, stack, off, ep = model.grid.cells, model.stamp, model.stack, model.off26, model.epoch
	local anchor = model.anchor
	buffer.writeu32(stamp, seed * 4, ep)
	buffer.writeu32(stack, 0, seed)
	local head, size = 0, 1
	if seed == anchor then
		return size, true, false
	end
	while head < size do
		local c = buffer.readu32(stack, head * 4)
		head += 1
		for k = 1, 26 do
			local nb = c + off[k]
			if buffer.readu8(cells, nb) ~= 0 then
				local st = buffer.readu32(stamp, nb * 4)
				if st ~= ep then
					if st >= base or nb == anchor then
						return size, true, false
					end
					if size >= cap then
						return size, false, true
					end
					buffer.writeu32(stamp, nb * 4, ep)
					buffer.writeu32(stack, size * 4, nb)
					size += 1
				end
			end
		end
	end
	return size, false, false
end

local function removeCells(model: Model, list: { number }, frag: Fragment)
	local g = model.grid
	local gp = g.pieces
	local sx, sy, sz = 0, 0, 0
	for _, i in list do
		local x, y, z = VoxelGrid.coords(g, i)
		local c = buffer.readu8(g.cells, i)
		table.move({ x, y, z, c }, 1, 4, #frag.cells + 1, frag.cells)
		buffer.writeu8(g.cells, i, 0)
		if gp then
			buffer.writeu8(gp, i, 0)
		end
		VoxelModel.markCell(model, x, y, z)
		sx += x + 0.5
		sy += y + 0.5
		sz += z + 0.5
	end
	local n = #list
	frag.count = n
	frag.cx, frag.cy, frag.cz = VoxelModel.toStuds(model, sx / n, sy / n, sz / n)
end

local function nextEpoch(model: Model)
	model.epoch += 1
end

-- Exact fallback: label everything, keep the anchor's component (or the largest), return the rest as fragments.
local function globalDebris(model: Model, out: { Fragment })
	local g = model.grid
	local count, labels, sizes = VoxelGrid.components(g)
	if count <= 1 then
		return
	end
	local keep = 0
	if model.anchor >= 0 and buffer.readu8(g.cells, model.anchor) ~= 0 then
		keep = buffer.readu32(labels, model.anchor * 4)
	else
		local best = -1
		for l = 1, count do
			if sizes[l] > best then
				best, keep = sizes[l], l
			end
		end
	end
	local lists: { [number]: { number } } = {}
	for i = 0, buffer.len(g.cells) - 1 do
		local l = buffer.readu32(labels, i * 4)
		if l ~= 0 and l ~= keep then
			local t = lists[l]
			if not t then
				t = {}
				lists[l] = t
			end
			table.insert(t, i)
		end
	end
	for l = 1, count do
		local t = lists[l]
		if t then
			local frag: Fragment = { count = 0, cells = {}, cx = 0, cy = 0, cz = 0 }
			removeCells(model, t, frag)
			table.insert(out, frag)
		end
	end
end

-- Carves a sphere (grid coordinates; radius in cells). Marks dirty chunks, removes loose fragments, returns them.
-- Call remeshDirty afterwards (or spread it over frames).
function VoxelModel.carveSphere(model: Model, cx: number, cy: number, cz: number, r: number): CarveResult
	local g = model.grid
	local cells, carved = g.cells, model.carved
	local gp = g.pieces
	local before = #model.dirtyList
	local r2 = r * r
	local removed = 0
	for z = math.max(0, math.floor(cz - r)), math.min(g.nz - 1, math.ceil(cz + r)) do
		local dz = z + 0.5 - cz
		for y = math.max(0, math.floor(cy - r)), math.min(g.ny - 1, math.ceil(cy + r)) do
			local dy = y + 0.5 - cy
			for x = math.max(0, math.floor(cx - r)), math.min(g.nx - 1, math.ceil(cx + r)) do
				local dx = x + 0.5 - cx
				if dx * dx + dy * dy + dz * dz <= r2 then
					local i = (x + 1) + g.sx * ((y + 1) + g.sy * (z + 1))
					if buffer.readu8(cells, i) ~= 0 then
						buffer.writeu8(cells, i, 0)
						if gp then
							buffer.writeu8(gp, i, 0)
						end
						buffer.writeu32(carved, removed * 4, i)
						removed += 1
						VoxelModel.markCell(model, x, y, z)
					end
				end
			end
		end
	end
	local result: CarveResult = { removed = removed, debris = {}, debrisCells = 0, dirtied = 0, globalPass = false }
	if removed == 0 then
		return result
	end
	if model.anchor < 0 or buffer.readu8(cells, model.anchor) == 0 then
		model.anchor = -1
	end
	-- local floods from every solid neighbour of the hole
	if model.epoch > 0x7FFFFFFF then
		buffer.fill(model.stamp, 0, 0)
		model.epoch = 0
	end
	local base = model.epoch + 1
	local off, stamp, stack = model.off26, model.stamp, model.stack
	local undecided = model.anchor < 0
	local loose: { { number } } = {}
	for k = 0, removed - 1 do
		if undecided then
			break
		end
		local c = buffer.readu32(carved, k * 4)
		for n = 1, 26 do
			local s = c + off[n]
			if buffer.readu8(cells, s) == 0 or buffer.readu32(stamp, s * 4) >= base then
				continue
			end
			nextEpoch(model)
			local size, attached, capped = flood(model, s, model.debrisMax, base)
			if capped and not attached then
				undecided = true
				break
			end
			if not attached then
				local list = table.create(size)
				for e = 0, size - 1 do
					list[e + 1] = buffer.readu32(stack, e * 4)
				end
				table.insert(loose, list)
			end
			-- attached floods stop at the first proof (anchor or an earlier stamp), so they stay small
		end
	end
	if undecided then
		result.globalPass = true
		globalDebris(model, result.debris)
		if model.anchor < 0 or buffer.readu8(cells, model.anchor) == 0 then
			model.anchor = chooseAnchor(g)
		end
	else
		for _, list in loose do
			local frag: Fragment = { count = 0, cells = {}, cx = 0, cy = 0, cz = 0 }
			removeCells(model, list, frag)
			table.insert(result.debris, frag)
		end
	end
	for _, f in result.debris do
		result.debrisCells += f.count
	end
	result.dirtied = #model.dirtyList - before
	return result
end

-- A fragment as its own small grid (for GreedyMesher.boxes -> Parts, or its own mesh). Returns the grid and the
-- grid-coordinate offset of its cell (0, 0, 0).
function VoxelModel.fragmentGrid(model: Model, frag: Fragment): (VoxelGrid.Grid, number, number, number)
	local cells = frag.cells
	local x0, y0, z0, x1, y1, z1 = math.huge, math.huge, math.huge, -math.huge, -math.huge, -math.huge
	for i = 1, #cells, 4 do
		x0, y0, z0 = math.min(x0, cells[i]), math.min(y0, cells[i + 1]), math.min(z0, cells[i + 2])
		x1, y1, z1 = math.max(x1, cells[i]), math.max(y1, cells[i + 1]), math.max(z1, cells[i + 2])
	end
	local fg = VoxelGrid.new(x1 - x0 + 1, y1 - y0 + 1, z1 - z0 + 1, model.grid.palette)
	for i = 1, #cells, 4 do
		VoxelGrid.set(fg, cells[i] - x0, cells[i + 1] - y0, cells[i + 2] - z0, cells[i + 3])
	end
	return fg, x0, y0, z0
end

-- Replaces every cell (e.g. a morph frame with the same dims). Dirties only chunks whose cells changed.
-- Returns the number of changed cells.
function VoxelModel.applyCells(model: Model, newCells: buffer, newPieces: buffer?): number
	local g = model.grid
	local cells = g.cells
	assert(buffer.len(newCells) == buffer.len(cells), "VoxelModel.applyCells: size mismatch")
	local changed = 0
	local sx, sy = g.sx, g.sy
	for z = 0, g.nz - 1 do
		for y = 0, g.ny - 1 do
			local row = 1 + sx * ((y + 1) + sy * (z + 1))
			for x = 0, g.nx - 1 do
				local i = row + x
				local nv = buffer.readu8(newCells, i)
				if buffer.readu8(cells, i) ~= nv then
					buffer.writeu8(cells, i, nv)
					changed += 1
					VoxelModel.markCell(model, x, y, z)
				end
			end
		end
	end
	if newPieces then
		local gp = g.pieces
		if not gp then
			gp = buffer.create(buffer.len(cells))
			g.pieces = gp
		end
		buffer.copy(gp :: buffer, 0, newPieces)
	end
	if model.anchor < 0 or buffer.readu8(cells, model.anchor) == 0 then
		model.anchor = chooseAnchor(g)
	end
	return changed
end

return VoxelModel
