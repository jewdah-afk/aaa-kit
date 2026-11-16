--!strict
local AuroraAura = require("./AuroraAura")
local t = require("../../../../tools/lib/t")

local a1 = AuroraAura.new(1337)
local a2 = AuroraAura.new(1337)
t.eq("same seed, same palette", a1.palette.d[2], a2.palette.d[2])
t.eq("same seed, same ribbons", #a1.ribbons, #a2.ribbons)
t.ok("different seed differs", AuroraAura.new(1338).palette.d[1] ~= a1.palette.d[1])

local r = AuroraAura.rng(7)
-- parity with JS mulberry32 (Math.imul) used by the web lab
t.near("mulberry32 #1", r(), 0.011704753153026104, 1e-12)
t.near("mulberry32 #2", r(), 0.06195825757458806, 1e-12)
t.near("mulberry32 #3", r(), 0.97690763277933, 1e-12)
local lo, hi = 1, 0
for _ = 1, 2000 do
	local v = r()
	lo, hi = math.min(lo, v), math.max(hi, v)
end
t.ok("rng in [0,1)", lo >= 0 and hi < 1 and hi - lo > 0.95)

-- optimisation beats a single draw on average
local sumBest, sumOne = 0, 0
for s = 1, 40 do
	sumBest += AuroraAura.new(s).score
	sumOne += AuroraAura.new(s, 1).score
end
t.ok("optimised palettes score higher", sumBest > sumOne)

for s = 1, 40 do
	local a = AuroraAura.new(s)
	t.ok("3-5 ribbons", #a.ribbons >= 3 and #a.ribbons <= 5)
	for _, rb in a.ribbons do
		t.ok("calm drift (>= 8 s per turn)", math.abs(rb.speed) <= 0.125)
	end
	local keys = AuroraAura.colorKeys(a, a.ribbons[1], 6)
	t.eq("6 keys", #keys, 6)
	t.ok("keys span 0..1", keys[1][1] == 0 and keys[6][1] == 1)
	for _, k in keys do
		t.ok("rgb in range", k[2] >= 0 and k[2] <= 1 and k[3] >= 0 and k[3] <= 1 and k[4] >= 0 and k[4] <= 1)
	end
end

t.eq("calm keeps all ribbons", AuroraAura.budget(0).ribbons, 5)
t.eq("boss keeps one", AuroraAura.budget(4).ribbons, 1)
t.eq("clamps rung", AuroraAura.budget(99).alpha, AuroraAura.budget(5).alpha)
t.done()
