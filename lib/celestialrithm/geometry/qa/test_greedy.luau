--!strict
-- GreedyMesher checks: surface area, watertightness, winding, world-aligned stud UVs, chunked meshing, tri-budget
-- splitting and determinism. Run: lune run lib/celestialrithm/geometry/qa/test_greedy.luau
local Check = require("./Check")
local Out = Check.Out
local VoxelGrid = require("../VoxelGrid")
local GreedyMesher = require("../GreedyMesher")
local SampleModels = require("../SampleModels")

local slime = VoxelGrid.sculpt(SampleModels.StudSlime, 32, { seed = 1 })
local chest = VoxelGrid.sculpt(SampleModels.RewardChest, 32, { seed = 1 })

-- Area: greedy quads cover exactly the naive exposed faces ------------------------------------------------------
for name, g in { slime = slime, chest = chest } do
	local naiveFaces = GreedyMesher.exposedFaces(g)
	local greedy = GreedyMesher.mesh(g)
	local naive = GreedyMesher.mesh(g, { greedy = false })
	Out.check(`greedy.area_equals_naive.{name}`, math.abs(GreedyMesher.area(greedy) - naiveFaces) < 1e-6 and naive.quads == naiveFaces, `greedy area {GreedyMesher.area(greedy)}, naive faces {naiveFaces}, naive quads {naive.quads}`)
	Out.check(`greedy.fewer_tris.{name}`, greedy.tcount < naive.tcount, `greedy {greedy.tcount} tris vs naive {naive.tcount} ({string.format("%.2f", naive.tcount / greedy.tcount)}x)`)
	-- scaled voxels: area in voxel units is unchanged
	local scaled = GreedyMesher.mesh(g, { voxelSize = 0.5, origin = { 3, 1, 2 } })
	Out.check(`greedy.area_scaled.{name}`, math.abs(GreedyMesher.area(scaled, 0.5) - naiveFaces) < 1e-3)
end

-- Watertight ---------------------------------------------------------------------------------------------------
do
	local box = VoxelGrid.new(8, 8, 8)
	VoxelGrid.paletteIndex(box.palette, 0xFF0000)
	VoxelGrid.fillBox(box, 1, 2, 1, 5, 6, 4, 1)
	local naive = GreedyMesher.mesh(box, { greedy = false })
	local bad, total, maxMul = Check.balance(Check.directedEdges(naive))
	-- each undirected edge: one per direction, so multiplicity exactly 2
	local exact2 = true
	local edges = Check.directedEdges(naive)
	for id, n in edges do
		local a, b = id:match("^(.-)|(.*)$")
		if n ~= 1 or (edges[(b :: string) .. "|" .. (a :: string)] or 0) ~= 1 then
			exact2 = false
			break
		end
	end
	Out.check("watertight.box_naive_each_edge_2_tris", bad == 0 and exact2 and maxMul == 2, `{total} directed edges, unmatched {bad}`)
	local greedy = GreedyMesher.mesh(box)
	local gbad, _, gmax = Check.balance(Check.directedEdges(greedy))
	Out.check("watertight.box_greedy_each_edge_2_tris", gbad == 0 and gmax == 2 and greedy.quads == 6, `{greedy.quads} quads`)
end
for name, g in { slime = slime, chest = chest } do
	local naive = GreedyMesher.mesh(g, { greedy = false })
	local bad, total, maxMul = Check.balance(Check.directedEdges(naive))
	Out.check(`watertight.naive_directed_balance.{name}`, bad == 0, `{total} directed edges, unmatched {bad}, max multiplicity {maxMul} (4 = two voxels touching only along an edge, 26-connected)`)
	local greedy = GreedyMesher.mesh(g)
	local gbad, gtotal = Check.balance(Check.unitSegments(greedy, 1))
	Out.check(`watertight.greedy_unit_segment_balance.{name}`, gbad == 0, `{gtotal} unit segments, unmatched {gbad} (greedy has T-junctions; closed at lattice resolution)`)
	local split = GreedyMesher.mesh(g, { splitEvery = 4 })
	local sbad = Check.balance(Check.unitSegments(split, 1))
	Out.check(`watertight.greedy_split4_balance.{name}`, sbad == 0, `{split.tcount} tris with splitEvery 4 (vs {greedy.tcount})`)
end

-- Winding and normals: (p1 - p0) x (p2 - p0) along the normal, and the normal points from solid into empty --------
do
	local m = GreedyMesher.mesh(slime)
	local badWind, badSide = 0, 0
	for t = 0, m.tcount - 1 do
		local v0, v1, v2 = buffer.readu32(m.idx, t * 12), buffer.readu32(m.idx, t * 12 + 4), buffer.readu32(m.idx, t * 12 + 8)
		local ax, ay, az = Check.vtx(m, v0)
		local bx, by, bz = Check.vtx(m, v1)
		local cx, cy, cz = Check.vtx(m, v2)
		local ux, uy, uz, wx, wy, wz = bx - ax, by - ay, bz - az, cx - ax, cy - ay, cz - az
		local nx, ny, nz = uy * wz - uz * wy, uz * wx - ux * wz, ux * wy - uy * wx
		local fx, fy, fz = buffer.readf32(m.nrm, v0 * 12), buffer.readf32(m.nrm, v0 * 12 + 4), buffer.readf32(m.nrm, v0 * 12 + 8)
		if nx * fx + ny * fy + nz * fz <= 0 then
			badWind += 1
		end
		-- probe half a voxel either side of the triangle centroid
		local mx, my, mz = (ax + bx + cx) / 3, (ay + by + cy) / 3, (az + bz + cz) / 3
		local outside = VoxelGrid.get(slime, math.floor(mx + fx * 0.5), math.floor(my + fy * 0.5), math.floor(mz + fz * 0.5))
		local inside = VoxelGrid.get(slime, math.floor(mx - fx * 0.5), math.floor(my - fy * 0.5), math.floor(mz - fz * 0.5))
		if outside ~= 0 or inside == 0 then
			badSide += 1
		end
	end
	Out.check("winding.outward_ccw", badWind == 0, `{m.tcount} tris, {badWind} wound inward`)
	Out.check("normals.solid_to_empty", badSide == 0, `{badSide} misplaced`)
end

-- World-aligned stud UVs: u, v = lattice coordinate on the face's in-plane axes x studsPerVoxel ------------------
do
	local spv = 0.5
	local m = GreedyMesher.mesh(slime, { studsPerVoxel = spv, voxelSize = 2, origin = { 0, 0, 0 } })
	local bad, flat = 0, 0
	for q = 0, m.quads - 1 do
		local axis = buffer.readu8(m.qaxis, q) // 2
		local u, v = (axis + 1) % 3, (axis + 2) % 3
		local isFlat = slime.palette.flat[buffer.readu8(m.qcolor, q)]
		for k = 0, 3 do
			local vi = q * 4 + k
			local p = { Check.vtx(m, vi) }
			local eu, ev = p[u + 1] / 2 * spv, p[v + 1] / 2 * spv
			local au, av = buffer.readf32(m.uv, vi * 8), buffer.readf32(m.uv, vi * 8 + 4)
			if isFlat then
				flat += 1
				if math.abs(au - 0.04) > 1e-6 or math.abs(av - 0.04) > 1e-6 then
					bad += 1
				end
			elseif math.abs(au - eu) > 1e-4 or math.abs(av - ev) > 1e-4 then
				bad += 1
			end
		end
	end
	Out.check("uv.world_aligned_studs", bad == 0, `{m.vcount} vertices ({flat} on flat colours), {bad} off-grid`)
	-- continuity: two coplanar neighbouring quads give the same UV at a shared lattice point
	local seen: { [string]: string } = {}
	local clash = 0
	for vi = 0, m.vcount - 1 do
		local q = vi // 4
		if slime.palette.flat[buffer.readu8(m.qcolor, q)] then
			continue
		end
		local key = Check.key3(Check.vtx(m, vi)) .. "#" .. buffer.readu8(m.qaxis, q)
		local uv = string.format("%.4f,%.4f", buffer.readf32(m.uv, vi * 8), buffer.readf32(m.uv, vi * 8 + 4))
		if seen[key] and seen[key] ~= uv then
			clash += 1
		end
		seen[key] = uv
	end
	Out.check("uv.continuous_across_quads", clash == 0, `{clash} seams`)
end

-- Chunked meshing: chunks tile the surface exactly ---------------------------------------------------------------
do
	local total, quads = 0, 0
	for z0 = 0, slime.nz - 1, 8 do
		for y0 = 0, slime.ny - 1, 8 do
			for x0 = 0, slime.nx - 1, 8 do
				local m = GreedyMesher.mesh(slime, { x0 = x0, y0 = y0, z0 = z0, x1 = x0 + 8, y1 = y0 + 8, z1 = z0 + 8 })
				total += GreedyMesher.area(m)
				quads += m.quads
			end
		end
	end
	Out.check("chunks.tile_surface", math.abs(total - GreedyMesher.exposedFaces(slime)) < 1e-6, `8^3 chunks: area {total}, {quads} quads`)
end

-- Tri budget splitting -------------------------------------------------------------------------------------------
do
	local noisy = VoxelGrid.new(40, 40, 40)
	for c = 1, 6 do
		VoxelGrid.paletteIndex(noisy.palette, c * 0x203040)
	end
	local rng = VoxelGrid.rng(42)
	for z = 0, 39 do
		for y = 0, 39 do
			for x = 0, 39 do
				if VoxelGrid.random(rng) < 0.35 then
					VoxelGrid.set(noisy, x, y, z, 1 + math.floor(VoxelGrid.random(rng) * 6))
				end
			end
		end
	end
	local m = GreedyMesher.mesh(noisy)
	local budget = 2000
	local parts = GreedyMesher.split(m, budget)
	local ok, sumT, sumA, worst = true, 0, 0, 0
	for _, p in parts do
		ok = ok and p.tcount <= budget and p.vcount <= 60000
		sumT += p.tcount
		sumA += GreedyMesher.area(p)
		worst = math.max(worst, p.tcount)
	end
	Out.check("split.parts_within_budget", ok and sumT == m.tcount and math.abs(sumA - GreedyMesher.area(m)) < 1e-3, `{m.tcount} tris -> {#parts} parts, worst {worst} <= {budget}`)
	local cap = GreedyMesher.split(m, 20000)
	local capOk = true
	for _, p in cap do
		capOk = capOk and p.tcount <= 20000 and p.vcount <= 60000
	end
	Out.check("split.editablemesh_caps", capOk, `{#cap} parts under 20k tris / 60k verts`)
end

-- Determinism ----------------------------------------------------------------------------------------------------
do
	local a = VoxelGrid.sculpt(SampleModels.StudSlime, 32, { seed = 7 })
	local b = VoxelGrid.sculpt(SampleModels.StudSlime, 32, { seed = 7 })
	local c = VoxelGrid.sculpt(SampleModels.StudSlime, 32, { seed = 8 })
	local same = VoxelGrid.hash(a) == VoxelGrid.hash(b) and Check.meshKey(GreedyMesher.mesh(a)) == Check.meshKey(GreedyMesher.mesh(b))
	Out.check("determinism.same_seed_same_mesh", same, string.format("hash %08x", VoxelGrid.hash(a)))
	Out.check("determinism.seed_changes_spots", VoxelGrid.hash(a) ~= VoxelGrid.hash(c), string.format("seed 8 hash %08x", VoxelGrid.hash(c)))
end

Out.done()
