--!strict
-- Contrast: the figure-ground gate (HIERARCHY.md §11) in code.
-- Converts sRGB to OKLab lightness (perceptual), maps it to 8 bands (B0–B7), and checks
-- that a silhouette's worst pixel is at least `minGap` bands away from the ring around it.

local Contrast = {}

local function toLinear(c: number): number
	c /= 255
	return if c <= 0.04045 then c / 12.92 else ((c + 0.055) / 1.055) ^ 2.4
end

-- OKLab L (0..1) from 8-bit sRGB.
function Contrast.lightness(r: number, g: number, b: number): number
	local lr, lg, lb = toLinear(r), toLinear(g), toLinear(b)
	local l = 0.4122214708 * lr + 0.5363325363 * lg + 0.0514459929 * lb
	local m = 0.2119034982 * lr + 0.6806995451 * lg + 0.1073969566 * lb
	local s = 0.0883024619 * lr + 0.2817188376 * lg + 0.6299787005 * lb
	l, m, s = l ^ (1 / 3), m ^ (1 / 3), s ^ (1 / 3)
	return 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s
end

-- Band centres (B0..B7). Spaced wider at the top where the eye separates highlights.
Contrast.BANDS = table.freeze({ 0.08, 0.16, 0.26, 0.38, 0.50, 0.63, 0.78, 0.93 })

function Contrast.band(L: number): number
	local best, bi = math.huge, 0
	for i, c in Contrast.BANDS do
		local d = math.abs(L - c)
		if d < best then
			best, bi = d, i - 1
		end
	end
	return bi
end

function Contrast.bandOf(rgb: { number }): number
	return Contrast.band(Contrast.lightness(rgb[1], rgb[2], rgb[3]))
end

-- Gate: every figure colour vs every ring colour, worst case. Returns ok, worstGap.
function Contrast.gate(figure: { { number } }, ring: { { number } }, minGap: number?): (boolean, number)
	local need = minGap or 2
	local worst = math.huge
	for _, f in figure do
		local bf = Contrast.bandOf(f)
		for _, r in ring do
			worst = math.min(worst, math.abs(bf - Contrast.bandOf(r)))
		end
	end
	return worst >= need, worst
end

-- Darken (or lighten) a colour by n bands while keeping its hue: scales linear RGB so the
-- OKLab L lands on the target band centre. Used for the hero's thin ring.
function Contrast.shiftBands(rgb: { number }, n: number): { number }
	local L = Contrast.lightness(rgb[1], rgb[2], rgb[3])
	local target = Contrast.BANDS[math.clamp(Contrast.band(L) + n, 0, 7) + 1]
	local k = if L > 0 then (target / L) ^ 3 else 0 -- L is ~cube-root of linear luminance
	local out = {}
	for i = 1, 3 do
		local lin = math.clamp(toLinear(rgb[i]) * k, 0, 1)
		local srgb = if lin <= 0.0031308 then lin * 12.92 else 1.055 * lin ^ (1 / 2.4) - 0.055
		out[i] = math.floor(srgb * 255 + 0.5)
	end
	return out
end

return Contrast
