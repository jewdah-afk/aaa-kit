--!native
--!optimize 2
-- Rig: segment hierarchy -> skinned vertex positions, no rebuild.
-- Each segment has a pose (rotation rx/ry/rz in radians, applied Y then X then Z; translation; uniform scale)
-- around its own pivot. World transform = parent world * T(pivot + t) * R * S * T(-pivot).
-- Every vertex belongs to one segment (rigid voxel parts); `skin` writes the posed positions into `out`
-- (n * 3 f32), which deformers then modify in place and the adapter pushes with one BatchSetValues.
-- No allocation in solve/skin. Pure Luau.

local Store = require("./Store")

local Rig = {}
Rig.__index = Rig

export type Pose = { rx: number, ry: number, rz: number, tx: number, ty: number, tz: number, s: number }
export type Rig = typeof(setmetatable(
	{} :: {
		data: Store.MeshData,
		pose: { Pose },
		world: buffer, -- segments * 12 f32, row-major 3x4
		out: buffer, -- n * 3 f32
		state: { [string]: any }, -- deformer scratch (spring velocities etc.)
	},
	Rig
))

local function identityPose(): Pose
	return { rx = 0, ry = 0, rz = 0, tx = 0, ty = 0, tz = 0, s = 1 }
end
Rig.identityPose = identityPose

function Rig.new(data: Store.MeshData): Rig
	local pose = table.create(#data.segments)
	for i = 1, #data.segments do
		pose[i] = identityPose()
	end
	local self = setmetatable({
		data = data,
		pose = pose,
		world = buffer.create(#data.segments * 48),
		out = buffer.create(data.n * 12),
		state = {},
	}, Rig)
	buffer.copy(self.out, 0, data.rest, 0, data.n * 12)
	return self
end

function Rig.resetPose(self: Rig)
	for _, p in self.pose do
		p.rx, p.ry, p.rz, p.tx, p.ty, p.tz, p.s = 0, 0, 0, 0, 0, 0, 1
	end
end

function Rig.segment(self: Rig, name: string): Pose
	local i = self.data.segIndex[name]
	assert(i, `no segment {name}`)
	return self.pose[i]
end

local rf, wf = buffer.readf32, buffer.writef32

-- Local 3x4 of one pose into 12 locals.
local function localMatrix(p: Pose, pv: { number })
	local cy, sy = math.cos(p.ry), math.sin(p.ry)
	local cx, sx = math.cos(p.rx), math.sin(p.rx)
	local cz, sz = math.cos(p.rz), math.sin(p.rz)
	-- R = Ry * Rx * Rz
	local a00 = cy * cz + sy * sx * sz
	local a01 = -cy * sz + sy * sx * cz
	local a02 = sy * cx
	local a10 = cx * sz
	local a11 = cx * cz
	local a12 = -sx
	local a20 = -sy * cz + cy * sx * sz
	local a21 = sy * sz + cy * sx * cz
	local a22 = cy * cx
	local s = p.s
	a00, a01, a02 = a00 * s, a01 * s, a02 * s
	a10, a11, a12 = a10 * s, a11 * s, a12 * s
	a20, a21, a22 = a20 * s, a21 * s, a22 * s
	local px, py, pz = pv[1], pv[2], pv[3]
	local t0 = px + p.tx - (a00 * px + a01 * py + a02 * pz)
	local t1 = py + p.ty - (a10 * px + a11 * py + a12 * pz)
	local t2 = pz + p.tz - (a20 * px + a21 * py + a22 * pz)
	return a00, a01, a02, t0, a10, a11, a12, t1, a20, a21, a22, t2
end

-- Solve world matrices parents-first.
function Rig.solve(self: Rig)
	local w, segs = self.world, self.data.segments
	for i, sg in segs do
		local l00, l01, l02, l03, l10, l11, l12, l13, l20, l21, l22, l23 = localMatrix(self.pose[i], sg.pivot)
		local o = (i - 1) * 48
		if sg.parent then
			local q = (sg.parent - 1) * 48
			local p00, p01, p02, p03 = rf(w, q), rf(w, q + 4), rf(w, q + 8), rf(w, q + 12)
			local p10, p11, p12, p13 = rf(w, q + 16), rf(w, q + 20), rf(w, q + 24), rf(w, q + 28)
			local p20, p21, p22, p23 = rf(w, q + 32), rf(w, q + 36), rf(w, q + 40), rf(w, q + 44)
			wf(w, o, p00 * l00 + p01 * l10 + p02 * l20)
			wf(w, o + 4, p00 * l01 + p01 * l11 + p02 * l21)
			wf(w, o + 8, p00 * l02 + p01 * l12 + p02 * l22)
			wf(w, o + 12, p00 * l03 + p01 * l13 + p02 * l23 + p03)
			wf(w, o + 16, p10 * l00 + p11 * l10 + p12 * l20)
			wf(w, o + 20, p10 * l01 + p11 * l11 + p12 * l21)
			wf(w, o + 24, p10 * l02 + p11 * l12 + p12 * l22)
			wf(w, o + 28, p10 * l03 + p11 * l13 + p12 * l23 + p13)
			wf(w, o + 32, p20 * l00 + p21 * l10 + p22 * l20)
			wf(w, o + 36, p20 * l01 + p21 * l11 + p22 * l21)
			wf(w, o + 40, p20 * l02 + p21 * l12 + p22 * l22)
			wf(w, o + 44, p20 * l03 + p21 * l13 + p22 * l23 + p23)
		else
			wf(w, o, l00); wf(w, o + 4, l01); wf(w, o + 8, l02); wf(w, o + 12, l03)
			wf(w, o + 16, l10); wf(w, o + 20, l11); wf(w, o + 24, l12); wf(w, o + 28, l13)
			wf(w, o + 32, l20); wf(w, o + 36, l21); wf(w, o + 40, l22); wf(w, o + 44, l23)
		end
	end
end

-- World-space position of a point given in a segment's rest frame (e.g. where to attach VFX).
function Rig.transformPoint(self: Rig, segName: string, x: number, y: number, z: number): (number, number, number)
	local i = self.data.segIndex[segName]
	local w, o = self.world, (i - 1) * 48
	return rf(w, o) * x + rf(w, o + 4) * y + rf(w, o + 8) * z + rf(w, o + 12),
		rf(w, o + 16) * x + rf(w, o + 20) * y + rf(w, o + 24) * z + rf(w, o + 28),
		rf(w, o + 32) * x + rf(w, o + 36) * y + rf(w, o + 40) * z + rf(w, o + 44)
end

-- Rest -> out through each vertex's segment matrix.
function Rig.skin(self: Rig)
	local d, w, out = self.data, self.world, self.out
	local rest, seg = d.rest, d.seg
	local last, m00, m01, m02, m03, m10, m11, m12, m13, m20, m21, m22, m23 = -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
	for v = 0, d.n - 1 do
		local si = buffer.readu16(seg, v * 2)
		if si ~= last then
			last = si
			local o = (si - 1) * 48
			m00, m01, m02, m03 = rf(w, o), rf(w, o + 4), rf(w, o + 8), rf(w, o + 12)
			m10, m11, m12, m13 = rf(w, o + 16), rf(w, o + 20), rf(w, o + 24), rf(w, o + 28)
			m20, m21, m22, m23 = rf(w, o + 32), rf(w, o + 36), rf(w, o + 40), rf(w, o + 44)
		end
		local b = v * 12
		local x, y, z = rf(rest, b), rf(rest, b + 4), rf(rest, b + 8)
		wf(out, b, m00 * x + m01 * y + m02 * z + m03)
		wf(out, b + 4, m10 * x + m11 * y + m12 * z + m13)
		wf(out, b + 8, m20 * x + m21 * y + m22 * z + m23)
	end
end

-- solve + skin + deformers in order. Deformers: { (rig, t, dt) -> () }.
function Rig.update(self: Rig, t: number, dt: number, deformers: { (Rig, number, number) -> () }?)
	self:solve()
	self:skin()
	if deformers then
		for _, f in deformers do
			f(self, t, dt)
		end
	end
end

return Rig
