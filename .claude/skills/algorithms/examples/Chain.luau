--!strict
-- Chain: the "Godrithm" idea in miniature. A look is a chain of small, typed passes over
-- a scalar field, each doing one job. Swapping or re-ordering passes gives a new look
-- with no new code. Deterministic: the same seed always gives the same field.
--
--   noise → warp → threshold → distance → bands
--   (shape)  (life)  (masks)   (edges/glow) (palette steps)

local Chain = {}

export type Field = { w: number, h: number, v: { number } }
export type Pass = (Field) -> Field

local function field(w: number, h: number): Field
	return { w = w, h = h, v = table.create(w * h, 0) }
end

-- Hash-based value noise (no global RNG, so it's seedable and stable across runs).
local function hash(x: number, y: number, seed: number): number
	local s = math.sin(x * 127.1 + y * 311.7 + seed * 74.7) * 43758.5453
	return s - math.floor(s)
end

local function vnoise(x: number, y: number, seed: number): number
	local xi, yi = math.floor(x), math.floor(y)
	local xf, yf = x - xi, y - yi
	local u, v = xf * xf * (3 - 2 * xf), yf * yf * (3 - 2 * yf)
	local a, b = hash(xi, yi, seed), hash(xi + 1, yi, seed)
	local c, d = hash(xi, yi + 1, seed), hash(xi + 1, yi + 1, seed)
	return (a * (1 - u) + b * u) * (1 - v) + (c * (1 - u) + d * u) * v
end

-- fBm: `octaves` layers of noise, each at double frequency and half amplitude.
function Chain.noise(w: number, h: number, scale: number, octaves: number, seed: number): Field
	local f = field(w, h)
	for y = 0, h - 1 do
		for x = 0, w - 1 do
			local amp, freq, sum, norm = 0.5, 1 / scale, 0, 0
			for o = 1, octaves do
				sum += amp * vnoise(x * freq, y * freq, seed + o)
				norm += amp
				amp *= 0.5
				freq *= 2
			end
			f.v[y * w + x + 1] = sum / norm
		end
	end
	return f
end

-- Domain warp: sample the field at a position pushed by a second noise (organic swirl).
function Chain.warp(strength: number, scale: number, seed: number): Pass
	return function(src: Field): Field
		local out = field(src.w, src.h)
		for y = 0, src.h - 1 do
			for x = 0, src.w - 1 do
				local dx = (vnoise(x / scale, y / scale, seed) - 0.5) * 2 * strength
				local dy = (vnoise(x / scale + 31.4, y / scale + 17.3, seed) - 0.5) * 2 * strength
				local sx = math.clamp(math.floor(x + dx + 0.5), 0, src.w - 1)
				local sy = math.clamp(math.floor(y + dy + 0.5), 0, src.h - 1)
				out.v[y * src.w + x + 1] = src.v[sy * src.w + sx + 1]
			end
		end
		return out
	end
end

function Chain.threshold(t: number): Pass
	return function(src: Field): Field
		local out = field(src.w, src.h)
		for i, v in src.v do
			out.v[i] = if v >= t then 1 else 0
		end
		return out
	end
end

-- Chamfer distance transform (two passes) from every "1" cell, in cells. Gives outlines,
-- glows and bevels from any mask.
function Chain.distance(): Pass
	return function(src: Field): Field
		local w, h, INF = src.w, src.h, 1e9
		local d = field(w, h)
		for i, v in src.v do
			d.v[i] = if v > 0 then 0 else INF
		end
		local function at(x: number, y: number): number
			return d.v[y * w + x + 1]
		end
		for y = 0, h - 1 do
			for x = 0, w - 1 do
				local i = y * w + x + 1
				local best = d.v[i]
				if x > 0 then best = math.min(best, at(x - 1, y) + 1) end
				if y > 0 then best = math.min(best, at(x, y - 1) + 1) end
				if x > 0 and y > 0 then best = math.min(best, at(x - 1, y - 1) + 1.4142) end
				if x < w - 1 and y > 0 then best = math.min(best, at(x + 1, y - 1) + 1.4142) end
				d.v[i] = best
			end
		end
		for y = h - 1, 0, -1 do
			for x = w - 1, 0, -1 do
				local i = y * w + x + 1
				local best = d.v[i]
				if x < w - 1 then best = math.min(best, at(x + 1, y) + 1) end
				if y < h - 1 then best = math.min(best, at(x, y + 1) + 1) end
				if x < w - 1 and y < h - 1 then best = math.min(best, at(x + 1, y + 1) + 1.4142) end
				if x > 0 and y < h - 1 then best = math.min(best, at(x - 1, y + 1) + 1.4142) end
				d.v[i] = best
			end
		end
		return d
	end
end

-- Quantise into `n` equal bands (0..n-1) after clamping to [0, maxValue]: cel steps.
function Chain.bands(n: number, maxValue: number): Pass
	return function(src: Field): Field
		local out = field(src.w, src.h)
		for i, v in src.v do
			out.v[i] = math.min(n - 1, math.floor(math.clamp(v / maxValue, 0, 1) * n))
		end
		return out
	end
end

function Chain.run(start: Field, passes: { Pass }): Field
	local f = start
	for _, p in passes do
		f = p(f)
	end
	return f
end

return Chain
