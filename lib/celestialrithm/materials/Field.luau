--!strict
--!native
--!optimize 2
-- Field: shared primitives for the Celestialrithm runtime materials.
-- Pure Luau, deterministic for a seed, no Roblox APIs. Port of tools/celestialrithm/foundry/fields.py
-- and the parts of optics.py the runtime needs (ramp, tonemap, sRGB encode, blackbody).
--
-- Everything that allocates (noise tables, ramps, LUTs, cell caches, upsamplers, scratch buffers)
-- is a constructor, called once per material. The per-pixel functions (noise3, fbm, ridged, worley,
-- hash01, put) never allocate.

local Field = {}

local floor, sqrt, exp, cos, sin, abs = math.floor, math.sqrt, math.exp, math.cos, math.sin, math.abs
local band, bxor, bor, rshift, lshift = bit32.band, bit32.bxor, bit32.bor, bit32.rshift, bit32.lshift
local writeu32 = buffer.writeu32

-- ---------------------------------------------------------------- data
-- Quality tiers: `scale` is the field resolution relative to the face, `octaves` is added to every
-- fbm/ridged octave count (never below 1), `simSteps` multiplies simulation substeps.
Field.QUALITY = {
	high = { scale = 1.0, octaves = 0 },
	mid = { scale = 0.5, octaves = 0 },
	low = { scale = 0.5, octaves = -2 },
}

local TONE_SHOULDER = 0.85 -- optics.tonemap shoulder: linear below, soft-clipped above
local TONE_WHITE = 0.35 -- hot cores desaturate to white: white = clamp((lum - 1) * 0.35)
local SRGB_LUT_SIZE = 4096
local ALPHA = 4278190080 -- 255 << 24

-- ---------------------------------------------------------------- integer hashing
-- 32-bit multiply without losing bits in a double: split b into 16-bit halves.
local function mul32(a: number, b: number): number
	local bl = band(b, 0xffff)
	local bh = rshift(b, 16)
	return band(a * bl + lshift(band(a * bh, 0xffff), 16), 0xffffffff)
end
Field.mul32 = mul32

-- Integer hash -> [0, 1). Bit-exact port of fields.hash01 for non-negative inputs < 2^32.
local function hash01(i: number): number
	i = band(i, 0xffffffff)
	i = band(bxor(bxor(i, 61), rshift(i, 16)) * 9, 0xffffffff)
	i = mul32(bxor(i, rshift(i, 4)), 0x27d4eb2d)
	i = bxor(i, rshift(i, 15))
	return band(i, 0xffffff) / 16777216
end
Field.hash01 = hash01

-- Worley cell hash: bit-exact port of the hash inside fields.voronoi (|cx|, |cy| < 2^20).
local function cellHash(cx: number, cy: number, seedTerm: number): number
	local h = band(cx * 374761393 + cy * 668265263 + seedTerm, 0x7fffffff)
	return band(mul32(bxor(h, rshift(h, 13)), 1274126177), 0x7fffffff)
end
Field.cellHash = cellHash

-- mulberry32: tiny deterministic PRNG. State lives in a one-field table so callers can share it.
export type Rng = { s: number }

function Field.rng(seed: number): Rng
	return { s = band(floor(seed) * 2654435761 + 0x9e3779b9, 0xffffffff) }
end

function Field.rand(r: Rng): number
	local s = band(r.s + 0x6D2B79F5, 0xffffffff)
	r.s = s
	local t = mul32(bxor(s, rshift(s, 15)), bor(s, 1))
	t = bxor(t, band(t + mul32(bxor(t, rshift(t, 7)), bor(t, 61)), 0xffffffff))
	return bxor(t, rshift(t, 14)) / 4294967296
end

function Field.uniform(r: Rng, a: number, b: number): number
	return a + (b - a) * Field.rand(r)
end

-- ---------------------------------------------------------------- gradient noise
-- 3D gradient (Perlin-style) noise on a permutation table; time is the third axis, so motion
-- evolves instead of sliding. Same construction as fields.Noise (unit gradients, quintic fade,
-- x1.6 gain), different random tables, so values differ but statistics match.
export type Noise = { perm: { number }, gx: { number }, gy: { number }, gz: { number } }

function Field.noise(seed: number): Noise
	local r = Field.rng(seed)
	local p = table.create(512, 0)
	for i = 1, 256 do
		p[i] = i - 1
	end
	for i = 256, 2, -1 do
		local j = floor(Field.rand(r) * i) + 1
		p[i], p[j] = p[j], p[i]
	end
	for i = 1, 256 do
		p[i + 256] = p[i]
	end
	local gx, gy, gz = table.create(256, 0), table.create(256, 0), table.create(256, 0)
	for i = 1, 256 do
		local z = Field.rand(r) * 2 - 1
		local a = Field.rand(r) * 6.283185307179586
		local q = sqrt(1 - z * z)
		gx[i], gy[i], gz[i] = q * cos(a), q * sin(a), z
	end
	return { perm = p, gx = gx, gy = gy, gz = gz }
end

local function noise3(n: Noise, x: number, y: number, z: number): number
	local xi, yi, zi = floor(x), floor(y), floor(z)
	local xf, yf, zf = x - xi, y - yi, z - zi
	xi = band(xi, 255)
	yi = band(yi, 255)
	zi = band(zi, 255)
	local u = xf * xf * xf * (xf * (xf * 6 - 15) + 10)
	local v = yf * yf * yf * (yf * (yf * 6 - 15) + 10)
	local w = zf * zf * zf * (zf * (zf * 6 - 15) + 10)
	local p, gx, gy, gz = n.perm, n.gx, n.gy, n.gz
	local a = p[xi + 1]
	local b = p[xi + 2]
	local aa = p[a + yi + 1] + zi
	local ab = p[a + yi + 2] + zi
	local ba = p[b + yi + 1] + zi
	local bb = p[b + yi + 2] + zi
	local x1, y1, z1 = xf - 1, yf - 1, zf - 1
	local h = p[aa + 1] + 1
	local n000 = gx[h] * xf + gy[h] * yf + gz[h] * zf
	h = p[ba + 1] + 1
	local n100 = gx[h] * x1 + gy[h] * yf + gz[h] * zf
	h = p[ab + 1] + 1
	local n010 = gx[h] * xf + gy[h] * y1 + gz[h] * zf
	h = p[bb + 1] + 1
	local n110 = gx[h] * x1 + gy[h] * y1 + gz[h] * zf
	h = p[aa + 2] + 1
	local n001 = gx[h] * xf + gy[h] * yf + gz[h] * z1
	h = p[ba + 2] + 1
	local n101 = gx[h] * x1 + gy[h] * yf + gz[h] * z1
	h = p[ab + 2] + 1
	local n011 = gx[h] * xf + gy[h] * y1 + gz[h] * z1
	h = p[bb + 2] + 1
	local n111 = gx[h] * x1 + gy[h] * y1 + gz[h] * z1
	local nx00 = n000 + (n100 - n000) * u
	local nx10 = n010 + (n110 - n010) * u
	local nx01 = n001 + (n101 - n001) * u
	local nx11 = n011 + (n111 - n011) * u
	local ny0 = nx00 + (nx10 - nx00) * v
	local ny1 = nx01 + (nx11 - nx01) * v
	return (ny0 + (ny1 - ny0) * w) * 1.6
end
Field.noise3 = noise3

-- fbm with the reference's per-octave offsets (17.3, -9.1) and time stretch (1 + 0.35 i).
function Field.fbm(n: Noise, x: number, y: number, z: number, octaves: number, lac: number, gain: number): number
	local a, f, s, norm = 1, 1, 0, 0
	for i = 0, octaves - 1 do
		s += a * noise3(n, x * f + 17.3 * i, y * f - 9.1 * i, z * (1 + 0.35 * i))
		norm += a
		a *= gain
		f *= lac
	end
	return s / norm
end

-- Ridged multifractal: sharp bright filaments; each octave is weighted by the previous ridge.
function Field.ridged(n: Noise, x: number, y: number, z: number, octaves: number, lac: number, gain: number): number
	local a, f, s, norm, prev = 1, 1, 0, 0, 1
	for i = 0, octaves - 1 do
		local r = 1 - abs(noise3(n, x * f + 5.7 * i, y * f + 3.3 * i, z * (1 + 0.4 * i)))
		r = r * r * prev
		prev = r * 1.6
		if prev > 1 then
			prev = 1
		end
		s += a * r
		norm += a
		a *= gain
		f *= lac
	end
	return s / norm
end

-- Octave count after the quality tier's adjustment (never below 1).
function Field.octaves(base: number, quality: string): number
	local q = Field.QUALITY[quality]
	local o = base + (if q then q.octaves else 0)
	return if o < 1 then 1 else o
end

-- ---------------------------------------------------------------- Worley
-- Feature points wander on circles over time (as fields.voronoi). A CellCache holds the points of a
-- window of cells for one frame, so per-pixel lookups are 9 table reads + distances instead of
-- 9 hashes + 18 trig calls. Lookups outside the window fall back to computing the point directly.
export type CellCache = {
	ncx: number,
	ncy: number,
	cx0: number,
	cy0: number,
	seedTerm: number,
	t: number,
	jitter: number,
	wander: number,
	px: { number },
	py: { number },
	id: { number },
}

function Field.cellCache(ncx: number, ncy: number): CellCache
	local n = ncx * ncy
	return {
		ncx = ncx,
		ncy = ncy,
		cx0 = 0,
		cy0 = 0,
		seedTerm = 0,
		t = 0,
		jitter = 0.85,
		wander = 0.25,
		px = table.create(n, 0),
		py = table.create(n, 0),
		id = table.create(n, 0),
	}
end

local function cellPoint(cx: number, cy: number, seedTerm: number, t: number, jitter: number, wander: number): (number, number, number)
	local h = cellHash(cx, cy, seedTerm)
	local r1 = band(h, 0xffff) / 65535
	local r2 = band(rshift(h, 16), 0x7fff) / 32767
	local ph = r1 * 6.2832 + t * (0.6 + r2)
	return cx + 0.5 + jitter * (r1 - 0.5) + wander * cos(ph), cy + 0.5 + jitter * (r2 - 0.5) + wander * sin(ph * 1.3), h
end

-- Fill the cache for cells [cx0, cx0 + ncx) x [cy0, cy0 + ncy) at time t.
function Field.fillCells(c: CellCache, cx0: number, cy0: number, seed: number, t: number, jitter: number, wander: number)
	local seedTerm = (seed % 65536) * 2147483647
	c.cx0, c.cy0, c.seedTerm, c.t, c.jitter, c.wander = cx0, cy0, seedTerm, t, jitter, wander
	local px, py, id, ncx = c.px, c.py, c.id, c.ncx
	for j = 0, c.ncy - 1 do
		for i = 0, ncx - 1 do
			local k = j * ncx + i + 1
			px[k], py[k], id[k] = cellPoint(cx0 + i, cy0 + j, seedTerm, t, jitter, wander)
		end
	end
end

-- F1, F2, nearest cell id and the offset (point - p) to the nearest point.
function Field.worley(c: CellCache, x: number, y: number): (number, number, number, number, number)
	local xi, yi = floor(x), floor(y)
	local d1, d2, cid, ox, oy = 81, 81, 0, 0, 0
	local px, py, id, ncx, ncy = c.px, c.py, c.id, c.ncx, c.ncy
	local bx, by = xi - c.cx0, yi - c.cy0
	for oyy = -1, 1 do
		local j = by + oyy
		for oxx = -1, 1 do
			local i = bx + oxx
			local qx, qy, h
			if i >= 0 and i < ncx and j >= 0 and j < ncy then
				local k = j * ncx + i + 1
				qx, qy, h = px[k], py[k], id[k]
			else
				qx, qy, h = cellPoint(xi + oxx, yi + oyy, c.seedTerm, c.t, c.jitter, c.wander)
			end
			local dx, dy = qx - x, qy - y
			local d = dx * dx + dy * dy
			if d < d1 then
				d2 = d1
				d1, cid, ox, oy = d, h, dx, dy
			elseif d < d2 then
				d2 = d
			end
		end
	end
	return sqrt(d1), sqrt(d2), cid, ox, oy
end

-- ---------------------------------------------------------------- scalar helpers
function Field.smoothstep(a: number, b: number, x: number): number
	local t = (x - a) / (b - a)
	if t < 0 then
		t = 0
	elseif t > 1 then
		t = 1
	end
	return t * t * (3 - 2 * t)
end

function Field.clamp01(x: number): number
	return if x < 0 then 0 elseif x > 1 then 1 else x
end

-- ---------------------------------------------------------------- colour
local function srgbToLinear(c: number): number
	return if c <= 0.04045 then c / 12.92 else ((c + 0.055) / 1.055) ^ 2.4
end

local function linearToSrgb(c: number): number
	if c <= 0 then
		return 0
	end
	return if c <= 0.0031308 then c * 12.92 else 1.055 * c ^ (1 / 2.4) - 0.055
end

-- '#rrggbb' -> linear RGB (as optics.hex_rgb).
function Field.hex(h: string): (number, number, number)
	local r = tonumber(h:sub(2, 3), 16) or 0
	local g = tonumber(h:sub(4, 5), 16) or 0
	local b = tonumber(h:sub(6, 7), 16) or 0
	return srgbToLinear(r / 255), srgbToLinear(g / 255), srgbToLinear(b / 255)
end

-- Piecewise-linear colour ramp baked into an n-entry LUT (linear RGB, times `gain`).
-- stops = { { pos, "#hex" }, ... } sorted by pos. Lookup: Field.rampIndex(lut, t).
export type Ramp = { n: number, r: { number }, g: { number }, b: { number } }

function Field.ramp(stops: { { any } }, n: number?, gain: number?): Ramp
	local size = n or 256
	local k = gain or 1
	local r, g, b = table.create(size, 0), table.create(size, 0), table.create(size, 0)
	local cols = {}
	for i, s in stops do
		local cr, cg, cb = Field.hex(s[2] :: string)
		cols[i] = { s[1] :: number, cr, cg, cb }
	end
	for i = 1, size do
		local t = (i - 1) / (size - 1)
		local j = 1
		while j < #cols - 1 and t >= cols[j + 1][1] do
			j += 1
		end
		local a, c = cols[j], cols[j + 1]
		local f = Field.clamp01((t - a[1]) / math.max(c[1] - a[1], 1e-6))
		r[i] = (a[2] + (c[2] - a[2]) * f) * k
		g[i] = (a[3] + (c[3] - a[3]) * f) * k
		b[i] = (a[4] + (c[4] - a[4]) * f) * k
	end
	return { n = size, r = r, g = g, b = b }
end

-- 1-based LUT index for t in [0, 1] (clamped).
function Field.rampIndex(lut: Ramp, t: number): number
	if t <= 0 then
		return 1
	elseif t >= 1 then
		return lut.n
	end
	return floor(t * (lut.n - 1) + 0.5) + 1
end

local SRGB = table.create(SRGB_LUT_SIZE, 0)
for i = 1, SRGB_LUT_SIZE do
	local v = floor(linearToSrgb((i - 1) / (SRGB_LUT_SIZE - 1)) * 255 + 0.5)
	SRGB[i] = if v > 255 then 255 elseif v < 0 then 0 else v
end
local SRGB_SCALE = SRGB_LUT_SIZE - 1

-- Tonemap (optics.tonemap, exposure 1) + sRGB encode + opaque alpha, one u32 write.
-- r, g, b are linear; o is a byte offset.
local function put(buf: buffer, o: number, r: number, g: number, b: number)
	local lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
	local sh = TONE_SHOULDER
	local k = 1 - sh
	if r > sh then
		r = sh + k * (1 - exp(-(r - sh) / k))
	end
	if g > sh then
		g = sh + k * (1 - exp(-(g - sh) / k))
	end
	if b > sh then
		b = sh + k * (1 - exp(-(b - sh) / k))
	end
	if lum > 1 then
		local wt = (lum - 1) * TONE_WHITE
		if wt > 1 then
			wt = 1
		end
		r = r * (1 - wt) + wt
		g = g * (1 - wt) + wt
		b = b * (1 - wt) + wt
	end
	-- NaN guard: (x ~= x) fails every comparison, so map it to 0 explicitly.
	local ir = if r > 0 then (if r < 1 then floor(r * SRGB_SCALE + 0.5) else SRGB_SCALE) else 0
	local ig = if g > 0 then (if g < 1 then floor(g * SRGB_SCALE + 0.5) else SRGB_SCALE) else 0
	local ib = if b > 0 then (if b < 1 then floor(b * SRGB_SCALE + 0.5) else SRGB_SCALE) else 0
	writeu32(buf, o, SRGB[ir + 1] + SRGB[ig + 1] * 256 + SRGB[ib + 1] * 65536 + ALPHA)
end
Field.put = put

-- ---------------------------------------------------------------- blackbody
-- Planck emission integrated against the CIE 1931 observer (Wyman, Sloan & Shirley 2013 fit),
-- normalised to max channel 1: optics.blackbody_lut. 512 entries over 800..12000 K, built once.
local BB_T0, BB_T1, BB_N = 800, 12000, 512
local function lobe(x: number, mu: number, s1: number, s2: number): number
	local s = if x < mu then s1 else s2
	local d = (x - mu) / s
	return exp(-0.5 * d * d)
end
local CMF_R, CMF_G, CMF_B, LAMBDA = {}, {}, {}, {}
do
	local sumG = 0
	for i = 0, 33 do
		local l = 390 + (720 - 390) * i / 33
		local X = 1.056 * lobe(l, 599.8, 37.9, 31.0) + 0.362 * lobe(l, 442.0, 16.0, 26.7) - 0.065 * lobe(l, 501.1, 20.4, 26.2)
		local Y = 0.821 * lobe(l, 568.8, 46.9, 40.5) + 0.286 * lobe(l, 530.9, 16.3, 31.1)
		local Z = 1.217 * lobe(l, 437.0, 11.8, 36.0) + 0.681 * lobe(l, 459.0, 26.0, 13.8)
		CMF_R[i + 1] = 3.2406 * X - 1.5372 * Y - 0.4986 * Z
		CMF_G[i + 1] = -0.9689 * X + 1.8758 * Y + 0.0415 * Z
		CMF_B[i + 1] = 0.0557 * X - 0.2040 * Y + 1.0570 * Z
		LAMBDA[i + 1] = l * 1e-9
		sumG += CMF_G[i + 1]
	end
	for i = 1, 34 do
		CMF_R[i] /= sumG
		CMF_G[i] /= sumG
		CMF_B[i] /= sumG
	end
end
local BB_R, BB_G, BB_B = table.create(BB_N, 0), table.create(BB_N, 0), table.create(BB_N, 0)
for k = 1, BB_N do
	local T = BB_T0 + (BB_T1 - BB_T0) * (k - 1) / (BB_N - 1)
	local r, g, b = 0, 0, 0
	for i = 1, 34 do
		local l = LAMBDA[i]
		local e = math.min(1.4387769e-2 / (l * T), 700)
		local spec = 3.741771e-16 / (l ^ 5 * (exp(e) - 1))
		r += spec * CMF_R[i]
		g += spec * CMF_G[i]
		b += spec * CMF_B[i]
	end
	r, g, b = math.max(r, 0), math.max(g, 0), math.max(b, 0)
	local m = math.max(r, g, b) + 1e-30
	BB_R[k], BB_G[k], BB_B[k] = r / m, g / m, b / m
end

-- Linear RGB (max channel 1) of a black body at temp K, nearest LUT entry.
function Field.blackbody(temp: number): (number, number, number)
	local i = floor((temp - BB_T0) / (BB_T1 - BB_T0) * (BB_N - 1))
	if i < 0 then
		i = 0
	elseif i > BB_N - 1 then
		i = BB_N - 1
	end
	return BB_R[i + 1], BB_G[i + 1], BB_B[i + 1]
end

-- ---------------------------------------------------------------- resolution
-- Field size for a face and tier. x runs [0, fw/fh], y runs [0, 1] in either size, so fields are
-- resolution independent; only pixel-unit constants scale by `s`.
function Field.fieldSize(width: number, height: number, quality: string): (number, number, number)
	local q = Field.QUALITY[quality]
	assert(q, "unknown quality tier: " .. tostring(quality))
	local fw = math.max(1, floor(width * q.scale + 0.5))
	local fh = math.max(1, floor(height * q.scale + 0.5))
	return fw, fh, fh / height
end

-- Bilinear RGBA8 upsampler (pixel-centre aligned, edge clamped, like fields.resize). Weights are
-- quantised to 1/16 per axis and two channels are blended per multiply (SWAR on 0x00ff00ff lanes).
export type Upsampler = {
	sw: number,
	sh: number,
	dw: number,
	dh: number,
	x0: { number },
	x1: { number },
	wx: { number },
	y0: { number },
	y1: { number },
	wy: { number },
}

function Field.upsampler(sw: number, sh: number, dw: number, dh: number): Upsampler
	local function axis(src: number, dst: number): ({ number }, { number }, { number })
		local a, b, w = table.create(dst, 0), table.create(dst, 0), table.create(dst, 0)
		for i = 0, dst - 1 do
			local s = (i + 0.5) * src / dst - 0.5
			local i0 = floor(s)
			local f = s - i0
			if i0 < 0 then
				i0, f = 0, 0
			end
			if i0 > src - 1 then
				i0 = src - 1
			end
			local i1 = math.min(i0 + 1, src - 1)
			a[i + 1], b[i + 1], w[i + 1] = i0, i1, floor(Field.clamp01(f) * 16 + 0.5)
		end
		return a, b, w
	end
	local x0, x1, wx = axis(sw, dw)
	local y0, y1, wy = axis(sh, dh)
	return { sw = sw, sh = sh, dw = dw, dh = dh, x0 = x0, x1 = x1, wx = wx, y0 = y0, y1 = y1, wy = wy }
end

local readu32 = buffer.readu32
function Field.upsample(u: Upsampler, src: buffer, dst: buffer)
	local sw, dw = u.sw, u.dw
	local X0, X1, WX, Y0, Y1, WY = u.x0, u.x1, u.wx, u.y0, u.y1, u.wy
	local M = 0x00ff00ff
	for j = 1, u.dh do
		local r0 = Y0[j] * sw * 4
		local r1 = Y1[j] * sw * 4
		local fy = WY[j]
		local gy = 16 - fy
		local o = (j - 1) * dw * 4
		for i = 1, dw do
			local c0, c1 = X0[i] * 4, X1[i] * 4
			local fx = WX[i]
			local gx = 16 - fx
			local wa, wb, wc, wd = gx * gy, fx * gy, gx * fy, fx * fy
			local a, b, c, d = readu32(src, r0 + c0), readu32(src, r0 + c1), readu32(src, r1 + c0), readu32(src, r1 + c1)
			local lo = band(rshift(band(a, M) * wa + band(b, M) * wb + band(c, M) * wc + band(d, M) * wd, 8), M)
			local hi = band(rshift(band(rshift(a, 8), M) * wa + band(rshift(b, 8), M) * wb + band(rshift(c, 8), M) * wc + band(rshift(d, 8), M) * wd, 8), M)
			writeu32(dst, o, lo + hi * 256)
			o += 4
		end
	end
end

-- Shared face plumbing for every material: field size, scratch target and upsampler for half-res
-- tiers. `target(face, out)` returns the buffer to shade into; `finish(face, out)` upsamples.
export type Face = {
	width: number,
	height: number,
	fw: number,
	fh: number,
	s: number,
	quality: string,
	scratch: buffer?,
	up: Upsampler?,
}

function Field.face(width: number, height: number, quality: string): Face
	local fw, fh, s = Field.fieldSize(width, height, quality)
	local scaled = fw ~= width or fh ~= height
	return {
		width = width,
		height = height,
		fw = fw,
		fh = fh,
		s = s,
		quality = quality,
		scratch = if scaled then buffer.create(fw * fh * 4) else nil,
		up = if scaled then Field.upsampler(fw, fh, width, height) else nil,
	}
end

function Field.target(f: Face, out: buffer): buffer
	assert(buffer.len(out) >= f.width * f.height * 4, "output buffer too small")
	return f.scratch or out
end

function Field.finish(f: Face, out: buffer)
	local sc, up = f.scratch, f.up
	if sc and up then
		Field.upsample(up, sc, out)
	end
end

-- Byte size of the face's own buffers (scratch only; materials add their fields).
function Field.faceBytes(f: Face): number
	return if f.scratch then f.fw * f.fh * 4 else 0
end

-- ---------------------------------------------------------------- lattice fields
-- A smooth field (low-frequency fbm, curl velocity, warp offsets) sampled every `step` field
-- pixels over the face plus a margin, then read back bilinearly at any normalised (x, y). Costs one
-- noise evaluation per lattice point instead of per pixel (step 4 = 1/16 of the work). Only use it
-- for fields whose finest octave spans >= 4 lattice steps and that are not differentiated again
-- (bilinear slopes are piecewise constant).
export type Lattice = {
	step: number, -- field pixels between lattice points
	nx: number,
	ny: number,
	ox: number, -- field-pixel coordinate of lattice point (0, 0)
	oy: number,
	fh: number,
	data: buffer,
}

-- stepFace is in face pixels; s is the field scale (Face.s). marginPx is in field pixels.
function Field.lattice(fw: number, fh: number, stepFace: number, s: number, marginPx: number?): Lattice
	local step = math.max(1, floor(stepFace * s + 0.5))
	local m = marginPx or 0
	local nx = math.ceil((fw + 2 * m) / step) + 2
	local ny = math.ceil((fh + 2 * m) / step) + 2
	return { step = step, nx = nx, ny = ny, ox = -m - step * 0.5, oy = -m - step * 0.5, fh = fh, data = buffer.create(nx * ny * 4) }
end

-- Normalised coordinates of lattice point (a, b), 0-based.
function Field.latticeXY(L: Lattice, a: number, b: number): (number, number)
	return (L.ox + a * L.step + 0.5) / L.fh, (L.oy + b * L.step + 0.5) / L.fh
end

function Field.latticeSet(L: Lattice, a: number, b: number, v: number)
	buffer.writef32(L.data, (b * L.nx + a) * 4, v)
end

function Field.latticeGet(L: Lattice, a: number, b: number): number
	return buffer.readf32(L.data, (b * L.nx + a) * 4)
end

-- Bilinear read at normalised (x, y), clamped to the lattice.
local readf32l = buffer.readf32
function Field.latticeSample(L: Lattice, x: number, y: number): number
	local step, nx = L.step, L.nx
	local u = (x * L.fh - 0.5 - L.ox) / step
	local v = (y * L.fh - 0.5 - L.oy) / step
	local a, b = floor(u), floor(v)
	local fu, fv = u - a, v - b
	if a < 0 then
		a, fu = 0, 0
	elseif a > nx - 2 then
		a, fu = nx - 2, 1
	end
	if b < 0 then
		b, fv = 0, 0
	elseif b > L.ny - 2 then
		b, fv = L.ny - 2, 1
	end
	local d = L.data
	local o = (b * nx + a) * 4
	local p00, p10 = readf32l(d, o), readf32l(d, o + 4)
	local o2 = o + nx * 4
	local p01, p11 = readf32l(d, o2), readf32l(d, o2 + 4)
	local top = p00 + (p10 - p00) * fu
	return top + (p01 + (p11 - p01) * fu - top) * fv
end

-- Central difference of an f32 field at (i, j), clamped at the edges, per field pixel.
local readf32 = buffer.readf32
function Field.gradient(buf: buffer, w: number, h: number, i: number, j: number): (number, number)
	local il = if i > 0 then i - 1 else 0
	local ir = if i < w - 1 then i + 1 else w - 1
	local ju = if j > 0 then j - 1 else 0
	local jd = if j < h - 1 then j + 1 else h - 1
	local row = j * w
	local gx = (readf32(buf, (row + ir) * 4) - readf32(buf, (row + il) * 4)) / math.max(ir - il, 1)
	local gy = (readf32(buf, (jd * w + i) * 4) - readf32(buf, (ju * w + i) * 4)) / math.max(jd - ju, 1)
	return gx, gy
end

return Field
