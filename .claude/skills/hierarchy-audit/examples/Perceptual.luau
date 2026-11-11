--!strict
-- Perceptual: APCA Lc, WCAG ratio, OKLab, deltaE and colour-blind simulation for Color3 values.
-- The in-game twin of tools/hierarchy/hierarchy.py. Pure maths: runs in lune, Studio or a live server.
-- Sources: docs/research/81-contrast-colour-and-colour-blindness.md

export type RGB = { r: number, g: number, b: number } -- 0..1, same fields as Color3
export type Lab = { L: number, a: number, b: number }

local Perceptual = {}

local function lin(c: number): number
	return if c <= 0.04045 then c / 12.92 else ((c + 0.055) / 1.055) ^ 2.4
end

local function unlin(c: number): number
	c = math.clamp(c, 0, 1)
	return if c <= 0.0031308 then c * 12.92 else 1.055 * c ^ (1 / 2.4) - 0.055
end

--- WCAG relative luminance, 0..1.
function Perceptual.luminance(c: RGB): number
	return 0.2126 * lin(c.r) + 0.7152 * lin(c.g) + 0.0722 * lin(c.b)
end

--- WCAG 2.x contrast ratio, 1..21. Symmetric.
function Perceptual.wcagRatio(x: RGB, y: RGB): number
	local a, b = Perceptual.luminance(x), Perceptual.luminance(y)
	return (math.max(a, b) + 0.05) / (math.min(a, b) + 0.05)
end

-- APCA 0.0.98G-4g constants (apca-w3)
local TRC, RCO, GCO, BCO = 2.4, 0.2126729, 0.7151522, 0.0721750
local NORM_BG, NORM_TXT, REV_TXT, REV_BG = 0.56, 0.57, 0.62, 0.65
local BLK_THRS, BLK_CLMP, SCALE, OFFSET, DELTA_Y_MIN, LO_CLIP = 0.022, 1.414, 1.14, 0.027, 0.0005, 0.1

local function apcaY(c: RGB): number
	return RCO * c.r ^ TRC + GCO * c.g ^ TRC + BCO * c.b ^ TRC
end

--- APCA lightness contrast of text on bg. Positive = dark on light, negative = light on dark.
--- Floors (abs): 90 preferred body, 75 body/play-critical, 60 labels, 45 headlines/icons, 30 disabled.
function Perceptual.apcaLc(text: RGB, bg: RGB): number
	local t, b = apcaY(text), apcaY(bg)
	if t <= BLK_THRS then
		t += (BLK_THRS - t) ^ BLK_CLMP
	end
	if b <= BLK_THRS then
		b += (BLK_THRS - b) ^ BLK_CLMP
	end
	if math.abs(b - t) < DELTA_Y_MIN then
		return 0
	end
	local out
	if b > t then
		local s = (b ^ NORM_BG - t ^ NORM_TXT) * SCALE
		out = if s < LO_CLIP then 0 else s - OFFSET
	else
		local s = (b ^ REV_BG - t ^ REV_TXT) * SCALE
		out = if s > -LO_CLIP then 0 else s + OFFSET
	end
	return out * 100
end

--- OKLab (Ottosson 2020).
function Perceptual.oklab(c: RGB): Lab
	local r, g, b = lin(c.r), lin(c.g), lin(c.b)
	local l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
	local m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
	local s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
	local l_, m_, s_ = math.sign(l) * math.abs(l) ^ (1 / 3), math.sign(m) * math.abs(m) ^ (1 / 3), math.sign(s) * math.abs(s) ^ (1 / 3)
	return {
		L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
		a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
		b = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_,
	}
end

--- Inverse OKLab -> sRGB (clamped).
function Perceptual.fromOklab(p: Lab): RGB
	local l_ = p.L + 0.3963377774 * p.a + 0.2158037573 * p.b
	local m_ = p.L - 0.1055613458 * p.a - 0.0638541728 * p.b
	local s_ = p.L - 0.0894841775 * p.a - 1.2914855480 * p.b
	local l, m, s = l_ ^ 3, m_ ^ 3, s_ ^ 3
	return {
		r = unlin(4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s),
		g = unlin(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s),
		b = unlin(-0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s),
	}
end

--- Euclidean OKLab distance (~0.02 is a just-visible step for neighbouring patches; house estimate).
function Perceptual.deltaE(x: RGB, y: RGB): number
	local p, q = Perceptual.oklab(x), Perceptual.oklab(y)
	return math.sqrt((p.L - q.L) ^ 2 + (p.a - q.a) ^ 2 + (p.b - q.b) ^ 2)
end

--- Mix two colours in OKLab (no muddy midpoints). t in 0..1.
function Perceptual.mixOklab(x: RGB, y: RGB, t: number): RGB
	local p, q = Perceptual.oklab(x), Perceptual.oklab(y)
	return Perceptual.fromOklab({ L = p.L + (q.L - p.L) * t, a = p.a + (q.a - p.a) * t, b = p.b + (q.b - p.b) * t })
end

-- Machado, Oliveira & Fernandes 2009, severity 1.0, applied to linear RGB.
local CVD = {
	protan = { 0.152286, 1.052583, -0.204868, 0.114503, 0.786281, 0.099216, -0.003882, -0.048116, 1.051998 },
	deutan = { 0.367322, 0.860646, -0.227968, 0.280085, 0.672501, 0.047413, -0.011820, 0.042940, 0.968881 },
	tritan = { 1.255528, -0.076749, -0.178779, -0.078411, 0.930809, 0.147602, 0.004733, 0.691367, 0.303900 },
}

--- Simulate colour vision deficiency. kind = "protan" | "deutan" | "tritan"; severity 0..1.
function Perceptual.simulateCvd(c: RGB, kind: string, severity: number?): RGB
	local m = CVD[kind]
	assert(m, "unknown CVD type " .. kind)
	local k = severity or 1
	local r, g, b = lin(c.r), lin(c.g), lin(c.b)
	local function row(i: number, own: number): number
		local v = m[i] * r + m[i + 1] * g + m[i + 2] * b
		return own * (1 - k) + v * k
	end
	return { r = unlin(row(1, r)), g = unlin(row(4, g)), b = unlin(row(7, b)) }
end

export type Pair = { name: string, fg: RGB, bg: RGB, floor: number }
export type Finding = { name: string, lc: number, floor: number }

--- Check theme pairs against their APCA floors. Returns the failures (empty = all pass).
function Perceptual.audit(pairs: { Pair }): { Finding }
	local out = {}
	for _, p in pairs do
		local lc = Perceptual.apcaLc(p.fg, p.bg)
		if math.abs(lc) < p.floor then
			table.insert(out, { name = p.name, lc = lc, floor = p.floor })
		end
	end
	return out
end

--- Check a ladder of colours (e.g. rarities, low to high).
--- problems: adjacent steps that collapse under deutan or protan simulation (OKLab dE < 0.04). These fail.
--- warnings: adjacent steps that are close in grey (dL < 0.05 and dC < 0.04), so they need another
--- channel (frame behaviour, icon, motion) to stay apart. House thresholds; see research ch. 81.
function Perceptual.ladder(colours: { RGB }): ({ string }, { string })
	local problems, warnings = {}, {}
	for i = 2, #colours do
		local p, q = Perceptual.oklab(colours[i - 1]), Perceptual.oklab(colours[i])
		local dL = math.abs(q.L - p.L)
		local dC = math.abs(math.sqrt(q.a ^ 2 + q.b ^ 2) - math.sqrt(p.a ^ 2 + p.b ^ 2))
		if dL < 0.05 and dC < 0.04 then
			table.insert(warnings, `step {i - 1}->{i}: dL {string.format("%.3f", dL)} dC {string.format("%.3f", dC)} close in grey`)
		end
		for _, kind in { "deutan", "protan" } do
			local d = Perceptual.deltaE(Perceptual.simulateCvd(colours[i - 1], kind), Perceptual.simulateCvd(colours[i], kind))
			if d < 0.04 then
				table.insert(problems, `step {i - 1}->{i}: {kind} dE {string.format("%.3f", d)} collapses`)
			end
		end
	end
	return problems, warnings
end

--- Hex "#rrggbb" or "#rgb" -> RGB.
function Perceptual.hex(s: string): RGB
	s = s:gsub("#", "")
	if #s == 3 then
		s = s:sub(1, 1):rep(2) .. s:sub(2, 2):rep(2) .. s:sub(3, 3):rep(2)
	end
	return {
		r = (tonumber(s:sub(1, 2), 16) :: number) / 255,
		g = (tonumber(s:sub(3, 4), 16) :: number) / 255,
		b = (tonumber(s:sub(5, 6), 16) :: number) / 255,
	}
end

return Perceptual
