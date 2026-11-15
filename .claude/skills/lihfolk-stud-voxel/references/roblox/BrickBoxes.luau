--!strict
-- BrickBoxes: a brick (voxel) model as data, merged into as few boxes as possible, for building in Studio without Blender
-- or the 3D Importer. Pure Luau (no Roblox types), so it runs under lune: see BrickBoxes.test.luau.
-- Roblox side: BrickBuild.luau turns the result into studded Parts on the same bone/Motor6D rig ModelBuild makes,
-- so ModelAnimator plays clips on it unchanged.
--
-- Grid coords are 0-based: x right, y up, z back (front = -z, like the brick pipeline). One cell = one brick.
-- Each solid cell stores a palette index (1..255) and a bone index (1..255). 0 = empty.
--
-- Why boxes: only cells with an exposed face need covering, hidden cells are free filler, and one Part per merged box
-- is far fewer instances than one per brick. Same-size studded Parts also batch well.

local BrickBoxes = {}
BrickBoxes.__index = BrickBoxes

export type Grid = typeof(setmetatable(
	{} :: { nx: number, ny: number, nz: number, colour: buffer, bone: buffer },
	BrickBoxes
))
-- one merged box: inclusive cell range, palette index, bone index
export type Box = { x0: number, y0: number, z0: number, x1: number, y1: number, z1: number, colour: number, bone: number }

function BrickBoxes.new(nx: number, ny: number, nz: number): Grid
	assert(nx > 0 and ny > 0 and nz > 0, "grid size must be positive")
	return setmetatable(
		{ nx = nx, ny = ny, nz = nz, colour = buffer.create(nx * ny * nz), bone = buffer.create(nx * ny * nz) },
		BrickBoxes
	)
end

local function index(self: Grid, x: number, y: number, z: number): number
	return x + self.nx * (z + self.nz * y)
end

function BrickBoxes.inside(self: Grid, x: number, y: number, z: number): boolean
	return x >= 0 and y >= 0 and z >= 0 and x < self.nx and y < self.ny and z < self.nz
end

function BrickBoxes.get(self: Grid, x: number, y: number, z: number): number
	if not self:inside(x, y, z) then
		return 0
	end
	return buffer.readu8(self.colour, index(self, x, y, z))
end

-- colour 0 erases. Later writes win, so paint eyes after the head.
function BrickBoxes.set(self: Grid, x: number, y: number, z: number, colour: number, bone: number?)
	if not self:inside(x, y, z) then
		return
	end
	local i = index(self, x, y, z)
	buffer.writeu8(self.colour, i, colour)
	buffer.writeu8(self.bone, i, if colour == 0 then 0 else (bone or 1))
end

-- test(x, y, z) -> boolean is evaluated at cell centres inside the given inclusive range
function BrickBoxes.fill(
	self: Grid,
	x0: number, y0: number, z0: number,
	x1: number, y1: number, z1: number,
	colour: number, bone: number?,
	test: ((number, number, number) -> boolean)?
)
	for y = math.max(y0, 0), math.min(y1, self.ny - 1) do
		for z = math.max(z0, 0), math.min(z1, self.nz - 1) do
			for x = math.max(x0, 0), math.min(x1, self.nx - 1) do
				if not test or test(x + 0.5, y + 0.5, z + 0.5) then
					self:set(x, y, z, colour, bone)
				end
			end
		end
	end
end

-- stepped ellipsoid: centre and radii in cells
function BrickBoxes.ellipsoid(
	self: Grid,
	cx: number, cy: number, cz: number,
	rx: number, ry: number, rz: number,
	colour: number, bone: number?
)
	self:fill(
		math.floor(cx - rx), math.floor(cy - ry), math.floor(cz - rz),
		math.ceil(cx + rx), math.ceil(cy + ry), math.ceil(cz + rz),
		colour, bone,
		function(x, y, z)
			local a, b, c = (x - cx) / rx, (y - cy) / ry, (z - cz) / rz
			return a * a + b * b + c * c < 1
		end
	)
end

local function exposedMask(self: Grid): buffer
	local nx, ny, nz = self.nx, self.ny, self.nz
	local col = self.colour
	local out = buffer.create(nx * ny * nz)
	local sy = nx * nz
	for y = 0, ny - 1 do
		for z = 0, nz - 1 do
			for x = 0, nx - 1 do
				local i = x + nx * (z + nz * y)
				if buffer.readu8(col, i) ~= 0 then
					if
						x == 0 or x == nx - 1 or y == 0 or y == ny - 1 or z == 0 or z == nz - 1
						or buffer.readu8(col, i - 1) == 0 or buffer.readu8(col, i + 1) == 0
						or buffer.readu8(col, i - nx) == 0 or buffer.readu8(col, i + nx) == 0
						or buffer.readu8(col, i - sy) == 0 or buffer.readu8(col, i + sy) == 0
					then
						buffer.writeu8(out, i, 1)
					end
				end
			end
		end
	end
	return out
end

-- Greedy merge. Every exposed cell ends up in exactly one box of its own colour and bone; hidden cells may be
-- swallowed by any box of the same bone (they are never seen), and hidden cells nobody needs are left out.
function BrickBoxes.boxes(self: Grid): { Box }
	local nx, ny, nz = self.nx, self.ny, self.nz
	local col, bon = self.colour, self.bone
	local exposed = exposedMask(self)
	local done = buffer.create(nx * ny * nz)
	local out: { Box } = {}

	for y = 0, ny - 1 do
		for z = 0, nz - 1 do
			for x = 0, nx - 1 do
				local i0 = x + nx * (z + nz * y)
				if buffer.readu8(exposed, i0) == 1 and buffer.readu8(done, i0) == 0 then
					local c, b = buffer.readu8(col, i0), buffer.readu8(bon, i0)
					local function ok(i: number): boolean
						if buffer.readu8(bon, i) ~= b then
							return false -- empty cells have bone 0
						end
						if buffer.readu8(exposed, i) == 0 then
							return true
						end
						return buffer.readu8(col, i) == c and buffer.readu8(done, i) == 0
					end
					local x1 = x
					while x1 + 1 < nx and ok(i0 + (x1 + 1 - x)) do
						x1 += 1
					end
					local z1 = z
					while z1 + 1 < nz do
						local row = x + nx * (z1 + 1 + nz * y)
						local all = true
						for k = 0, x1 - x do
							if not ok(row + k) then
								all = false
								break
							end
						end
						if not all then
							break
						end
						z1 += 1
					end
					local y1 = y
					while y1 + 1 < ny do
						local all = true
						for zz = z, z1 do
							local row = x + nx * (zz + nz * (y1 + 1))
							for k = 0, x1 - x do
								if not ok(row + k) then
									all = false
									break
								end
							end
							if not all then
								break
							end
						end
						if not all then
							break
						end
						y1 += 1
					end
					for yy = y, y1 do
						for zz = z, z1 do
							local row = x + nx * (zz + nz * yy)
							for k = 0, x1 - x do
								if buffer.readu8(exposed, row + k) == 1 then
									buffer.writeu8(done, row + k, 1)
								end
							end
						end
					end
					table.insert(out, { x0 = x, y0 = y, z0 = z, x1 = x1, y1 = y1, z1 = z1, colour = c, bone = b })
				end
			end
		end
	end
	return out
end

-- Checks the skill's hard rules without rendering anything.
-- floating = solid cells not 26-connected to the largest piece (cells resting on y = 0 count as grounded when
-- groundOk is true: coins, rubble).
function BrickBoxes.lint(self: Grid, groundOk: boolean?): { bricks: number, exposed: number, colours: number, floating: number }
	local nx, ny, nz = self.nx, self.ny, self.nz
	local col = self.colour
	local n = nx * ny * nz
	local label = table.create(n, 0)
	local sizes: { number } = {}
	local grounded: { boolean } = {}
	local seen: { [number]: boolean } = {}
	local bricks, colours = 0, 0
	local stack: { number } = {}
	for start = 0, n - 1 do
		local c = buffer.readu8(col, start)
		if c ~= 0 then
			bricks += 1
			if not seen[c] then
				seen[c] = true
				colours += 1
			end
			if label[start + 1] == 0 then
				local id = #sizes + 1
				sizes[id], grounded[id] = 0, false
				label[start + 1] = id
				stack[1] = start
				local top = 1
				while top > 0 do
					local i = stack[top]
					top -= 1
					sizes[id] += 1
					local x = i % nx
					local z = (i // nx) % nz
					local y = i // (nx * nz)
					if y == 0 then
						grounded[id] = true
					end
					for dy = -1, 1 do
						for dz = -1, 1 do
							for dx = -1, 1 do
								local xx, yy, zz = x + dx, y + dy, z + dz
								if xx >= 0 and yy >= 0 and zz >= 0 and xx < nx and yy < ny and zz < nz then
									local j = xx + nx * (zz + nz * yy)
									if label[j + 1] == 0 and buffer.readu8(col, j) ~= 0 then
										label[j + 1] = id
										top += 1
										stack[top] = j
									end
								end
							end
						end
					end
				end
			end
		end
	end
	local biggest = 0
	for id, s in sizes do
		if s > (sizes[biggest] or 0) then
			biggest = id
		end
	end
	local floating = 0
	for id, s in sizes do
		if id ~= biggest and not (groundOk and grounded[id]) then
			floating += s
		end
	end
	local exposed = exposedMask(self)
	local ex = 0
	for i = 0, n - 1 do
		ex += buffer.readu8(exposed, i)
	end
	return { bricks = bricks, exposed = ex, colours = colours, floating = floating }
end

return BrickBoxes
