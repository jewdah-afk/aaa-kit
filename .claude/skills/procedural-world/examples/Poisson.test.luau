--!strict
--# selene: allow(multiple_statements)
local Poisson = require("./Poisson")
local t = require("../../../../tools/lib/t")

local function lcg(seed: number): () -> number
	local x = seed
	return function()
		x = (x * 1103515245 + 12345) % 2147483648
		return x / 2147483648
	end
end

local pts = Poisson.sample(200, 120, 10, lcg(9))
t.ok("fills the area", #pts > 120)
local minD = math.huge
for i = 1, #pts do
	for j = i + 1, #pts do
		local dx, dy = pts[i].x - pts[j].x, pts[i].y - pts[j].y
		minD = math.min(minD, math.sqrt(dx * dx + dy * dy))
	end
end
t.ok("respects spacing", minD >= 10 - 1e-9)

local again = Poisson.sample(200, 120, 10, lcg(9))
t.eq("deterministic", #again, #pts)

local masked = Poisson.sample(200, 120, 10, lcg(9), 30, function(x)
	return x < 100 -- left half only
end)
local ok = true
for _, p in masked do
	if p.x >= 100 then ok = false end
end
t.ok("mask honoured", ok and #masked > 40)

t.done()
