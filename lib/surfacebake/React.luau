--!strict
--# selene: allow(mixed_table) -- recipe terms are { kind, key = value } by design
-- React: surfaces that respond. On top of a bake, each texel keeps a little state (heat, frost)
-- that hits, other effects and the object's own motion change over time:
--
--   hits        React.hit(st, objectSpacePos, strength) at a raycast point: adds heat around
--               it and starts a ripple ring travelling across the surface (in 3D, so it wraps
--               around edges and over seams)
--   heat        accumulates where you keep hitting, glows dark red -> orange -> white, cools
--               back down (decay per second)
--   frost       grows outward from frost hits and stays; heat melts it back
--   flow        a lava/plasma flow (like Animate "flow") that FREEZES where frost lies, and
--               whose heat keeps melting the frost at its edges: the two fight in realtime
--   shimmer     a shield pattern whose brightness follows the object's angular speed
--
-- profile = {
--   heat    = { gain = 1, radius = 0.35, decay = 0.6 },
--   ripple  = { speed = 2.5, width = 0.08, life = 1.2, color = { 0.4, 0.9, 1 } },
--   frost   = { onHit = true, speed = 0.6, max = 0.9, width = 0.08, melt = 0.8, color = { 0.82, 0.93, 1 } },
--   flow    = { mask = {...}, phase = { "y", scale = 1 }, speed = 0.35, freq = 1.2, color = { 1, 0.5, 0.1 }, heat = 0.25 },
--   shimmer = { mask = {...}, phase = { "voronoi", ... }, color = { 0.3, 0.8, 1 }, gain = 0.6 },
-- }
-- Every field that needs noise/Voronoi is evaluated once in prepare(); per frame is arithmetic.
-- Roblox: raycast the MeshPart, convert the hit with part.CFrame:PointToObjectSpace(hit) and
-- divide by (part.Size / meshSize) to get mesh space; upload state.out like Animate.

local Raster = require("./Raster")
local Recipe = require("./Recipe")
local Noise = require("./Noise")
local Bake = require("./Bake")

export type Hit = { x: number, y: number, z: number, t: number, s: number, frost: boolean }

export type State = {
	W: number,
	H: number,
	profile: any,
	base: buffer, -- RGBA8 baked albedo
	out: buffer, -- RGBA8 result (upload this)
	pos: buffer, -- f32 xyz per texel (object space)
	heat: buffer, -- f32 per texel
	frost: buffer, -- f32 per texel 0..1
	flowMask: buffer?, -- f32
	flowPhase: buffer?, -- f32
	shimMask: buffer?, -- f32
	shimPhase: buffer?, -- f32
	crystal: buffer?, -- f32 frost facet brightness
	hits: { Hit },
	lut: { number },
	t: number,
	spin: number, -- smoothed angular speed (rad/s)
}

local React = {}

local MAX_HITS = 12

local function u8(v: number): number
	return math.clamp(math.floor(v + 0.5), 0, 255)
end

function React.prepare(maps: Bake.Maps, profile: any): State
	local W, H, G = maps.W, maps.H, maps.G
	local n = W * H
	local base = buffer.create(n * 4)
	buffer.copy(base, 0, maps.albedo, 0, n * 4)
	local out = buffer.create(n * 4)
	buffer.copy(out, 0, maps.albedo, 0, n * 4)
	local pos = buffer.create(n * 12)
	buffer.copy(pos, 0, G.pos, 0, n * 12)
	local st: State = {
		W = W,
		H = H,
		profile = profile,
		base = base,
		out = out,
		pos = pos,
		heat = buffer.create(n * 4),
		frost = buffer.create(n * 4),
		hits = {},
		lut = {},
		t = 0,
		spin = 0,
	}
	local c = { px = 0, py = 0, pz = 0, nx = 0, ny = 1, nz = 0, curv = 0.5, ao = 1, edge = 0 }
	local function fieldPair(spec: any): (buffer, buffer)
		local mask, phase = buffer.create(n * 4), buffer.create(n * 4)
		for i = 0, n - 1 do
			if buffer.readu8(G.cover, i) ~= 0 then
				local px, py, pz = Raster.readVec(G.pos, i)
				local nx, ny, nz = Raster.readVec(G.nrm, i)
				c.px, c.py, c.pz, c.nx, c.ny, c.nz = px, py, pz, nx, ny, nz
				c.curv = buffer.readf32(maps.fields.curv, i * 4)
				c.ao = buffer.readf32(maps.fields.ao, i * 4)
				c.edge = buffer.readf32(maps.fields.edge, i * 4)
				buffer.writef32(mask, i * 4, Recipe.mask(spec.mask, c :: any, px, py, pz))
				buffer.writef32(phase, i * 4, Recipe.field(spec.phase or { "y", scale = 1 }, c :: any, px, py, pz))
			end
		end
		return mask, phase
	end
	if profile.flow then
		st.flowMask, st.flowPhase = fieldPair(profile.flow)
	end
	if profile.shimmer then
		st.shimMask, st.shimPhase = fieldPair(profile.shimmer)
	end
	if profile.frost then
		st.crystal = require("./Animate").crystalField(maps)
	end
	for k = 0, 255 do
		local a = k / 256 * 2 * math.pi
		st.lut[k + 1] = math.clamp(Noise.fbm(math.cos(a) * 2, math.sin(a) * 2, 0.5, 4) * 0.6 + 0.5, 0, 1)
	end
	return st
end

--- A hit at an object-space point. strength ~1 for a normal hit. frost = true makes it a frost
--- seed (when the profile has frost), otherwise it's a heat/ripple hit.
function React.hit(st: State, x: number, y: number, z: number, strength: number?, frost: boolean?)
	local s = strength or 1
	local p = st.profile
	table.insert(st.hits, { x = x, y = y, z = z, t = st.t, s = s, frost = frost == true })
	if #st.hits > MAX_HITS then
		table.remove(st.hits, 1)
	end
	-- heat is a field, so add it now (one pass over texels, only on hits)
	if p.heat and not frost then
		local r2 = (p.heat.radius or 0.35) ^ 2
		local gain = (p.heat.gain or 1) * s
		local n = st.W * st.H
		for i = 0, n - 1 do
			if buffer.readu32(st.base, i * 4) >= 16777216 then
				local px, py, pz = Raster.readVec(st.pos, i)
				local d2 = (px - x) ^ 2 + (py - y) ^ 2 + (pz - z) ^ 2
				if d2 < r2 * 9 then
					buffer.writef32(st.heat, i * 4, buffer.readf32(st.heat, i * 4) + gain * math.exp(-d2 / r2))
				end
			end
		end
	end
end

--- Advance by dt seconds. spin = the object's current angular speed (rad/s), for shimmer.
function React.step(st: State, dt: number, spin: number?)
	st.t += dt
	st.spin += ((spin or 0) - st.spin) * math.min(1, dt * 4)
	local p = st.profile
	local t = st.t
	local n = st.W * st.H
	local heatDecay = if p.heat then math.exp(-(p.heat.decay or 0.6) * dt) else 1
	local rp = p.ripple
	local fr = p.frost
	local fl = p.flow
	local sh = p.shimmer
	-- live ripples and frost seeds this frame
	local rips, seeds = {}, {}
	for _, h in st.hits do
		local age = t - h.t
		if h.frost then
			table.insert(seeds, h)
		elseif rp and age < (rp.life or 1.2) then
			table.insert(rips, { h.x, h.y, h.z, (rp.speed or 2.5) * age, h.s * (1 - age / (rp.life or 1.2)) })
		end
	end
	local rw = if rp then rp.width or 0.08 else 1
	local rc = if rp then rp.color or { 0.4, 0.9, 1 } else { 1, 1, 1 }
	local fc = if fr then fr.color or { 0.82, 0.93, 1 } else { 1, 1, 1 }
	local flc = if fl then fl.color or { 1, 0.5, 0.1 } else { 1, 1, 1 }
	local shc = if sh then sh.color or { 0.3, 0.8, 1 } else { 1, 1, 1 }
	local shAmt = if sh then math.min(1.5, st.spin * (sh.gain or 0.6)) else 0
	local lut = st.lut
	for i = 0, n - 1 do
		local q = i * 4
		local v = buffer.readu32(st.base, q)
		local a = v // 16777216
		if a > 0 then
			local r, g, b = v % 256, (v // 256) % 256, (v // 65536) % 256
			local px, py, pz = Raster.readVec(st.pos, i)
			-- heat: decays every frame
			local heat = 0
			if p.heat then
				heat = buffer.readf32(st.heat, q) * heatDecay
			end
			-- flow (lava): glow along the phase, suppressed by frost, and it heats its surroundings
			local frost = if fr then buffer.readf32(st.frost, q) else 0
			if fl then
				local m = buffer.readf32(st.flowMask :: buffer, q)
				if m > 0 then
					local u = (buffer.readf32(st.flowPhase :: buffer, q) * (fl.freq or 1.2) + t * (fl.speed or 0.35)) % 1
					local fi = u * 256
					local i0 = math.floor(fi)
					local l0, l1 = lut[i0 % 256 + 1], lut[(i0 + 1) % 256 + 1]
					local k = m * (l0 + (l1 - l0) * (fi - i0)) ^ 2 * (1 - frost)
					r += (flc[1] * 255 - r) * k + flc[1] * 90 * k
					g += (flc[2] * 255 - g) * k + flc[2] * 90 * k
					b += (flc[3] * 255 - b) * k + flc[3] * 90 * k
					heat = math.max(heat, m * (fl.heat or 0.25) * (1 - frost))
				end
			end
			-- frost: grows from seeds, melted by heat; frozen texels lose their glow
			if fr then
				-- only the moving front freezes texels (a band just behind it), so ice that heat
				-- has melted inside the circle stays melted instead of re-freezing every frame
				local grow = 0
				local fw = fr.width or 0.08
				for _, s in seeds do
					local d = math.sqrt((px - s.x) ^ 2 + (py - s.y) ^ 2 + (pz - s.z) ^ 2)
					local reach = (fr.max or 0.9) * s.s
					local radius = math.min(reach, (fr.speed or 0.6) * (t - s.t) * s.s)
					if radius < reach or d > radius - fw * 2 then
						if d > radius - fw * 3 then
							grow = math.max(grow, math.clamp((radius - d) / fw, 0, 1))
						end
					end
				end
				frost = math.clamp(math.max(frost, grow) - heat * (fr.melt or 0.8) * dt, 0, 1)
				buffer.writef32(st.frost, q, frost)
				if frost > 0 then
					-- crystalline frost (facets from Animate.crystalField), 88% cover
					local spark = buffer.readf32(st.crystal :: buffer, q)
					local f = frost * 0.88
					r += (fc[1] * 255 * spark - r) * f
					g += (fc[2] * 255 * spark - g) * f
					b += (fc[3] * 255 * spark - b) * f
				end
			end
			if p.heat then
				buffer.writef32(st.heat, q, if heat < 0.002 then 0 else heat)
				-- blackbody-ish ramp: dark red -> orange -> yellow-white
				if heat > 0.02 then
					local h1 = math.min(1, heat)
					local hr, hg, hb = 255, 60 + 195 * h1 * h1, 20 + 200 * math.max(0, heat - 0.8)
					local k = math.min(1, heat * 1.3)
					r += (hr - r) * k
					g += (hg - g) * k
					b += (hb - b) * k
				end
			end
			-- ripples: rings travelling out from recent hits, measured in 3D
			for _, rr in rips do
				local d = math.sqrt((px - rr[1]) ^ 2 + (py - rr[2]) ^ 2 + (pz - rr[3]) ^ 2)
				local e = (d - rr[4]) / rw
				local k = rr[5] * math.exp(-e * e)
				if k > 0.01 then
					r += (rc[1] * 255 - r) * math.min(1, k) + rc[1] * 60 * k
					g += (rc[2] * 255 - g) * math.min(1, k) + rc[2] * 60 * k
					b += (rc[3] * 255 - b) * math.min(1, k) + rc[3] * 60 * k
				end
			end
			-- shimmer with spin speed
			if sh and shAmt > 0.01 then
				local m = buffer.readf32(st.shimMask :: buffer, q)
				if m > 0 then
					local w = 0.5 + 0.5 * math.sin((buffer.readf32(st.shimPhase :: buffer, q) * 6 - t * 3) * math.pi)
					local k = m * shAmt * w
					r += (shc[1] * 255 - r) * math.min(1, k)
					g += (shc[2] * 255 - g) * math.min(1, k)
					b += (shc[3] * 255 - b) * math.min(1, k)
				end
			end
			buffer.writeu32(st.out, q, u8(r) + u8(g) * 256 + u8(b) * 65536 + a * 16777216)
		end
	end
end

--- A spring for things that should react to the object's motion (fur shells, hanging cloth,
--- jelly): feed the object's acceleration (studs/s^2, object space) every frame; read
--- spring.x/y/z as the offset to apply to the outermost shell (scale inner shells by h^2).
export type Spring = { x: number, y: number, z: number, vx: number, vy: number, vz: number, k: number, damp: number }

function React.spring(stiffness: number?, damping: number?): Spring
	return { x = 0, y = 0, z = 0, vx = 0, vy = 0, vz = 0, k = stiffness or 60, damp = damping or 7 }
end

function React.springStep(s: Spring, ax: number, ay: number, az: number, dt: number)
	-- inertia: the tips lag behind the body's acceleration, then spring back
	s.vx += (-ax - s.k * s.x - s.damp * s.vx) * dt
	s.vy += (-ay - s.k * s.y - s.damp * s.vy) * dt
	s.vz += (-az - s.k * s.z - s.damp * s.vz) * dt
	s.x += s.vx * dt
	s.y += s.vy * dt
	s.z += s.vz * dt
end

return React
