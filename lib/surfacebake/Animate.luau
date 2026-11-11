--!strict
--# selene: allow(mixed_table) -- recipe terms are { kind, key = value } by design
-- Animate: realtime moving surfaces on a baked model. Everything expensive (noise, Voronoi, edge
-- distance, AO, position) is evaluated ONCE per texel by prepare(); each frame is then a few
-- multiplies per texel over plain buffers, with an optional texel budget so the cost per frame is
-- fixed (rows are updated round-robin, and the dirty rows are returned for a region upload).
--
-- Effects (spec.effect):
--   "pulse"    glow travels along `phase` as a sine wave: rune channels, energy veins, heartbeat
--   "flow"     a 1D noise table scrolls along `phase`: lava rivers, plasma, conveyor grime
--   "dissolve" texels vanish where noise < progress, with a burning rim: death, teleport, reveal
--   "scan"     a soft band sweeps across `phase`: scanner, hologram reveal, heal wave
--   "spread"   a front grows from a seed point and leaves a new material behind: frost, corruption, paint
--
-- spec = {
--   effect = "pulse", color = { r, g, b }, mask = { ...Recipe mask terms... }, -- where it applies
--   phase = { "y", scale = 1 } | "edge" | "ao" | "seed",  -- the coordinate the motion follows
--   speed = 1, freq = 1, width = 0.1, sharp = 2, seed = { x, y, z }, after = { r, g, b } (spread),
--   noise = { "noise", scale = 4, octaves = 3 },          -- dissolve field (default fBm)
-- }
-- Roblox: write rows with EditableImage:WritePixelsBuffer(Vector2.new(0, y0), Vector2.new(W, rows), buf)
-- using Animate.rows(state, y0, rows) to get the slice; only one EditableImage is pushed per frame.

local Raster = require("./Raster")
local Recipe = require("./Recipe")
local Noise = require("./Noise")
local Bake = require("./Bake")

export type State = {
	W: number,
	H: number,
	effect: string,
	base: buffer, -- RGBA8 copy of the baked albedo
	out: buffer, -- RGBA8 animated albedo (upload this)
	mask: buffer, -- f32 0..1
	phase: buffer, -- f32
	noise: buffer, -- f32 0..1 (dissolve)
	lut: { number }, -- 256-entry 0..1 noise table (flow)
	spec: any,
	cursor: number, -- next row for budgeted updates
	slice: buffer?, -- reused upload slice (no per-frame allocation)
}

local Animate = {}

local function u8(v: number): number
	return math.clamp(math.floor(v * 255 + 0.5), 0, 255)
end

--- Precomputes every per-texel field the effect needs. Cost ~ one extra recipe layer per texel.
function Animate.prepare(maps: Bake.Maps, spec: any): State
	local W, H, G = maps.W, maps.H, maps.G
	local n = W * H
	local base = buffer.create(n * 4)
	buffer.copy(base, 0, maps.albedo, 0, n * 4)
	local out = buffer.create(n * 4)
	buffer.copy(out, 0, maps.albedo, 0, n * 4)
	local mask, phase, nz = buffer.create(n * 4), buffer.create(n * 4), buffer.create(n * 4)
	local c = { px = 0, py = 0, pz = 0, nx = 0, ny = 1, nz = 0, curv = 0.5, ao = 1, edge = 0 }
	local ph = spec.phase or { "y", scale = 1 }
	local nterm = spec.noise or { "noise", scale = 4, octaves = 3 }
	local seed = spec.seed or { 0, 0, 0 }
	for i = 0, n - 1 do
		if buffer.readu8(G.cover, i) ~= 0 then
			local px, py, pz = Raster.readVec(G.pos, i)
			local nx, ny, nzz = Raster.readVec(G.nrm, i)
			c.px, c.py, c.pz, c.nx, c.ny, c.nz = px, py, pz, nx, ny, nzz
			c.curv = buffer.readf32(maps.fields.curv, i * 4)
			c.ao = buffer.readf32(maps.fields.ao, i * 4)
			c.edge = buffer.readf32(maps.fields.edge, i * 4)
			buffer.writef32(mask, i * 4, Recipe.mask(spec.mask, c :: any, px, py, pz))
			local p
			if ph == "edge" then
				p = c.edge
			elseif ph == "ao" then
				p = c.ao
			elseif ph == "seed" then
				p = math.sqrt((px - seed[1]) ^ 2 + (py - seed[2]) ^ 2 + (pz - seed[3]) ^ 2)
			else
				p = Recipe.field(ph, c :: any, px, py, pz)
			end
			buffer.writef32(phase, i * 4, p)
			local v = Recipe.field(nterm, c :: any, px, py, pz)
			buffer.writef32(nz, i * 4, math.clamp(v * 0.5 + 0.5, 0, 1))
		end
	end
	local lut = table.create(256, 0)
	for k = 0, 255 do
		local a = k / 256 * 2 * math.pi
		-- a closed loop through noise space, so the table wraps seamlessly
		lut[k + 1] = math.clamp(Noise.fbm(math.cos(a) * 2, math.sin(a) * 2, 0.5, 4) * 0.6 + 0.5, 0, 1)
	end
	return {
		W = W,
		H = H,
		effect = spec.effect or "pulse",
		base = base,
		out = out,
		mask = mask,
		phase = phase,
		noise = nz,
		lut = lut,
		spec = spec,
		cursor = 0,
	}
end

--- Updates rows [y0, y0 + rows) of state.out for time t (seconds).
function Animate.shadeRows(st: State, t: number, y0: number, rows: number)
	local s = st.spec
	local W = st.W
	local col = s.color or { 1, 0.6, 0.2 }
	local cr, cg, cb = col[1] * 255, col[2] * 255, col[3] * 255
	local speed, freq, width, sharp = s.speed or 1, s.freq or 1, s.width or 0.1, s.sharp or 2
	local eff = st.effect
	local lut = st.lut
	local after = s.after or { 0.85, 0.93, 1 }
	local ar, ag, ab = after[1] * 255, after[2] * 255, after[3] * 255
	-- per-frame constants
	local progress = (t * speed) % 1.25 - 0.1 -- dissolve: -0.1 .. 1.15, then loops
	local scanC = (t * speed) % ((s.range or 2) + width * 4) + (s.min or -1) - width * 2
	local front = (t * speed) % (s.maxRadius or 3)
	for y = y0, y0 + rows - 1 do
		for x = 0, W - 1 do
			local i = y * W + x
			local q = i * 4
			local v = buffer.readu32(st.base, q)
			local a = v // 16777216
			if a > 0 then
				local r, g, b = v % 256, (v // 256) % 256, (v // 65536) % 256
				local m = buffer.readf32(st.mask, q)
				local p = buffer.readf32(st.phase, q)
				local k = 0
				if eff == "pulse" then
					local w = 0.5 + 0.5 * math.sin((p * freq - t * speed) * 2 * math.pi)
					k = m * w ^ sharp
				elseif eff == "flow" then
					local u = (p * freq + t * speed) % 1
					local fi = u * 256
					local i0 = math.floor(fi)
					local fr = fi - i0
					local l0, l1 = lut[i0 % 256 + 1], lut[(i0 + 1) % 256 + 1]
					k = m * (l0 + (l1 - l0) * fr) ^ sharp
				elseif eff == "dissolve" then
					local nzv = buffer.readf32(st.noise, q)
					local d = nzv - progress
					if d < 0 then
						a = 0
					elseif d < width then
						k = 1 - d / width
					end
				elseif eff == "scan" then
					local d = (p - scanC) / width
					k = m * math.exp(-d * d)
				elseif eff == "spread" then
					local d = front - p
					if d > 0 then
						-- behind the front: the new material
						local mm = math.min(1, d / (width * 4)) * (if m > 0 then m else 1)
						r, g, b = r + (ar - r) * mm, g + (ag - g) * mm, b + (ab - b) * mm
					end
					local e = d / width
					k = math.exp(-e * e)
				end
				if k > 0 then
					-- additive glow toward the colour (saturates like an emissive)
					r, g, b = r + (cr - r) * math.min(1, k), g + (cg - g) * math.min(1, k), b + (cb - b) * math.min(1, k)
					r, g, b = r + cr * k * 0.35, g + cg * k * 0.35, b + cb * k * 0.35
				end
				buffer.writeu32(st.out, q, u8(r / 255) + u8(g / 255) * 256 + u8(b / 255) * 65536 + a * 16777216)
			end
		end
	end
end

--- Advances the animation. With `budgetTexels`, only that many texels (whole rows, round-robin)
--- are reshaded this frame; returns the dirty region (y0, rows) to upload. Without a budget the
--- whole image is reshaded and (0, H) is returned.
function Animate.step(st: State, t: number, budgetTexels: number?): (number, number)
	if not budgetTexels or budgetTexels >= st.W * st.H then
		Animate.shadeRows(st, t, 0, st.H)
		return 0, st.H
	end
	local rows = math.max(1, budgetTexels // st.W)
	local y0 = st.cursor
	rows = math.min(rows, st.H - y0)
	Animate.shadeRows(st, t, y0, rows)
	st.cursor = (y0 + rows) % st.H
	return y0, rows
end

--- The RGBA8 slice for rows [y0, y0 + rows), ready for WritePixelsBuffer on a region. The slice
--- buffer is reused while the row count stays the same, so steady-state frames allocate nothing.
function Animate.rows(st: State, y0: number, rows: number): buffer
	local len = st.W * rows * 4
	local b = st.slice
	if not b or buffer.len(b) ~= len then
		b = buffer.create(len)
		st.slice = b
	end
	buffer.copy(b :: buffer, 0, st.out, y0 * st.W * 4, len)
	return b :: buffer
end

return Animate
