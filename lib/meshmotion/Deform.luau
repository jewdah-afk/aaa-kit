--!native
--!optimize 2
-- Deform: procedural vertex modifiers run after Rig.skin, in place on rig.out.
-- Each constructor returns a deformer (rig, t, dt) -> (). Options may limit it to some segments
-- (`segments = {"Tail", "FinL"}`), which also gives creatures with many parts cheap per-part motion.
-- All are deterministic in t except `jiggle`, which integrates a spring per vertex with a fixed max step.
-- No allocation per frame after the first call. Pure Luau.

local Deform = {}

local rf, wf = buffer.readf32, buffer.writef32

type Rig = any

-- Per-mesh segment mask, built once per MeshData.
local function maskFor(names: { string }?)
	local cache = setmetatable({}, { __mode = "k" })
	return function(data): { boolean }?
		if not names then
			return nil
		end
		local m = cache[data]
		if not m then
			m = table.create(#data.segments, false)
			for _, nm in names do
				local i = data.segIndex[nm]
				assert(i, `deformer: no segment {nm}`)
				m[i] = true
			end
			cache[data] = m
		end
		return m
	end
end

local function on(mask: { boolean }?, data, v: number): boolean
	return mask == nil or mask[buffer.readu16(data.seg, v * 2)]
end

-- Whole-body vertical bob.
function Deform.bob(o: { amp: number, freq: number, phase: number?, segments: { string }? })
	local getMask = maskFor(o.segments)
	return function(rig: Rig, t: number)
		local d, out = rig.data, rig.out
		local mask = getMask(d)
		local dy = o.amp * math.sin((t * o.freq + (o.phase or 0)) * 2 * math.pi)
		for v = 0, d.n - 1 do
			if on(mask, d, v) then
				local b = v * 12 + 4
				wf(out, b, rf(out, b) + dy)
			end
		end
	end
end

-- Volume-preserving squash and stretch from the feet: y scales by s, x and z by 1/sqrt(s).
function Deform.squash(o: { amount: number, freq: number, phase: number?, segments: { string }? })
	local getMask = maskFor(o.segments)
	return function(rig: Rig, t: number)
		local d, out = rig.data, rig.out
		local mask = getMask(d)
		local s = 1 + o.amount * math.sin((t * o.freq + (o.phase or 0)) * 2 * math.pi)
		local inv = 1 / math.sqrt(s)
		local bmin, bmax = d.bounds.min, d.bounds.max
		local cx, cz, base = (bmin[1] + bmax[1]) * 0.5, (bmin[3] + bmax[3]) * 0.5, bmin[2]
		for v = 0, d.n - 1 do
			if on(mask, d, v) then
				local b = v * 12
				wf(out, b, cx + (rf(out, b) - cx) * inv)
				wf(out, b + 4, base + (rf(out, b + 4) - base) * s)
				wf(out, b + 8, cz + (rf(out, b + 8) - cz) * inv)
			end
		end
	end
end

-- Travelling sine wave along one rest axis, displacing another (tails, fins, tentacles).
-- Amplitude ramps from 0 at `from` to full at `to` along the axis (rest coordinates), so roots stay put.
function Deform.wave(o: {
	amp: number,
	wavelength: number,
	speed: number,
	along: number?, -- 1 x, 2 y, 3 z (default 3)
	push: number?, -- axis displaced (default 1)
	from: number?,
	to: number?,
	segments: { string }?,
})
	local getMask = maskFor(o.segments)
	local along, push = o.along or 3, o.push or 1
	return function(rig: Rig, t: number)
		local d, out, rest = rig.data, rig.out, rig.data.rest
		local mask = getMask(d)
		local from = o.from or d.bounds.min[along]
		local to = o.to or d.bounds.max[along]
		local span = if to ~= from then to - from else 1
		local k, w = 2 * math.pi / o.wavelength, 2 * math.pi * o.speed
		for v = 0, d.n - 1 do
			if on(mask, d, v) then
				local a = rf(rest, v * 12 + (along - 1) * 4)
				local ramp = math.clamp((a - from) / span, 0, 1)
				ramp = ramp * ramp * (3 - 2 * ramp)
				local b = v * 12 + (push - 1) * 4
				wf(out, b, rf(out, b) + o.amp * ramp * math.sin(k * a - w * t))
			end
		end
	end
end

-- Twist around the vertical axis through each vertex's segment pivot (posed), growing with height above it
-- (horns, drills, spirals). Pass `segments` to twist only those parts.
function Deform.twist(o: { rate: number, speed: number, segments: { string }? })
	local getMask = maskFor(o.segments)
	local px, py, pz = {}, {}, {}
	return function(rig: Rig, t: number)
		local d, out = rig.data, rig.out
		local mask = getMask(d)
		for i, sg in d.segments do
			if mask == nil or mask[i] then
				local pv = sg.pivot
				px[i], py[i], pz[i] = rig:transformPoint(sg.name, pv[1], pv[2], pv[3])
			end
		end
		local amt = o.rate * math.sin(t * o.speed * 2 * math.pi)
		for v = 0, d.n - 1 do
			local si = buffer.readu16(d.seg, v * 2)
			if mask == nil or mask[si] then
				local b = v * 12
				local cx, cz = px[si], pz[si]
				local x, y, z = rf(out, b) - cx, rf(out, b + 4), rf(out, b + 8) - cz
				local ang = amt * math.max(0, y - py[si])
				local c, s = math.cos(ang), math.sin(ang)
				wf(out, b, cx + x * c - z * s)
				wf(out, b + 8, cz + x * s + z * c)
			end
		end
	end
end

-- Secondary motion: each vertex trails its posed position on a damped spring, scaled by its weight
-- (MeshData.weight; 0 = rigid). Crystals, ears, antennae wobble after the body moves.
function Deform.jiggle(o: { stiffness: number, damping: number, maxStep: number?, key: string? })
	local key = o.key or "jiggle"
	local maxStep = o.maxStep or (1 / 60)
	return function(rig: Rig, _t: number, dt: number)
		local d, out = rig.data, rig.out
		local st = rig.state[key]
		if not st then
			st = { p = buffer.create(d.n * 12), vel = buffer.create(d.n * 12) }
			buffer.copy(st.p, 0, out, 0, d.n * 12)
			rig.state[key] = st
			return
		end
		local p, vel, weight = st.p, st.vel, d.weight
		local steps = math.clamp(math.ceil(dt / maxStep), 1, 8)
		local h = math.min(dt, maxStep * 8) / steps
		local k, c = o.stiffness, o.damping
		for v = 0, d.n - 1 do
			local wgt = rf(weight, v * 4)
			local b = v * 12
			if wgt <= 0 then
				-- rigid: keep the spring at rest so turning jiggle on later does not snap
				buffer.copy(p, b, out, b, 12)
				wf(vel, b, 0); wf(vel, b + 4, 0); wf(vel, b + 8, 0)
			else
				for a = 0, 8, 4 do
					local target = rf(out, b + a)
					local x, u = rf(p, b + a), rf(vel, b + a)
					for _ = 1, steps do
						u += (k * (target - x) - c * u) * h -- semi-implicit Euler
						x += u * h
					end
					wf(p, b + a, x)
					wf(vel, b + a, u)
					wf(out, b + a, target + (x - target) * wgt)
				end
			end
		end
	end
end

return Deform
