--!strict
--!native
--!optimize 2
-- Hydroglass: 3D-noise swell + damped wave equation -> Snell refraction photon-splat caustics ->
-- depth colour ramp + Fresnel sky + Blinn glints. Port of foundry/materials.py Hydroglass.frame.
-- Tier 5 material; caustic peaks stay a small share of the face. Press = central drop whose ring
-- waves refract into caustic rings.
--
-- Simulation state lives on the instance, so call Render in time order. All buffers are allocated
-- in new(); Render allocates nothing.

local Field = require("./Field")

local DATA = {
	salt = 101, -- noise seed salt (per material)
	wave = { c = 0.45, damp = 0.993, steps = 2 }, -- verlet wave sim, steps per frame at full res
	drop = { first = 0.2, gapMin = 0.25, gapMax = 0.6, radius = 2.2, ampMin = 0.4, ampMax = 0.8 },
	press = { on = 0.6, off = 0.1, radius = 7, amp = 2.0 },
	swell = { freq = 2.0, z = 0.3, octaves = 4, detailFreq = 5, detailX = 0.25, detailZ = 0.5, detail = 0.3, gain = 4.2 },
	waveGain = 0.45,
	caustic = { depth = 40, ior = 1.33, threshold = 1.15, power = 1.15, gain = 1.5 },
	-- 3-tap blur passes on the photon accumulator per tier. The reference's sigma 0.45 rounds to a
	-- zero-radius box (no blur), so high matches it; half-res splats alias more and get one pass.
	blurPasses = { high = 0, mid = 1, low = 1 },
	normalScale = 0.35,
	fresnelF0 = 0.03,
	depthField = { freq = 1.3, offset = 3, z = 0.1, octaves = 3, base = 0.55, amp = 0.45, yFade = 0.3 },
	-- The depth tint is low frequency (finest octave ~21 px at 112 px tall), so it is evaluated on a
	-- lattice every N face pixels and read back bilinearly.
	lattice = { depth = 4 },
	base = { { 0, "#04305a" }, { 0.45, "#0870b0" }, { 0.8, "#10a8e0" }, { 1, "#2cd2f2" } },
	causticTint = "#8ff6ff",
	causticTintMul = 0.75,
	causticTintAdd = 0.12,
	sky = { { 0, "#0d7fc0" }, { 1, "#c9f7ff" } },
	skyGain = 0.25,
	light = { -0.4, -0.7, 0.6 },
	glintPower = 220,
	glintGain = 2.2,
}

local Hydroglass = {}
Hydroglass.__index = Hydroglass
Hydroglass.DATA = DATA
Hydroglass.ID = "hydroglass"

local floor, sqrt = math.floor, math.sqrt
local readf32, writef32 = buffer.readf32, buffer.writef32
local noise3, fbm, put, gradient = Field.noise3, Field.fbm, Field.put, Field.gradient

type Self = {
	face: Field.Face,
	noise: Field.Noise,
	rng: Field.Rng,
	h: buffer, -- wave height (current)
	p: buffer, -- wave height (previous)
	ht: buffer, -- total water height this frame
	acc: buffer, -- photon accumulator
	tmp: buffer, -- blur scratch
	depthL: Field.Lattice,
	steps: number,
	damp: number,
	octSwell: number,
	octDepth: number,
	blur: number,
	nextDrop: number,
	pressed: boolean,
	baseLut: Field.Ramp,
	skyR: { number },
	skyG: { number },
	skyB: { number },
	ctR: number,
	ctG: number,
	ctB: number,
}
export type Hydroglass = typeof(setmetatable({} :: Self, Hydroglass))

function Hydroglass.new(width: number, height: number, seed: number, quality: string?): Hydroglass
	local q = quality or "high"
	local face = Field.face(width, height, q)
	local n = face.fw * face.fh
	local wave = DATA.wave
	-- Half-res tiers run one substep per frame with the damping of two, so waves cross the face at
	-- the same speed in face units.
	local steps = if face.s < 1 then math.max(1, floor(wave.steps * face.s + 0.5)) else wave.steps
	local skyLut = Field.ramp(DATA.sky, 256)
	local skyR, skyG, skyB = table.create(face.fh, 0), table.create(face.fh, 0), table.create(face.fh, 0)
	for j = 0, face.fh - 1 do
		local k = Field.rampIndex(skyLut, 1 - (j + 0.5) / face.fh)
		skyR[j + 1], skyG[j + 1], skyB[j + 1] = skyLut.r[k], skyLut.g[k], skyLut.b[k]
	end
	local tr, tg, tb = Field.hex(DATA.causticTint)
	local self: Self = {
		face = face,
		noise = Field.noise(seed * 7919 + DATA.salt),
		rng = Field.rng(seed + 1234),
		h = buffer.create(n * 4),
		p = buffer.create(n * 4),
		ht = buffer.create(n * 4),
		acc = buffer.create(n * 4),
		tmp = buffer.create(n * 4),
		depthL = Field.lattice(face.fw, face.fh, DATA.lattice.depth, face.s),
		steps = steps,
		damp = wave.damp ^ (wave.steps / steps),
		octSwell = Field.octaves(DATA.swell.octaves, q),
		octDepth = Field.octaves(DATA.depthField.octaves, q),
		blur = (DATA.blurPasses :: any)[q] or 0,
		nextDrop = DATA.drop.first,
		pressed = false,
		baseLut = Field.ramp(DATA.base, 256),
		skyR = skyR,
		skyG = skyG,
		skyB = skyB,
		ctR = tr * DATA.causticTintMul + DATA.causticTintAdd,
		ctG = tg * DATA.causticTintMul + DATA.causticTintAdd,
		ctB = tb * DATA.causticTintMul + DATA.causticTintAdd,
	}
	return setmetatable(self, Hydroglass)
end

-- Bytes held by this face (fields + scratch).
function Hydroglass.Bytes(self: Hydroglass): number
	return buffer.len(self.h) * 5 + buffer.len(self.depthL.data) + Field.faceBytes(self.face)
end

-- Gaussian drop added to the wave height, evaluated only inside a 3-radius box.
local function drop(self: Hydroglass, x: number, y: number, r: number, amp: number)
	local fw, fh, h = self.face.fw, self.face.fh, self.h
	local reach = math.ceil(r * 3)
	local x0, x1 = math.max(0, floor(x) - reach), math.min(fw - 1, floor(x) + reach)
	local y0, y1 = math.max(0, floor(y) - reach), math.min(fh - 1, floor(y) + reach)
	local inv = 1 / (r * r)
	for j = y0, y1 do
		for i = x0, x1 do
			local dx, dy = i - x, j - y
			local o = (j * fw + i) * 4
			writef32(h, o, readf32(h, o) + amp * math.exp(-(dx * dx + dy * dy) * inv))
		end
	end
end

-- One verlet step of the damped wave equation, periodic boundary. Writes the new height over the
-- previous buffer, then swaps.
local function waveStep(self: Hydroglass)
	local fw, fh, h, p = self.face.fw, self.face.fh, self.h, self.p
	local c2, damp = DATA.wave.c * DATA.wave.c, self.damp
	for j = 0, fh - 1 do
		local up = (if j > 0 then j - 1 else fh - 1) * fw
		local dn = (if j < fh - 1 then j + 1 else 0) * fw
		local row = j * fw
		for i = 0, fw - 1 do
			local l = if i > 0 then i - 1 else fw - 1
			local r = if i < fw - 1 then i + 1 else 0
			local o = (row + i) * 4
			local c = readf32(h, o)
			local lap = readf32(h, (row + l) * 4) + readf32(h, (row + r) * 4) + readf32(h, (up + i) * 4) + readf32(h, (dn + i) * 4) - 4 * c
			writef32(p, o, (2 * c - readf32(p, o) + c2 * lap) * damp)
		end
	end
	self.h, self.p = p, h
end

-- Separable [1 2 1]/4 blur of src (periodic), result back in src.
local function blur3(src: buffer, tmp: buffer, w: number, h: number)
	for j = 0, h - 1 do
		local row = j * w
		for i = 0, w - 1 do
			local l = if i > 0 then i - 1 else w - 1
			local r = if i < w - 1 then i + 1 else 0
			writef32(tmp, (row + i) * 4, (readf32(src, (row + l) * 4) + 2 * readf32(src, (row + i) * 4) + readf32(src, (row + r) * 4)) * 0.25)
		end
	end
	for j = 0, h - 1 do
		local up = (if j > 0 then j - 1 else h - 1) * w
		local dn = (if j < h - 1 then j + 1 else 0) * w
		local row = j * w
		for i = 0, w - 1 do
			writef32(src, (row + i) * 4, (readf32(tmp, (up + i) * 4) + 2 * readf32(tmp, (row + i) * 4) + readf32(tmp, (dn + i) * 4)) * 0.25)
		end
	end
end

function Hydroglass.Render(self: Hydroglass, t: number, press: number, out: buffer)
	local face = self.face
	local fw, fh, s = face.fw, face.fh, face.s
	local target = Field.target(face, out)
	local n, rng = self.noise, self.rng
	local D, P = DATA.drop, DATA.press

	-- 1. Rain drops and the press drop feed the wave sim.
	if t >= self.nextDrop then
		drop(self, Field.uniform(rng, 0, fw), Field.uniform(rng, 0, fh), D.radius * s, Field.uniform(rng, D.ampMin, D.ampMax))
		self.nextDrop = t + Field.uniform(rng, D.gapMin, D.gapMax)
	end
	if press > P.on and not self.pressed then
		drop(self, fw * 0.5, fh * 0.5, P.radius * s, P.amp)
		self.pressed = true
	end
	if press < P.off then
		self.pressed = false
	end
	for _ = 1, self.steps do
		waveStep(self)
	end

	-- 2. Total height = noise swell + wave.
	local W, ht = self.h, self.ht
	local SW = DATA.swell
	local freq, zs, dfreq, dx, dz, damt, sgain = SW.freq, t * SW.z, SW.detailFreq, t * SW.detailX, t * SW.detailZ, SW.detail, SW.gain
	local wgain, oct, invH = DATA.waveGain, self.octSwell, 1 / fh
	for j = 0, fh - 1 do
		local y = (j + 0.5) * invH
		for i = 0, fw - 1 do
			local x = (i + 0.5) * invH
			local o = (j * fw + i) * 4
			local swell = fbm(n, x * freq, y * freq, zs, oct, 2, 0.5) + damt * noise3(n, x * dfreq + dx, y * dfreq, dz)
			writef32(ht, o, swell * sgain + readf32(W, o) * wgain)
		end
	end

	-- 3. Photon splat: each texel's light is displaced by the refracted slope and splatted
	-- bilinearly. Displacement in field pixels scales by s^2 (slope per pixel and pixels per unit).
	local acc = self.acc
	buffer.fill(acc, 0, 0)
	local C = DATA.caustic
	local k = C.depth * (1 - 1 / C.ior) * s * s
	for j = 0, fh - 1 do
		for i = 0, fw - 1 do
			local gx, gy = gradient(ht, fw, fh, i, j)
			local px, py = i - k * gx, j - k * gy
			local x0, y0 = floor(px), floor(py)
			local fx, fy = px - x0, py - y0
			local xa, ya = x0 % fw, y0 % fh
			local xb, yb = (xa + 1) % fw, (ya + 1) % fh
			local o
			o = (ya * fw + xa) * 4
			writef32(acc, o, readf32(acc, o) + (1 - fx) * (1 - fy))
			o = (ya * fw + xb) * 4
			writef32(acc, o, readf32(acc, o) + fx * (1 - fy))
			o = (yb * fw + xa) * 4
			writef32(acc, o, readf32(acc, o) + (1 - fx) * fy)
			o = (yb * fw + xb) * 4
			writef32(acc, o, readf32(acc, o) + fx * fy)
		end
	end
	for _ = 1, self.blur do
		blur3(acc, self.tmp, fw, fh)
	end

	-- 4. Shade.
	local DF = DATA.depthField
	local dfq, doff, dzs, dbase, damp2, dyf, octD = DF.freq, DF.offset, t * DF.z, DF.base, DF.amp, DF.yFade, self.octDepth
	local depthL = self.depthL
	for b = 0, depthL.ny - 1 do
		for a = 0, depthL.nx - 1 do
			local x, y = Field.latticeXY(depthL, a, b)
			Field.latticeSet(depthL, a, b, dbase + damp2 * fbm(n, x * dfq + doff, y * dfq, dzs, octD, 2, 0.5))
		end
	end
	local sample = Field.latticeSample
	local lut, skyR, skyG, skyB = self.baseLut, self.skyR, self.skyG, self.skyB
	local lr, lg, lb = lut.r, lut.g, lut.b
	local ctR, ctG, ctB = self.ctR, self.ctG, self.ctB
	local thr, cpow, cgain = C.threshold, C.power, C.gain
	local ns, f0, sky = DATA.normalScale * s, DATA.fresnelF0, DATA.skyGain
	local L = DATA.light
	local hx, hy, hz = L[1], L[2], L[3] + 1
	local hl = sqrt(hx * hx + hy * hy + hz * hz)
	hx, hy, hz = hx / hl, hy / hl, hz / hl
	local gpow, ggain = DATA.glintPower, DATA.glintGain
	local lutMax = lut.n - 1
	for j = 0, fh - 1 do
		local y = (j + 0.5) * invH
		local sr, sg, sb = skyR[j + 1], skyG[j + 1], skyB[j + 1]
		local yfade = 1 - dyf * y
		for i = 0, fw - 1 do
			local x = (i + 0.5) * invH
			local o = (j * fw + i) * 4
			local c = readf32(acc, o) - thr
			c = if c > 0 then c ^ cpow * cgain else 0
			local gx, gy = gradient(ht, fw, fh, i, j)
			local nx, ny = -gx * ns, -gy * ns
			local inv = 1 / sqrt(nx * nx + ny * ny + 1)
			nx, ny = nx * inv, ny * inv
			local nz = inv
			local f = 1 - nz
			local f2 = f * f
			local fres = f0 + (1 - f0) * f2 * f2 * f
			local depth = sample(depthL, x, y) * yfade
			local li = if depth <= 0 then 1 elseif depth >= 1 then lutMax + 1 else floor(depth * lutMax + 0.5) + 1
			local shade = 0.8 + 0.2 * nz
			local d = nx * hx + ny * hy + nz * hz
			local glint = if d > 0.95 then d ^ gpow * ggain else 0
			local fs = fres * sky
			put(target, o,
				lr[li] * shade + c * ctR + sr * fs + glint,
				lg[li] * shade + c * ctG + sg * fs + glint,
				lb[li] * shade + c * ctB + sb * fs + glint)
		end
	end
	Field.finish(face, out)
end

return Hydroglass
