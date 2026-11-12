--!strict
--!native
--!optimize 2
-- VoxelMorph: blend two voxel models through their distance fields and re-voxelize, for a transformation moment.
--
--   d_t(cell) = (1 - t) * dA(cell) + t * dB(cell)          solid where d_t <= 0 (so it steps, voxel by voxel)
--   colour: cells solid in only one input keep that input's colour; cells in both (or in neither, i.e. new bridge
--   cells) switch from A to B when a fixed 4x4x4 ordered-dither threshold passes t, so the colour change sparkles
--   across the surface instead of popping. The same island cleanup as VoxelGrid.sculpt runs on every frame.
-- Endpoints are exact: t = 0 reproduces fromField(A) + dropIslands, t = 1 reproduces fromField(B) + dropIslands.
-- Both fields must come from one evaluation box and one palette: use fromRecipes. No palette quantise per frame
-- (keep the combined palette <= 16 colours; SampleModels does).
-- Pure Luau, no Roblox API.

local VoxelGrid = require("./VoxelGrid")

local VoxelMorph = {}

export type Morph = {
	a: VoxelGrid.Field,
	b: VoxelGrid.Field,
	out: VoxelGrid.Grid, -- reused for every sample
}

-- 4x4x4 ordered dither thresholds in [0, 1): a 3D extension of the 4x4 Bayer matrix.
local BAYER4 = { 0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5 }
local DITHER = table.create(64, 0)
for z = 0, 3 do
	for y = 0, 3 do
		for x = 0, 3 do
			local b2 = BAYER4[1 + x + 4 * y]
			local zb = ({ 0, 2, 3, 1 })[z + 1]
			DITHER[1 + x + 4 * y + 16 * z] = (b2 * 4 + zb + 0.5) / 64
		end
	end
end

function VoxelMorph.new(a: VoxelGrid.Field, b: VoxelGrid.Field): Morph
	assert(a.nx == b.nx and a.ny == b.ny and a.nz == b.nz, "VoxelMorph: fields must share dimensions")
	assert(a.palette == b.palette, "VoxelMorph: fields must share one palette")
	return { a = a, b = b, out = VoxelGrid.new(a.nx, a.ny, a.nz, a.palette) }
end

-- Evaluates both recipes over the union of their bounds into one palette.
function VoxelMorph.fromRecipes(ra: VoxelGrid.Recipe, rb: VoxelGrid.Recipe, res: number, seedA: number?, seedB: number?): Morph
	local mn, mx = {}, {}
	for k = 1, 3 do
		mn[k] = math.min(ra.bounds.min[k], rb.bounds.min[k])
		mx[k] = math.max(ra.bounds.max[k], rb.bounds.max[k])
	end
	local bounds = { min = mn, max = mx }
	local pal = VoxelGrid.newPalette()
	local fa = VoxelGrid.evalRecipe(ra, res, { seed = seedA, palette = pal, bounds = bounds })
	local fb = VoxelGrid.evalRecipe(rb, res, { seed = seedB, palette = pal, bounds = bounds })
	return VoxelMorph.new(fa, fb)
end

-- Writes frame t (clamped to [0, 1]) into m.out and returns it. Allocation-free apart from the island pass's
-- component-size table.
function VoxelMorph.sample(m: Morph, t: number, keepIslands: boolean?): VoxelGrid.Grid
	t = math.clamp(t, 0, 1)
	local a, b, g = m.a, m.b, m.out
	local da, db, ca, cb = a.dist, b.dist, a.color, b.color
	local cells, sx, sy = g.cells, g.sx, g.sy
	buffer.fill(cells, 0, 0)
	local s = 1 - t
	local i = 0
	for z = 0, a.nz - 1 do
		for y = 0, a.ny - 1 do
			local row = 1 + sx * ((y + 1) + sy * (z + 1))
			local dbase = 1 + 4 * (y % 4) + 16 * (z % 4)
			for x = 0, a.nx - 1 do
				local fa, fb = buffer.readf32(da, i * 4), buffer.readf32(db, i * 4)
				local d = if t == 0 then fa elseif t == 1 then fb else s * fa + t * fb
				if d <= 0 then
					local inA, inB = fa <= 0, fb <= 0
					local c
					if inA and not inB then
						c = buffer.readu8(ca, i)
					elseif inB and not inA then
						c = buffer.readu8(cb, i)
					elseif DITHER[dbase + x % 4] < t then
						c = buffer.readu8(cb, i)
					else
						c = buffer.readu8(ca, i)
					end
					buffer.writeu8(cells, row + x, c)
				end
				i += 1
			end
		end
	end
	if not keepIslands then
		VoxelGrid.dropIslands(g)
	end
	return g
end

return VoxelMorph
