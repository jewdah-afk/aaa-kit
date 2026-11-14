--!strict
-- JellyMeter: a rounded 3D fill meter for EditableMesh. Fixed topology (rings x segments), so a
-- frame only moves vertices and recolours them. Pure geometry + spring here; `mount` is the
-- Roblox wrapper (ViewportFrame + EditableMesh), not run by the lune test.
--
-- Look: a dark glass capsule; inside, a liquid body whose level springs to the target with a
-- small overshoot, whose top surface tilts and ripples while it moves (slosh), and whose colour
-- climbs green -> yellow -> orange -> red with the level. Vertical shading gives depth; the top
-- surface is lighter so the level always reads.

export type Params = {
	Height: number, -- inner capsule height (studs)
	Radius: number, -- inner capsule radius
	Rings: number, -- rings up the body (>= 6)
	Segments: number, -- around (>= 12)
}

export type Geo = { Pos: { Vector3 }, Col: { Color3 }, Tri: { { number } } }

export type Spring = { Level: number, Vel: number, Target: number, Slosh: number }

local JellyMeter = {}

-- Roblox has these as globals; lune gets them from @lune/roblox so the test can run headless.
local RobloxTypes = if typeof(Vector3) == "nil" then (require :: any)("@lune/roblox") else nil
local Vector3 = if RobloxTypes then RobloxTypes.Vector3 else Vector3
local Color3 = if RobloxTypes then RobloxTypes.Color3 else Color3

JellyMeter.Default = { Height = 6, Radius = 0.7, Rings = 14, Segments = 24 } :: Params

-- Colour ramp by level (sRGB stops; lerped in a perceptual-ish way via gamma 2.2).
local STOPS = {
	{ 0.00, Color3.fromRGB(88, 214, 74) },
	{ 0.45, Color3.fromRGB(255, 232, 96) },
	{ 0.75, Color3.fromRGB(255, 140, 34) },
	{ 1.00, Color3.fromRGB(255, 64, 54) },
}

local function lin(c: number): number
	return c ^ 2.2
end
local function enc(c: number): number
	return math.clamp(c, 0, 1) ^ (1 / 2.2)
end

function JellyMeter.ramp(t: number): Color3
	t = math.clamp(t, 0, 1)
	for i = 1, #STOPS - 1 do
		local a, b = STOPS[i], STOPS[i + 1]
		if t <= b[1] then
			local k = (t - a[1]) / (b[1] - a[1])
			local ca, cb = a[2], b[2]
			return Color3.new(
				enc(lin(ca.R) + (lin(cb.R) - lin(ca.R)) * k),
				enc(lin(ca.G) + (lin(cb.G) - lin(ca.G)) * k),
				enc(lin(ca.B) + (lin(cb.B) - lin(ca.B)) * k)
			)
		end
	end
	return STOPS[#STOPS][2]
end

-- Capsule radius at height y (hemispherical ends).
local function capR(p: Params, y: number): number
	local R, H = p.Radius, p.Height
	if y < R then
		local d = R - y
		return math.sqrt(math.max(0, R * R - d * d))
	elseif y > H - R then
		local d = y - (H - R)
		return math.sqrt(math.max(0, R * R - d * d))
	end
	return R
end

-- Topology: ring 1 is the bottom pole (one vertex), rings 2..Rings are full rings, the last ring
-- is the liquid surface edge, plus one surface centre vertex. Counts never change.
function JellyMeter.counts(p: Params): (number, number)
	local nv = 1 + (p.Rings - 1) * p.Segments + 1
	local nt = p.Segments + (p.Rings - 2) * p.Segments * 2 + p.Segments
	return nv, nt
end

-- level 0..1, slosh = surface tilt (studs of rise at the front edge), ripple 0..1, t = seconds.
function JellyMeter.liquid(p: Params, level: number, slosh: number, ripple: number, t: number): Geo
	level = math.clamp(level, 0.02, 1)
	local top = p.Height * level
	local S = p.Segments
	local pos: { Vector3 } = {}
	local col: { Color3 } = {}
	local base = JellyMeter.ramp(level)
	local function shade(c: Color3, k: number): Color3
		return Color3.new(math.clamp(c.R * k, 0, 1), math.clamp(c.G * k, 0, 1), math.clamp(c.B * k, 0, 1))
	end
	table.insert(pos, Vector3.new(0, 0, 0))
	table.insert(col, shade(base, 0.55))
	for k = 2, p.Rings do
		-- the first B rings follow the rounded base (fixed heights), the rest share the column,
		-- so the bottom stays round at any level instead of stretching into a point
		local B = math.max(3, math.floor(p.Rings * 0.3))
		local yb = math.min(top, p.Radius)
		local y
		if k - 1 <= B then
			y = math.min(top, p.Radius * (1 - math.cos((k - 1) / B * math.pi / 2)))
		else
			y = yb + (top - yb) * ((k - 1 - B) / (p.Rings - 1 - B))
		end
		local e = y / p.Height
		local r = capR(p, y)
		local isTop = k == p.Rings
		for s = 0, S - 1 do
			local a = s / S * math.pi * 2
			local x, z = math.cos(a) * r, math.sin(a) * r
			local yy = y
			if isTop then
				yy += slosh * (z / p.Radius) + ripple * 0.06 * math.sin(a * 3 + t * 9)
				yy = math.clamp(yy, 0.02, p.Height)
			end
			table.insert(pos, Vector3.new(x, yy, z))
			local side = 0.82 + 0.18 * math.cos(a - math.pi * 0.75) -- key light from front-left
			local vert = 0.6 + 0.4 * e
			table.insert(col, shade(base, side * vert * (isTop and 1.12 or 1)))
		end
	end
	table.insert(pos, Vector3.new(0, top + ripple * 0.04 * math.sin(t * 7), 0))
	table.insert(col, shade(base, 1.25))
	-- triangles
	local tri: { { number } } = {}
	local function ring(k: number, s: number): number
		return 1 + (k - 2) * S + (s % S) + 1
	end
	for s = 0, S - 1 do
		table.insert(tri, { 1, ring(2, s + 1), ring(2, s) })
	end
	for k = 2, p.Rings - 1 do
		for s = 0, S - 1 do
			local a, b, c, d = ring(k, s), ring(k, s + 1), ring(k + 1, s), ring(k + 1, s + 1)
			table.insert(tri, { a, b, d })
			table.insert(tri, { a, d, c })
		end
	end
	local centre = #pos
	for s = 0, S - 1 do
		table.insert(tri, { centre, ring(p.Rings, s), ring(p.Rings, s + 1) })
	end
	return { Pos = pos, Col = col, Tri = tri }
end

-- Spring toward Target: slight overshoot (reads as "growing"), slosh follows level velocity.
function JellyMeter.spring(target: number): Spring
	return { Level = target, Vel = 0, Target = target, Slosh = 0 }
end

function JellyMeter.step(sp: Spring, dt: number)
	local k, c = 140, 15 -- stiffness, damping (zeta ~0.63: one small overshoot)
	local acc = (sp.Target - sp.Level) * k - sp.Vel * c
	sp.Vel += acc * dt
	sp.Level = math.clamp(sp.Level + sp.Vel * dt, 0, 1)
	local want = math.clamp(-sp.Vel * 0.18, -0.25, 0.25)
	sp.Slosh += (want - sp.Slosh) * math.min(1, dt * 10)
end

-- Roblox wrapper. Builds the mesh once, then `update(dt)` moves vertices and recolours.
-- Returns the MeshPart (parent it into a WorldModel inside a ViewportFrame) and a controller.
function JellyMeter.mount(p: Params?)
	local AssetService = game:GetService("AssetService")
	local params = p or JellyMeter.Default
	local sp = JellyMeter.spring(0)
	local g = JellyMeter.liquid(params, sp.Level, 0, 0, 0)
	local em = AssetService:CreateEditableMesh()
	local vids, cids = {}, {}
	for i, v in g.Pos do
		vids[i] = em:AddVertex(v)
		cids[i] = em:AddColor(g.Col[i], 1)
	end
	for _, t in g.Tri do
		local fid = em:AddTriangle(vids[t[1]], vids[t[2]], vids[t[3]])
		em:SetFaceColors(fid, { cids[t[1]], cids[t[2]], cids[t[3]] })
	end
	local part = AssetService:CreateMeshPartAsync(Content.fromObject(em))
	part.Anchored = true
	local clock = 0
	local ctl = {}
	function ctl.set(target: number)
		sp.Target = math.clamp(target, 0, 1)
	end
	function ctl.update(dt: number)
		clock += dt
		JellyMeter.step(sp, dt)
		local moving = math.abs(sp.Vel) + math.abs(sp.Slosh)
		if moving < 1e-3 and math.abs(sp.Target - sp.Level) < 1e-3 then
			return -- at rest: nothing loops (calm frame)
		end
		local geo = JellyMeter.liquid(params, sp.Level, sp.Slosh, math.min(1, moving * 4), clock)
		for i, v in geo.Pos do
			em:SetPosition(vids[i], v)
			em:SetColor(cids[i], geo.Col[i])
		end
	end
	return part, ctl
end

return JellyMeter
