--!strict
local JellyMeter = require("./JellyMeter")
local t = require("../../../../tools/lib/t")

local p = JellyMeter.Default
local nv, nt = JellyMeter.counts(p)
local a = JellyMeter.liquid(p, 0.2, 0, 0, 0)
local b = JellyMeter.liquid(p, 0.9, 0.2, 1, 1.3)
t.eq("vertex count fixed (low)", #a.Pos, nv)
t.eq("vertex count fixed (high)", #b.Pos, nv)
t.eq("triangle count fixed", #b.Tri, nt)
t.eq("colour per vertex", #b.Col, nv)

-- surface centre sits at the level
t.near("surface at level", a.Pos[#a.Pos].Y, p.Height * 0.2, 1e-6)
-- every vertex stays inside the capsule
local inside = true
for _, v in b.Pos do
	if v.Y < -1e-6 or v.Y > p.Height + 1e-6 or math.sqrt(v.X * v.X + v.Z * v.Z) > p.Radius + 1e-6 then
		inside = false
	end
end
t.ok("inside capsule", inside)
-- triangle indices valid
local ok = true
for _, tri in b.Tri do
	for _, i in tri do
		if i < 1 or i > nv then
			ok = false
		end
	end
end
t.ok("indices valid", ok)

-- colour climbs: low is greener, high is redder
local lo, hi = JellyMeter.ramp(0.05), JellyMeter.ramp(0.98)
t.ok("low green", lo.G > lo.R)
t.ok("high red", hi.R > hi.G)
-- slosh tilts the surface ring
local flat = JellyMeter.liquid(p, 0.5, 0, 0, 0)
local tilt = JellyMeter.liquid(p, 0.5, 0.2, 0, 0)
local i = 1 + (p.Rings - 2) * p.Segments + p.Segments // 4 + 1 -- a = 90deg, z = +R
t.ok("slosh raises front edge", tilt.Pos[i].Y > flat.Pos[i].Y + 0.1)

-- spring: overshoots a little, then settles on target
local sp = JellyMeter.spring(0)
sp.Target = 0.6
local peak = 0
for _ = 1, 240 do
	JellyMeter.step(sp, 1 / 60)
	peak = math.max(peak, sp.Level)
end
t.ok("small overshoot", peak > 0.6 and peak < 0.72)
t.near("settles", sp.Level, 0.6, 1e-3)
t.ok("slosh decays", math.abs(sp.Slosh) < 1e-2)
t.done()
