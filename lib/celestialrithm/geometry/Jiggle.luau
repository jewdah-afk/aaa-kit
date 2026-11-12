--!strict
--!native
--!optimize 2
-- Jiggle: squash-and-stretch and wobble for voxel meshes, as spring-driven per-vertex offsets (topology unchanged).
--
-- Design (why a spring lattice and not one spring per vertex):
--   Greedy meshes have T-junctions (a vertex of one quad lying on the edge of a bigger neighbour). If each vertex
--   moved by an arbitrary function, the long edge would stay straight while the T vertex left it: cracks. So every
--   offset is a function of the REST position that is linear along every axis-aligned edge:
--     offset.y = -S * (y - pivotY)                                  (global squash; affine)
--     offset.x = swayX(y) + (x - pivotX) * radial(y)                (sway + volume bulge)
--     offset.z = swayZ(y) + (z - pivotZ) * radial(y)
--   swayX/swayZ/radial are piecewise linear in y between lattice nodes spaced `spacing` studs apart. Mesh with
--   GreedyMesher's `splitEvery` = the same spacing in cells so no edge crosses a node, and the mesh stays closed.
--   (Tested: qa/test_runtime.luau checks linearity along every quad edge, with and without the cut.)
-- Springs: one global squash spring S (default critically damped, so it recovers without ringing) and per node one
-- sway spring per axis plus one radial wobble spring (default under-damped, frequency falling with height, so the
-- top lags and the wobble travels up). Node 0 has weight 0: the base stays planted.
-- Integration is the exact solution of the damped oscillator over dt (coefficients cached per dt), so it is stable
-- at any frame time and its energy 0.5 * (v^2 + w^2 x^2) never increases. step/apply allocate nothing.
-- Pure Luau, no Roblox API.

local Jiggle = {}

export type Rig = {
	nodes: number,
	y0: number, -- stud Y of node 0
	spacing: number, -- studs between nodes
	px: number, -- pivot (studs): base centre
	py: number,
	pz: number,
	weight: buffer, -- f32 per node: impulse response (0 at the base)
	omega: buffer, -- f32 per node: sway / wobble angular frequency
	zeta: number,
	-- node states (f32 per node): position + velocity for sway x, sway z, radial
	sx: buffer,
	vx: buffer,
	sz: buffer,
	vz: buffer,
	sr: buffer,
	vr: buffer,
	-- cached exact transition coefficients for the last dt (f32 per node: a11, a12, a21, a22)
	coef: buffer,
	coefDt: number,
	-- global squash spring
	S: number,
	vS: number,
	omegaS: number,
	zetaS: number,
	sq: buffer, -- 4 f64: squash coefficients
	bulge: number, -- horizontal response to squash (0.5 ~ volume preserving)
	maxSquash: number,
	-- per-step lattice values (f32 per node): total sway / radial after clamps, read by apply()
	ox: buffer,
	oz: buffer,
	orad: buffer,
	Sd: number, -- displayed (clamped) squash
}

export type Binding = {
	count: number,
	rest: buffer, -- f32 x3 rest positions (studs)
	out: buffer, -- f32 x3 deformed positions
	node: buffer, -- u16 per vertex: lower lattice node
	frac: buffer, -- f32 per vertex: position between node and node + 1
}

export type RigOptions = {
	pivot: { number }, -- base centre, studs
	y0: number, -- stud Y of the first node (usually the model bottom)
	height: number, -- studs covered by the lattice
	spacing: number, -- studs between nodes (match GreedyMesher splitEvery * voxelSize)
	freqBase: number?, -- Hz of the lowest moving node, default 2.6
	freqTop: number?, -- Hz of the top node, default 1.6
	zeta: number?, -- wobble damping ratio, default 0.22
	squashFreq: number?, -- Hz, default 3.2
	squashZeta: number?, -- default 1 (critically damped)
	bulge: number?, -- default 0.5
	maxSquash: number?, -- clamp on the displayed squash, default 0.45
}

function Jiggle.newRig(o: RigOptions): Rig
	local nodes = math.max(2, math.ceil(o.height / o.spacing - 1e-6) + 1)
	local function f32(): buffer
		return buffer.create(nodes * 4)
	end
	local rig: Rig = {
		nodes = nodes,
		y0 = o.y0,
		spacing = o.spacing,
		px = o.pivot[1],
		py = o.pivot[2],
		pz = o.pivot[3],
		weight = f32(),
		omega = f32(),
		zeta = o.zeta or 0.22,
		sx = f32(),
		vx = f32(),
		sz = f32(),
		vz = f32(),
		sr = f32(),
		vr = f32(),
		coef = buffer.create(nodes * 16),
		coefDt = -1,
		S = 0,
		vS = 0,
		omegaS = 2 * math.pi * (o.squashFreq or 3.2),
		zetaS = o.squashZeta or 1,
		sq = buffer.create(32),
		bulge = o.bulge or 0.5,
		maxSquash = o.maxSquash or 0.45,
		ox = f32(),
		oz = f32(),
		orad = f32(),
		Sd = 0,
	}
	local fb, ft = o.freqBase or 2.6, o.freqTop or 1.6
	for k = 0, nodes - 1 do
		local t = k / (nodes - 1)
		buffer.writef32(rig.weight, k * 4, t ^ 1.5)
		buffer.writef32(rig.omega, k * 4, 2 * math.pi * (fb + (ft - fb) * t))
	end
	return rig
end

-- Binds a vertex buffer (f32 x3 rest positions) to the rig. Allocates once; apply() reuses everything.
function Jiggle.bind(rig: Rig, rest: buffer, count: number): Binding
	local b: Binding = { count = count, rest = rest, out = buffer.create(count * 12), node = buffer.create(count * 2), frac = buffer.create(count * 4) }
	buffer.copy(b.out, 0, rest, 0, count * 12)
	local last = rig.nodes - 1
	for v = 0, count - 1 do
		local t = (buffer.readf32(rest, v * 12 + 4) - rig.y0) / rig.spacing
		t = math.clamp(t, 0, last)
		local k = math.min(math.floor(t), last - 1)
		buffer.writeu16(b.node, v * 2, k)
		buffer.writef32(b.frac, v * 4, t - k)
	end
	return b
end

-- Exact damped-oscillator transition over dt: [x', v'] = [[a11, a12], [a21, a22]] [x, v].
local function transition(w: number, z: number, dt: number): (number, number, number, number)
	local e = math.exp(-z * w * dt)
	if math.abs(z - 1) < 1e-6 then
		return e * (1 + w * dt), e * dt, -e * w * w * dt, e * (1 - w * dt)
	elseif z < 1 then
		local wd = w * math.sqrt(1 - z * z)
		local c, s = math.cos(wd * dt), math.sin(wd * dt)
		return e * (c + z * w / wd * s), e * s / wd, -e * w * w / wd * s, e * (c - z * w / wd * s)
	end
	local wh = w * math.sqrt(z * z - 1)
	local c, s = math.cosh(wh * dt), math.sinh(wh * dt)
	return e * (c + z * w / wh * s), e * s / wh, -e * w * w / wh * s, e * (c - z * w / wh * s)
end

local function ensureCoef(rig: Rig, dt: number)
	if dt == rig.coefDt then
		return
	end
	rig.coefDt = dt
	for k = 0, rig.nodes - 1 do
		local a11, a12, a21, a22 = transition(buffer.readf32(rig.omega, k * 4), rig.zeta, dt)
		buffer.writef32(rig.coef, k * 16, a11)
		buffer.writef32(rig.coef, k * 16 + 4, a12)
		buffer.writef32(rig.coef, k * 16 + 8, a21)
		buffer.writef32(rig.coef, k * 16 + 12, a22)
	end
	local a11, a12, a21, a22 = transition(rig.omegaS, rig.zetaS, dt)
	buffer.writef64(rig.sq, 0, a11)
	buffer.writef64(rig.sq, 8, a12)
	buffer.writef64(rig.sq, 16, a21)
	buffer.writef64(rig.sq, 24, a22)
end

-- Adds velocity: (vx, vz) studs/s of sideways sway at full weight, squashVel (1/s) to the squash spring
-- (positive = squash down, negative = stretch up), wobbleVel (1/s) to the radial wobble.
function Jiggle.impulse(rig: Rig, vx: number, vz: number, squashVel: number, wobbleVel: number?)
	local wv = wobbleVel or 0
	for k = 0, rig.nodes - 1 do
		local w = buffer.readf32(rig.weight, k * 4)
		buffer.writef32(rig.vx, k * 4, buffer.readf32(rig.vx, k * 4) + vx * w)
		buffer.writef32(rig.vz, k * 4, buffer.readf32(rig.vz, k * 4) + vz * w)
		buffer.writef32(rig.vr, k * 4, buffer.readf32(rig.vr, k * 4) + wv * w)
	end
	rig.vS += squashVel
end

-- Advances all springs by dt and refreshes the lattice values apply() reads. Returns the total energy.
function Jiggle.step(rig: Rig, dt: number): number
	ensureCoef(rig, dt)
	local coef = rig.coef
	local energy = 0
	local sx, vx, sz, vz, sr, vr = rig.sx, rig.vx, rig.sz, rig.vz, rig.sr, rig.vr
	local a11s, a12s, a21s, a22s = buffer.readf64(rig.sq, 0), buffer.readf64(rig.sq, 8), buffer.readf64(rig.sq, 16), buffer.readf64(rig.sq, 24)
	local S, vS = rig.S, rig.vS
	S, vS = a11s * S + a12s * vS, a21s * S + a22s * vS
	rig.S, rig.vS = S, vS
	energy += 0.5 * (vS * vS + rig.omegaS * rig.omegaS * S * S)
	local Sd = math.clamp(S, -rig.maxSquash, rig.maxSquash)
	rig.Sd = Sd
	local bulgeS = Sd * rig.bulge
	for k = 0, rig.nodes - 1 do
		local o = k * 4
		local a11, a12, a21, a22 = buffer.readf32(coef, k * 16), buffer.readf32(coef, k * 16 + 4), buffer.readf32(coef, k * 16 + 8), buffer.readf32(coef, k * 16 + 12)
		local w = buffer.readf32(rig.omega, o)
		local x, v = buffer.readf32(sx, o), buffer.readf32(vx, o)
		x, v = a11 * x + a12 * v, a21 * x + a22 * v
		buffer.writef32(sx, o, x)
		buffer.writef32(vx, o, v)
		energy += 0.5 * (v * v + w * w * x * x)
		buffer.writef32(rig.ox, o, x)
		x, v = buffer.readf32(sz, o), buffer.readf32(vz, o)
		x, v = a11 * x + a12 * v, a21 * x + a22 * v
		buffer.writef32(sz, o, x)
		buffer.writef32(vz, o, v)
		energy += 0.5 * (v * v + w * w * x * x)
		buffer.writef32(rig.oz, o, x)
		x, v = buffer.readf32(sr, o), buffer.readf32(vr, o)
		x, v = a11 * x + a12 * v, a21 * x + a22 * v
		buffer.writef32(sr, o, x)
		buffer.writef32(vr, o, v)
		energy += 0.5 * (v * v + w * w * x * x)
		buffer.writef32(rig.orad, o, math.clamp(x, -0.4, 0.4) + bulgeS)
	end
	return energy
end

-- Deformed position of one rest point (the same function apply() uses; for tests and attachments).
function Jiggle.deformPoint(rig: Rig, x: number, y: number, z: number): (number, number, number)
	local last = rig.nodes - 1
	local t = math.clamp((y - rig.y0) / rig.spacing, 0, last)
	local k = math.min(math.floor(t), last - 1)
	local f = t - k
	local o0, o1 = k * 4, k * 4 + 4
	local swx = buffer.readf32(rig.ox, o0) + (buffer.readf32(rig.ox, o1) - buffer.readf32(rig.ox, o0)) * f
	local swz = buffer.readf32(rig.oz, o0) + (buffer.readf32(rig.oz, o1) - buffer.readf32(rig.oz, o0)) * f
	local rad = buffer.readf32(rig.orad, o0) + (buffer.readf32(rig.orad, o1) - buffer.readf32(rig.orad, o0)) * f
	return x + swx + (x - rig.px) * rad, y - rig.Sd * (y - rig.py), z + swz + (z - rig.pz) * rad
end

-- Writes deformed positions for a binding into binding.out. No allocation.
function Jiggle.apply(rig: Rig, b: Binding)
	local rest, out, node, frac = b.rest, b.out, b.node, b.frac
	local ox, oz, orad = rig.ox, rig.oz, rig.orad
	local px, py, pz, Sd = rig.px, rig.py, rig.pz, rig.Sd
	for v = 0, b.count - 1 do
		local k = buffer.readu16(node, v * 2)
		local f = buffer.readf32(frac, v * 4)
		local o0 = k * 4
		local a = buffer.readf32(ox, o0)
		local swx = a + (buffer.readf32(ox, o0 + 4) - a) * f
		a = buffer.readf32(oz, o0)
		local swz = a + (buffer.readf32(oz, o0 + 4) - a) * f
		a = buffer.readf32(orad, o0)
		local rad = a + (buffer.readf32(orad, o0 + 4) - a) * f
		local p = v * 12
		local x, y, z = buffer.readf32(rest, p), buffer.readf32(rest, p + 4), buffer.readf32(rest, p + 8)
		buffer.writef32(out, p, x + swx + (x - px) * rad)
		buffer.writef32(out, p + 4, y - Sd * (y - py))
		buffer.writef32(out, p + 8, z + swz + (z - pz) * rad)
	end
end

function Jiggle.energy(rig: Rig): number
	local e = 0.5 * (rig.vS * rig.vS + rig.omegaS * rig.omegaS * rig.S * rig.S)
	for k = 0, rig.nodes - 1 do
		local o = k * 4
		local w = buffer.readf32(rig.omega, o)
		for _, pair in { { rig.sx, rig.vx }, { rig.sz, rig.vz }, { rig.sr, rig.vr } } do
			local x, v = buffer.readf32(pair[1], o), buffer.readf32(pair[2], o)
			e += 0.5 * (v * v + w * w * x * x)
		end
	end
	return e
end

return Jiggle
