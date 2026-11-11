--!strict
local Curves = require("./Curves")
local t = require("../../../../tools/lib/t")

t.near("geometric", Curves.geometric(10, 1.15, 2), 13.225, 1e-9)
t.near("polynomial", Curves.polynomial(100, 2, 2), 900)
t.near("soft cap below", Curves.softCap(50, 100), 50)
t.ok("soft cap above grows slower", Curves.softCap(200, 100) < 200 and Curves.softCap(200, 100) > 100)
t.ok("prestige sublinear", Curves.prestige(2e6, 1, 0.5) < 2 * Curves.prestige(1e6, 1, 0.5))
t.near("payback", Curves.payback(100, 4), 25)
t.ok("payback no gain", Curves.payback(100, 0) == math.huge)

-- costs grow 1.15x, income grows +1/s per level: waits grow smoothly (ratio ~1.15 or less)
local worst = Curves.pacing(function(l)
	return Curves.geometric(10, 1.15, l)
end, function(l)
	return 1 + l
end, 60)
t.ok("smooth pacing", worst < 1.2)

-- a wall: cost jumps 10x at level 30
local wall, at = Curves.pacing(function(l)
	return Curves.geometric(10, 1.15, l) * (if l >= 30 then 10 else 1)
end, function(l)
	return 1 + l
end, 60)
t.ok("detects wall", wall > 5 and at == 30)

t.near("offline cap", Curves.offline(10, 48 * 3600, 8, 0.5), 10 * 8 * 3600 * 0.5)
t.done()
