--!strict
-- Recipe: a material described as data (a base plus a stack of masked layers), evaluated per texel.
-- Balance lives in data: a new look is a new recipe table, not new code.
--
-- recipe = {
--   base   = { color = {r,g,b}, rough = 0.5, metal = 0, vary = { scale = 6, amount = 0.08 } },
--   detail = { { "noise", scale = 8, octaves = 4, amp = 0.15 }, ... },   -- height everywhere
--   layers = {
--     { name = "rust", color = {..}, rough = 0.9, metal = 0, height = -0.2, opacity = 1,
--       vary = { scale = 20, amount = 0.15 },
--       mask = { { "noise", scale = 3, octaves = 5, lo = 0.1, hi = 0.3 }, { "curvature", lo = 0.55, hi = 0.7 } } },
--   },
--   normalStrength = 1,
-- }
--
-- Mask terms multiply. Each maps a field through smoothstep(lo, hi) (lo > hi inverts):
--   noise      fBm of position * scale (+ warp = domain-warp strength)    roughly -1..1
--   ridged     ridged multifractal                                         0..1
--   voronoi    F2 - F1 (0 on cell borders: cracks, tiles)  or field = "f1" / "id"
--   curvature  0.5 flat, > 0.5 convex edges, < 0.5 creases
--   ao         1 open, 0 enclosed
--   edge       distance in studs to the nearest sharp edge (wear width independent of tessellation)
--   up         normal . (0,1,0): 1 faces the sky (dust, snow, moss), -1 faces the ground
--   y          object-space height in studs (water lines, mud splash)
--   image      triplanar sample of an RGBA8 buffer (img, w, h, scale, channel 1-4): any 2D algorithm render
-- Colours are 0..1 sRGB. Everything is evaluated in object space, so it is seamless across UV islands.

local Noise = require("./Noise")

export type Ctx = {
	px: number, py: number, pz: number,
	nx: number, ny: number, nz: number,
	curv: number, ao: number, edge: number,
}

local Recipe = {}

local function smooth(lo: number, hi: number, x: number): number
	if lo == hi then
		return if x >= lo then 1 else 0
	end
	local t = math.clamp((x - lo) / (hi - lo), 0, 1)
	return t * t * (3 - 2 * t)
end

local function field(term: any, c: Ctx, px: number, py: number, pz: number): number
	local kind = term[1]
	local s = term.scale or 1
	local sx, sy, sz = px * s + (term.seed or 0) * 31.7, py * s, pz * s
	if kind == "noise" then
		if term.warp then
			return Noise.warped(sx, sy, sz, term.octaves or 4, term.warp)
		end
		return Noise.fbm(sx, sy, sz, term.octaves or 4)
	elseif kind == "ridged" then
		return Noise.ridged(sx, sy, sz, term.octaves or 4)
	elseif kind == "voronoi" then
		local f1, f2, id = Noise.voronoi(sx, sy, sz, term.jitter)
		if term.field == "f1" then
			return f1
		elseif term.field == "id" then
			return id
		end
		return f2 - f1
	elseif kind == "curvature" then
		return c.curv
	elseif kind == "ao" then
		return c.ao
	elseif kind == "edge" then
		return c.edge
	elseif kind == "up" then
		return c.ny
	elseif kind == "y" then
		return py
	elseif kind == "image" then
		local r, g, b, a = Noise.triplanar(term.img, term.w, term.h, px, py, pz, c.nx, c.ny, c.nz, s, term.sharp)
		local ch = term.channel or 1
		return if ch == 1 then r elseif ch == 2 then g elseif ch == 3 then b else a
	end
	error("unknown mask term " .. tostring(kind))
end

--- Mask value 0..1 of a term list at a position (geometry context fixed).
function Recipe.mask(terms: { any }?, c: Ctx, px: number, py: number, pz: number): number
	if not terms then
		return 1
	end
	local m = 1
	for _, term in terms do
		local v = field(term, c, px, py, pz)
		if term.lo ~= nil then
			v = smooth(term.lo, term.hi, v)
		end
		m *= v
		if m <= 0 then
			return 0
		end
	end
	return m
end

--- Height at a position: base detail + every layer's height times its mask.
function Recipe.height(r: any, c: Ctx, px: number, py: number, pz: number): number
	local h = 0
	if r.detail then
		for _, term in r.detail do
			local v = field(term, c, px, py, pz)
			if term.lo ~= nil then
				v = smooth(term.lo, term.hi, v)
			end
			h += v * (term.amp or 1)
		end
	end
	if r.layers then
		for _, L in r.layers do
			if L.height and L.height ~= 0 then
				h += L.height * Recipe.mask(L.mask, c, px, py, pz) * (L.opacity or 1)
			end
		end
	end
	return h
end

--- Full shade at the texel's own position: r, g, b, roughness, metalness, height.
function Recipe.shade(r: any, c: Ctx): (number, number, number, number, number, number)
	local base = r.base or {}
	local col = base.color or { 0.5, 0.5, 0.5 }
	local cr, cg, cb = col[1], col[2], col[3]
	local rough, metal = base.rough or 0.5, base.metal or 0
	local px, py, pz = c.px, c.py, c.pz
	if base.vary then
		local k = 1 + Noise.fbm(px * base.vary.scale, py * base.vary.scale, pz * base.vary.scale, 3) * base.vary.amount
		cr, cg, cb = cr * k, cg * k, cb * k
	end
	if r.layers then
		for _, L in r.layers do
			local m = Recipe.mask(L.mask, c, px, py, pz) * (L.opacity or 1)
			if m > 0 then
				local lc = L.color
				if lc then
					local lr, lg, lb = lc[1], lc[2], lc[3]
					if L.vary then
						local k = 1 + Noise.fbm(px * L.vary.scale + 7, py * L.vary.scale, pz * L.vary.scale, 3) * L.vary.amount
						lr, lg, lb = lr * k, lg * k, lb * k
					end
					if L.blend == "multiply" then
						lr, lg, lb = cr * lr, cg * lg, cb * lb
					end
					cr, cg, cb = cr + (lr - cr) * m, cg + (lg - cg) * m, cb + (lb - cb) * m
				end
				if L.rough then
					rough += (L.rough - rough) * m
				end
				if L.metal then
					metal += (L.metal - metal) * m
				end
			end
		end
	end
	return math.clamp(cr, 0, 1), math.clamp(cg, 0, 1), math.clamp(cb, 0, 1), math.clamp(rough, 0, 1), math.clamp(metal, 0, 1), Recipe.height(r, c, px, py, pz)
end

return Recipe
