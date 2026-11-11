--# selene: allow(mixed_table) -- recipe mask terms are { kind, key = value } by design
-- Headless checks for Animate and Parallax. Run: cd lib/surfacebake/qa && lune run test_motion.luau | grep -a '^@@'
local Out = require("../../frontier/qa/Out")
local Mesh = require("../Mesh")
local Bake = require("../Bake")
local Presets = require("../Presets")
local Animate = require("../Animate")
local Parallax = require("../Parallax")

local S = 64
local maps = Bake.run(Mesh.box(1, 1, 1, 3), Presets.runeStone, { size = S, aoRays = 8 })
local function px(b: buffer, i: number): (number, number, number, number)
	local v = buffer.readu32(b, i * 4)
	return v % 256, (v // 256) % 256, (v // 65536) % 256, v // 16777216
end

-- Animate ------------------------------------------------------------------------------------------

local pulse = Animate.prepare(maps, { effect = "pulse", color = { 0.3, 1, 1 }, phase = { "y", scale = 1 }, speed = 1, freq = 1,
	mask = { { "y", lo = 0, hi = 0.01 } } }) -- only the upper half (y > 0) pulses
Animate.step(pulse, 0)
local a0 = buffer.tostring(pulse.out)
Animate.step(pulse, 0.25)
local a1 = buffer.tostring(pulse.out)
Out.check("animate.pulse_changes_over_time", a0 ~= a1)
-- texels with mask 0 stay exactly the baked colour
local untouched = true
for i = 0, S * S - 1 do
	if buffer.readf32(pulse.mask, i * 4) == 0 and buffer.readu32(pulse.out, i * 4) ~= buffer.readu32(pulse.base, i * 4) then
		untouched = false
	end
end
Out.check("animate.mask_zero_untouched", untouched)

local dis = Animate.prepare(maps, { effect = "dissolve", color = { 1, 0.5, 0.1 }, speed = 1, width = 0.08 })
Animate.step(dis, 0) -- progress -0.1: nothing gone
local covered, visible = 0, 0
for i = 0, S * S - 1 do
	local _, _, _, a = px(dis.base, i)
	local _, _, _, b = px(dis.out, i)
	if a > 0 then
		covered += 1
		if b > 0 then
			visible += 1
		end
	end
end
Out.check("animate.dissolve_starts_whole", visible == covered, string.format("%d/%d", visible, covered))
Animate.step(dis, 1.15) -- progress 1.05: everything gone
visible = 0
for i = 0, S * S - 1 do
	local _, _, _, b = px(dis.out, i)
	if b > 0 then
		visible += 1
	end
end
Out.check("animate.dissolve_ends_gone", visible == 0, tostring(visible))

local spread = Animate.prepare(maps, { effect = "spread", phase = "seed", seed = { 1, 1, 1 }, speed = 1, width = 0.05, maxRadius = 5, after = { 0.9, 0.95, 1 } })
Animate.step(spread, 0.3)
local near, far = 0, 0
for i = 0, S * S - 1 do
	local _, _, _, a = px(spread.base, i)
	if a > 0 then
		local changed = buffer.readu32(spread.out, i * 4) ~= buffer.readu32(spread.base, i * 4)
		local d = buffer.readf32(spread.phase, i * 4)
		if d < 0.2 and changed then
			near += 1
		elseif d > 1.5 and changed then
			far += 1
		end
	end
end
Out.check("animate.spread_front_grows_from_seed", near > 0 and far == 0, string.format("near %d far %d", near, far))

local flow = Animate.prepare(maps, { effect = "flow", phase = { "y", scale = 1 }, speed = 0.5, freq = 2 })
Animate.step(flow, 0.1)
local f0 = buffer.tostring(flow.out)
Animate.step(flow, 0.1 + 1 / 0.5) -- one full LUT cycle later (speed 0.5 -> period 2 s): identical
Out.check("animate.flow_loops_seamlessly", buffer.tostring(flow.out) == f0)

local scan = Animate.prepare(maps, { effect = "scan", phase = { "y", scale = 1 }, speed = 1, width = 0.1, range = 2, min = -1 })
local rowsSeen = {}
for _ = 1, 10 do
	local y0, rows = Animate.step(scan, 0.5, S * 8)
	for y = y0, y0 + rows - 1 do
		rowsSeen[y] = true
	end
	Out.check("animate.budget_rows_" .. y0, rows == 8)
	if y0 + rows >= S then
		break
	end
end
local all = true
for y = 0, S - 1 do
	if not rowsSeen[y] then
		all = false
	end
end
Out.check("animate.budget_round_robin_covers_all_rows", all)
local slice1 = Animate.rows(scan, 0, 8)
local slice2 = Animate.rows(scan, 8, 8)
Out.check("animate.upload_slice_reused", slice1 == slice2 and buffer.len(slice1) == S * 8 * 4)

-- Parallax.pom -------------------------------------------------------------------------------------

local HW = 32
local height, colour = buffer.create(HW * HW * 4), buffer.create(HW * HW * 4)
for y = 0, HW - 1 do
	for x = 0, HW - 1 do
		local hi = x < HW // 2
		buffer.writef32(height, (y * HW + x) * 4, if hi then 1 else 0)
		buffer.writeu32(colour, (y * HW + x) * 4, if hi then 0xff0000ff else 0xffff0000) -- red / blue
	end
end
local out = buffer.create(HW * HW * 4)
Parallax.pom(height, colour, HW, HW, out, HW, HW, 0, 0, 1, 0.2, 16, 0)
local same = true
for i = 0, HW * HW - 1 do
	if buffer.readu32(out, i * 4) ~= buffer.readu32(colour, i * 4) then
		same = false
	end
end
Out.check("pom.straight_down_is_identity", same)
local outL, outR = buffer.create(HW * HW * 4), buffer.create(HW * HW * 4)
Parallax.pom(height, colour, HW, HW, outL, HW, HW, -0.7, 0, 0.7, 0.2, 16, 0)
Parallax.pom(height, colour, HW, HW, outR, HW, HW, 0.7, 0, 0.7, 0.2, 16, 0)
-- pixel just inside the pit, right of the cliff at x = 16: from the right the eye looks left, the
-- ray runs into the red cliff (occluded); from the left it reaches the blue pit floor.
local function isRed(o: buffer, x: number, y: number): boolean
	local r, _, b = px(o, y * HW + x)
	return r > b
end
Out.check("pom.cliff_occludes_from_the_right", isRed(outR, 17, 16) and not isRed(outL, 17, 16))
Out.check("pom.view_changes_image", buffer.tostring(outL) ~= buffer.tostring(outR))

-- Parallax.interior --------------------------------------------------------------------------------

local i1, i2 = buffer.create(64 * 64 * 4), buffer.create(64 * 64 * 4)
Parallax.interior(i1, 64, 64, 4, 4, 0, 0, 1, 1, 3)
Parallax.interior(i2, 64, 64, 4, 4, 0.5, 0.2, 0.84, 1, 3)
Out.check("interior.view_changes_rooms", buffer.tostring(i1) ~= buffer.tostring(i2))
local lit, dark = 0, 0
for cy = 0, 3 do
	for cx = 0, 3 do
		local i = (math.floor((cy + 0.5) * 16) * 64 + math.floor((cx + 0.5) * 16))
		local r, g, b = px(i1, i)
		if r + g + b > 300 then
			lit += 1
		else
			dark += 1
		end
	end
end
Out.check("interior.some_rooms_lit_some_dark", lit > 0 and dark > 0, string.format("lit %d dark %d", lit, dark))

-- Parallax.zoom ------------------------------------------------------------------------------------

local TW = 32
local tile = buffer.create(TW * TW * 4)
for y = 0, TW - 1 do
	for x = 0, TW - 1 do
		local v = math.floor(127 + 127 * math.sin(x / TW * 2 * math.pi) * math.cos(y / TW * 2 * math.pi))
		buffer.writeu32(tile, (y * TW + x) * 4, v + (255 - v) * 256 + 128 * 65536 + 255 * 16777216)
	end
end
local Z = 48
local function frame(z: number): buffer
	local o = buffer.create(Z * Z * 4)
	Parallax.zoom(o, Z, Z, tile, TW, TW, z, 5, 0.3, 0.5)
	return o
end
local function diff(a: buffer, b: buffer): number
	local d = 0
	for i = 0, Z * Z - 1 do
		local r1, g1, b1 = px(a, i)
		local r2, g2, b2 = px(b, i)
		d += math.abs(r1 - r2) + math.abs(g1 - g2) + math.abs(b1 - b2)
	end
	return d / (Z * Z)
end
local acrossBoundary = diff(frame(2.995), frame(3.005))
local midOctave = diff(frame(2.495), frame(2.505))
Out.check("zoom.seamless_across_octave_boundary", acrossBoundary < midOctave * 2 + 1, string.format("boundary %.2f mid %.2f", acrossBoundary, midOctave))
Out.check("zoom.actually_moves", midOctave > 0.05, string.format("%.3f", midOctave))

-- Parallax.shells ----------------------------------------------------------------------------------

local sphere = Mesh.sphere(1, 16, 8)
local shellMeshes, shellMasks = Parallax.shells(sphere, { count = 8, length = 0.2, density = 0.6, cells = 24, root = { 0.2, 0.15, 0.1 }, tip = { 0.9, 0.8, 0.6 } }, 64)
Out.check("shells.count", #shellMeshes == 8 and #shellMasks == 8)
local r1 = math.sqrt(shellMeshes[1].P[1] ^ 2 + shellMeshes[1].P[2] ^ 2 + shellMeshes[1].P[3] ^ 2)
local r8 = math.sqrt(shellMeshes[8].P[1] ^ 2 + shellMeshes[8].P[2] ^ 2 + shellMeshes[8].P[3] ^ 2)
Out.check("shells.offset_outward", math.abs(r8 - 1.2) < 1e-4 and r1 < r8, string.format("%.3f -> %.3f", r1, r8))
local function coverage(b: buffer): number
	local n = 0
	for i = 0, 64 * 64 - 1 do
		if buffer.readu32(b, i * 4) // 16777216 > 0 then
			n += 1
		end
	end
	return n / (64 * 64)
end
local c1, c2, c5, c8 = coverage(shellMasks[1]), coverage(shellMasks[2]), coverage(shellMasks[5]), coverage(shellMasks[8])
Out.check("shells.root_solid_tips_sparse", c1 == 1 and c2 > c5 and c5 > c8, string.format("%.2f %.2f %.2f %.2f", c1, c2, c5, c8))

Out.done()
