--!strict
-- Rig: plays a Blueprint in the world. Roblox only (it needs Instance), so it is compile-checked here, NOT run in lune and NOT
-- yet play-tested in Studio: play each template once, at rungs 0, 2 and 3, before shipping it.
-- The rules live in Blueprint and the clock in Timeline (both tested in lune); this file only turns a Plan into instances and
-- starts and stops them on the Timeline's cues.
--
-- Patterns it follows (../patterns.md): everything is built unparented and the effect is parented last; Beam and Trail
-- attachments exist before the Beam or Trail is created; bursts are Rate 0 + Emit; a Trail is enabled only after its part is
-- placed; tweens start from Timeline cues with explicit lengths in frames / 60; one PreRender connection drives the effect;
-- Debris destroys it after the longest particle life.
--
-- Setup once on the client:
--   Rig.setTextures({ ring_thin = "rbxassetid://...", ... })           roles listed in Blueprint.TEXTURE_ROLES
--   ReplicatedStorage.VfxMeshes holds the MeshPart templates a blueprint names (live EditableMeshes are capped at ~7 per client)
-- Ground contact: pass an origin CFrame at floor level. For a directional blueprint, forward is -Z: CFrame.lookAt(pos, pos + dir).

local Blueprint = require("./Blueprint")
local Timeline = require("./Timeline")

local Rig = {}

local RunService = (game :: any):GetService("RunService")
local TweenService = (game :: any):GetService("TweenService")
local Debris = (game :: any):GetService("Debris")
local ReplicatedStorage = (game :: any):GetService("ReplicatedStorage")
local Workspace = (game :: any):GetService("Workspace")

export type Options = { parent: Instance?, onHit: (() -> ())? }
export type Handle = { stop: () -> (), timeline: Timeline.Timeline }
type Runner = { start: (now: number) -> (), stop: () -> (), update: ((now: number) -> ())? }

Rig.MAX_ACTIVE = 8 -- start value, tune in play: past this a friendly effect is skipped, never queued (HIERARCHY.md §9)
local FADE_FRAMES = 4

local active = 0
local textures: { [string]: string } = {}
local warned: { [string]: boolean } = {}

local function warnOnce(key: string, msg: string)
	if not warned[key] then
		warned[key] = true
		warn(msg)
	end
end

function Rig.setTextures(map: { [string]: string })
	for role, id in map do
		textures[role] = id
	end
end

local function textureFor(role: string?): string?
	if role == nil then
		return nil
	end
	local id = textures[role]
	if id == nil then
		warnOnce("tex:" .. role, `Rig: no texture for role '{role}' (Rig.setTextures)`)
	end
	return id
end

-- plain data -> Roblox value (see Blueprint's header for the encodings)
local function resolve(v: any): any
	if type(v) ~= "table" then
		return v
	elseif v.range then
		return NumberRange.new(v.range[1], v.range[2])
	elseif v.seq then
		local keys = {}
		for _, k in v.seq do
			table.insert(keys, NumberSequenceKeypoint.new(k[1], k[2]))
		end
		return NumberSequence.new(keys)
	elseif v.cseq then
		local keys = {}
		for _, k in v.cseq do
			table.insert(keys, ColorSequenceKeypoint.new(k[1], Color3.new(k[2], k[3], k[4])))
		end
		return ColorSequence.new(keys)
	elseif v.color then
		return Color3.new(v.color[1], v.color[2], v.color[3])
	elseif v.vec then
		return Vector3.new(v.vec[1], v.vec[2], v.vec[3])
	elseif v.vec2 then
		return Vector2.new(v.vec2[1], v.vec2[2])
	elseif v.enum then
		return (Enum :: any)[v.enum[1]][v.enum[2]]
	end
	return v
end

-- PascalCase keys are Roblox properties; lowercase keys belong to the Rig
local function applyProps(inst: any, props: { [string]: any })
	for key, value in props do
		local c = string.byte(key, 1)
		if c >= 65 and c <= 90 and key ~= "Material" then
			inst[key] = resolve(value)
		end
	end
end

local function tint(c: { number }): Color3
	return Color3.new(c[1], c[2], c[3])
end

local function vec3(v: { number }?, fallback: Vector3): Vector3
	return if v then Vector3.new(v[1], v[2], v[3]) else fallback
end

local function newPart(name: string, cf: CFrame, size: Vector3): any
	local p = Instance.new("Part")
	p.Name = name
	p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch, p.CastShadow = true, false, false, false, false
	p.Transparency = 1
	p.Size = size
	p.CFrame = cf
	return p
end

local function seconds(L: Blueprint.Layer): number
	return (L.stop - L.start + 1) / Blueprint.FPS
end

local function tween(inst: any, length: number, goal: { [string]: any }, style: any?)
	TweenService:Create(inst, TweenInfo.new(length, style or Enum.EasingStyle.Quart, Enum.EasingDirection.Out), goal):Play()
end

-- ---- builders: each returns a Runner, parented under `root`, idle until its start cue

local function buildEmitter(L: Blueprint.Layer, root: any, origin: CFrame): Runner
	local host = newPart(L.name, origin * CFrame.new(vec3(L.props.offset, Vector3.zero)), vec3(L.props.hostSize, Vector3.new(0.5, 0.5, 0.5)))
	local e: any = Instance.new("ParticleEmitter")
	e.Rate = 0 -- burst emitters stay enabled at Rate 0 and are driven by :Emit
	e.Color = ColorSequence.new(tint(L.color))
	local id = textureFor(L.props.texture)
	if id then
		e.Texture = id
	end
	applyProps(e, L.props)
	e.Parent = host
	host.Parent = root
	return {
		start = function(_now: number)
			if L.rate then
				e.Rate = L.rate
			end
			if L.count then
				e:Emit(L.count)
			end
		end,
		stop = function()
			e.Rate = 0 -- live particles finish their Lifetime; Debris removes the host later
		end,
	}
end

local function buildBeam(L: Blueprint.Layer, root: any, origin: CFrame, directional: boolean): Runner
	local P = L.props
	local anchor = newPart(L.name, origin, Vector3.new(0.2, 0.2, 0.2))
	local beams: { any } = {}
	local arcs = if P.mode == "arc" then (P.arcs or 1) else 1
	for i = 1, arcs do
		local a0: any, a1: any = Instance.new("Attachment"), Instance.new("Attachment")
		if P.mode == "arc" then
			local base = (i - 1) / arcs * math.pi * 2
			local sweep = math.rad(P.sweep or 60)
			a0.Position = Vector3.new(math.cos(base) * P.radius, 0.2, math.sin(base) * P.radius)
			a1.Position = Vector3.new(math.cos(base + sweep) * P.radius, P.height, math.sin(base + sweep) * P.radius)
			-- the Bézier bulges along A0's +X and A1's -X: point both up so the arc arches over
			a0.Axis, a1.Axis = Vector3.yAxis, -Vector3.yAxis
		else
			a0.Position = Vector3.zero
			a1.Position = if directional then Vector3.new(0, 0.5, -(P.length or 10)) else Vector3.new(0, P.length or 10, 0)
		end
		a0.Parent, a1.Parent = anchor, anchor -- attachments exist and are parented BEFORE the Beam references them
		local b: any = Instance.new("Beam")
		b.Attachment0, b.Attachment1 = a0, a1
		b.Color = ColorSequence.new(tint(L.color))
		local id = textureFor(P.texture)
		if id then
			b.Texture = id
		end
		applyProps(b, P)
		b.Enabled = false
		b.Parent = anchor
		table.insert(beams, b)
	end
	anchor.Parent = root
	local width0, width1 = P.Width0 or 1, P.Width1 or 1
	local t0 = 0
	local running = false
	local spin = math.rad(P.spin or 0)
	return {
		start = function(now: number)
			t0, running = now, true
			for _, b in beams do
				b.Width0, b.Width1 = width0, width1
				b.Enabled = true
			end
		end,
		stop = function()
			running = false
			for _, b in beams do
				tween(b, FADE_FRAMES / Blueprint.FPS, { Width0 = 0, Width1 = 0 }, Enum.EasingStyle.Linear)
			end
		end,
		update = function(now: number)
			if running and spin ~= 0 then
				anchor.CFrame = origin * CFrame.Angles(0, spin * (now - t0), 0)
			end
		end,
	}
end

local function buildTrail(L: Blueprint.Layer, root: any, origin: CFrame): Runner
	local P = L.props
	local count = P.orbiters or 1
	local orbiters: { { part: any, trail: any, phase: number, yaw: number } } = {}
	for i = 1, count do
		local part = newPart(`{L.name}{i}`, origin, Vector3.new(0.3, 0.3, 0.3))
		local half = (P.width or 0.4) / 2
		local a0: any, a1: any = Instance.new("Attachment"), Instance.new("Attachment")
		a0.Position, a1.Position = Vector3.new(0, half, 0), Vector3.new(0, -half, 0) -- width = the gap between them
		a0.Parent, a1.Parent = part, part
		local tr: any = Instance.new("Trail")
		tr.Attachment0, tr.Attachment1 = a0, a1
		tr.Color = ColorSequence.new(tint(L.color))
		local id = textureFor(P.texture)
		if id then
			tr.Texture = id
		end
		applyProps(tr, P)
		tr.Enabled = false
		tr.Parent = part
		part.Parent = root
		local fan = math.rad(P.fan or 0)
		orbiters[i] = {
			part = part,
			trail = tr,
			phase = (i - 1) / count * math.pi * 2,
			yaw = if count > 1 then -fan / 2 + fan * (i - 1) / (count - 1) else 0,
		}
	end
	local t0 = 0
	local running = false
	local function place(o: any, t: number)
		if P.motion == "shoot" then
			o.part.CFrame = origin * CFrame.Angles(0, o.yaw, 0) * CFrame.new(0, P.height or 1, -(P.speed or 40) * t)
		else
			o.part.CFrame = origin * CFrame.Angles(0, o.phase + math.rad(P.spin or 0) * t, 0)
				* CFrame.new(P.radius or 3, (P.height or 1) + (P.rise or 0) * t, 0)
		end
	end
	return {
		start = function(now: number)
			t0, running = now, true
			for _, o in orbiters do
				place(o, 0) -- place first, then enable: no streak from wherever the part was
				o.trail:Clear()
				o.trail.Enabled = true
			end
		end,
		stop = function()
			running = false
			for _, o in orbiters do
				o.trail.Enabled = false
			end
		end,
		update = function(now: number)
			if running then
				for _, o in orbiters do
					place(o, now - t0)
				end
			end
		end,
	}
end

local function buildMesh(L: Blueprint.Layer, root: any, origin: CFrame): Runner?
	local folder = ReplicatedStorage:FindFirstChild("VfxMeshes")
	local template = if folder then folder:FindFirstChild(L.props.template) else nil
	if not template then
		warnOnce("mesh:" .. L.props.template, `Rig: ReplicatedStorage.VfxMeshes.{L.props.template} is missing; layer {L.name} skipped`)
		return nil
	end
	local part: any = template:Clone()
	part.Anchored, part.CanCollide, part.CanQuery, part.CanTouch, part.CastShadow = true, false, false, false, false
	part.Color = tint(L.color)
	part.Material = (Enum :: any).Material[L.props.Material or "Neon"]
	part.Transparency = 1
	local base: Vector3 = part.Size
	local stretch = Vector3.new(L.props.stretch or 1, 1, 1)
	local at = origin * CFrame.new(vec3(L.props.offset, Vector3.zero))
	part.CFrame = at
	part.Parent = root
	local length = seconds(L)
	return {
		start = function(_now: number)
			part.CFrame = at
			part.Size = base * (L.props.from or 1) * stretch
			part.Transparency = 0
			tween(part, length, { Size = base * (L.props.to or 1) * stretch })
			tween(part, length, { Transparency = 1 }, Enum.EasingStyle.Linear)
		end,
		stop = function()
			part.Transparency = 1
		end,
	}
end

local function buildDecal(L: Blueprint.Layer, root: any, origin: CFrame): Runner?
	local id = textureFor(L.props.texture)
	if not id then
		return nil
	end
	local s0, s1 = L.props.size0, L.props.size1
	local part = newPart(L.name, origin * CFrame.new(vec3(L.props.offset, Vector3.zero) + Vector3.new(0, 0.05, 0)), Vector3.new(s0[1], 0.05, s0[2]))
	local d: any = Instance.new("Decal")
	d.Face, d.Texture, d.Color3, d.Transparency = Enum.NormalId.Top, id, tint(L.color), 1
	d.Parent = part
	part.Parent = root
	local length = seconds(L)
	return {
		start = function(_now: number)
			part.Size = Vector3.new(s0[1], 0.05, s0[2])
			d.Transparency = 0.1
			tween(part, length, { Size = Vector3.new(s1[1], 0.05, s1[2]) })
			tween(d, length, { Transparency = 1 }, Enum.EasingStyle.Linear)
		end,
		stop = function()
			d.Transparency = 1
		end,
	}
end

local function buildLight(L: Blueprint.Layer, root: any, origin: CFrame, bloom: number): Runner
	local host = newPart(L.name, origin * CFrame.new(vec3(L.props.offset, Vector3.new(0, 2, 0))), Vector3.new(0.2, 0.2, 0.2))
	local light: any = Instance.new("PointLight")
	light.Color, light.Range, light.Brightness, light.Shadows = tint(L.color), L.props.Range, 0, false
	light.Parent = host
	host.Parent = root
	local peak = L.props.Brightness * bloom
	local length = seconds(L)
	local gathers = L.phase == "Telegraph" -- a telegraph swells; every other light flashes and decays
	return {
		start = function(_now: number)
			light.Brightness = if gathers then 0 else peak
			tween(light, length, { Brightness = if gathers then peak else 0 }, if gathers then Enum.EasingStyle.Linear else Enum.EasingStyle.Quad)
		end,
		stop = function()
			light.Brightness = 0
		end,
	}
end

-- Play `bp` at `origin` with the Intensity.BUDGET row for the current rung. Returns nil when a friendly effect is skipped.
function Rig.play(bp: Blueprint.Blueprint, origin: CFrame, budget: Blueprint.Budget, options: Options?): Handle?
	if active >= Rig.MAX_ACTIVE and not bp.hostile then
		return nil -- skipped, never queued (HIERARCHY.md §9); a hostile effect is a critical cue and always plays
	end
	local plan = Blueprint.plan(bp, budget)
	local root: any = Instance.new("Folder") -- built offscreen, parented last
	root.Name = bp.name
	local runners: { [string]: Runner } = {}
	local updating: { Runner } = {}
	for _, L in plan.layers do
		local r: Runner? = nil
		if L.kind == "Emitter" then
			r = buildEmitter(L, root, origin)
		elseif L.kind == "Beam" then
			r = buildBeam(L, root, origin, bp.directional)
		elseif L.kind == "Trail" then
			r = buildTrail(L, root, origin)
		elseif L.kind == "Mesh" then
			r = buildMesh(L, root, origin)
		elseif L.kind == "Decal" then
			r = buildDecal(L, root, origin)
		elseif L.kind == "Light" then
			r = buildLight(L, root, origin, plan.bloom)
		end
		if r then
			runners[L.name] = r
			if r.update then
				table.insert(updating, r)
			end
		end
	end
	root.Parent = (options and options.parent) or Workspace
	active += 1

	local tl = Timeline.new(plan.layers, bp.hitFrame, bp.duration)
	local conn: any = nil
	local finished = false
	local function finish()
		if finished then
			return
		end
		finished = true
		if conn then
			conn:Disconnect()
		end
		active -= 1
		for _, r in runners do
			r.stop()
		end
		Debris:AddItem(root, Blueprint.endSeconds(plan) + 0.5)
	end
	conn = RunService.PreRender:Connect(function(dt: number)
		for _, cue in tl:step(dt) do
			local r = if cue.layer then runners[cue.layer] else nil
			if cue.kind == "start" and r then
				r.start(tl:seconds())
			elseif cue.kind == "stop" and r then
				r.stop()
			elseif cue.kind == "hit" and options and options.onHit then
				options.onHit()
			elseif cue.kind == "done" then
				finish()
			end
		end
		local now = tl:seconds()
		for _, r in updating do
			(r.update :: (number) -> ())(now)
		end
	end)
	return { stop = finish, timeline = tl }
end

return Rig
