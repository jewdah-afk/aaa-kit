--!strict
--!native
--!optimize 2
-- SolarPlasma: curl-advected ridged multifractal temperature + Worley granulation -> temperature
-- ramp graded in blackbody order -> filmic shoulder. Port of foundry/materials.py SolarPlasma.frame.
-- Tier 5; the brightest emissive material, one per screen at most. Press = flare: a travelling
-- +1800 K front from the centre plus a core lift.
--
-- Runtime change from the reference: the curl velocity is the finite difference of a 2-octave
-- potential sampled on a coarse lattice (the potential's finest octave spans ~47 px at 112 px tall),
-- then read back bilinearly, instead of four offset fbm calls per pixel. Render allocates nothing.

local Field = require("./Field")

local DATA = {
	salt = 303,
	curl = { freq = 1.2, z = 0.15, octaves = 2, amount = 0.25, lattice = 4 }, -- lattice step in face px
	ridge = { freq = 2.6, drift = 0.08, z = 0.45, octaves = 5, lac = 2.1, gain = 0.55 },
	gran = { freq = 9, z = 0.7, jitter = 0.85, wander = 0.18, edge = 0.35 },
	temp = { base = 2300, ridge = 3600, ridgePow = 1.5, gran = 500, front = 1800, core = 1600, span = 4400 },
	flare = { speed = 1.3, width = 0.18, coreRadius = 0.5 },
	ramp = {
		{ 0, "#6a1300" },
		{ 0.25, "#d84a00" },
		{ 0.5, "#ff8a00" },
		{ 0.72, "#ffc21a" },
		{ 0.9, "#fff07a" },
		{ 1, "#ffffff" },
	},
	rampGain = 1.15,
}

local SolarPlasma = {}
SolarPlasma.__index = SolarPlasma
SolarPlasma.DATA = DATA
SolarPlasma.ID = "solar_plasma"

local floor, sqrt, exp, ceil = math.floor, math.sqrt, math.exp, math.ceil
local fbm, ridged, worley, put = Field.fbm, Field.ridged, Field.worley, Field.put

type Self = {
	face: Field.Face,
	noise: Field.Noise,
	seed: number,
	pot: Field.Lattice,
	vx: Field.Lattice,
	vy: Field.Lattice,
	cells: Field.CellCache,
	octRidge: number,
	lut: Field.Ramp,
}
export type SolarPlasma = typeof(setmetatable({} :: Self, SolarPlasma))

function SolarPlasma.new(width: number, height: number, seed: number, quality: string?): SolarPlasma
	local q = quality or "high"
	local face = Field.face(width, height, q)
	local g = DATA.gran.freq
	local self: Self = {
		face = face,
		noise = Field.noise(seed * 7919 + DATA.salt),
		seed = seed,
		pot = Field.lattice(face.fw, face.fh, DATA.curl.lattice, face.s),
		vx = Field.lattice(face.fw, face.fh, DATA.curl.lattice, face.s),
		vy = Field.lattice(face.fw, face.fh, DATA.curl.lattice, face.s),
		cells = Field.cellCache(ceil(g * face.fw / face.fh) + 3, g + 3),
		octRidge = Field.octaves(DATA.ridge.octaves, q),
		lut = Field.ramp(DATA.ramp, 512, DATA.rampGain),
	}
	return setmetatable(self, SolarPlasma)
end

function SolarPlasma.Bytes(self: SolarPlasma): number
	return buffer.len(self.pot.data) * 3 + Field.faceBytes(self.face)
end

function SolarPlasma.Render(self: SolarPlasma, t: number, press: number, out: buffer)
	local face = self.face
	local fw, fh = face.fw, face.fh
	local target = Field.target(face, out)
	local n, pot = self.noise, self.pot
	local invH = 1 / fh
	local CU, RI, GR, TE, FL = DATA.curl, DATA.ridge, DATA.gran, DATA.temp, DATA.flare

	-- 1. Curl velocity on the lattice: v = (dP/dy, -dP/dx) of the potential, times the advection
	-- amount, in the potential's own (scaled) coordinates.
	local cf, cz, co = CU.freq, t * CU.z, CU.octaves
	local nx, ny = pot.nx, pot.ny
	for b = 0, ny - 1 do
		for a = 0, nx - 1 do
			local x, y = Field.latticeXY(pot, a, b)
			Field.latticeSet(pot, a, b, fbm(n, x * cf, y * cf, cz, co, 2, 0.5))
		end
	end
	local vx, vy, get, set = self.vx, self.vy, Field.latticeGet, Field.latticeSet
	local k = CU.amount * fh / (cf * pot.step) -- per lattice step -> per scaled unit
	for b = 0, ny - 1 do
		local bu, bd = if b > 0 then b - 1 else 0, if b < ny - 1 then b + 1 else ny - 1
		for a = 0, nx - 1 do
			local al, ar = if a > 0 then a - 1 else 0, if a < nx - 1 then a + 1 else nx - 1
			local dx = (get(pot, ar, b) - get(pot, al, b)) / (ar - al)
			local dy = (get(pot, a, bd) - get(pot, a, bu)) / (bd - bu)
			set(vx, a, b, dy * k)
			set(vy, a, b, -dx * k)
		end
	end
	local sample = Field.latticeSample

	-- 2. Granulation cells for this frame.
	local cells = self.cells
	Field.fillCells(cells, -1, -1, self.seed, t * GR.z, GR.jitter, GR.wander)

	-- 3. Temperature -> colour.
	local rf, rdrift, rz, ro, rlac, rgain = RI.freq, t * RI.drift, t * RI.z, self.octRidge, RI.lac, RI.gain
	local gfreq, gedge = GR.freq, GR.edge
	local xm = fw * invH * 0.5
	local front0, fw2, core = press * FL.speed, FL.width, FL.coreRadius
	local lut = self.lut
	local lr, lg, lb, lmax = lut.r, lut.g, lut.b, lut.n - 1
	local tb, tr, tp, tg, tf, tc, tspan = TE.base, TE.ridge, TE.ridgePow, TE.gran, TE.front, TE.core, TE.span
	for j = 0, fh - 1 do
		local y = (j + 0.5) * invH
		for i = 0, fw - 1 do
			local x = (i + 0.5) * invH
			local wx, wy = x + sample(vx, x, y), y + sample(vy, x, y)
			local rid = ridged(n, wx * rf + rdrift, wy * rf, rz, ro, rlac, rgain)
			local f1, f2 = worley(cells, x * gfreq, y * gfreq)
			local gt = (f2 - f1) / gedge
			if gt > 1 then
				gt = 1
			end
			local gran = gt * gt * (3 - 2 * gt)
			local T = tb + tr * rid ^ tp + tg * gran
			if press > 0 then
				local dx, dy = x - xm, y - 0.5
				local r = sqrt(dx * dx + dy * dy)
				local fr = (r - front0) / fw2
				local rc = r / core
				T += tf * exp(-fr * fr) * press + tc * press * exp(-rc * rc)
			end
			local tn = (T - tb) / tspan
			local li = if tn <= 0 then 1 elseif tn >= 1 then lmax + 1 else floor(tn * lmax + 0.5) + 1
			put(target, (j * fw + i) * 4, lr[li], lg[li], lb[li])
		end
	end
	Field.finish(face, out)
end

return SolarPlasma
