--!strict
--!native
--!optimize 2
-- GreedyMesher: exposed voxel faces -> greedy-merged quads -> flat vertex / index / uv / colour buffers.
--
-- Technique:
--   * Six sweeps (3 axes x 2 directions). For each slice a 2D mask holds the colour of every face whose cell is solid
--     and whose neighbour (read from the WHOLE grid, so chunk borders are right) is empty.
--   * The mask is consumed greedily: run right while the colour matches, then grow down while the whole run matches.
--     Only same-colour, coplanar faces merge. `greedy = false` gives the naive one-quad-per-face mesh (for tests).
--   * Stud UVs are world aligned: u, v = grid coordinate along the face's two in-plane axes x studsPerVoxel, so studs
--     run continuously across merged quads, across chunks, and around corners (every edge sits on the lattice).
--     Flat colours (eyes, shines) get one constant UV in the flat gap of the stud tile, so they render unstudded.
--   * Optional `splitEvery` cuts quads at every K-th lattice plane of `splitAxis` (default Y). Jiggle.luau deforms
--     piecewise-linearly between those planes, which keeps greedy T-junctions closed while vertices move.
--   * split(): Morton-sorted quads packed into parts of at most `triBudget` triangles (EditableMesh caps at 20k).
-- Output buffers are owned by a Mesh and reused (grown by doubling) across remeshes: no allocation in steady state.
-- Winding: (p1 - p0) x (p2 - p0) points out of the solid (same convention as lib/frontier/mesh).
-- Pure Luau, no Roblox API.

local VoxelGrid = require("./VoxelGrid")

local GreedyMesher = {}

export type Mesh = {
	quads: number,
	vcount: number,
	tcount: number,
	cap: number, -- quad capacity
	pos: buffer, -- f32 x3 per vertex, studs
	nrm: buffer, -- f32 x3 per vertex
	uv: buffer, -- f32 x2 per vertex, stud units (1.0 = one stud)
	col: buffer, -- u32 RGBA8 per vertex (r in the low byte)
	idx: buffer, -- u32 x3 per triangle, 0-based
	qaxis: buffer, -- u8 per quad: axis * 2 + (1 if facing negative)
	qcolor: buffer, -- u8 per quad: palette index
}

export type MeshOptions = {
	x0: number?, -- region (grid cells), end exclusive; defaults to the whole grid
	y0: number?,
	z0: number?,
	x1: number?,
	y1: number?,
	z1: number?,
	greedy: boolean?, -- default true
	voxelSize: number?, -- studs per voxel, default 1
	studsPerVoxel: number?, -- texture studs per voxel, default 1
	origin: { number }?, -- studs subtracted from every position, default {0, 0, 0}
	splitAxis: number?, -- 0 = x, 1 = y (default), 2 = z
	splitEvery: number?, -- 0 = never cut (default)
	piece: number?, -- only cells of this rigid piece (needs grid.pieces); other pieces count as empty
}

local FLAT_UV = 0.04 -- stud units: lands in the flat gap of the stud tile (see StudTexture)

function GreedyMesher.newMesh(capQuads: number?): Mesh
	local cap = math.max(capQuads or 256, 1)
	return {
		quads = 0,
		vcount = 0,
		tcount = 0,
		cap = cap,
		pos = buffer.create(cap * 4 * 12),
		nrm = buffer.create(cap * 4 * 12),
		uv = buffer.create(cap * 4 * 8),
		col = buffer.create(cap * 4 * 4),
		idx = buffer.create(cap * 2 * 12),
		qaxis = buffer.create(cap),
		qcolor = buffer.create(cap),
	}
end

local function growTo(old: buffer, bytes: number, used: number): buffer
	local b = buffer.create(bytes)
	buffer.copy(b, 0, old, 0, used)
	return b
end

local function reserve(m: Mesh, quads: number)
	if quads <= m.cap then
		return
	end
	local cap = m.cap
	while cap < quads do
		cap *= 2
	end
	local q = m.quads
	m.pos = growTo(m.pos, cap * 48, q * 48)
	m.nrm = growTo(m.nrm, cap * 48, q * 48)
	m.uv = growTo(m.uv, cap * 32, q * 32)
	m.col = growTo(m.col, cap * 16, q * 16)
	m.idx = growTo(m.idx, cap * 24, q * 24)
	m.qaxis = growTo(m.qaxis, cap, q)
	m.qcolor = growTo(m.qcolor, cap, q)
	m.cap = cap
end

function GreedyMesher.packColor(rgb: number): number
	local r, g, b = bit32.rshift(rgb, 16), bit32.band(bit32.rshift(rgb, 8), 255), bit32.band(rgb, 255)
	return bit32.bor(r, bit32.lshift(g, 8), bit32.lshift(b, 16), 0xFF000000)
end

local packColor = GreedyMesher.packColor

local maskBuf: buffer = buffer.create(0)

-- Writes one quad. (a0, b0) = start on the face's (u, v) axes, w x h its size, plane = coordinate on axis d.
local function emit(m: Mesh, d: number, neg: boolean, plane: number, a0: number, b0: number, w: number, h: number, colorIndex: number, rgba: number, flat: boolean, vs: number, spv: number, ox: number, oy: number, oz: number)
	local q = m.quads
	reserve(m, q + 1)
	local pos, nrm, uvb, col, idx = m.pos, m.nrm, m.uv, m.col, m.idx
	local nx, ny, nz = 0, 0, 0
	local sgn = if neg then -1 else 1
	if d == 0 then
		nx = sgn
	elseif d == 1 then
		ny = sgn
	else
		nz = sgn
	end
	local vb = q * 4
	for corner = 0, 3 do
		-- + face: (0,0) (w,0) (w,h) (0,h); - face swaps the order so the winding flips
		local ca, cb
		if corner == 0 then
			ca, cb = 0, 0
		elseif corner == 2 then
			ca, cb = w, h
		elseif (corner == 1) ~= neg then
			ca, cb = w, 0
		else
			ca, cb = 0, h
		end
		local ua, vb2 = a0 + ca, b0 + cb
		local x, y, z
		if d == 0 then
			x, y, z = plane, ua, vb2
		elseif d == 1 then
			x, y, z = vb2, plane, ua
		else
			x, y, z = ua, vb2, plane
		end
		local v = vb + corner
		buffer.writef32(pos, v * 12, x * vs - ox)
		buffer.writef32(pos, v * 12 + 4, y * vs - oy)
		buffer.writef32(pos, v * 12 + 8, z * vs - oz)
		buffer.writef32(nrm, v * 12, nx)
		buffer.writef32(nrm, v * 12 + 4, ny)
		buffer.writef32(nrm, v * 12 + 8, nz)
		if flat then
			buffer.writef32(uvb, v * 8, FLAT_UV)
			buffer.writef32(uvb, v * 8 + 4, FLAT_UV)
		else
			buffer.writef32(uvb, v * 8, ua * spv)
			buffer.writef32(uvb, v * 8 + 4, vb2 * spv)
		end
		buffer.writeu32(col, v * 4, rgba)
	end
	local t = q * 2
	buffer.writeu32(idx, t * 12, vb)
	buffer.writeu32(idx, t * 12 + 4, vb + 1)
	buffer.writeu32(idx, t * 12 + 8, vb + 2)
	buffer.writeu32(idx, t * 12 + 12, vb)
	buffer.writeu32(idx, t * 12 + 16, vb + 2)
	buffer.writeu32(idx, t * 12 + 20, vb + 3)
	buffer.writeu8(m.qaxis, q, d * 2 + (if neg then 1 else 0))
	buffer.writeu8(m.qcolor, q, colorIndex)
	m.quads = q + 1
	m.vcount = (q + 1) * 4
	m.tcount = (q + 1) * 2
end

-- Meshes a region of the grid into `out` (reset first) or a new Mesh.
function GreedyMesher.mesh(g: VoxelGrid.Grid, opts: MeshOptions?, out: Mesh?): Mesh
	local o: MeshOptions = opts or {}
	local m = out or GreedyMesher.newMesh()
	m.quads, m.vcount, m.tcount = 0, 0, 0
	local lo = { o.x0 or 0, o.y0 or 0, o.z0 or 0 }
	local hi = { math.min(o.x1 or g.nx, g.nx), math.min(o.y1 or g.ny, g.ny), math.min(o.z1 or g.nz, g.nz) }
	if hi[1] <= lo[1] or hi[2] <= lo[2] or hi[3] <= lo[3] then
		return m
	end
	local greedy = o.greedy ~= false
	local vs, spv = o.voxelSize or 1, o.studsPerVoxel or 1
	local org = o.origin or { 0, 0, 0 }
	local ox, oy, oz = org[1], org[2], org[3]
	local splitAxis, K = o.splitAxis or 1, o.splitEvery or 0
	local cells = g.cells
	local pieces = g.pieces
	local piece = o.piece
	local usePiece = piece ~= nil and pieces ~= nil
	local pal = g.palette
	local colors, flats = pal.colors, pal.flat
	-- packed colours per palette index, built once per call (palette has <= 255 entries)
	local packed = table.create(#colors, 0)
	for c = 1, #colors do
		packed[c] = packColor(colors[c])
	end
	local stride = { 1, g.sx, g.sx * g.sy }
	local maxMask = 0
	for d = 0, 2 do
		local u, v = (d + 1) % 3, (d + 2) % 3
		maxMask = math.max(maxMask, (hi[u + 1] - lo[u + 1]) * (hi[v + 1] - lo[v + 1]))
	end
	if buffer.len(maskBuf) < maxMask * 2 then
		maskBuf = buffer.create(maxMask * 2)
	end
	local mask = maskBuf
	for d = 0, 2 do
		local u, v = (d + 1) % 3, (d + 2) % 3
		local nu, nv = hi[u + 1] - lo[u + 1], hi[v + 1] - lo[v + 1]
		local su, sv, sd = stride[u + 1], stride[v + 1], stride[d + 1]
		local cutU = K > 0 and u == splitAxis
		local cutV = K > 0 and v == splitAxis
		local lu, lv = lo[u + 1], lo[v + 1]
		for side = 0, 1 do
			local neg = side == 1
			local dOff = if neg then -sd else sd
			for s = lo[d + 1], hi[d + 1] - 1 do
				-- 1. mask: colour of each exposed face in this slice (0 = none)
				local coord = { 0, 0, 0 }
				coord[d + 1], coord[u + 1], coord[v + 1] = s, lu, lv
				local base = (coord[1] + 1) + g.sx * ((coord[2] + 1) + g.sy * (coord[3] + 1))
				local any = false
				local n = 0
				for j = 0, nv - 1 do
					local idx = base + j * sv
					for _ = 0, nu - 1 do
						local c = buffer.readu8(cells, idx)
						local val = 0
						if c ~= 0 then
							local nb = buffer.readu8(cells, idx + dOff)
							if usePiece then
								local pb = pieces :: buffer
								if buffer.readu8(pb, idx) ~= piece then
									c = 0
								elseif nb ~= 0 and buffer.readu8(pb, idx + dOff) ~= piece then
									nb = 0
								end
							end
							if c ~= 0 and nb == 0 then
								val = c
								any = true
							end
						end
						buffer.writeu16(mask, n * 2, val)
						n += 1
						idx += su
					end
				end
				if not any then
					continue
				end
				local plane = if neg then s else s + 1
				-- 2. consume greedily
				n = 0
				for j = 0, nv - 1 do
					local i = 0
					while i < nu do
						local c = buffer.readu16(mask, n * 2)
						if c == 0 then
							i += 1
							n += 1
							continue
						end
						local w, h = 1, 1
						if greedy then
							while i + w < nu and buffer.readu16(mask, (n + w) * 2) == c and not (cutU and (lu + i + w) % K == 0) do
								w += 1
							end
							while j + h < nv and not (cutV and (lv + j + h) % K == 0) do
								local row = n + h * nu
								local ok = true
								for kk = 0, w - 1 do
									if buffer.readu16(mask, (row + kk) * 2) ~= c then
										ok = false
										break
									end
								end
								if not ok then
									break
								end
								h += 1
							end
						end
						emit(m, d, neg, plane, lu + i, lv + j, w, h, c, packed[c], flats[c], vs, spv, ox, oy, oz)
						for l = 0, h - 1 do
							local row = n + l * nu
							for kk = 0, w - 1 do
								buffer.writeu16(mask, (row + kk) * 2, 0)
							end
						end
						i += w
						n += w
					end
				end
			end
		end
	end
	return m
end

-- Count of exposed unit faces (the naive mesh's quad count) in a region.
function GreedyMesher.exposedFaces(g: VoxelGrid.Grid, opts: MeshOptions?): number
	local o: MeshOptions = opts or {}
	local x0, y0, z0 = o.x0 or 0, o.y0 or 0, o.z0 or 0
	local x1, y1, z1 = math.min(o.x1 or g.nx, g.nx), math.min(o.y1 or g.ny, g.ny), math.min(o.z1 or g.nz, g.nz)
	local cells, sx, sxy = g.cells, g.sx, g.sx * g.sy
	local off = { 1, -1, sx, -sx, sxy, -sxy }
	local n = 0
	for z = z0, z1 - 1 do
		for y = y0, y1 - 1 do
			for x = x0, x1 - 1 do
				local i = (x + 1) + sx * ((y + 1) + g.sy * (z + 1))
				if buffer.readu8(cells, i) ~= 0 then
					for k = 1, 6 do
						if buffer.readu8(cells, i + off[k]) == 0 then
							n += 1
						end
					end
				end
			end
		end
	end
	return n
end

-- Total quad area in voxel-face units (positions are divided by voxelSize).
function GreedyMesher.area(m: Mesh, voxelSize: number?): number
	local vs = voxelSize or 1
	local total = 0
	for q = 0, m.quads - 1 do
		local b = q * 48
		local x0, y0, z0 = buffer.readf32(m.pos, b), buffer.readf32(m.pos, b + 4), buffer.readf32(m.pos, b + 8)
		local x2, y2, z2 = buffer.readf32(m.pos, b + 24), buffer.readf32(m.pos, b + 28), buffer.readf32(m.pos, b + 32)
		local ex, ey, ez = math.abs(x2 - x0), math.abs(y2 - y0), math.abs(z2 - z0)
		local axis = buffer.readu8(m.qaxis, q) // 2
		local a = if axis == 0 then ey * ez elseif axis == 1 then ex * ez else ex * ey
		total += a / (vs * vs)
	end
	return total
end

local function part3(x: number): number
	x = bit32.band(x, 0x3FF)
	x = bit32.band(bit32.bor(x, bit32.lshift(x, 16)), 0x030000FF)
	x = bit32.band(bit32.bor(x, bit32.lshift(x, 8)), 0x0300F00F)
	x = bit32.band(bit32.bor(x, bit32.lshift(x, 4)), 0x030C30C3)
	x = bit32.band(bit32.bor(x, bit32.lshift(x, 2)), 0x09249249)
	return x
end

-- Splits a mesh into parts of at most triBudget triangles. Quads are Morton-sorted by centre first, so each part
-- is a compact region (better culling, smaller re-uploads). Returns { m } unchanged when it already fits.
function GreedyMesher.split(m: Mesh, triBudget: number): { Mesh }
	assert(triBudget >= 2, "GreedyMesher.split: budget must allow one quad")
	if m.tcount <= triBudget then
		return { m }
	end
	local nq = m.quads
	local cx, cy, cz = table.create(nq, 0), table.create(nq, 0), table.create(nq, 0)
	local minX, minY, minZ, maxX, maxY, maxZ = math.huge, math.huge, math.huge, -math.huge, -math.huge, -math.huge
	for q = 0, nq - 1 do
		local b = q * 48
		local x = (buffer.readf32(m.pos, b) + buffer.readf32(m.pos, b + 24)) * 0.5
		local y = (buffer.readf32(m.pos, b + 4) + buffer.readf32(m.pos, b + 28)) * 0.5
		local z = (buffer.readf32(m.pos, b + 8) + buffer.readf32(m.pos, b + 32)) * 0.5
		cx[q + 1], cy[q + 1], cz[q + 1] = x, y, z
		minX, minY, minZ = math.min(minX, x), math.min(minY, y), math.min(minZ, z)
		maxX, maxY, maxZ = math.max(maxX, x), math.max(maxY, y), math.max(maxZ, z)
	end
	local span = math.max(maxX - minX, maxY - minY, maxZ - minZ, 1e-6)
	local keys, order = table.create(nq, 0), table.create(nq, 0)
	for q = 1, nq do
		local ix = math.floor((cx[q] - minX) / span * 1023)
		local iy = math.floor((cy[q] - minY) / span * 1023)
		local iz = math.floor((cz[q] - minZ) / span * 1023)
		keys[q] = bit32.bor(part3(ix), bit32.lshift(part3(iy), 1), bit32.lshift(part3(iz), 2))
		order[q] = q
	end
	table.sort(order, function(a: number, b: number): boolean
		if keys[a] ~= keys[b] then
			return keys[a] < keys[b]
		end
		return a < b
	end)
	local perPart = triBudget // 2
	local parts: { Mesh } = {}
	local k = 1
	while k <= nq do
		local count = math.min(perPart, nq - k + 1)
		local p = GreedyMesher.newMesh(count)
		for e = 0, count - 1 do
			local q = order[k + e] - 1
			buffer.copy(p.pos, e * 48, m.pos, q * 48, 48)
			buffer.copy(p.nrm, e * 48, m.nrm, q * 48, 48)
			buffer.copy(p.uv, e * 32, m.uv, q * 32, 32)
			buffer.copy(p.col, e * 16, m.col, q * 16, 16)
			buffer.writeu8(p.qaxis, e, buffer.readu8(m.qaxis, q))
			buffer.writeu8(p.qcolor, e, buffer.readu8(m.qcolor, q))
			local vb, t = e * 4, e * 2
			buffer.writeu32(p.idx, t * 12, vb)
			buffer.writeu32(p.idx, t * 12 + 4, vb + 1)
			buffer.writeu32(p.idx, t * 12 + 8, vb + 2)
			buffer.writeu32(p.idx, t * 12 + 12, vb)
			buffer.writeu32(p.idx, t * 12 + 16, vb + 2)
			buffer.writeu32(p.idx, t * 12 + 20, vb + 3)
		end
		p.quads, p.vcount, p.tcount = count, count * 4, count * 2
		table.insert(parts, p)
		k += count
	end
	return parts
end

-- 3D greedy box merge of same-colour cells: the Part fallback and debris spawner use it (fewer Parts than voxels).
-- Returns a flat array x, y, z, w, h, d, colour per box (grid cells, end exclusive = start + size).
function GreedyMesher.boxes(g: VoxelGrid.Grid, opts: MeshOptions?): { number }
	local o: MeshOptions = opts or {}
	local x0, y0, z0 = o.x0 or 0, o.y0 or 0, o.z0 or 0
	local x1, y1, z1 = math.min(o.x1 or g.nx, g.nx), math.min(o.y1 or g.ny, g.ny), math.min(o.z1 or g.nz, g.nz)
	local cells, sx, sy = g.cells, g.sx, g.sy
	local used = buffer.create(buffer.len(cells))
	local out: { number } = {}
	local function at(x: number, y: number, z: number): number
		return (x + 1) + sx * ((y + 1) + sy * (z + 1))
	end
	for z = z0, z1 - 1 do
		for y = y0, y1 - 1 do
			for x = x0, x1 - 1 do
				local i = at(x, y, z)
				local c = buffer.readu8(cells, i)
				if c == 0 or buffer.readu8(used, i) ~= 0 then
					continue
				end
				local w = 1
				while x + w < x1 do
					local j = i + w
					if buffer.readu8(cells, j) ~= c or buffer.readu8(used, j) ~= 0 then
						break
					end
					w += 1
				end
				local h = 1
				while y + h < y1 do
					local ok = true
					for k = 0, w - 1 do
						local j = at(x + k, y + h, z)
						if buffer.readu8(cells, j) ~= c or buffer.readu8(used, j) ~= 0 then
							ok = false
							break
						end
					end
					if not ok then
						break
					end
					h += 1
				end
				local dd = 1
				while z + dd < z1 do
					local ok = true
					for b = 0, h - 1 do
						for k = 0, w - 1 do
							local j = at(x + k, y + b, z + dd)
							if buffer.readu8(cells, j) ~= c or buffer.readu8(used, j) ~= 0 then
								ok = false
								break
							end
						end
						if not ok then
							break
						end
					end
					if not ok then
						break
					end
					dd += 1
				end
				for c2 = 0, dd - 1 do
					for b = 0, h - 1 do
						for k = 0, w - 1 do
							buffer.writeu8(used, at(x + k, y + b, z + c2), 1)
						end
					end
				end
				table.move({ x, y, z, w, h, dd, c }, 1, 7, #out + 1, out)
			end
		end
	end
	return out
end

return GreedyMesher
