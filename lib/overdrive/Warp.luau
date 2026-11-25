--!native
--!optimize 2
-- Warp: move a whole image along a flow field for one tap per pixel. The flow is evaluated only at the nodes of a
-- coarse grid (every `cell` pixels) and interpolated in between, the way Milkdrop's per-vertex warp mesh works.
-- Feed the previous frame through it with a fade and you get smoke, accretion swirls, portals, heat haze and
-- long trails for the price of one pass (the "feedback buffer").
-- Measured (tools/vfxbench, interpreter): a swirl with exp/cos/sin/sqrt per pixel 5.8 ms at 256²; on an 8 px grid 2.9 ms.
--
-- Sampling: nearest is one tap but sticks when the flow moves less than half a pixel per frame. `jitter = true`
-- adds a per-pixel offset from a 4x4 ordered pattern that rotates every frame, so one nearest tap averages to a
-- bilinear sample over a few frames (stochastic bilinear). With feedback, the average happens for free.

local Warp = {}
Warp.__index = Warp

local readu8, writeu8, readu32, writeu32 = buffer.readu8, buffer.writeu8, buffer.readu32, buffer.writeu32
local floor = math.floor

export type Warp = typeof(setmetatable(
	{} :: {
		w: number,
		h: number,
		cell: number,
		gw: number,
		gh: number,
		gu: { number },
		gv: { number },
		frame: number,
	},
	Warp
))

-- 4x4 Bayer offsets in [-0.5, 0.5), indexed (y%4)*4 + x%4; each frame shifts the pattern.
local BAYER = { 0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5 }
local JX, JY = table.create(16), table.create(16)
for i = 1, 16 do
	JX[i] = BAYER[i] / 16 - 0.5 + 1 / 32
	JY[i] = BAYER[((i + 5) % 16) + 1] / 16 - 0.5 + 1 / 32
end

function Warp.new(w: number, h: number, cell: number?): Warp
	local c = cell or 8
	local gw, gh = (w + c - 1) // c + 1, (h + c - 1) // c + 1
	return setmetatable({
		w = w,
		h = h,
		cell = c,
		gw = gw,
		gh = gh,
		gu = table.create(gw * gh, 0),
		gv = table.create(gw * gh, 0),
		frame = 0,
	}, Warp)
end

-- Set the flow: fn(x, y) returns the source position (u, v) to fetch for destination pixel (x, y).
-- Called once per grid node, so it can afford real maths (noise, trig, attractors).
function Warp.set(self: Warp, fn: (x: number, y: number) -> (number, number))
	local c, gw = self.cell, self.gw
	local gu, gv = self.gu, self.gv
	for gy = 0, self.gh - 1 do
		for gx = 0, gw - 1 do
			local u, v = fn(gx * c, gy * c)
			gu[gy * gw + gx + 1], gv[gy * gw + gx + 1] = u, v
		end
	end
end

-- Warp a u8 field: dst(x, y) = src(u, v) * fade / 256 (0 outside). fade in 0..256; 256 keeps it.
function Warp.applyField(self: Warp, src: buffer, dst: buffer, fade: number?, jitter: boolean?)
	local w, h, c, gw = self.w, self.h, self.cell, self.gw
	local gu, gv = self.gu, self.gv
	local k = fade or 256
	local jit = jitter == true
	self.frame += 1
	local shift = self.frame % 16
	local invc = 1 / c
	for gy = 0, self.gh - 2 do
		local y0 = gy * c
		if y0 >= h then
			break
		end
		local yEnd = math.min(c, h - y0) - 1
		for gx = 0, gw - 2 do
			local x0 = gx * c
			if x0 >= w then
				break
			end
			local xEnd = math.min(c, w - x0) - 1
			local n = gy * gw + gx + 1
			local u00, v00, u10, v10 = gu[n], gv[n], gu[n + 1], gv[n + 1]
			local u01, v01, u11, v11 = gu[n + gw], gv[n + gw], gu[n + gw + 1], gv[n + gw + 1]
			for j = 0, yEnd do
				local fy = j * invc
				local ul, vl = u00 + (u01 - u00) * fy, v00 + (v01 - v00) * fy
				local du = ((u10 + (u11 - u10) * fy) - ul) * invc
				local dv = ((v10 + (v11 - v10) * fy) - vl) * invc
				local y = y0 + j
				local o = y * w + x0
				local jrow = (y % 4) * 4
				for i = 0, xEnd do
					local su, sv = ul, vl
					if jit then
						local q = (jrow + ((x0 + i + shift) % 4) + shift) % 16 + 1
						su += JX[q]
						sv += JY[q]
					end
					local iu, iv = floor(su + 0.5), floor(sv + 0.5)
					if iu >= 0 and iu < w and iv >= 0 and iv < h then
						writeu8(dst, o, (readu8(src, iv * w + iu) * k) // 256)
					else
						writeu8(dst, o, 0)
					end
					ul += du
					vl += dv
					o += 1
				end
			end
		end
	end
end

-- Warp an RGBA8 image (nearest; outside -> `outside` colour, default transparent).
function Warp.applyRGBA(self: Warp, src: buffer, dst: buffer, outside: number?)
	local w, h, c, gw = self.w, self.h, self.cell, self.gw
	local gu, gv = self.gu, self.gv
	local out = outside or 0
	local invc = 1 / c
	for gy = 0, self.gh - 2 do
		local y0 = gy * c
		if y0 >= h then
			break
		end
		local yEnd = math.min(c, h - y0) - 1
		for gx = 0, gw - 2 do
			local x0 = gx * c
			if x0 >= w then
				break
			end
			local xEnd = math.min(c, w - x0) - 1
			local n = gy * gw + gx + 1
			local u00, v00, u10, v10 = gu[n], gv[n], gu[n + 1], gv[n + 1]
			local u01, v01, u11, v11 = gu[n + gw], gv[n + gw], gu[n + gw + 1], gv[n + gw + 1]
			for j = 0, yEnd do
				local fy = j * invc
				local ul, vl = u00 + (u01 - u00) * fy, v00 + (v01 - v00) * fy
				local du = ((u10 + (u11 - u10) * fy) - ul) * invc
				local dv = ((v10 + (v11 - v10) * fy) - vl) * invc
				local o = ((y0 + j) * w + x0) * 4
				for _ = 0, xEnd do
					local iu, iv = floor(ul + 0.5), floor(vl + 0.5)
					if iu >= 0 and iu < w and iv >= 0 and iv < h then
						writeu32(dst, o, readu32(src, (iv * w + iu) * 4))
					else
						writeu32(dst, o, out)
					end
					ul += du
					vl += dv
					o += 4
				end
			end
		end
	end
end

-- Common flows. Each returns fn(x, y) -> (u, v) for Warp.set.

-- Swirl + zoom about (cx, cy): rotate by `spin` radians at the centre falling off with radius (scale `reach`),
-- and pull inward by `pull` (0.02 = 2% per frame). The accretion-disk / vortex / portal motion.
function Warp.vortex(cx: number, cy: number, spin: number, reach: number, pull: number)
	return function(x: number, y: number): (number, number)
		local dx, dy = x - cx, y - cy
		local r2 = dx * dx + dy * dy
		local a = spin * math.exp(-r2 / (reach * reach))
		local c, s = math.cos(a), math.sin(a)
		local z = 1 - pull
		return (dx * c - dy * s) * z + cx, (dx * s + dy * c) * z + cy
	end
end

-- Radial lens about (cx, cy): fetch from closer to (strength < 0) or further from (> 0) the centre, peaking at
-- radius r0 and fading by `width`. Use on a copy of the scene for gravitational lensing or a shockwave ring.
function Warp.lens(cx: number, cy: number, r0: number, width: number, strength: number)
	return function(x: number, y: number): (number, number)
		local dx, dy = x - cx, y - cy
		local r = math.sqrt(dx * dx + dy * dy) + 1e-6
		local d = (r - r0) / width
		local push = strength * math.exp(-d * d)
		local k = (r + push) / r
		return dx * k + cx, dy * k + cy
	end
end

return Warp
