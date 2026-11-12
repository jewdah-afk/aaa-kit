--!strict
--!native
-- StudTexture: a procedural square-stud tile (RGBA8, row-major, top-left origin: the EditableImage buffer layout).
-- Multiply semantics, because a Roblox texture can only darken the vertex colour: the flat gap between studs is
-- BASE (slightly under white), the stud top a little brighter, its top-left rim white, its bottom-right rim and the
-- drop shadow darker. GreedyMesher puts flat colours (eyes) on one UV inside the gap, so they read unstudded.
-- One tile = studsPerTile x studsPerTile studs; mesh UVs are in stud units, so the adapter divides by studsPerTile.
-- Drawn from scratch (no external stud image). The qa preview renderer samples this exact tile.

local StudTexture = {}

export type Tile = { w: number, h: number, pixels: buffer, studsPerTile: number }

local BASE, TOP, LIGHT, DARK, SHADOW = 236, 244, 255, 172, 206

-- Value of one point inside a stud cell, (u, v) in [0, 1), v down.
local function sampleStud(u: number, v: number): number
	local lo, hi, rim = 0.2, 0.8, 0.07
	local inside = u >= lo and u < hi and v >= lo and v < hi
	if inside then
		local dl, dt, dr, db = u - lo, v - lo, hi - u, hi - v
		local m = math.min(dl, dt, dr, db)
		if m < rim then
			-- rim: lit from the top-left
			if (dl == m or dt == m) and not (dr < rim * 0.6 or db < rim * 0.6) then
				return LIGHT
			end
			return DARK
		end
		return TOP
	end
	-- soft drop shadow down-right of the stud
	local su, sv = u - 0.05, v - 0.05
	if su >= lo and su < hi and sv >= lo and sv < hi then
		return SHADOW
	end
	return BASE
end

function StudTexture.generate(pxPerStud: number?, studsPerTile: number?): Tile
	local p = pxPerStud or 32
	local n = studsPerTile or 1
	local size = p * n
	local pixels = buffer.create(size * size * 4)
	local SS = 4 -- supersamples per axis (anti-aliased edges)
	for y = 0, size - 1 do
		for x = 0, size - 1 do
			local acc = 0
			for sy = 0, SS - 1 do
				for sx = 0, SS - 1 do
					local fx = ((x + (sx + 0.5) / SS) / p) % 1
					local fy = ((y + (sy + 0.5) / SS) / p) % 1
					acc += sampleStud(fx, fy)
				end
			end
			local val = math.floor(acc / (SS * SS) + 0.5)
			local o = (y * size + x) * 4
			buffer.writeu8(pixels, o, val)
			buffer.writeu8(pixels, o + 1, val)
			buffer.writeu8(pixels, o + 2, val)
			buffer.writeu8(pixels, o + 3, 255)
		end
	end
	return { w = size, h = size, pixels = pixels, studsPerTile = n }
end

StudTexture.BASE = BASE

return StudTexture
