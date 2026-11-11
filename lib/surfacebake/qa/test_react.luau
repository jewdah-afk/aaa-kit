--# selene: allow(mixed_table, multiple_statements) -- recipe terms are { kind, key = value }; one-line predicates
-- Headless checks for React. Run: cd lib/surfacebake/qa && lune run test_react.luau | grep -a '^@@'
local Out = require("../../frontier/qa/Out")
local Mesh = require("../Mesh")
local Bake = require("../Bake")
local Presets = require("../Presets")
local React = require("../React")
local Raster = require("../Raster")

local S = 64
local maps = Bake.run(Mesh.box(1, 1, 1, 3), Presets.paintedMetal, { size = S, aoRays = 8 })
local n = S * S

local function texelsWhere(st, f: (number, number, number, number) -> boolean): number
	local c = 0
	for i = 0, n - 1 do
		if buffer.readu32(st.base, i * 4) >= 16777216 then
			local x, y, z = Raster.readVec(st.pos, i)
			if f(i, x, y, z) then
				c += 1
			end
		end
	end
	return c
end
local function dist(x, y, z, a, b, c)
	return math.sqrt((x - a) ^ 2 + (y - b) ^ 2 + (z - c) ^ 2)
end

-- heat ---------------------------------------------------------------------------------------------
local st = React.prepare(maps, { heat = { gain = 1, radius = 0.3, decay = 1 }, ripple = { speed = 2, width = 0.08, life = 1 } })
React.hit(st, 1, 0, 0, 1)
local near = texelsWhere(st, function(i, x, y, z) return dist(x, y, z, 1, 0, 0) < 0.15 and buffer.readf32(st.heat, i * 4) > 0.5 end)
local far = texelsWhere(st, function(i, x, y, z) return dist(x, y, z, 1, 0, 0) > 1.2 and buffer.readf32(st.heat, i * 4) > 0.01 end)
Out.check("react.heat_local_to_hit", near > 0 and far == 0, string.format("near %d far %d", near, far))
local function maxHeat(s)
	local m = 0
	for i = 0, n - 1 do
		m = math.max(m, buffer.readf32(s.heat, i * 4))
	end
	return m
end
local h0 = maxHeat(st)
for _ = 1, 60 do
	React.step(st, 1 / 60)
end
Out.check("react.heat_cools", maxHeat(st) < h0 * 0.45 and maxHeat(st) > 0, string.format("%.2f -> %.2f", h0, maxHeat(st)))
-- heat stacks with repeated hits
local st2 = React.prepare(maps, { heat = { gain = 0.5, radius = 0.3, decay = 0.1 } })
React.hit(st2, 1, 0, 0)
local one = maxHeat(st2)
React.hit(st2, 1, 0, 0)
React.hit(st2, 1, 0, 0)
Out.check("react.heat_accumulates", maxHeat(st2) > one * 2.5, string.format("%.2f -> %.2f", one, maxHeat(st2)))

-- ripple: at age 0.4 s the brightened ring sits at radius ~0.8 --------------------------------------
local rp = React.prepare(maps, { ripple = { speed = 2, width = 0.06, life = 2, color = { 0.2, 1, 1 } } })
React.hit(rp, 1, 0, 0)
for _ = 1, 24 do
	React.step(rp, 1 / 60)
end
local onRing = texelsWhere(rp, function(i, x, y, z)
	local d = dist(x, y, z, 1, 0, 0)
	return d > 0.7 and d < 0.9 and buffer.readu32(rp.out, i * 4) ~= buffer.readu32(rp.base, i * 4)
end)
local inside = texelsWhere(rp, function(i, x, y, z)
	return dist(x, y, z, 1, 0, 0) < 0.4 and buffer.readu32(rp.out, i * 4) ~= buffer.readu32(rp.base, i * 4)
end)
Out.check("react.ripple_ring_travels", onRing > 0 and inside == 0, string.format("ring %d inside %d", onRing, inside))

-- frost grows from a seed, persists, and heat melts it ---------------------------------------------
local fz = React.prepare(maps, { heat = { gain = 3, radius = 0.25, decay = 0.2 }, frost = { onHit = true, speed = 0.8, max = 0.8, width = 0.05, melt = 2 } })
React.hit(fz, 0, 1, 0, 1, true) -- frost seed on the top face
for _ = 1, 60 do
	React.step(fz, 1 / 60)
end
local frozenNear = texelsWhere(fz, function(i, x, y, z) return dist(x, y, z, 0, 1, 0) < 0.4 and buffer.readf32(fz.frost, i * 4) > 0.9 end)
local frozenFar = texelsWhere(fz, function(i, x, y, z) return dist(x, y, z, 0, 1, 0) > 1.2 and buffer.readf32(fz.frost, i * 4) > 0 end)
Out.check("react.frost_spreads_from_seed", frozenNear > 0 and frozenFar == 0, string.format("near %d far %d", frozenNear, frozenFar))
local function frostSum(s)
	local t = 0
	for i = 0, n - 1 do
		t += buffer.readf32(s.frost, i * 4)
	end
	return t
end
local before = frostSum(fz)
React.hit(fz, 0, 1, 0, 1) -- a heat hit on the frost
for _ = 1, 60 do
	React.step(fz, 1 / 60)
end
Out.check("react.heat_melts_frost", frostSum(fz) < before * 0.9, string.format("%.0f -> %.0f", before, frostSum(fz)))

-- lava flow freezes under frost ---------------------------------------------------------------------
local lavaMaps = Bake.run(Mesh.box(1, 1, 1, 3), Presets.lavaRock, { size = S, aoRays = 8 })
local lv = React.prepare(lavaMaps, {
	flow = { mask = { { "voronoi", scale = 4, lo = 0.12, hi = 0 } }, phase = { "y", scale = 1 }, speed = 0.4, color = { 1, 0.5, 0.1 }, heat = 0 },
	frost = { onHit = true, speed = 2, max = 0.9, width = 0.05, melt = 0 },
})
React.hit(lv, 0, 1, 0, 1, true)
for _ = 1, 40 do
	React.step(lv, 1 / 60)
end
local function glowDelta(s, inFrost: boolean): number
	local tot, cnt = 0, 0
	for i = 0, n - 1 do
		local m = buffer.readf32(s.flowMask, i * 4)
		if m > 0.5 then
			local f = buffer.readf32(s.frost, i * 4)
			if (inFrost and f > 0.95) or (not inFrost and f == 0) then
				local o, b = buffer.readu32(s.out, i * 4), buffer.readu32(s.base, i * 4)
				-- red-channel boost from the flow glow (frost recolours toward pale blue instead)
				tot += (o % 256) - (b % 256) - (((o // 65536) % 256) - ((b // 65536) % 256))
				cnt += 1
			end
		end
	end
	return if cnt > 0 then tot / cnt else 0
end
local hot, frozen = glowDelta(lv, false), glowDelta(lv, true)
Out.check("react.frost_freezes_flow", hot > frozen + 20, string.format("unfrozen %.0f frozen %.0f", hot, frozen))

-- shimmer follows spin speed -----------------------------------------------------------------------
local sh = React.prepare(maps, { shimmer = { mask = { { "voronoi", scale = 3, lo = 0.08, hi = 0 } }, phase = { "voronoi", scale = 3, field = "f1" }, color = { 0.3, 0.8, 1 }, gain = 0.8 } })
React.step(sh, 1 / 60, 0)
Out.check("react.no_spin_no_shimmer", buffer.tostring(sh.out) == buffer.tostring(sh.base))
for _ = 1, 30 do
	React.step(sh, 1 / 60, 3)
end
Out.check("react.spin_drives_shimmer", buffer.tostring(sh.out) ~= buffer.tostring(sh.base) and sh.spin > 2, string.format("spin %.2f", sh.spin))

-- spring -------------------------------------------------------------------------------------------
local sp = React.spring(60, 7)
React.springStep(sp, 40, 0, 0, 1 / 60) -- the body lurches +x
for _ = 1, 5 do
	React.springStep(sp, 40, 0, 0, 1 / 60)
end
Out.check("react.spring_lags_behind_motion", sp.x < 0, string.format("%.3f", sp.x))
for _ = 1, 240 do
	React.springStep(sp, 0, 0, 0, 1 / 60)
end
Out.check("react.spring_settles", math.abs(sp.x) < 0.002 and math.abs(sp.vx) < 0.01, string.format("%.4f", sp.x))

Out.done()
