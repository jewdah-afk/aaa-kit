--# selene: allow(mixed_table)
-- Latency bench for surfacebake: prints markdown tables (ms, median of N runs, single thread).
-- Run: cd lib/surfacebake/qa && lune run bench.luau            (add --quick for fewer runs)
local process = require("@lune/process")
local Mesh = require("../Mesh")
local Bake = require("../Bake")
local Presets = require("../Presets")
local Animate = require("../Animate")
local Parallax = require("../Parallax")
local React = require("../React")

local quick = table.find(process.args, "--quick") ~= nil

local function median(f: () -> (), runs: number): number
	local t = {}
	for i = 1, runs do
		local t0 = os.clock()
		f()
		t[i] = (os.clock() - t0) * 1000
	end
	table.sort(t)
	return t[(runs + 1) // 2]
end

local crate = Mesh.box(1, 0.75, 0.85, 6)

print("### Bake: every preset, 256x256, crate (432 tris)\n")
print("| Preset | raster | surface | shade | total ms |")
print("|---|---:|---:|---:|---:|")
local names = {}
for name in Presets do
	table.insert(names, name)
end
table.sort(names)
for _, name in names do
	local maps = Bake.run(crate, Presets[name], { size = 256 })
	local ms = maps.ms
	print(string.format("| %s | %.0f | %.0f | %.0f | %.0f |", name, ms.raster, ms.surface, ms.shade, ms.raster + ms.surface + ms.shade))
end

print("\n### Bake: size scaling (paintedMetal, crate)\n")
print("| Size | total ms | ms per 1k texels |")
print("|---|---:|---:|")
for _, S in { 128, 256, 512, if quick then nil else 1024 } do
	local maps = Bake.run(crate, Presets.paintedMetal, { size = S })
	local ms = maps.ms.raster + maps.ms.surface + maps.ms.shade
	print(string.format("| %d² | %.0f | %.3f |", S, ms, ms / (S * S / 1000)))
end

print("\n### Animate: one full frame (every texel), runeStone base\n")
print("| Effect | 128² | 256² | 512² |")
print("|---|---:|---:|---:|")
local specs = {
	{ "pulse", { effect = "pulse", phase = { "y", scale = 1 }, speed = 1, mask = { { "y", lo = -1, hi = 1 } } } },
	{ "flow", { effect = "flow", phase = { "y", scale = 1 }, speed = 0.5, freq = 2 } },
	{ "dissolve", { effect = "dissolve", speed = 1, width = 0.08 } },
	{ "scan", { effect = "scan", phase = { "y", scale = 1 }, width = 0.1 } },
	{ "spread", { effect = "spread", phase = "seed", seed = { 1, 1, 1 }, width = 0.05 } },
}
local bakes = {}
for _, S in { 128, 256, 512 } do
	bakes[S] = Bake.run(crate, Presets.runeStone, { size = S })
end
local runs = if quick then 3 else 7
for _, sp in specs do
	local row = { sp[1] }
	for _, S in { 128, 256, 512 } do
		local st = Animate.prepare(bakes[S], sp[2])
		local t = 0
		row[#row + 1] = string.format("%.2f", median(function()
			t += 1 / 60
			Animate.step(st, t)
		end, runs))
	end
	print("| " .. table.concat(row, " | ") .. " |")
end
local st = Animate.prepare(bakes[256], specs[1][2])
local budgetMs = median(function()
	Animate.step(st, 0.5, 256 * 32)
end, runs)
print(string.format("\nBudgeted update, 256² at 32 rows/frame (8,192 texels): **%.2f ms** per frame; the whole image refreshes every 8 frames.", budgetMs))

print("\n### React: one frame, all texels\n")
print("| Profile | 128² | 256² |")
print("|---|---:|---:|")
local profiles = {
	{ "molten hits (heat + ripple, 4 live hits)", { heat = { gain = 1, radius = 0.28, decay = 0.55 }, ripple = { speed = 2.2, width = 0.07, life = 1.1 } }, false },
	{ "ice vs lava (flow + frost, 3 seeds)", { flow = { mask = { { "voronoi", scale = 4, lo = 0.12, hi = 0 } }, phase = { "y", scale = 1 }, heat = 0.35 }, frost = { speed = 0.55, max = 0.75, width = 0.07, melt = 0.5 } }, true },
	{ "force field (shimmer + ripple)", { shimmer = { mask = { { "voronoi", scale = 3, lo = 0.16, hi = 0.02 } }, phase = { "voronoi", scale = 3, field = "f1" }, gain = 1.4 }, ripple = { speed = 2.8, width = 0.06, life = 0.9 } }, false },
}
for _, pr in profiles do
	local row = { pr[1] }
	for _, S in { 128, 256 } do
		local rst = React.prepare(bakes[S], pr[2])
		for k = 1, (if pr[3] then 3 else 4) do
			React.hit(rst, 0.9 - k * 0.3, 0.75, 0.2 * k, 1, pr[3])
		end
		row[#row + 1] = string.format("%.2f", median(function()
			React.step(rst, 1 / 60, 1.5)
		end, runs))
	end
	print("| " .. table.concat(row, " | ") .. " |")
end

print("\n### Depth effects, one frame\n")
print("| Effect | Size | ms |")
print("|---|---|---:|")
local HW = 256
local height, colour = buffer.create(HW * HW * 4), buffer.create(HW * HW * 4)
for i = 0, HW * HW - 1 do
	buffer.writef32(height, i * 4, 0.5 + 0.5 * math.noise(i % HW / 20, i // HW / 20, 0.3))
	buffer.writeu32(colour, i * 4, 0xff808080)
end
for _, cfg in { { 128, 16 }, { 128, 32 }, { 256, 16 } } do
	local O = cfg[1]
	local out = buffer.create(O * O * 4)
	print(string.format("| POM, %d steps | %d² | %.1f |", cfg[2], O, median(function()
		Parallax.pom(height, colour, HW, HW, out, O, O, 0.5, 0.3, 0.81, 0.15, cfg[2], 0.5)
	end, runs)))
end
for _, O in { 128, 256 } do
	local out = buffer.create(O * O * 4)
	print(string.format("| Interior mapping, 4x4 rooms | %d² | %.1f |", O, median(function()
		Parallax.interior(out, O, O, 4, 4, 0.4, 0.2, 0.89, 1, 3)
	end, runs)))
end
local tile = buffer.create(96 * 96 * 4)
for _, cfg in { { 128, 5 }, { 128, 7 }, { 256, 5 } } do
	local O = cfg[1]
	local out = buffer.create(O * O * 4)
	local z = 0
	print(string.format("| Infinite zoom, %d octaves | %d² | %.1f |", cfg[2], O, median(function()
		z += 0.01
		Parallax.zoom(out, O, O, tile, 96, 96, z, cfg[2], 0.3, 0.5)
	end, runs)))
end
local layers = {}
for d = 1, 4 do
	layers[d] = { img = buffer.create(256 * 128 * 4), w = 256, h = 128, depth = 1 - d / 5 }
end
local lout = buffer.create(256 * 144 * 4)
print(string.format("| 2D parallax, 4 layers | 256x144 | %.1f |", median(function()
	Parallax.layers(lout, 256, 144, layers, 13, 2)
end, runs)))
local sph = Mesh.sphere(1, 32, 16)
print(string.format("| Shells (one-off build), 16 shells | 256² masks | %.0f |", median(function()
	Parallax.shells(sph, { count = 16, length = 0.15, density = 0.7, cells = 64, root = { 0.2, 0.1, 0.05 }, tip = { 0.9, 0.7, 0.4 } }, 256)
end, if quick then 1 else 3)))
