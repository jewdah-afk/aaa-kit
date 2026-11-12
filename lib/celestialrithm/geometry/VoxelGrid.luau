--!strict
--!native
--!optimize 2
-- VoxelGrid: dense, buffer-backed stud-voxel grid (one palette index per cell) plus the SDF sculpting that fills it.
--
-- Technique (reimplemented from first principles; see docs/celestialrithm/frontier/editablemesh-voxel.md):
--   * A model is a recipe (pure data): a list of SDF primitives (sphere, ellipsoid, box, capsule) combined in order
--     with hard or smooth union / subtract / intersect, plus "paint" ops that recolour solid cells without changing
--     the shape (eyes, belly patch, tone bands). Seeded "scatter" entries expand into extra paint ops.
--   * evalRecipe samples the combined distance at every cell centre (a Field: f32 distance + u8 colour + u8 piece).
--     fromField keeps cells with distance <= 0, which is what gives the stepped voxel silhouette.
--   * dropIslands: 26-connected components; everything not connected to the kept body is removed.
--   * quantise: merges palette entries (Ward-weighted nearest pair, snapping to an existing colour, never inventing
--     one) until at most maxColors remain.
-- Storage is padded by one empty cell on every side, so neighbour reads never need bounds checks:
--   index(x, y, z) = (x + 1) + sx * ((y + 1) + sy * (z + 1)),  sx = nx + 2, sy = ny + 2.
-- Cell value 0 = empty, 1..255 = palette index. Pure Luau, no Roblox API.

local VoxelGrid = {}

export type Palette = {
	colors: { number }, -- 0xRRGGBB per index (1-based, index = cell value)
	flat: { boolean }, -- true = no stud texture on this colour (eyes, shines, glow)
	lookup: { [number]: number },
	keys: { [string]: number }, -- recipe colour key -> index (filled as recipes are evaluated)
}

export type Grid = {
	nx: number,
	ny: number,
	nz: number,
	sx: number,
	sy: number,
	sz: number,
	cells: buffer, -- u8, padded
	pieces: buffer?, -- u8, padded: rigid piece id per cell (0 = main), optional
	palette: Palette,
}

export type Field = {
	nx: number,
	ny: number,
	nz: number,
	cell: number, -- recipe units per voxel
	ox: number, -- recipe-space position of the corner of cell (0,0,0)
	oy: number,
	oz: number,
	dist: buffer, -- f32 per cell, unpadded: x + nx * (y + ny * z)
	color: buffer, -- u8 colour index per cell (nearest union primitive, then paint)
	piece: buffer, -- u8 piece id per cell
	palette: Palette,
	pieceNames: { string }, -- piece id (1-based) -> name; id 0 = main
}

export type Op = {
	op: string, -- "union" | "subtract" | "intersect" | "paint"
	shape: string, -- "sphere" | "ellipsoid" | "box" | "capsule"
	c: { number }?, -- centre (sphere / ellipsoid / box)
	r: any?, -- number (sphere, capsule) or {rx, ry, rz} (ellipsoid)
	h: { number }?, -- box half extents
	round: number?, -- box corner radius
	a: { number }?, -- capsule end points
	b: { number }?,
	k: number?, -- smooth blend radius (0 = hard)
	color: string?,
	piece: string?,
}

export type Scatter = {
	count: number,
	around: { c: { number }, r: { number } }, -- ellipsoid whose surface the spots sit on
	radius: { number }, -- {min, max}
	color: string,
	minY: number?,
	minZ: number?,
	maxZ: number?,
	salt: number?,
}

export type Recipe = {
	name: string,
	bounds: { min: { number }, max: { number } },
	palette: { [string]: number },
	flat: { [string]: boolean }?,
	ops: { Op },
	scatter: { Scatter }?,
}

-- Palette ----------------------------------------------------------------------------------------------------

function VoxelGrid.newPalette(): Palette
	return { colors = {}, flat = {}, lookup = {}, keys = {} }
end

function VoxelGrid.paletteIndex(pal: Palette, rgb: number, flat: boolean?): number
	local key = rgb + (if flat then 0x1000000 else 0)
	local i = pal.lookup[key]
	if i then
		return i
	end
	i = #pal.colors + 1
	assert(i <= 255, "VoxelGrid: palette is full (255 colours)")
	pal.colors[i] = rgb
	pal.flat[i] = flat == true
	pal.lookup[key] = i
	return i
end

local function keyIndex(pal: Palette, recipe: Recipe, name: string): number
	local i = pal.keys[name]
	if i then
		return i
	end
	local rgb = recipe.palette[name]
	assert(rgb ~= nil, `VoxelGrid: recipe '{recipe.name}' uses unknown colour '{name}'`)
	i = VoxelGrid.paletteIndex(pal, rgb, recipe.flat ~= nil and recipe.flat[name] == true)
	pal.keys[name] = i
	return i
end

-- Grid basics ------------------------------------------------------------------------------------------------

function VoxelGrid.new(nx: number, ny: number, nz: number, palette: Palette?): Grid
	local sx, sy, sz = nx + 2, ny + 2, nz + 2
	return {
		nx = nx,
		ny = ny,
		nz = nz,
		sx = sx,
		sy = sy,
		sz = sz,
		cells = buffer.create(sx * sy * sz),
		pieces = nil,
		palette = palette or VoxelGrid.newPalette(),
	}
end

function VoxelGrid.index(g: Grid, x: number, y: number, z: number): number
	return (x + 1) + g.sx * ((y + 1) + g.sy * (z + 1))
end

-- Inverse of index for interior cells.
function VoxelGrid.coords(g: Grid, i: number): (number, number, number)
	local sx, sy = g.sx, g.sy
	local x = i % sx
	local r = (i - x) // sx
	local y = r % sy
	local z = (r - y) // sy
	return x - 1, y - 1, z - 1
end

function VoxelGrid.get(g: Grid, x: number, y: number, z: number): number
	if x < 0 or y < 0 or z < 0 or x >= g.nx or y >= g.ny or z >= g.nz then
		return 0
	end
	return buffer.readu8(g.cells, (x + 1) + g.sx * ((y + 1) + g.sy * (z + 1)))
end

function VoxelGrid.set(g: Grid, x: number, y: number, z: number, c: number)
	if x < 0 or y < 0 or z < 0 or x >= g.nx or y >= g.ny or z >= g.nz then
		return
	end
	buffer.writeu8(g.cells, (x + 1) + g.sx * ((y + 1) + g.sy * (z + 1)), c)
end

function VoxelGrid.fillBox(g: Grid, x0: number, y0: number, z0: number, x1: number, y1: number, z1: number, c: number)
	for z = math.max(z0, 0), math.min(z1, g.nz - 1) do
		for y = math.max(y0, 0), math.min(y1, g.ny - 1) do
			for x = math.max(x0, 0), math.min(x1, g.nx - 1) do
				buffer.writeu8(g.cells, (x + 1) + g.sx * ((y + 1) + g.sy * (z + 1)), c)
			end
		end
	end
end

function VoxelGrid.clone(g: Grid): Grid
	local c = buffer.create(buffer.len(g.cells))
	buffer.copy(c, 0, g.cells)
	local p: buffer? = nil
	local gp = g.pieces
	if gp then
		local pb = buffer.create(buffer.len(gp))
		buffer.copy(pb, 0, gp)
		p = pb
	end
	return { nx = g.nx, ny = g.ny, nz = g.nz, sx = g.sx, sy = g.sy, sz = g.sz, cells = c, pieces = p, palette = g.palette }
end

function VoxelGrid.count(g: Grid): number
	local n, cells = 0, g.cells
	for i = 0, buffer.len(cells) - 1 do
		if buffer.readu8(cells, i) ~= 0 then
			n += 1
		end
	end
	return n
end

-- FNV-1a over the cell bytes: a cheap determinism fingerprint.
function VoxelGrid.hash(g: Grid): number
	local h, cells = 2166136261, g.cells
	for i = 0, buffer.len(cells) - 1 do
		h = bit32.bxor(h, buffer.readu8(cells, i))
		-- h * 16777619 mod 2^32, split so the product stays exact in a double
		h = (bit32.band(h, 0xFFFF) * 16777619 + (bit32.rshift(h, 16) * 16777619 % 65536) * 65536) % 4294967296
	end
	return h
end

function VoxelGrid.equals(a: Grid, b: Grid): boolean
	if a.nx ~= b.nx or a.ny ~= b.ny or a.nz ~= b.nz then
		return false
	end
	return buffer.tostring(a.cells) == buffer.tostring(b.cells)
end

-- A grid holding only the cells of one rigid piece (same dims, so world placement is unchanged).
function VoxelGrid.extractPiece(g: Grid, piece: number): Grid
	local out = VoxelGrid.new(g.nx, g.ny, g.nz, g.palette)
	local gp = g.pieces
	if not gp then
		if piece == 0 then
			buffer.copy(out.cells, 0, g.cells)
		end
		return out
	end
	local src, dst = g.cells, out.cells
	for i = 0, buffer.len(src) - 1 do
		if buffer.readu8(gp, i) == piece then
			buffer.writeu8(dst, i, buffer.readu8(src, i))
		end
	end
	return out
end

-- Deterministic RNG -------------------------------------------------------------------------------------------

local function mul32(a: number, b: number): number
	return (bit32.band(a, 0xFFFF) * b + (bit32.rshift(a, 16) * b % 65536) * 65536) % 4294967296
end

local function mix32(x: number): number
	x = bit32.bxor(x, bit32.rshift(x, 16))
	x = mul32(x, 0x7FEB352D)
	x = bit32.bxor(x, bit32.rshift(x, 15))
	x = mul32(x, 0x846CA68B)
	return bit32.bxor(x, bit32.rshift(x, 16))
end

export type Rng = { state: number }

function VoxelGrid.rng(seed: number): Rng
	return { state = mix32(bit32.bor(0, math.floor(seed) % 4294967296) + 0x9E3779B9) }
end

-- Uniform in [0, 1).
function VoxelGrid.random(r: Rng): number
	r.state = (mul32(r.state, 1664525) + 1013904223) % 4294967296
	return mix32(r.state) / 4294967296
end

-- SDF primitives and blends (all exact except the ellipsoid, which uses the usual bound k0*(k0-1)/k1) ----------

function VoxelGrid.sdSphere(px: number, py: number, pz: number, cx: number, cy: number, cz: number, r: number): number
	local dx, dy, dz = px - cx, py - cy, pz - cz
	return math.sqrt(dx * dx + dy * dy + dz * dz) - r
end

function VoxelGrid.sdEllipsoid(px: number, py: number, pz: number, cx: number, cy: number, cz: number, rx: number, ry: number, rz: number): number
	local dx, dy, dz = px - cx, py - cy, pz - cz
	local ax, ay, az = dx / rx, dy / ry, dz / rz
	local k0 = math.sqrt(ax * ax + ay * ay + az * az)
	local bx, by, bz = ax / rx, ay / ry, az / rz
	local k1 = math.sqrt(bx * bx + by * by + bz * bz)
	if k1 < 1e-9 then
		return -math.min(rx, ry, rz)
	end
	return k0 * (k0 - 1) / k1
end

function VoxelGrid.sdBox(px: number, py: number, pz: number, cx: number, cy: number, cz: number, hx: number, hy: number, hz: number, round: number?): number
	local rr = round or 0
	local qx, qy, qz = math.abs(px - cx) - hx + rr, math.abs(py - cy) - hy + rr, math.abs(pz - cz) - hz + rr
	local mx, my, mz = math.max(qx, 0), math.max(qy, 0), math.max(qz, 0)
	return math.sqrt(mx * mx + my * my + mz * mz) + math.min(math.max(qx, qy, qz), 0) - rr
end

function VoxelGrid.sdCapsule(px: number, py: number, pz: number, ax: number, ay: number, az: number, bx: number, by: number, bz: number, r: number): number
	local pax, pay, paz = px - ax, py - ay, pz - az
	local bax, bay, baz = bx - ax, by - ay, bz - az
	local bb = bax * bax + bay * bay + baz * baz
	local t = if bb > 0 then math.clamp((pax * bax + pay * bay + paz * baz) / bb, 0, 1) else 0
	local dx, dy, dz = pax - bax * t, pay - bay * t, paz - baz * t
	return math.sqrt(dx * dx + dy * dy + dz * dz) - r
end

-- Quadratic smooth minimum: equals min(a, b) whenever |a - b| >= k.
function VoxelGrid.smin(a: number, b: number, k: number): number
	if k <= 0 then
		return math.min(a, b)
	end
	local h = math.max(k - math.abs(a - b), 0) / k
	return math.min(a, b) - h * h * k * 0.25
end

function VoxelGrid.smax(a: number, b: number, k: number): number
	return -VoxelGrid.smin(-a, -b, k)
end

local sdSphere, sdEllipsoid, sdBox, sdCapsule, smin = VoxelGrid.sdSphere, VoxelGrid.sdEllipsoid, VoxelGrid.sdBox, VoxelGrid.sdCapsule, VoxelGrid.smin

-- Recipe evaluation -------------------------------------------------------------------------------------------

local OP_UNION, OP_SUB, OP_INTER, OP_PAINT = 1, 2, 3, 4
local SH_SPHERE, SH_ELL, SH_BOX, SH_CAP = 1, 2, 3, 4
local OPCODE = { union = OP_UNION, subtract = OP_SUB, intersect = OP_INTER, paint = OP_PAINT }
local SHAPE = { sphere = SH_SPHERE, ellipsoid = SH_ELL, box = SH_BOX, capsule = SH_CAP }

-- Expands seeded scatter entries into paint ops (deterministic for a seed).
function VoxelGrid.expandRecipe(recipe: Recipe, seed: number): { Op }
	local ops = table.clone(recipe.ops)
	local scatter = recipe.scatter
	if not scatter then
		return ops
	end
	for si, s in scatter do
		local rng = VoxelGrid.rng(seed * 7919 + si * 104729 + (s.salt or 0))
		local placed, attempts = 0, 0
		while placed < s.count and attempts < s.count * 40 do
			attempts += 1
			local u, v = VoxelGrid.random(rng), VoxelGrid.random(rng)
			local theta, cphi = u * 2 * math.pi, 2 * v - 1
			local sphi = math.sqrt(1 - cphi * cphi)
			local c, r = s.around.c, s.around.r
			local x, y, z = c[1] + r[1] * sphi * math.cos(theta), c[2] + r[2] * cphi, c[3] + r[3] * sphi * math.sin(theta)
			if (s.minY and y < s.minY) or (s.minZ and z < s.minZ) or (s.maxZ and z > s.maxZ) then
				continue
			end
			local rad = s.radius[1] + (s.radius[2] - s.radius[1]) * VoxelGrid.random(rng)
			table.insert(ops, { op = "paint", shape = "sphere", c = { x, y, z }, r = rad, color = s.color })
			placed += 1
		end
	end
	return ops
end

type Compiled = {
	n: number,
	opc: { number },
	shp: { number },
	k: { number },
	col: { number },
	pce: { number }, -- -1 = keep
	p: { { number } }, -- shape params
	lo: { { number } }, -- bbox min
	hi: { { number } }, -- bbox max
}

local function compile(recipe: Recipe, ops: { Op }, pal: Palette, pieceNames: { string }): Compiled
	local cc: Compiled = { n = #ops, opc = {}, shp = {}, k = {}, col = {}, pce = {}, p = {}, lo = {}, hi = {} }
	for i, o in ops do
		local opc = OPCODE[o.op]
		local shp = SHAPE[o.shape]
		assert(opc and shp, `VoxelGrid: bad op {o.op}/{o.shape} in '{recipe.name}'`)
		cc.opc[i], cc.shp[i], cc.k[i] = opc, shp, o.k or 0
		cc.col[i] = if o.color then keyIndex(pal, recipe, o.color) else 0
		local pc = -1
		if o.piece then
			pc = table.find(pieceNames, o.piece) or 0
			if pc == 0 then
				table.insert(pieceNames, o.piece)
				pc = #pieceNames
			end
		end
		cc.pce[i] = pc
		local lo, hi, p
		if shp == SH_SPHERE then
			local c, r = o.c :: { number }, o.r :: number
			p = { c[1], c[2], c[3], r }
			lo, hi = { c[1] - r, c[2] - r, c[3] - r }, { c[1] + r, c[2] + r, c[3] + r }
		elseif shp == SH_ELL then
			local c, r = o.c :: { number }, o.r :: { number }
			p = { c[1], c[2], c[3], r[1], r[2], r[3] }
			lo, hi = { c[1] - r[1], c[2] - r[2], c[3] - r[3] }, { c[1] + r[1], c[2] + r[2], c[3] + r[3] }
		elseif shp == SH_BOX then
			local c, h = o.c :: { number }, o.h :: { number }
			p = { c[1], c[2], c[3], h[1], h[2], h[3], o.round or 0 }
			lo, hi = { c[1] - h[1], c[2] - h[2], c[3] - h[3] }, { c[1] + h[1], c[2] + h[2], c[3] + h[3] }
		else
			local a, b, r = o.a :: { number }, o.b :: { number }, o.r :: number
			p = { a[1], a[2], a[3], b[1], b[2], b[3], r }
			lo = { math.min(a[1], b[1]) - r, math.min(a[2], b[2]) - r, math.min(a[3], b[3]) - r }
			hi = { math.max(a[1], b[1]) + r, math.max(a[2], b[2]) + r, math.max(a[3], b[3]) + r }
		end
		cc.p[i], cc.lo[i], cc.hi[i] = p, lo, hi
	end
	return cc
end

local function evalShape(shp: number, p: { number }, x: number, y: number, z: number): number
	if shp == SH_SPHERE then
		return sdSphere(x, y, z, p[1], p[2], p[3], p[4])
	elseif shp == SH_ELL then
		return sdEllipsoid(x, y, z, p[1], p[2], p[3], p[4], p[5], p[6])
	elseif shp == SH_BOX then
		return sdBox(x, y, z, p[1], p[2], p[3], p[4], p[5], p[6], p[7])
	end
	return sdCapsule(x, y, z, p[1], p[2], p[3], p[4], p[5], p[6], p[7])
end

-- Grid dimensions for a recipe: `res` voxels along the bounds' longest axis.
function VoxelGrid.dimsFor(bounds: { min: { number }, max: { number } }, res: number): (number, number, number, number)
	local ex, ey, ez = bounds.max[1] - bounds.min[1], bounds.max[2] - bounds.min[2], bounds.max[3] - bounds.min[3]
	local cell = math.max(ex, ey, ez) / res
	return math.max(1, math.ceil(ex / cell - 1e-6)), math.max(1, math.ceil(ey / cell - 1e-6)), math.max(1, math.ceil(ez / cell - 1e-6)), cell
end

export type EvalOptions = { seed: number?, palette: Palette?, bounds: { min: { number }, max: { number } }? }

-- Samples the recipe's combined SDF at every cell centre. Primitives whose bounding box cannot change the running
-- result are skipped; the skip test is exact for union / subtract / paint because smin(a, b, k) == a when b >= a + k.
function VoxelGrid.evalRecipe(recipe: Recipe, res: number, opts: EvalOptions?): Field
	local o: EvalOptions = opts or {}
	local pal = o.palette or VoxelGrid.newPalette()
	local bounds = o.bounds or recipe.bounds
	local nx, ny, nz, cell = VoxelGrid.dimsFor(bounds, res)
	local ox, oy, oz = bounds.min[1], bounds.min[2], bounds.min[3]
	local pieceNames: { string } = {}
	local cc = compile(recipe, VoxelGrid.expandRecipe(recipe, o.seed or 1), pal, pieceNames)
	local total = nx * ny * nz
	local dist, color, piece = buffer.create(total * 4), buffer.create(total), buffer.create(total)
	local n, opc, shp, kk, col, pce, prm, lo, hi = cc.n, cc.opc, cc.shp, cc.k, cc.col, cc.pce, cc.p, cc.lo, cc.hi
	local INF = math.huge
	local i = 0
	for z = 0, nz - 1 do
		local pz = oz + (z + 0.5) * cell
		for y = 0, ny - 1 do
			local py = oy + (y + 0.5) * cell
			for x = 0, nx - 1 do
				local px = ox + (x + 0.5) * cell
				local d, c, pc = INF, 0, 0
				for j = 1, n do
					local l, h = lo[j], hi[j]
					-- distance from p to the primitive's bounding box: a lower bound on its SDF
					local qx = math.max(l[1] - px, px - h[1], 0)
					local qy = math.max(l[2] - py, py - h[2], 0)
					local qz = math.max(l[3] - pz, pz - h[3], 0)
					local lb = math.sqrt(qx * qx + qy * qy + qz * qz)
					local code, k = opc[j], kk[j]
					if code == OP_UNION then
						if lb >= d + k then
							continue
						end
						local s = evalShape(shp[j], prm[j], px, py, pz)
						if s < d then
							if col[j] ~= 0 then
								c = col[j]
							end
							if pce[j] >= 0 then
								pc = pce[j]
							end
						end
						d = smin(d, s, k)
					elseif code == OP_PAINT then
						if lb > 0 or d > 0 then
							continue
						end
						if evalShape(shp[j], prm[j], px, py, pz) <= 0 then
							if col[j] ~= 0 then
								c = col[j]
							end
							if pce[j] >= 0 then
								pc = pce[j]
							end
						end
					elseif code == OP_SUB then
						if lb >= k - d then
							continue
						end
						local s = evalShape(shp[j], prm[j], px, py, pz)
						d = -smin(-d, s, k)
					else -- intersect: no cheap skip
						local s = evalShape(shp[j], prm[j], px, py, pz)
						d = -smin(-d, -s, k)
					end
				end
				buffer.writef32(dist, i * 4, d)
				buffer.writeu8(color, i, if c == 0 then 1 else c)
				buffer.writeu8(piece, i, pc)
				i += 1
			end
		end
	end
	if #pal.colors == 0 then
		VoxelGrid.paletteIndex(pal, 0x808080, false)
	end
	return { nx = nx, ny = ny, nz = nz, cell = cell, ox = ox, oy = oy, oz = oz, dist = dist, color = color, piece = piece, palette = pal, pieceNames = pieceNames }
end

-- Voxelize: a cell is solid where the distance is <= 0.
function VoxelGrid.fromField(f: Field): Grid
	local g = VoxelGrid.new(f.nx, f.ny, f.nz, f.palette)
	local pieces = buffer.create(buffer.len(g.cells))
	local anyPiece = false
	local cells, sx, sy = g.cells, g.sx, g.sy
	local i = 0
	for z = 0, f.nz - 1 do
		for y = 0, f.ny - 1 do
			local row = 1 + sx * ((y + 1) + sy * (z + 1))
			for x = 0, f.nx - 1 do
				if buffer.readf32(f.dist, i * 4) <= 0 then
					buffer.writeu8(cells, row + x, buffer.readu8(f.color, i))
					local pc = buffer.readu8(f.piece, i)
					if pc ~= 0 then
						buffer.writeu8(pieces, row + x, pc)
						anyPiece = true
					end
				end
				i += 1
			end
		end
	end
	if anyPiece then
		g.pieces = pieces
	end
	return g
end

-- Connectivity (26-neighbourhood) ------------------------------------------------------------------------------

local scratchLabels: buffer = buffer.create(0)
local scratchStack: buffer = buffer.create(0)

local function ensureScratch(bytes: number)
	if buffer.len(scratchLabels) < bytes then
		scratchLabels = buffer.create(bytes)
		scratchStack = buffer.create(bytes)
	end
end

function VoxelGrid.offsets26(g: Grid): { number }
	local o = table.create(26)
	for dz = -1, 1 do
		for dy = -1, 1 do
			for dx = -1, 1 do
				if dx ~= 0 or dy ~= 0 or dz ~= 0 then
					table.insert(o, dx + g.sx * (dy + g.sy * dz))
				end
			end
		end
	end
	return o
end

-- Labels every 26-connected solid component. Returns the component count, a u32 label buffer (padded indexing,
-- 0 = empty; valid until the next call), and the size of each component.
function VoxelGrid.components(g: Grid): (number, buffer, { number })
	local cells = g.cells
	local total = buffer.len(cells)
	ensureScratch(total * 4)
	local labels, stack = scratchLabels, scratchStack
	buffer.fill(labels, 0, 0, total * 4)
	local off = VoxelGrid.offsets26(g)
	local sizes: { number } = {}
	local count = 0
	for i = 0, total - 1 do
		if buffer.readu8(cells, i) == 0 or buffer.readu32(labels, i * 4) ~= 0 then
			continue
		end
		count += 1
		local size, sp = 0, 1
		buffer.writeu32(stack, 0, i)
		buffer.writeu32(labels, i * 4, count)
		while sp > 0 do
			sp -= 1
			local c = buffer.readu32(stack, sp * 4)
			size += 1
			for k = 1, 26 do
				local nb = c + off[k]
				if buffer.readu8(cells, nb) ~= 0 and buffer.readu32(labels, nb * 4) == 0 then
					buffer.writeu32(labels, nb * 4, count)
					buffer.writeu32(stack, sp * 4, nb)
					sp += 1
				end
			end
		end
		sizes[count] = size
	end
	return count, labels, sizes
end

-- Removes every cell not 26-connected to the kept component: the one containing `keepIndex` (padded index) if it
-- is solid, else the largest. Returns the number of cells removed.
function VoxelGrid.dropIslands(g: Grid, keepIndex: number?): number
	local count, labels, sizes = VoxelGrid.components(g)
	if count <= 1 then
		return 0
	end
	local keep = 0
	if keepIndex and buffer.readu8(g.cells, keepIndex) ~= 0 then
		keep = buffer.readu32(labels, keepIndex * 4)
	else
		local best = -1
		for l = 1, count do
			if sizes[l] > best then
				best, keep = sizes[l], l
			end
		end
	end
	local removed, cells = 0, g.cells
	local gp = g.pieces
	for i = 0, buffer.len(cells) - 1 do
		local l = buffer.readu32(labels, i * 4)
		if l ~= 0 and l ~= keep then
			buffer.writeu8(cells, i, 0)
			if gp then
				buffer.writeu8(gp, i, 0)
			end
			removed += 1
		end
	end
	return removed
end

-- Palette quantisation -----------------------------------------------------------------------------------------

local function rgbDist2(a: number, b: number): number
	local ar, ag, ab = bit32.rshift(a, 16), bit32.band(bit32.rshift(a, 8), 255), bit32.band(a, 255)
	local br, bg, bb = bit32.rshift(b, 16), bit32.band(bit32.rshift(b, 8), 255), bit32.band(b, 255)
	local rm = (ar + br) * 0.5
	local dr, dg, db = ar - br, ag - bg, ab - bb
	-- "redmean" weighting: a cheap step towards perceptual distance
	return (2 + rm / 256) * dr * dr + 4 * dg * dg + (2 + (255 - rm) / 256) * db * db
end

-- Snaps the colours actually used by the grid down to at most maxColors (default 16). Each merge folds the less
-- used colour of the cheapest pair (Ward cost) into the more used one, so every surviving colour is an authored
-- one. Flat (unstudded) colours only merge with flat colours unless nothing else is left. Returns merges done.
function VoxelGrid.quantise(g: Grid, maxColors: number?): number
	local limit = maxColors or 16
	local cells, pal = g.cells, g.palette
	local counts: { number } = table.create(#pal.colors, 0)
	for i = 0, buffer.len(cells) - 1 do
		local c = buffer.readu8(cells, i)
		if c ~= 0 then
			counts[c] = (counts[c] or 0) + 1
		end
	end
	local active: { number } = {}
	for c = 1, #pal.colors do
		if (counts[c] or 0) > 0 then
			table.insert(active, c)
		end
	end
	local remap: { number } = table.create(#pal.colors, 0)
	for c = 1, #pal.colors do
		remap[c] = c
	end
	local merges = 0
	while #active > limit do
		local bi, bj, best = 0, 0, math.huge
		for i = 1, #active do
			for j = i + 1, #active do
				local a, b = active[i], active[j]
				local na, nb = counts[a], counts[b]
				local cost = na * nb / (na + nb) * rgbDist2(pal.colors[a], pal.colors[b])
				if pal.flat[a] ~= pal.flat[b] then
					cost += 1e12
				end
				if cost < best then
					best, bi, bj = cost, i, j
				end
			end
		end
		local a, b = active[bi], active[bj]
		local keepC, dropC, dropAt = a, b, bj
		if counts[b] > counts[a] then
			keepC, dropC, dropAt = b, a, bi
		end
		counts[keepC] += counts[dropC]
		counts[dropC] = 0
		for c = 1, #remap do
			if remap[c] == dropC then
				remap[c] = keepC
			end
		end
		table.remove(active, dropAt)
		merges += 1
	end
	if merges > 0 then
		for i = 0, buffer.len(cells) - 1 do
			local c = buffer.readu8(cells, i)
			if c ~= 0 and remap[c] ~= c then
				buffer.writeu8(cells, i, remap[c])
			end
		end
	end
	return merges
end

function VoxelGrid.colorsUsed(g: Grid): number
	local seen, n, cells = {}, 0, g.cells
	for i = 0, buffer.len(cells) - 1 do
		local c = buffer.readu8(cells, i)
		if c ~= 0 and not seen[c] then
			seen[c] = true
			n += 1
		end
	end
	return n
end

-- One call: recipe -> field -> voxels -> drop islands -> <= maxColors colours.
export type SculptOptions = { seed: number?, palette: Palette?, bounds: { min: { number }, max: { number } }?, keepIslands: boolean?, maxColors: number? }

function VoxelGrid.sculpt(recipe: Recipe, res: number, opts: SculptOptions?): (Grid, Field)
	local o: SculptOptions = opts or {}
	local f = VoxelGrid.evalRecipe(recipe, res, { seed = o.seed, palette = o.palette, bounds = o.bounds })
	local g = VoxelGrid.fromField(f)
	if not o.keepIslands then
		VoxelGrid.dropIslands(g)
	end
	VoxelGrid.quantise(g, o.maxColors or 16)
	return g, f
end

return VoxelGrid
