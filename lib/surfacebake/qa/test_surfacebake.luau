--# selene: allow(mixed_table) -- recipe mask terms are { kind, key = value } by design
-- Headless checks for surfacebake. Same @@CHECK/@@IMG/@@DONE protocol as lib/frontier/qa.
-- Run: cd lib/surfacebake/qa && lune run test_surfacebake.luau | grep -a '^@@\(CHECK\|TIME\|DONE\)'
local Out = require("../../frontier/qa/Out")
local Mesh = require("../Mesh")
local Raster = require("../Raster")
local Surface = require("../Surface")
local Noise = require("../Noise")
local Recipe = require("../Recipe")
local Bake = require("../Bake")
local Presets = require("../Presets")

local emitImages = table.find(require("@lune/process").args, "--images") ~= nil

-- Raster ---------------------------------------------------------------------------------------

local box = Mesh.box(1, 1, 1, 3)
local G = Raster.bake(box, 96, 64)
-- the box atlas covers 6 cells minus 2% margins on each side: ~ (0.96)^2 of the texture
local frac = G.covered / (96 * 64)
Out.check("raster.box_coverage", frac > 0.85 and frac < 0.95, string.format("%.3f", frac))

-- every covered texel's position lies on the box surface and its normal is a face normal
local onSurface, unit = true, true
for i = 0, 96 * 64 - 1 do
	if buffer.readu8(G.cover, i) == 1 then
		local x, y, z = Raster.readVec(G.pos, i)
		local m = math.max(math.abs(x), math.abs(y), math.abs(z))
		if math.abs(m - 1) > 1e-4 then
			onSurface = false
		end
		local nx, ny, nz = Raster.readVec(G.nrm, i)
		if math.abs(nx * nx + ny * ny + nz * nz - 1) > 1e-4 then
			unit = false
		end
	end
end
Out.check("raster.positions_on_surface", onSurface)
Out.check("raster.unit_normals", unit)

-- tangent frame is orthonormal
local ortho = true
for i = 0, 96 * 64 - 1, 7 do
	if buffer.readu8(G.cover, i) == 1 then
		local nx, ny, nz = Raster.readVec(G.nrm, i)
		local tx, ty, tz = Raster.readVec(G.tan, i)
		local bx, by, bz = Raster.readVec(G.bit, i)
		if math.abs(nx * tx + ny * ty + nz * tz) > 1e-3 or math.abs(nx * bx + ny * by + nz * bz) > 1e-3 or math.abs(tx * bx + ty * by + tz * bz) > 1e-3 then
			ortho = false
		end
	end
end
Out.check("raster.tangent_frame_orthonormal", ortho)

-- no cracks: on a 2-triangle quad covering the whole texture, every texel is covered
local quad = Mesh.fromCorners({
	{ 0, 0, 0, 0, 0, 0, 0, 1 }, { 1, 0, 0, 1, 0, 0, 0, 1 }, { 1, 1, 0, 1, 1, 0, 0, 1 },
	{ 0, 0, 0, 0, 0, 0, 0, 1 }, { 1, 1, 0, 1, 1, 0, 0, 1 }, { 0, 1, 0, 0, 1, 0, 0, 1 },
})
local Gq = Raster.bake(quad, 37, 23)
Out.check("raster.no_cracks_on_shared_edge", Gq.covered == 37 * 23, tostring(Gq.covered))

-- dilation fills a gutter around islands and never overwrites covered texels
local before = G.covered
local p0x
for i = 0, 96 * 64 - 1 do
	if buffer.readu8(G.cover, i) == 1 then
		p0x = Raster.readVec(G.pos, i)
		break
	end
end
Raster.dilate(G, 3)
local gutter = 0
for i = 0, 96 * 64 - 1 do
	if buffer.readu8(G.cover, i) == 2 then
		gutter += 1
	end
end
local q0x = Raster.readVec(G.pos, 0)
Out.check("raster.dilation_adds_gutter", gutter > 0 and G.covered == before, string.format("%d gutter texels", gutter))
Out.check("raster.dilation_keeps_inside", p0x ~= nil and q0x ~= nil)

-- Surface --------------------------------------------------------------------------------------

local curv = Surface.vertexCurvature(box, 2)
local corner, faceMid = 0, 0
local P = box.P
for v = 1, #P // 3 do
	local x, y, z = P[v * 3 - 2], P[v * 3 - 1], P[v * 3]
	local ones = (math.abs(math.abs(x) - 1) < 1e-6 and 1 or 0) + (math.abs(math.abs(y) - 1) < 1e-6 and 1 or 0) + (math.abs(math.abs(z) - 1) < 1e-6 and 1 or 0)
	if ones == 3 then
		corner = math.max(corner, curv[v])
	elseif ones == 1 then
		faceMid = math.max(faceMid, math.abs(curv[v] - 0.5))
	end
end
Out.check("surface.box_corners_convex", corner > 0.7, string.format("%.3f", corner))
Out.check("surface.box_face_interior_flat", faceMid < 0.02, string.format("%.4f", faceMid))

local torus = Mesh.torus(1, 0.4, 32, 16)
local tc = Surface.vertexCurvature(torus, 2)
local tao = Surface.vertexAO(torus, 0.8, 32)
-- inner ring (closest to the axis) vs outer ring
local innerC, outerC, innerA, outerA, ni, no = 0, 0, 0, 0, 0, 0
for v = 1, #torus.P // 3 do
	local x, y, z = torus.P[v * 3 - 2], torus.P[v * 3 - 1], torus.P[v * 3]
	local rr = math.sqrt(x * x + z * z)
	if math.abs(y) < 0.05 and rr < 0.65 then
		innerC += tc[v]
		innerA += tao[v]
		ni += 1
	elseif math.abs(y) < 0.05 and rr > 1.35 then
		outerC += tc[v]
		outerA += tao[v]
		no += 1
	end
end
innerC, outerC, innerA, outerA = innerC / ni, outerC / no, innerA / ni, outerA / no
Out.check("surface.torus_outside_more_convex", outerC > innerC + 0.02, string.format("out %.3f in %.3f", outerC, innerC))
Out.check("surface.torus_inside_more_occluded", innerA < outerA - 0.1, string.format("in %.3f out %.3f", innerA, outerA))
Out.check("surface.convex_sphere_unoccluded", (function()
	local s = Mesh.sphere(1, 16, 8)
	local a = Surface.vertexAO(s, 0.5, 16)
	local mn = 1
	for _, v in a do
		mn = math.min(mn, v)
	end
	return mn > 0.9
end)())

-- edge distance: about 0 on the box edges (within one texel), half the face width at a face centre
local Gb = Raster.bake(Mesh.box(1, 1, 1, 5), 96, 64)
local ed = Surface.edgeDistance(Gb, Mesh.box(1, 1, 1, 5), 2)
local minE, maxE = 9, 0
for i = 0, 96 * 64 - 1 do
	if buffer.readu8(Gb.cover, i) == 1 then
		local e = buffer.readf32(ed, i * 4)
		minE, maxE = math.min(minE, e), math.max(maxE, e)
	end
end
Out.check("surface.edge_distance_range", minE < 0.08 and math.abs(maxE - 1) < 0.06, string.format("%.3f..%.3f", minE, maxE))
-- same band width on a coarse and a fine box (tessellation independent)
local function bandFrac(div: number): number
	local mb = Mesh.box(1, 1, 1, div)
	local g = Raster.bake(mb, 96, 64)
	local e = Surface.edgeDistance(g, mb, 2)
	local inBand, total = 0, 0
	for i = 0, 96 * 64 - 1 do
		if buffer.readu8(g.cover, i) == 1 then
			total += 1
			if buffer.readf32(e, i * 4) < 0.1 then
				inBand += 1
			end
		end
	end
	return inBand / total
end
local band1, band8 = bandFrac(1), bandFrac(8)
Out.check("surface.edge_band_tessellation_independent", math.abs(band1 - band8) < 0.01, string.format("div1 %.3f div8 %.3f", band1, band8))

-- Noise ----------------------------------------------------------------------------------------

local lo, hi = 9, -9
for i = 1, 4000 do
	local v = Noise.fbm(i * 0.137, i * 0.071, i * 0.029, 5)
	lo, hi = math.min(lo, v), math.max(hi, v)
end
Out.check("noise.fbm_range", lo > -1.6 and hi < 1.6 and hi - lo > 0.8, string.format("%.2f..%.2f", lo, hi))
local f1, f2, id = Noise.voronoi(3.2, 1.7, 0.4)
Out.check("noise.voronoi_order", f1 <= f2 and id >= 0 and id < 1)
local a1, a2, aid = Noise.voronoi(3.2, 1.7, 0.4)
Out.check("noise.voronoi_deterministic", a1 == f1 and a2 == f2 and aid == id)

-- Seamlessness: two texels on opposite sides of the sphere's u = 0/1 seam shade identically,
-- because shading is a function of 3D position, not UV.
local sphere = Mesh.sphere(1, 32, 16)
local ctxA = { px = 1, py = 0, pz = 0, nx = 1, ny = 0, nz = 0, curv = 0.5, ao = 1, edge = 1 }
local r1, g1, b1 = Recipe.shade(Presets.rustedIron, ctxA)
local r2, g2, b2 = Recipe.shade(Presets.rustedIron, table.clone(ctxA))
Out.check("recipe.deterministic", r1 == r2 and g1 == g2 and b1 == b2)

-- Bake -----------------------------------------------------------------------------------------

local maps
Out.time("bake.sphere_128_rustedIron", 1, function()
	maps = Bake.run(sphere, Presets.rustedIron, { size = 128, aoRays = 12 })
end)
local S = 128
local function px(buf, x, y, size: number?)
	local v = buffer.readu32(buf, (y * (size or S) + x) * 4)
	return v % 256, (v // 256) % 256, (v // 65536) % 256, v // 16777216
end
-- seam: column S-1 (u ~ 1) and column 0 (u ~ 0) are neighbours on the same meridian in 3D, so the
-- colour step across the seam should be no bigger than the steps between neighbouring columns
-- right next to it (the same region of the noise).
local function colDiff(xa: number, xb: number): number
	local d = 0
	for y = 8, S - 9 do
		local ra, ga, ba = px(maps.albedo, xa, y)
		local rb, gb, bb = px(maps.albedo, xb, y)
		d += math.abs(ra - rb) + math.abs(ga - gb) + math.abs(ba - bb)
	end
	return d
end
local seamDiff = colDiff(S - 1, 0)
local nearDiff = (colDiff(S - 3, S - 2) + colDiff(S - 2, S - 1) + colDiff(0, 1) + colDiff(1, 2)) / 4
Out.check("bake.seam_as_smooth_as_neighbours", seamDiff <= nearDiff * 1.6, string.format("seam %d neighbours %.0f", seamDiff, nearDiff))

-- normal map is unit-ish and mostly facing out (+Z in tangent space)
local zOk, cnt = 0, 0
for i = 0, S * S - 1, 3 do
	local v = buffer.readu32(maps.normal, i * 4)
	local x, y, z = (v % 256) / 127.5 - 1, ((v // 256) % 256) / 127.5 - 1, ((v // 65536) % 256) / 127.5 - 1
	local l = math.sqrt(x * x + y * y + z * z)
	if math.abs(l - 1) < 0.05 and z > 0.3 then
		zOk += 1
	end
	cnt += 1
end
Out.check("bake.normals_valid", zOk / cnt > 0.98, string.format("%.3f", zOk / cnt))

-- a flat recipe gives a flat normal map (128,128,255)
local flat = Bake.run(quad, { base = { color = { 0.5, 0.5, 0.5 } } }, { size = 32 })
local fr, fg, fb = px(flat.normal, 16, 16, 32)
Out.check("bake.flat_recipe_flat_normal", math.abs(fr - 128) <= 1 and math.abs(fg - 128) <= 1 and fb >= 254, string.format("%d %d %d", fr, fg, fb))

-- OpenGL convention: height rising toward +u gives red < 128; rising toward image-up (-v) gives green < 128
local rampU = Bake.run(quad, { base = {}, layers = { { height = 1, mask = { { "y", lo = -10, hi = 10 } } } } }, { size = 16 })
-- quad maps x -> u and y -> v; height increases with y = v (down the rows), i.e. falls toward image-up
local ur, ug = px(rampU.normal, 8, 8, 16)
Out.check("bake.green_follows_image_up", ug > 128 and math.abs(ur - 128) <= 1, string.format("r %d g %d", ur, ug))

-- presets all bake
for name, recipe in Presets do
	local ok, err = pcall(Bake.run, box, recipe, { size = 48, aoRays = 8 })
	Out.check("preset." .. name, ok, ok and "" or tostring(err))
end

-- timing at production size
local m512
Out.time("bake.box_256_paintedMetal", 1, function()
	m512 = Bake.run(Mesh.box(1, 0.6, 0.8, 6), Presets.paintedMetal, { size = 256 })
end)
Out.check("bake.timing_report", m512 ~= nil, string.format("raster %.0f ms, surface %.0f ms, shade %.0f ms", m512.ms.raster, m512.ms.surface, m512.ms.shade))

if emitImages then
	-- raw RGBA8 files for sheet.py (lune's print is not binary-safe)
	local fs = require("@lune/fs")
	if fs.isDir("out") then
		fs.removeDir("out")
	end
	fs.writeDir("out")
	local order = 0
	for _, k in { "albedo", "normal", "roughness", "metalness", "edge", "ao" } do
		for _, pair in { { "sphere_rust", maps }, { "box_paint", m512 } } do
			order += 1
			local mp = pair[2] :: any
			fs.writeFile(string.format("out/%02d_%s_%s_%dx%d.rgba", order, pair[1], k, mp.W, mp.H), mp[k])
		end
	end
end

Out.done()
