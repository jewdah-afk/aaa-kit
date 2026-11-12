--!strict
--!native
--!optimize 2
-- CrystalIce: Worley facets with per-cell hashed normals -> faceted refraction of a noise backdrop
-- + per-facet Blinn glints under an orbiting light; F2-F1 fracture lines; frost speckle.
-- Port of foundry/materials.py CrystalIce.frame. Tier 5; glints are capped per pixel (0.45).
-- Press = crack-light: a bright front runs outward along the fracture net, which stays lit.
--
-- Facets do not move (the reference evaluates Worley at t = 0 with no wander), so the cell
-- geometry, normals, glint mask, edge mask, radius and frost are baked once in new(). Each frame
-- evaluates only the refracted backdrop (fbm + ridged) and the lighting. Render allocates nothing.

local Field = require("./Field")

local DATA = {
	salt = 505,
	seedOffset = 11,
	cells = { freq = 5.2, jitter = 0.85 },
	tilt = { base = 0.12, range = 0.22 },
	light = { speed = 0.9, radius = 0.7, yBias = -0.3, z = 0.6 },
	refract = 0.18,
	back = { freq = 1.6, z0 = 0.5, z = 0.05, octaves = 4 },
	streak = { fx = 1.8, fxy = 0.6, fy = 2.4, z = 0.08, octaves = 3, lac = 2.1, gain = 0.55, cut = 0.5, gain2 = 1.8 },
	base = { { 0, "#20457a" }, { 0.4, "#5c93cf" }, { 0.75, "#b5d9f7" }, { 1, "#f2f9ff" } },
	glint = { power = 400, gain = 1.6, cap = 0.45 },
	edge = { width = 0.035 },
	crack = { speed = 1.4, width = 0.12, gain = 3, net = 0.6 },
	frost = { kx = 997, ky = 991, mix = 131, threshold = 0.985, amount = 0.25 },
	ice = "#e8f6ff",
	crackTint = "#bff0ff",
	streakMix = 0.35,
	edgeMix = 0.45,
}

local CrystalIce = {}
CrystalIce.__index = CrystalIce
CrystalIce.DATA = DATA
CrystalIce.ID = "crystal_ice"

local floor, sqrt, exp, cos, sin = math.floor, math.sqrt, math.exp, math.cos, math.sin
local readf32, writef32 = buffer.readf32, buffer.writef32
local fbm, ridged, put, hash01, smoothstep = Field.fbm, Field.ridged, Field.put, Field.hash01, Field.smoothstep

-- Baked per-pixel record (f32 lanes): nx, ny, nz, glint mask, edge mask, radius, frost.
local LANES = 7

type Self = {
	face: Field.Face,
	noise: Field.Noise,
	bake: buffer,
	octBack: number,
	octStreak: number,
	lut: Field.Ramp,
	iceR: number,
	iceG: number,
	iceB: number,
	crR: number,
	crG: number,
	crB: number,
}
export type CrystalIce = typeof(setmetatable({} :: Self, CrystalIce))

function CrystalIce.new(width: number, height: number, seed: number, quality: string?): CrystalIce
	local q = quality or "high"
	local face = Field.face(width, height, q)
	local fw, fh = face.fw, face.fh
	local C, TI, FR, E = DATA.cells, DATA.tilt, DATA.frost, DATA.edge
	local cells = Field.cellCache(math.ceil(C.freq * fw / fh) + 3, math.ceil(C.freq) + 3)
	Field.fillCells(cells, -1, -1, seed + DATA.seedOffset, 0, C.jitter, 0)
	local bake = buffer.create(fw * fh * LANES * 4)
	local invH = 1 / fh
	local xm = fw * invH * 0.5
	for j = 0, fh - 1 do
		local y = (j + 0.5) * invH
		for i = 0, fw - 1 do
			local x = (i + 0.5) * invH
			local f1, f2, cid, dx, dy = Field.worley(cells, x * C.freq, y * C.freq)
			local a = hash01(cid) * 6.2832
			local tilt = TI.base + TI.range * hash01(cid + 7)
			local o = (j * fw + i) * LANES * 4
			writef32(bake, o, cos(a) * tilt)
			writef32(bake, o + 4, sin(a) * tilt)
			writef32(bake, o + 8, sqrt(1 - tilt * tilt))
			writef32(bake, o + 12, smoothstep(0, 0.5, f1 * 1.2 + 0.3 * sin(dx * 9 + dy * 7)))
			writef32(bake, o + 16, smoothstep(E.width, 0, f2 - f1))
			local rx, ry = x - xm, y - 0.5
			writef32(bake, o + 20, sqrt(rx * rx + ry * ry))
			local fh01 = hash01(floor(x * FR.kx) * FR.mix + floor(y * FR.ky))
			writef32(bake, o + 24, if fh01 > FR.threshold then FR.amount else 0)
		end
	end
	local ir, ig, ib = Field.hex(DATA.ice)
	local cr, cg, cb = Field.hex(DATA.crackTint)
	local self: Self = {
		face = face,
		noise = Field.noise(seed * 7919 + DATA.salt),
		bake = bake,
		octBack = Field.octaves(DATA.back.octaves, q),
		octStreak = Field.octaves(DATA.streak.octaves, q),
		lut = Field.ramp(DATA.base, 256),
		iceR = ir,
		iceG = ig,
		iceB = ib,
		crR = cr,
		crG = cg,
		crB = cb,
	}
	return setmetatable(self, CrystalIce)
end

function CrystalIce.Bytes(self: CrystalIce): number
	return buffer.len(self.bake) + Field.faceBytes(self.face)
end

function CrystalIce.Render(self: CrystalIce, t: number, press: number, out: buffer)
	local face = self.face
	local fw, fh = face.fw, face.fh
	local target = Field.target(face, out)
	local n, bake = self.noise, self.bake
	local invH = 1 / fh
	local L, B, S, G, K = DATA.light, DATA.back, DATA.streak, DATA.glint, DATA.crack

	local la = t * L.speed
	local lx, ly, lz = L.radius * cos(la), L.radius * sin(la) + L.yBias, L.z
	local hx, hy, hz = lx, ly, lz + 1
	local hl = sqrt(hx * hx + hy * hy + hz * hz)
	hx, hy, hz = hx / hl, hy / hl, hz / hl
	local refr = DATA.refract
	local bf, bz, bo = B.freq, B.z0 + t * B.z, self.octBack
	local sfx, sfxy, sfy, sz, so, slac, sgain, scut, sg2 = S.fx, S.fxy, S.fy, t * S.z, self.octStreak, S.lac, S.gain, S.cut, S.gain2
	local gpow, ggain, gcap = G.power, G.gain, G.cap
	local kfront, kw, kgain, knet = press * K.speed, K.width, K.gain, K.net
	local lut = self.lut
	local lr, lg, lb, lmax = lut.r, lut.g, lut.b, lut.n - 1
	local iR, iG, iB = self.iceR, self.iceG, self.iceB
	local cR, cG, cB = self.crR, self.crG, self.crB
	local smix, emix = DATA.streakMix, DATA.edgeMix
	for j = 0, fh - 1 do
		local y = (j + 0.5) * invH
		for i = 0, fw - 1 do
			local x = (i + 0.5) * invH
			local o = (j * fw + i) * LANES * 4
			local nx, ny, nz = readf32(bake, o), readf32(bake, o + 4), readf32(bake, o + 8)
			local bx, by = x + nx * refr, y + ny * refr
			local back = fbm(n, bx * bf, by * bf, bz, bo, 2, 0.5) * 0.5 + 0.5
			local streak = (ridged(n, bx * sfx + by * sfxy, by * sfy, sz, so, slac, sgain) - scut)
			streak = if streak <= 0 then 0 elseif streak >= 1 then sg2 else streak * sg2
			local tb = back * 0.75 + 0.25 * (1 - y) + streak * 0.3
			local li = if tb <= 0 then 1 elseif tb >= 1 then lmax + 1 else floor(tb * lmax + 0.5) + 1
			local diff = nx * lx + ny * ly + nz * lz
			diff = if diff < 0 then 0 elseif diff > 1 then 1 else diff
			local d = nx * hx + ny * hy + nz * hz
			local glint = 0
			if d > 0.97 then
				glint = d ^ gpow * ggain
				if glint > gcap then
					glint = gcap
				end
				glint *= readf32(bake, o + 12)
			end
			local side = nx * lx + ny * ly
			side = if side < 0 then 0 elseif side > 1 then 1 else side
			local edge = readf32(bake, o + 16) * (0.5 + 0.5 * side)
			local crack = 0
			if press > 0 then
				local fr = (readf32(bake, o + 20) - kfront) / kw
				crack = exp(-fr * fr) * press * edge * kgain + press * edge * knet
			end
			local frost = readf32(bake, o + 24)
			local shade = 0.7 + 0.4 * diff
			local sm, em = streak * smix, edge * emix
			local add = glint + frost
			put(target, o // LANES,
				lr[li] * shade + add + (sm + em) * iR + crack * cR,
				lg[li] * shade + add + (sm + em) * iG + crack * cG,
				lb[li] * shade + add + (sm + em) * iB + crack * cB)
		end
	end
	Field.finish(face, out)
end

return CrystalIce
