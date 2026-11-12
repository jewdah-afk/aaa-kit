--!strict
-- VoxelGrid checks: SDF primitives and blends, 26-connected island removal, palette quantise, rigid pieces.
-- Run: lune run lib/celestialrithm/geometry/qa/test_voxelgrid.luau
local Check = require("./Check")
local Out = Check.Out
local VoxelGrid = require("../VoxelGrid")
local SampleModels = require("../SampleModels")

-- SDF primitives ---------------------------------------------------------------------------------------------------
do
	local ok = math.abs(VoxelGrid.sdSphere(3, 0, 0, 0, 0, 0, 2) - 1) < 1e-9
		and VoxelGrid.sdSphere(0, 0, 0, 0, 0, 0, 2) < 0
		and math.abs(VoxelGrid.sdBox(3, 0, 0, 0, 0, 0, 1, 1, 1) - 2) < 1e-9
		and math.abs(VoxelGrid.sdCapsule(0, 3, 0, 0, 0, 0, 0, 1, 0, 0.5) - 1.5) < 1e-9
		and math.abs(VoxelGrid.sdEllipsoid(4, 0, 0, 0, 0, 0, 2, 1, 1) - 2) < 1e-6
		and VoxelGrid.sdEllipsoid(0, 0.5, 0, 0, 0, 0, 2, 1, 1) < 0
	Out.check("sdf.primitives", ok)
	local far = VoxelGrid.smin(1, 5, 2) == 1
	local near = VoxelGrid.smin(1, 1.5, 2) < 1
	local hard = VoxelGrid.smin(1, 1.5, 0) == 1
	Out.check("sdf.smooth_min", far and near and hard and VoxelGrid.smax(1, 5, 2) == 5)
end

-- Island removal (26-connected) ------------------------------------------------------------------------------------
do
	local g = VoxelGrid.new(16, 16, 16)
	VoxelGrid.paletteIndex(g.palette, 0x55AA55)
	VoxelGrid.fillBox(g, 2, 2, 2, 9, 9, 9, 1) -- body: 512 cells
	VoxelGrid.set(g, 10, 10, 10, 1) -- touches the body only at a corner: 26-connected, must stay
	VoxelGrid.fillBox(g, 13, 13, 13, 14, 14, 14, 1) -- 8-cell island
	VoxelGrid.set(g, 0, 15, 0, 1) -- 1-cell island
	local count, _, sizes = VoxelGrid.components(g)
	table.sort(sizes)
	Out.check("flood.components_26", count == 3 and sizes[1] == 1 and sizes[2] == 8 and sizes[3] == 513, `{count} components: {table.concat(sizes, ", ")}`)
	local removed = VoxelGrid.dropIslands(g)
	Out.check("flood.removes_islands", removed == 9 and VoxelGrid.count(g) == 513 and VoxelGrid.get(g, 10, 10, 10) == 1, `removed {removed}, left {VoxelGrid.count(g)}`)
	-- keepIndex keeps the chosen component even if smaller
	local h = VoxelGrid.new(8, 8, 8)
	VoxelGrid.fillBox(h, 0, 0, 0, 3, 3, 3, 1)
	VoxelGrid.set(h, 7, 7, 7, 1)
	VoxelGrid.dropIslands(h, VoxelGrid.index(h, 7, 7, 7))
	Out.check("flood.keep_index", VoxelGrid.count(h) == 1 and VoxelGrid.get(h, 7, 7, 7) == 1)
	-- sculpted samples end as one component
	local s = VoxelGrid.sculpt(SampleModels.StudSlime, 48, { seed = 3 })
	local n = VoxelGrid.components(s)
	Out.check("flood.sample_single_component", n == 1, `{VoxelGrid.count(s)} cells`)
end

-- Palette quantise -------------------------------------------------------------------------------------------------
do
	local g = VoxelGrid.new(24, 4, 4)
	local rng = VoxelGrid.rng(5)
	local originals: { [number]: boolean } = {}
	for i = 1, 24 do
		local rgb = math.floor(VoxelGrid.random(rng) * 0xFFFFFF)
		originals[rgb] = true
		VoxelGrid.paletteIndex(g.palette, rgb, i == 24)
		VoxelGrid.fillBox(g, i - 1, 0, 0, i - 1, 3, if i % 3 == 0 then 3 else 1, i)
	end
	local merges = VoxelGrid.quantise(g, 16)
	local used: { [number]: boolean } = {}
	local allOriginal = true
	for i = 0, buffer.len(g.cells) - 1 do
		local c = buffer.readu8(g.cells, i)
		if c ~= 0 then
			used[c] = true
			allOriginal = allOriginal and originals[g.palette.colors[c]] == true
		end
	end
	local n = 0
	for _ in used do
		n += 1
	end
	Out.check("quantise.at_most_16", n <= 16 and merges == 8 and VoxelGrid.count(g) == 24 * 4 * 2 + 8 * 4 * 2, `{n} colours after {merges} merges`)
	Out.check("quantise.snaps_to_authored_colours", allOriginal)
	Out.check("quantise.flat_kept_separate", used[24] == true, "the only flat colour survives")
	local s = VoxelGrid.sculpt(SampleModels.StudSlime, 32, { seed = 1 })
	Out.check("quantise.sample_palette", VoxelGrid.colorsUsed(s) <= 16, `{VoxelGrid.colorsUsed(s)} colours`)
end

-- Recipes: seeded scatter and rigid pieces -------------------------------------------------------------------------
do
	local a = VoxelGrid.expandRecipe(SampleModels.StudSlime, 11)
	local b = VoxelGrid.expandRecipe(SampleModels.StudSlime, 11)
	local c = VoxelGrid.expandRecipe(SampleModels.StudSlime, 12)
	local same, diff = #a == #b, false
	for i = #SampleModels.StudSlime.ops + 1, #a do
		same = same and (a[i].c :: any)[1] == (b[i].c :: any)[1]
		diff = diff or (a[i].c :: any)[1] ~= (c[i].c :: any)[1]
	end
	Out.check("recipe.scatter_deterministic", same and diff and #a == #SampleModels.StudSlime.ops + 6, `{#a - #SampleModels.StudSlime.ops} spots`)
	local chest, field = VoxelGrid.sculpt(SampleModels.RewardChest, 32, { seed = 1 })
	local lidId = table.find(field.pieceNames, "lid")
	local body = VoxelGrid.extractPiece(chest, 0)
	local lid = VoxelGrid.extractPiece(chest, lidId or 99)
	Out.check("recipe.rigid_pieces", lidId ~= nil and VoxelGrid.count(lid) > 0 and VoxelGrid.count(body) + VoxelGrid.count(lid) == VoxelGrid.count(chest), `body {VoxelGrid.count(body)}, lid {VoxelGrid.count(lid)}`)
end

Out.done()
