--!strict
-- AuroraAura: a procedurally seeded aurora aura (status effect, tier 2; hero rank).
-- One seed -> an optimised cosine palette (A + B*cos(2pi(C*t + D))) plus a set of
-- folded curtain ribbons. Pure data: the Roblox side turns ribbons into Beams
-- (ColorSequence from colorKeys, TextureSpeed from speed) and never invents numbers.
--
-- Colour optimisation: draw K candidate palettes from the seed, score each on
-- chroma, hue spread and value band (aura must stay below the hero's highlight
-- band and never go muddy), keep the best. Same seed -> same aura everywhere.

local AuroraAura = {}

export type Vec3 = { number }
export type Palette = { a: Vec3, b: Vec3, c: Vec3, d: Vec3 }
export type Ribbon = {
	radius: number, -- studs from the hero's axis
	height: number, -- studs tall
	phase: number, -- 0..1 start angle around the hero
	speed: number, -- turns per second (slow: one turn >= 8 s, calm rule)
	fold: number, -- fold count along the curtain
	width: number, -- Beam width in studs
	hem: number, -- palette offset at the bottom hem (the magenta fringe)
	offset: number, -- palette offset of this ribbon
}
export type Aura = { seed: number, palette: Palette, ribbons: { Ribbon }, score: number }

-- Deterministic PRNG: mulberry32 with an exact 32-bit multiply, so the web lab
-- (Math.imul) produces the same numbers from the same seed.
local function imul(a: number, b: number): number
	local ah, al = a // 65536, a % 65536
	return (al * b + ((ah * b) % 65536) * 65536) % 4294967296
end

local function rng(seed: number): () -> number
	local s = seed % 4294967296
	return function(): number
		s = (s + 0x6D2B79F5) % 4294967296
		local t = imul(bit32.bxor(s, bit32.rshift(s, 15)), bit32.bor(s, 1))
		t = bit32.bxor(t, (t + imul(bit32.bxor(t, bit32.rshift(t, 7)), bit32.bor(t, 61))) % 4294967296)
		return bit32.bxor(t, bit32.rshift(t, 14)) / 4294967296
	end
end
AuroraAura.rng = rng

local function clamp01(x: number): number
	return if x < 0 then 0 elseif x > 1 then 1 else x
end

function AuroraAura.sample(p: Palette, t: number): (number, number, number)
	local out = table.create(3, 0)
	for i = 1, 3 do
		out[i] = clamp01(p.a[i] + p.b[i] * math.cos(2 * math.pi * (p.c[i] * t + p.d[i])))
	end
	return out[1], out[2], out[3]
end

local function luma(r: number, g: number, b: number): number
	return 0.2126 * r + 0.7152 * g + 0.0722 * b
end

-- Score a palette over 32 samples. Higher is better.
function AuroraAura.score(p: Palette): number
	local chroma, lumaSum, lumaMax, lumaMin = 0, 0, 0, 1
	local hx, hy = 0, 0
	for i = 0, 31 do
		local r, g, b = AuroraAura.sample(p, i / 31)
		local mx, mn = math.max(r, g, b), math.min(r, g, b)
		local c = mx - mn
		chroma += c
		local l = luma(r, g, b)
		lumaSum += l
		lumaMax = math.max(lumaMax, l)
		lumaMin = math.min(lumaMin, l)
		-- hue direction on the opponent plane, weighted by chroma
		local ox, oy = r - 0.5 * (g + b), 0.866 * (g - b)
		local len = math.sqrt(ox * ox + oy * oy) + 1e-6
		hx += ox / len
		hy += oy / len
	end
	chroma /= 32
	local mean = lumaSum / 32
	local spread = 1 - math.sqrt(hx * hx + hy * hy) / 32 -- 0 = one hue, 1 = all around
	local s = chroma * 2 + math.min(spread, 0.55) -- two to three hue families, not a rainbow
	if lumaMax > 0.82 then -- the hero's highlight band is reserved
		s -= (lumaMax - 0.82) * 6
	end
	if mean < 0.22 or mean > 0.55 then
		s -= 1
	end
	if lumaMax - lumaMin < 0.25 then -- flat = no curtain depth
		s -= 0.5
	end
	return s
end

local function candidate(r: () -> number): Palette
	local a, b, c, d = {}, {}, {}, {}
	local base = 0.35 + r() * 0.2
	local harmonic = if r() < 0.6 then 1 else 0.5
	for i = 1, 3 do
		a[i] = base + (r() - 0.5) * 0.15
		b[i] = 0.3 + r() * 0.25
		c[i] = harmonic * (if r() < 0.7 then 1 else 0.5 + math.floor(r() * 3) * 0.5)
		d[i] = r()
	end
	return { a = a, b = b, c = c, d = d }
end

function AuroraAura.new(seed: number, candidates: number?): Aura
	local r = rng(seed)
	local best: Palette, bestScore = candidate(r), -math.huge
	bestScore = AuroraAura.score(best)
	for _ = 2, candidates or 12 do
		local p = candidate(r)
		local s = AuroraAura.score(p)
		if s > bestScore then
			best, bestScore = p, s
		end
	end
	local ribbons = {}
	local count = 3 + math.floor(r() * 3) -- 3..5 curtains: one hero + supports
	local dir = if r() < 0.5 then -1 else 1
	for i = 1, count do
		local lead = i == 1
		table.insert(ribbons, {
			radius = (if lead then 2.2 else 2.6 + r() * 1.4),
			height = (if lead then 7 else 4.5 + r() * 3),
			phase = (i - 1) / count + (r() - 0.5) * 0.15,
			speed = dir * (0.05 + r() * 0.07),
			fold = 2 + math.floor(r() * 4),
			width = (if lead then 1.6 else 0.8 + r() * 0.8),
			hem = 0.25 + r() * 0.2,
			offset = r(),
		})
	end
	return { seed = seed, palette = best, ribbons = ribbons, score = bestScore }
end

-- n keyframes for a ribbon's ColorSequence: {time, r, g, b}. Hem at time 0.
function AuroraAura.colorKeys(aura: Aura, ribbon: Ribbon, n: number): { { number } }
	local keys = {}
	for i = 0, n - 1 do
		local t = i / (n - 1)
		local r, g, b = AuroraAura.sample(aura.palette, ribbon.offset + (1 - t) * ribbon.hem)
		table.insert(keys, { t, r, g, b })
	end
	return keys
end

-- Budget by intensity rung (HIERARCHY.md section 4). The aura is a status effect:
-- full at calm/build, thinned at surge, a faint lead curtain only at boss and above.
local RUNG = {
	[0] = { ribbons = 5, particles = 1, alpha = 1 },
	[1] = { ribbons = 5, particles = 1, alpha = 1 },
	[2] = { ribbons = 2, particles = 0.3, alpha = 0.6 },
	[3] = { ribbons = 1, particles = 0, alpha = 0.4 },
	[4] = { ribbons = 1, particles = 0, alpha = 0.35 },
	[5] = { ribbons = 1, particles = 0, alpha = 0.3 },
}
function AuroraAura.budget(rung: number)
	return RUNG[math.clamp(math.floor(rung), 0, 5)]
end

return AuroraAura
