--!strict
local Chain = require("./Chain")
local t = require("../../../../tools/lib/t")

local a = Chain.noise(32, 32, 8, 4, 42)
local b = Chain.noise(32, 32, 8, 4, 42)
local c = Chain.noise(32, 32, 8, 4, 43)
local same, diff = true, false
for i = 1, #a.v do
	if a.v[i] ~= b.v[i] then same = false end
	if a.v[i] ~= c.v[i] then diff = true end
end
t.ok("deterministic per seed", same)
t.ok("seed changes field", diff)
local lo, hi = 1, 0
for _, v in a.v do
	lo, hi = math.min(lo, v), math.max(hi, v)
end
t.ok("noise in [0,1]", lo >= 0 and hi <= 1)

local out = Chain.run(a, { Chain.warp(3, 6, 1), Chain.threshold(0.5), Chain.distance(), Chain.bands(4, 6) })
local maxBand = 0
for _, v in out.v do
	maxBand = math.max(maxBand, v)
end
t.ok("bands quantise", maxBand <= 3 and maxBand >= 1)

-- distance transform on a single seed cell
local m = { w = 5, h = 5, v = table.create(25, 0) }
m.v[13] = 1
local d = Chain.distance()(m)
t.near("dt centre", d.v[13], 0)
t.near("dt neighbour", d.v[14], 1)
t.near("dt diagonal", d.v[19], 1.4142, 1e-4)

t.done()
