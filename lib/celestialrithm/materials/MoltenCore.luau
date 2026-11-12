--!strict
--!native
--!optimize 2
-- MoltenCore: drifting, noise-warped Worley crust plates; F2-F1 cracks carry a travelling heat pulse
-- -> Planck colour in the cracks, rim-lit basalt domes with ember speckle.
-- Port of foundry/materials.py MoltenCore.frame. Tier 5; red is reserved for danger in the HUD,
-- so this is a rarity/material look only. Press = crust splits wider and the cracks run hotter.
--
-- Two passes: (1) warp + Worley -> crack, pulse, dome per pixel; (2) dome normals -> shading.
-- The fine crust noise is static (z = 0) and baked once in new(). Render allocates nothing.

local Field = require("./Field")

local DATA = {
	salt = 909,
	seedOffset = 9,
	warp = { freq = 1.5, amount = 0.15, z = 0.1, offset = 4 },
	plates = { freq = 4.2, drift = 0.05, z = 0.25, jitter = 0.85, wander = 0.22 },
	crack = { width = 0.08, pressWidth = 0.06 },
	pulse = { base = 0.6, amp = 0.4, idFreq = 30, speed = 2.5, slope = 4 },
	temp = { base = 900, crack = 1500, press = 600 },
	hot = { base = 0.4, pulse = 0.9, gain = 1.6 },
	dome = { falloff = 1.4, height = 8 },
	rim = { x = -0.5, y = -0.7 },
	crustNoise = { freq = 9, amount = 0.2, dome = 0.8 },
	crust = { { 0, "#24030a" }, { 0.5, "#4a0a10" }, { 1, "#7a1a17" } },
	ember = { kx = 211, ky = 197, mix = 977, rate = 6, threshold = 0.995, amount = 0.8, color = "#ff9a3a" },
	crackGlow = { color = "#ff3b30", amount = 0.25 },
}

local MoltenCore = {}
MoltenCore.__index = MoltenCore
MoltenCore.DATA = DATA
MoltenCore.ID = "molten_core"

local floor, sqrt, sin, ceil = math.floor, math.sqrt, math.sin, math.ceil
local readf32, writef32 = buffer.readf32, buffer.writef32
local noise3, worley, put, hash01, blackbody, gradient = Field.noise3, Field.worley, Field.put, Field.hash01, Field.blackbody, Field.gradient

type Self = {
	face: Field.Face,
	noise: Field.Noise,
	seed: number,
	cells: Field.CellCache,
	crack: buffer,
	pulse: buffer,
	dome: buffer,
	crustN: buffer,
	lut: Field.Ramp,
	emR: number,
	emG: number,
	emB: number,
	cgR: number,
	cgG: number,
	cgB: number,
}
export type MoltenCore = typeof(setmetatable({} :: Self, MoltenCore))

function MoltenCore.new(width: number, height: number, seed: number, quality: string?): MoltenCore
	local q = quality or "high"
	local face = Field.face(width, height, q)
	local fw, fh = face.fw, face.fh
	local n = fw * fh
	local noise = Field.noise(seed * 7919 + DATA.salt)
	local P, CN = DATA.plates, DATA.crustNoise
	local margin = DATA.warp.amount * 1.5
	local crustN = buffer.create(n * 4)
	for j = 0, fh - 1 do
		for i = 0, fw - 1 do
			writef32(crustN, (j * fw + i) * 4, noise3(noise, (i + 0.5) / fh * CN.freq, (j + 0.5) / fh * CN.freq, 0))
		end
	end
	local er, eg, eb = Field.hex(DATA.ember.color)
	local cr, cg, cb = Field.hex(DATA.crackGlow.color)
	local self: Self = {
		face = face,
		noise = noise,
		seed = seed,
		cells = Field.cellCache(ceil((fw / fh + 2 * margin) * P.freq) + 4, ceil((1 + 2 * margin) * P.freq) + 4),
		crack = buffer.create(n * 4),
		pulse = buffer.create(n * 4),
		dome = buffer.create(n * 4),
		crustN = crustN,
		lut = Field.ramp(DATA.crust, 256),
		emR = er * DATA.ember.amount,
		emG = eg * DATA.ember.amount,
		emB = eb * DATA.ember.amount,
		cgR = cr * DATA.crackGlow.amount,
		cgG = cg * DATA.crackGlow.amount,
		cgB = cb * DATA.crackGlow.amount,
	}
	return setmetatable(self, MoltenCore)
end

function MoltenCore.Bytes(self: MoltenCore): number
	return buffer.len(self.crack) * 4 + Field.faceBytes(self.face)
end

function MoltenCore.Render(self: MoltenCore, t: number, press: number, out: buffer)
	local face = self.face
	local fw, fh, s = face.fw, face.fh, face.s
	local target = Field.target(face, out)
	local n = self.noise
	local invH = 1 / fh
	local WA, P, CK, PU, TE, HO, DO, EM = DATA.warp, DATA.plates, DATA.crack, DATA.pulse, DATA.temp, DATA.hot, DATA.dome, DATA.ember

	-- 1. Plates: warped, drifting Worley cells.
	local margin = WA.amount * 1.5
	local cells = self.cells
	Field.fillCells(cells, floor(-margin * P.freq + t * P.drift) - 1, floor(-margin * P.freq) - 1, self.seed + DATA.seedOffset, t * P.z, P.jitter, P.wander)
	local crackB, pulseB, domeB = self.crack, self.pulse, self.dome
	local wf, wa, wz, woff = WA.freq, WA.amount, t * WA.z, WA.offset
	local pf, pdrift = P.freq, t * P.drift
	local width = CK.width + CK.pressWidth * press
	local pb, pamp, pid, pt, pslope = PU.base, PU.amp, PU.idFreq, t * PU.speed, PU.slope
	local dfall = DO.falloff
	for j = 0, fh - 1 do
		local y = (j + 0.5) * invH
		for i = 0, fw - 1 do
			local x = (i + 0.5) * invH
			local wx = x + wa * noise3(n, x * wf, y * wf, wz)
			local wy = y + wa * noise3(n, x * wf + woff, y * wf, wz)
			local f1, f2, cid = worley(cells, wx * pf + pdrift, wy * pf)
			local ct = 1 - (f2 - f1) / width
			ct = if ct <= 0 then 0 elseif ct >= 1 then 1 else ct
			local o = (j * fw + i) * 4
			writef32(crackB, o, ct * ct * (3 - 2 * ct))
			writef32(pulseB, o, pb + pamp * sin(hash01(cid) * pid + pt - (x + y) * pslope))
			local d = 1 - f1 * dfall
			writef32(domeB, o, if d < 0 then 0 else d)
		end
	end

	-- 2. Shade: rim-lit domes, Planck cracks, embers.
	local dh = DO.height * s -- dome slope per field pixel matches the full-res reference
	local rimx, rimy = DATA.rim.x, DATA.rim.y
	local CN = DATA.crustNoise
	local cnA, cnD = CN.amount, CN.dome
	local crustN = self.crustN
	local lut = self.lut
	local lr, lg, lb, lmax = lut.r, lut.g, lut.b, lut.n - 1
	local tb, tc, tp = TE.base, TE.crack, TE.press * press
	local hb, hp, hg = HO.base, HO.pulse, HO.gain
	local ekx, eky, emix, eframe, ethr = EM.kx, EM.ky, EM.mix, floor(t * EM.rate), EM.threshold
	local emR, emG, emB = self.emR, self.emG, self.emB
	local cgR, cgG, cgB = self.cgR, self.cgG, self.cgB
	for j = 0, fh - 1 do
		local y = (j + 0.5) * invH
		local ey = floor(y * eky) + eframe
		for i = 0, fw - 1 do
			local x = (i + 0.5) * invH
			local o = (j * fw + i) * 4
			local gx, gy = gradient(domeB, fw, fh, i, j)
			local nx, ny = -gx * dh, -gy * dh
			local inv = 1 / sqrt(nx * nx + ny * ny + 1)
			local rim = (nx * rimx + ny * rimy) * inv
			rim = if rim <= 0 then 0 elseif rim >= 1 then 1 else rim
			rim *= rim
			local dome = readf32(domeB, o)
			local ct = dome * cnD + cnA * readf32(crustN, o)
			local li = if ct <= 0 then 1 elseif ct >= 1 then lmax + 1 else floor(ct * lmax + 0.5) + 1
			local shade = 0.6 + 0.5 * rim
			local r, g, b = lr[li] * shade, lg[li] * shade, lb[li] * shade
			local crack = readf32(crackB, o)
			if crack > 0 then
				local pulse = readf32(pulseB, o)
				local br, bg, bb = blackbody(tb + tc * crack * pulse + tp * crack)
				local k = crack * (hb + hp * pulse) * hg
				r += br * k + cgR * crack
				g += bg * k + cgG * crack
				b += bb * k + cgB * crack
			end
			if hash01(floor(x * ekx) * emix + ey) > ethr then
				r += emR
				g += emG
				b += emB
			end
			put(target, o, r, g, b)
		end
	end
	Field.finish(face, out)
end

return MoltenCore
