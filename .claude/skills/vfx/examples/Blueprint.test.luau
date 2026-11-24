--!strict
local t = require("../../../../tools/lib/t")
local Blueprint = require("./Blueprint")
local Intensity = require("../../../../examples/framework-starter/src/shared/Systems/Intensity")
local VoidRings = require("./blueprints/VoidRings")
local VortexSingularity = require("./blueprints/VortexSingularity")
local CrystalSlash = require("./blueprints/CrystalSlash")

local templates = { VoidRings, VortexSingularity, CrystalSlash }

local function clone(bp: Blueprint.Blueprint): Blueprint.Blueprint
	local copy = table.clone(bp)
	copy.layers = {}
	for _, L in bp.layers do
		local c = table.clone(L)
		c.props = table.clone(L.props)
		table.insert(copy.layers, c)
	end
	return copy
end

local function layer(bp: Blueprint.Blueprint, name: string): Blueprint.Layer
	for _, L in bp.layers do
		if L.name == name then
			return L
		end
	end
	error("no layer " .. name)
end

-- The validator must name the broken rule: some error contains `needle`.
local function rejects(label: string, bp: Blueprint.Blueprint, needle: string)
	local hit = false
	for _, e in Blueprint.validate(bp) do
		if e:find(needle, 1, true) then
			hit = true
		end
	end
	t.ok(label .. ` (expects '{needle}')`, hit)
end

-- The three shipped templates are valid and play at every rung
for _, bp in templates do
	local errs = Blueprint.validate(bp)
	for _, e in errs do
		print("  ", e)
	end
	t.eq(bp.name .. " is valid", #errs, 0)
	local phases: { [string]: boolean } = {}
	for _, L in bp.layers do
		phases[L.phase] = true
	end
	for _, p in Blueprint.PHASES do
		t.ok(`{bp.name} has {p}`, phases[p])
	end
	for rung = 0, 5 do
		local plan = Blueprint.plan(bp, Intensity.BUDGET[rung])
		t.ok(`{bp.name} rung {rung} stays under maxParticles`, plan.particles <= bp.maxParticles)
		local hasCore = false
		for _, L in plan.layers do
			if L.peak == 1 then
				hasCore = true
			end
		end
		t.ok(`{bp.name} rung {rung} keeps the peak-1 onset layer`, hasCore)
	end
end

-- Mutations: every rule of the standard fails loudly
do
	local bp = clone(VoidRings)
	local kept = {}
	for _, L in bp.layers do
		if L.phase ~= "Dissipation" then
			table.insert(kept, L)
		end
	end
	bp.layers = kept
	rejects("no Dissipation", bp, "no Dissipation layer")
end
do
	local bp = clone(VoidRings)
	bp.hitFrame = 2
	rejects("hit frame too early", bp, "hitFrame must be")
end
do
	local bp = clone(VoidRings)
	bp.duration = 200
	rejects("effect too long", bp, "duration must be")
end
do
	local bp = clone(VoidRings)
	layer(bp, "VoidCore").start = 25
	rejects("late Core onset", bp, "Core starts on the hit frame")
end
do
	local bp = clone(VoidRings)
	layer(bp, "RuneSeal").peak = 1
	rejects("two peak-1 layers", bp, "exactly one layer has peak 1")
end
do
	local bp = clone(VoidRings)
	layer(bp, "ShardDebris").peak = 0.9
	rejects("non-Core above 0.7", bp, "only Core goes above")
end
do
	local bp = clone(VoidRings)
	layer(bp, "SuckMotes").stop = 30
	rejects("Telegraph runs past the hit", bp, "Telegraph starts before the hit")
end
do
	local bp = clone(VoidRings)
	layer(bp, "RuneSeal").stop = 90
	rejects("loud layer lasts too long", bp, "may last")
end
do
	local bp = clone(VoidRings)
	layer(bp, "ShardDebris").start, layer(bp, "ShardDebris").stop = 40, 44
	rejects("Secondary starts late", bp, "Secondary starts between")
end
do
	local bp = clone(VoidRings)
	layer(bp, "VoidSmoke").start = 20
	rejects("Dissipation starts too early", bp, "Dissipation starts at hitFrame+6")
end
do
	local bp = clone(VoidRings)
	layer(bp, "VoidSmoke").gate = nil
	rejects("Dissipation ungated", bp, "gated \"ambient\"")
end
do
	local bp = clone(VoidRings)
	layer(bp, "VoidSmoke").stop = 90
	rejects("Dissipation cuts instead of fading", bp, "runs to the last frame")
end
do
	local bp = clone(VoidRings)
	layer(bp, "Ring1").color = { 0.95, 0.1, 0.1 }
	rejects("red on a friendly effect", bp, "red is reserved")
end
do
	local bp = clone(VoidRings)
	layer(bp, "CoreBloom").props.ZOffset = nil
	rejects("ZOffset left to defaults", bp, "set ZOffset explicitly")
end
do
	local bp = clone(VoidRings)
	layer(bp, "SuckMotes").props.LightInfluence = nil
	rejects("LightInfluence left to defaults", bp, "set LightInfluence explicitly")
end
do
	local bp = clone(VoidRings)
	layer(bp, "CoreBloom").color = { 0.05, 0.02, 0.1 }
	rejects("dark colour under additive", bp, "invisible")
end
do
	local bp = clone(VoidRings)
	layer(bp, "OrbitTrails").props.MinLength = nil
	rejects("Trail without MinLength", bp, "MinLength")
end
do
	local bp = clone(VoidRings)
	layer(bp, "OrbitArcs").props.FaceCamera = nil
	rejects("Beam without FaceCamera", bp, "FaceCamera")
end
do
	local bp = clone(VoidRings)
	layer(bp, "SuckMotes").props.Colour = 1
	rejects("typo in a prop", bp, "not allowed")
end
do
	local bp = clone(VoidRings)
	layer(bp, "Ring1").props.texture = "ring_fat"
	rejects("unknown texture role", bp, "unknown texture role")
end
do
	local bp = clone(VoidRings)
	layer(bp, "VoidSmoke").props.LightEmission = 1
	rejects("Dissipation without smoke", bp, "smoke")
end
do
	local bp = clone(VoidRings)
	layer(bp, "VoidSmoke").props.ZOffset = 0.9
	rejects("smoke in front", bp, "lowest ZOffset")
end
do
	local bp = clone(VoidRings)
	layer(bp, "CoreBloom").props.ZOffset = 0
	rejects("Core not in front", bp, "highest ZOffset")
end
do
	local bp = clone(VortexSingularity)
	layer(bp, "DustDraw").gate = "ambient"
	rejects("hostile Telegraph gated", bp, "never gated")
end
do
	local bp = clone(VoidRings)
	bp.maxParticles = 10
	rejects("particle budget", bp, "exceed maxParticles")
end
do
	local bp = clone(VoidRings)
	bp.layers[1].name = bp.layers[2].name
	rejects("duplicate name", bp, "duplicate name")
end

-- Rung gating and scaling
do
	local calm = Blueprint.plan(VoidRings, Intensity.BUDGET[0]) -- impact off, ambient on, particles x0.5
	local surge = Blueprint.plan(VoidRings, Intensity.BUDGET[2]) -- impact on, ambient off, particles x0.6
	local ceremony = Blueprint.plan(VoidRings, Intensity.BUDGET[3])
	local function has(plan: Blueprint.Plan, name: string): boolean
		for _, L in plan.layers do
			if L.name == name then
				return true
			end
		end
		return false
	end
	t.ok("calm drops the impact flash", not has(calm, "ImpactFlash"))
	t.ok("surge keeps the impact flash", has(surge, "ImpactFlash"))
	t.ok("surge drops lingering smoke", not has(surge, "VoidSmoke") and not has(surge, "FadingEmbers"))
	t.ok("calm keeps lingering smoke", has(calm, "VoidSmoke"))
	t.ok("ceremony keeps everything", #ceremony.layers == #VoidRings.layers)
	t.ok("calm spends fewer particles than ceremony", calm.particles < ceremony.particles)
	t.near("rate scales with the budget", layer(calm :: any, "SuckMotes").rate :: number, 40, 1e-9)

	local tiny = Blueprint.plan(VoidRings, { impact = true, ambient = true, particles = 0.01, bloom = 1 })
	for _, L in tiny.layers do
		if L.count then
			t.ok(L.name .. " keeps at least one particle", L.count >= 1)
		end
	end
end

-- A hostile Telegraph is a gameplay footprint: same at every rung
do
	for rung = 0, 5 do
		local plan = Blueprint.plan(VortexSingularity, Intensity.BUDGET[rung])
		for _, name in { "SuctionRing", "DustDraw", "WarnPulse" } do
			local found = false
			for _, L in plan.layers do
				if L.name == name then
					found = true
					t.eq(`rung {rung} {name} rate`, L.rate, layer(VortexSingularity, name).rate)
				end
			end
			t.ok(`rung {rung} keeps hostile {name}`, found)
		end
	end
end

-- Cleanup time covers the longest particle life
do
	local plan = Blueprint.plan(VoidRings, Intensity.BUDGET[3])
	t.near("VoidRings is safe to destroy after 3.48 s", Blueprint.endSeconds(plan), 101 / 60 + 1.8, 1e-9)
	t.eq("particles of a burst", Blueprint.particlesOf(layer(VoidRings, "ShardDebris")), 18)
	t.eq("particles of a rate emitter", Blueprint.particlesOf(layer(VoidRings, "SuckMotes")), 24)
	t.eq("a Beam spends no particles", Blueprint.particlesOf(layer(VoidRings, "OrbitArcs")), 0)
end

t.done()
