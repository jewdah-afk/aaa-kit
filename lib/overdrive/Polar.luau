--!native
--!optimize 2
-- Polar: angle and radius for every pixel, computed once. Spirals, tunnels, rings, sunbursts, magic circles and
-- rotating anything then cost table reads instead of atan2 + sqrt per pixel.
-- Measured (tools/vfxbench, interpreter): a tunnel at 256² costs 6.4 ms with atan2+sqrt per pixel, 2.4 ms from a table.

local Polar = {}
Polar.__index = Polar

local readu8, writeu8, readu16 = buffer.readu8, buffer.writeu8, buffer.readu16
local floor, sin, pi = math.floor, math.sin, math.pi

export type Polar = typeof(setmetatable(
	{} :: {
		w: number,
		h: number,
		angle: buffer, -- u8 per pixel: 0..255 around the circle
		radius: buffer, -- u16 per pixel: radius * 8 (1/8 px steps)
		maxR: number,
	},
	Polar
))

function Polar.new(w: number, h: number, cx: number?, cy: number?): Polar
	local ox, oy = cx or (w - 1) / 2, cy or (h - 1) / 2
	local angle, radius = buffer.create(w * h), buffer.create(w * h * 2)
	local maxR = 0
	for y = 0, h - 1 do
		for x = 0, w - 1 do
			local dx, dy = x - ox, y - oy
			local i = y * w + x
			writeu8(angle, i, floor(256 * (math.atan2(dy, dx) / (2 * pi) + 0.5)) % 256)
			local r = math.sqrt(dx * dx + dy * dy)
			buffer.writeu16(radius, i * 2, math.min(65535, floor(r * 8 + 0.5)))
			if r > maxR then
				maxR = r
			end
		end
	end
	return setmetatable({ w = w, h = h, angle = angle, radius = radius, maxR = maxR }, Polar)
end

-- 256-entry sine table scaled to 0..amp (one period over 256 steps).
function Polar.sineTable(amp: number?): { number }
	local a = amp or 255
	local t = table.create(256)
	for i = 0, 255 do
		t[i + 1] = floor((sin(i / 256 * 2 * pi) * 0.5 + 0.5) * a + 0.5)
	end
	return t
end

-- A radial profile: profile[r8 + 1] for r8 = radius*8 in 0..maxR*8, from fn(r) -> 0..256 (a weight).
function Polar.profile(self: Polar, fn: (r: number) -> number): { number }
	local n = floor(self.maxR * 8) + 2
	local t = table.create(n)
	for i = 0, n - 1 do
		t[i + 1] = floor(fn(i / 8) + 0.5)
	end
	return t
end

-- Spiral arms into a u8 field (saturating add): arms around the circle, twisting `twist` steps per pixel of
-- radius, rotated by `phase` (0..255 = one turn), shaped by `wave` (a 256 table, e.g. sineTable) and weighted
-- by `profile` (Polar.profile). Changing only `phase` per frame rotates it.
function Polar.spiralAdd(self: Polar, dst: buffer, arms: number, twist: number, phase: number, wave: { number }, profile: { number })
	local angle, radius = self.angle, self.radius
	local ph = floor(phase) % 256
	local tw = twist / 8 -- per radius-8 unit
	for i = 0, self.w * self.h - 1 do
		local r8 = readu16(radius, i * 2)
		local wgt = profile[r8 + 1]
		if wgt > 0 then
			local a = (readu8(angle, i) * arms + floor(r8 * tw) + ph) % 256
			local v = readu8(dst, i) + (wave[a + 1] * wgt) // 256
			writeu8(dst, i, if v > 255 then 255 else v)
		end
	end
end

-- Concentric rings moving outward: wave indexed by radius*density - phase. Shockwave trains, sonar, halos.
function Polar.ringsAdd(self: Polar, dst: buffer, density: number, phase: number, wave: { number }, profile: { number })
	local radius = self.radius
	local ph = floor(phase)
	local d = density / 8
	for i = 0, self.w * self.h - 1 do
		local r8 = readu16(radius, i * 2)
		local wgt = profile[r8 + 1]
		if wgt > 0 then
			local v = readu8(dst, i) + (wave[(floor(r8 * d) - ph) % 256 + 1] * wgt) // 256
			writeu8(dst, i, if v > 255 then 255 else v)
		end
	end
end

return Polar
