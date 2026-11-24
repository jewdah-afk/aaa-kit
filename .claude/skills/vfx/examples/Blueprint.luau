--!strict
-- Blueprint: the strict multi-phase standard for ONE visual effect (vfx skill). Pure data and checks, so lune can test it.
--
-- An effect is a list of layers on a 60 fps frame clock. Every layer sits in exactly one of five phases:
--   Telegraph    warns and gathers; ends by the hit frame (hostile telegraphs are critical cues: never gated or scaled)
--   Core         the focal point (bloom + mesh core); starts ON the hit frame; holds the one brightest layer
--   Ground       runes, rings, cracks and decals projected on the floor
--   Secondary    orbiting trails, arcs and debris that carry the motion after the hit
--   Dissipation  lingering smoke and sparks: quiet, tier 4, the first thing the intensity ladder drops
--
-- Colours are {r, g, b} in 0..1. Roblox property values are plain data so lune can hold them:
--   { range = {a, b} }  NumberRange      { seq = {{t, v}, ...} }  NumberSequence     { cseq = {{t, r, g, b}, ...} }  ColorSequence
--   { color = {r, g, b} }  Color3       { vec = {x, y, z} }  Vector3       { vec2 = {x, y} }  Vector2
--   { enum = {"NormalId", "Front"} }  Enum item
-- Keys in `props` that start with a lowercase letter are Rig keys (how the layer moves); PascalCase keys are Roblox properties.

local Blueprint = {}

export type Phase = "Telegraph" | "Core" | "Ground" | "Secondary" | "Dissipation"
export type Kind = "Emitter" | "Beam" | "Trail" | "Mesh" | "Decal" | "Light"
export type Gate = "impact" | "ambient"

export type Layer = {
	name: string,
	phase: Phase,
	kind: Kind,
	start: number, -- first visible frame
	stop: number, -- last visible frame
	peak: number, -- 0..1, share of the effect's brightness at this layer's brightest
	tier: number, -- HIERARCHY.md §2: 2 combat, 4 atmosphere
	count: number?, -- Emitter burst size at budget 1.0
	rate: number?, -- Emitter particles per second at budget 1.0
	gate: Gate?, -- impact: needs budget.impact; ambient: needs budget.ambient
	color: { number },
	props: { [string]: any },
}

export type Blueprint = {
	name: string,
	hostile: boolean,
	directional: boolean,
	hitFrame: number,
	duration: number,
	maxParticles: number,
	layers: { Layer },
}

-- The row of Intensity.BUDGET (HIERARCHY.md §4) for the current rung.
export type Budget = { impact: boolean, ambient: boolean, particles: number, bloom: number }

export type Plan = { layers: { Layer }, particles: number, bloom: number, impact: boolean }

Blueprint.FPS = 60
Blueprint.PHASES = table.freeze({ "Telegraph", "Core", "Ground", "Secondary", "Dissipation" })
Blueprint.MAX_DURATION = 180 -- 3 s: a combat effect never loops
Blueprint.LOUD_PEAK, Blueprint.LOUD_FRAMES = 0.7, 24 -- a layer above 0.7 lasts at most 24 frames (400 ms, HIERARCHY.md §2)
Blueprint.MID_PEAK, Blueprint.MID_FRAMES = 0.35, 60 -- a layer above 0.35 lasts at most 60 frames; quieter layers may linger
Blueprint.MAX_CORE_START = 2 -- onset window: Core layers start on the hit frame, at most 2 frames later

-- Texture roles a template may ask for. The game maps each role to an uploaded asset id (Rig.setTextures).
Blueprint.TEXTURE_ROLES = table.freeze({
	soft_glow = true, spark = true, mote = true, star4 = true, shard = true, streak = true, smoke_puff = true,
	mist = true, ring_thin = true, rune_circle = true, crack_radial = true, crack_line = true, spiral_scorch = true,
	arc_beam = true, trail_soft = true,
})

local function set(names: { string }): { [string]: boolean }
	local out: { [string]: boolean } = {}
	for _, n in names do
		out[n] = true
	end
	return table.freeze(out)
end

-- Allowed prop keys per kind. A typo fails the test instead of silently doing nothing in Studio.
Blueprint.PROPS = table.freeze({
	Emitter = set({
		"Lifetime", "Speed", "SpreadAngle", "Size", "Transparency", "Rotation", "RotSpeed", "Acceleration", "Drag", "Squash",
		"LightEmission", "LightInfluence", "Brightness", "ZOffset", "EmissionDirection", "Shape", "ShapeStyle", "ShapeInOut",
		"FlipbookLayout", "FlipbookMode", "FlipbookFramerate", "FlipbookStartRandom", "Orientation", "LockedToPart",
		"texture", "hostSize", "offset",
	}),
	Beam = set({
		"Width0", "Width1", "FaceCamera", "LightEmission", "LightInfluence", "Brightness", "Segments", "CurveSize0", "CurveSize1",
		"Transparency", "TextureSpeed", "TextureMode", "TextureLength", "ZOffset",
		"texture", "mode", "arcs", "radius", "height", "sweep", "spin", "length", "offset",
	}),
	Trail = set({
		"Lifetime", "MinLength", "MaxLength", "WidthScale", "FaceCamera", "LightEmission", "LightInfluence", "Brightness",
		"Transparency", "TextureMode", "TextureLength",
		"texture", "motion", "orbiters", "radius", "height", "spin", "rise", "speed", "fan", "width", "offset",
	}),
	Mesh = set({ "template", "from", "to", "Material", "stretch", "offset" }),
	Decal = set({ "texture", "size0", "size1", "offset" }),
	Light = set({ "Brightness", "Range", "offset" }),
})

local function isWhole(n: any): boolean
	return type(n) == "number" and n == math.floor(n)
end

local function luma(c: { number }): number
	return 0.2126 * c[1] + 0.7152 * c[2] + 0.0722 * c[3]
end

local function isRed(c: { number }): boolean
	return c[1] >= 0.6 and c[2] <= 0.35 and c[3] <= 0.35
end

-- Particles one emitter layer spends over its life at budget 1.0.
function Blueprint.particlesOf(layer: Layer): number
	if layer.kind ~= "Emitter" then
		return 0
	end
	return (layer.count or 0) + math.ceil((layer.rate or 0) * (layer.stop - layer.start + 1) / Blueprint.FPS)
end

-- Every rule of the standard. Returns the error strings; an empty list means the blueprint is valid.
function Blueprint.validate(bp: Blueprint): { string }
	local errs: { string } = {}
	local function bad(msg: string)
		table.insert(errs, `{bp.name}: {msg}`)
	end

	if not (isWhole(bp.hitFrame) and bp.hitFrame >= 3 and bp.hitFrame <= 90) then
		bad("hitFrame must be a whole frame in 3..90 (a 3-frame tick is the shortest telegraph)")
	end
	if not (isWhole(bp.duration) and bp.duration <= Blueprint.MAX_DURATION and bp.duration >= bp.hitFrame + 24) then
		bad(`duration must be a whole frame in hitFrame+24..{Blueprint.MAX_DURATION}`)
	end

	local seen: { [string]: boolean } = {}
	local perPhase: { [string]: number } = {}
	local ones: { Layer } = {}
	local particles = 0
	local coreZ, otherZ, smokeZ, nonSmokeZ = {}, {}, {}, {}
	local reachesEnd, hasSmoke = false, false

	for _, L in bp.layers do
		local at = `layer {L.name}`
		if seen[L.name] then
			bad(`{at}: duplicate name`)
		end
		seen[L.name] = true
		perPhase[L.phase] = (perPhase[L.phase] or 0) + 1

		if not table.find(Blueprint.PHASES, L.phase) then
			bad(`{at}: unknown phase {L.phase}`)
			continue
		end
		local allowed = (Blueprint.PROPS :: any)[L.kind]
		if not allowed then
			bad(`{at}: unknown kind {L.kind}`)
			continue
		end
		if not (isWhole(L.start) and isWhole(L.stop) and L.start >= 0 and L.start <= L.stop and L.stop <= bp.duration) then
			bad(`{at}: start/stop must be whole frames with 0 <= start <= stop <= duration`)
			continue
		end
		if not (L.peak > 0 and L.peak <= 1) then
			bad(`{at}: peak must be in (0, 1]`)
		end
		if #L.color ~= 3 or L.color[1] < 0 or L.color[1] > 1 or L.color[2] < 0 or L.color[2] > 1 or L.color[3] < 0 or L.color[3] > 1 then
			bad(`{at}: color must be three numbers in 0..1`)
			continue
		end
		for key in L.props do
			if not allowed[key] then
				bad(`{at}: prop '{key}' is not allowed on a {L.kind}`)
			end
		end

		-- phase timing
		if L.phase == "Telegraph" then
			if L.start >= bp.hitFrame or L.stop > bp.hitFrame + 4 then
				bad(`{at}: a Telegraph starts before the hit and ends by hitFrame+4`)
			end
			if bp.hostile and L.gate then
				bad(`{at}: a hostile Telegraph is a critical cue and is never gated`)
			end
		elseif L.phase == "Core" then
			if L.start < bp.hitFrame or L.start > bp.hitFrame + Blueprint.MAX_CORE_START then
				bad(`{at}: Core starts on the hit frame (hitFrame..hitFrame+{Blueprint.MAX_CORE_START})`)
			end
		elseif L.phase == "Ground" then
			if L.start > bp.hitFrame + 8 then
				bad(`{at}: Ground starts by hitFrame+8`)
			end
		elseif L.phase == "Secondary" then
			if L.start < bp.hitFrame or L.start > bp.hitFrame + 12 then
				bad(`{at}: Secondary starts between hitFrame and hitFrame+12`)
			end
		elseif L.phase == "Dissipation" then
			if L.start < bp.hitFrame + 6 then
				bad(`{at}: Dissipation starts at hitFrame+6 or later`)
			end
			if L.peak > Blueprint.MID_PEAK then
				bad(`{at}: Dissipation peak must be <= {Blueprint.MID_PEAK}`)
			end
			if L.tier ~= 4 or L.gate ~= "ambient" then
				bad(`{at}: Dissipation is tier 4 and gated "ambient" (the ladder drops it first)`)
			end
			if L.stop == bp.duration then
				reachesEnd = true
			end
		end
		if L.phase ~= "Dissipation" and L.tier ~= 2 then
			bad(`{at}: combat layers are tier 2`)
		end

		-- loud layers are short (HIERARCHY.md §2)
		local len = L.stop - L.start + 1
		if L.peak > Blueprint.LOUD_PEAK and len > Blueprint.LOUD_FRAMES then
			bad(`{at}: peak {L.peak} may last {Blueprint.LOUD_FRAMES} frames, not {len}`)
		elseif L.peak > Blueprint.MID_PEAK and len > Blueprint.MID_FRAMES then
			bad(`{at}: peak {L.peak} may last {Blueprint.MID_FRAMES} frames, not {len}`)
		end
		if L.peak == 1 then
			table.insert(ones, L)
		end

		-- colour jobs (§5): red is for threats
		if not bp.hostile and isRed(L.color) then
			bad(`{at}: red is reserved for hostile effects`)
		end

		-- kind rules
		local P = L.props
		if L.kind == "Emitter" then
			if (L.count or 0) < 1 and (L.rate or 0) <= 0 then
				bad(`{at}: an Emitter needs count (burst) or rate`)
			end
			for _, k in { "LightEmission", "LightInfluence", "ZOffset" } do
				if P[k] == nil then
					bad(`{at}: set {k} explicitly (defaults differ between Studio and Instance.new)`)
				end
			end
			if type(P.LightEmission) == "number" and P.LightEmission >= 0.5 and luma(L.color) < 0.25 then
				bad(`{at}: dark colour under additive blending is invisible; use LightEmission 0 or a brighter colour`)
			end
			if type(P.ZOffset) == "number" then
				if L.phase == "Core" then
					table.insert(coreZ, P.ZOffset)
				else
					table.insert(otherZ, P.ZOffset)
				end
				if L.phase == "Dissipation" and P.LightEmission == 0 then
					hasSmoke = true
					table.insert(smokeZ, P.ZOffset)
				else
					table.insert(nonSmokeZ, P.ZOffset)
				end
			end
			particles += Blueprint.particlesOf(L)
		elseif L.kind == "Beam" then
			for _, k in { "Width0", "Width1", "FaceCamera", "LightEmission", "LightInfluence" } do
				if P[k] == nil then
					bad(`{at}: a Beam sets {k} explicitly`)
				end
			end
		elseif L.kind == "Trail" then
			for _, k in { "Lifetime", "MinLength", "MaxLength", "LightEmission", "LightInfluence" } do
				if P[k] == nil then
					bad(`{at}: a Trail sets {k} (MinLength stops idle jitter, MaxLength is the geometry budget)`)
				end
			end
		elseif L.kind == "Mesh" then
			if type(P.template) ~= "string" then
				bad(`{at}: a Mesh names a template in ReplicatedStorage.VfxMeshes`)
			end
		elseif L.kind == "Decal" then
			if not Blueprint.TEXTURE_ROLES[P.texture] then
				bad(`{at}: unknown texture role '{tostring(P.texture)}'`)
			end
		elseif L.kind == "Light" then
			if P.Brightness == nil or P.Range == nil then
				bad(`{at}: a Light sets Brightness and Range`)
			end
		end
		if (L.kind == "Emitter" or L.kind == "Beam" or L.kind == "Trail") and P.texture ~= nil and not Blueprint.TEXTURE_ROLES[P.texture] then
			bad(`{at}: unknown texture role '{tostring(P.texture)}'`)
		end
	end

	for _, phase in Blueprint.PHASES do
		if (perPhase[phase] or 0) < 1 then
			bad(`no {phase} layer`)
		end
	end
	if #ones ~= 1 or ones[1].phase ~= "Core" then
		bad("exactly one layer has peak 1 and it is a Core layer (the onset is the brightest frame)")
	end
	for _, L in bp.layers do
		if L.phase ~= "Core" and L.peak > Blueprint.LOUD_PEAK then
			bad(`layer {L.name}: only Core goes above {Blueprint.LOUD_PEAK}`)
		end
	end
	if perPhase.Dissipation and not reachesEnd then
		bad("a Dissipation layer runs to the last frame, so the effect fades out instead of cutting")
	end
	if perPhase.Dissipation and not hasSmoke then
		bad("Dissipation includes smoke: an Emitter with LightEmission 0")
	end
	if #coreZ > 0 and #otherZ > 0 and math.min(table.unpack(coreZ)) <= math.max(table.unpack(otherZ)) then
		bad("the Core emitter has the highest ZOffset (front of the sort)")
	end
	if #smokeZ > 0 and #nonSmokeZ > 0 and math.max(table.unpack(smokeZ)) >= math.min(table.unpack(nonSmokeZ)) then
		bad("Dissipation smoke has the lowest ZOffset (behind everything)")
	end
	if particles > bp.maxParticles then
		bad(`{particles} particles at budget 1.0 exceed maxParticles {bp.maxParticles}`)
	end
	return errs
end

-- Resolve a blueprint for one rung (a row of Intensity.BUDGET): drop gated layers, scale counts.
-- A hostile Telegraph is a gameplay footprint, so it is never scaled or dropped (HIERARCHY.md §9, §10).
function Blueprint.plan(bp: Blueprint, budget: Budget): Plan
	local out: { Layer } = {}
	local total = 0
	for _, L in bp.layers do
		local critical = bp.hostile and L.phase == "Telegraph"
		if not critical and L.gate == "impact" and not budget.impact then
			continue
		end
		if not critical and L.gate == "ambient" and not budget.ambient then
			continue
		end
		local copy = table.clone(L)
		if L.kind == "Emitter" and not critical then
			if L.count then
				copy.count = math.max(1, math.floor(L.count * budget.particles + 0.5))
			end
			if L.rate then
				copy.rate = L.rate * budget.particles
			end
		end
		total += Blueprint.particlesOf(copy)
		table.insert(out, copy)
	end
	return { layers = out, particles = total, bloom = budget.bloom, impact = budget.impact }
end

local function lifetimeOf(v: any): number
	if type(v) == "number" then
		return v
	elseif type(v) == "table" and v.range then
		return math.max(v.range[1], v.range[2])
	end
	return 0
end

-- Seconds until the last particle or trail segment has faded: when the Rig may destroy the effect.
function Blueprint.endSeconds(plan: Plan): number
	local last = 0
	for _, L in plan.layers do
		local t = (L.stop + 1) / Blueprint.FPS
		if L.kind == "Emitter" or L.kind == "Trail" then
			t += lifetimeOf(L.props.Lifetime)
		end
		last = math.max(last, t)
	end
	return last
end

return Blueprint
