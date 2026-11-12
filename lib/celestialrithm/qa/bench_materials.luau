--!strict
-- Bench: ms per Render() for every material, tier and face size, headless in lune.
-- lune runs the Luau VM without Roblox's native codegen, so this approximates a Roblox client
-- running interpreted Luau on this machine. Studio and phone timings will differ; see
-- docs/celestialrithm/frontier/runtime.md for the Studio plan.
-- Usage: lune run bench_materials.luau [frames]

local process = require("@lune/process")
local Registry = require("../materials/Registry")

local FRAMES = tonumber(process.args[1]) or 30
local SIZES = { { 240, 112 }, { 120, 56 } }

print(string.format("| material | size | tier | ms/frame | KB held |"))
print("|---|---|---|---|---|")
for _, id in Registry.order do
	local M = (Registry.byId :: any)[id]
	for _, sz in SIZES do
		local w, h = sz[1], sz[2]
		local out = buffer.create(w * h * 4)
		for _, tier in Registry.tiers do
			local m = M.new(w, h, 1, tier)
			for f = 0, 4 do -- warm-up (sims settle, caches fill)
				m:Render(f / 30, 0, out)
			end
			local t0 = os.clock()
			for f = 5, 4 + FRAMES do
				m:Render(f / 30, if f % 20 < 3 then 1 else 0, out)
			end
			local ms = (os.clock() - t0) * 1000 / FRAMES
			print(string.format("| %s | %dx%d | %s | %.2f | %.0f |", id, w, h, tier, ms, (m:Bytes() + w * h * 4) / 1024))
			print(string.format("@@TIME %s.%dx%d.%s %.4f %d", id, w, h, tier, ms, FRAMES))
		end
	end
end
