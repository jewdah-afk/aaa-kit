--!strict
-- VoidRings: a multi-ring void / arcane impact (friendly, tier 2). 100 frames (1.67 s), hit on frame 18.
--
--   0-17   Telegraph    violet motes are drawn inward and a light swells while a rune seal turns in on the floor
--   18     Core         a void sphere pops (the one peak-1 layer) with a bloom burst and a 3-frame light flash
--   18-49  Ground       three rings roll out 4 frames apart; the seal holds; cracks scorch the floor
--   20-62  Secondary    three arcs and three orbiters wheel round the core in opposite directions; shards fly
--   30-100 Dissipation  dark violet smoke (alpha blended) and a few embers linger, then fade
--
-- Assets: mesh template "VoidSphere" (a smooth unit sphere, saved in ReplicatedStorage.VfxMeshes);
-- texture roles soft_glow, mote, shard, smoke_puff, spark, ring_thin, rune_circle, crack_radial, arc_beam, trail_soft.
-- Play it: Rig.play(VoidRings, origin, Intensity.BUDGET[level])

-- selene: allow(unused_variable)
local Blueprint = require("../Blueprint") -- used for its types only

local VIOLET = { 0.46, 0.18, 0.95 }
local HOT = { 0.93, 0.86, 1.0 }
local MAGENTA = { 0.82, 0.30, 1.0 }
local SMOKE = { 0.20, 0.10, 0.34 }

local VoidRings: Blueprint.Blueprint = {
	name = "VoidRings",
	hostile = false,
	directional = false,
	hitFrame = 18,
	duration = 100,
	maxParticles = 120,
	layers = {
		-- Telegraph / Anticipation
		{
			name = "SuckMotes", phase = "Telegraph", kind = "Emitter", start = 0, stop = 17, peak = 0.35, tier = 2,
			rate = 80, color = VIOLET,
			props = {
				texture = "mote", hostSize = { 9, 9, 9 },
				Shape = { enum = { "ParticleEmitterShape", "Sphere" } }, ShapeInOut = { enum = { "ParticleEmitterShapeInOut", "Inward" } },
				Lifetime = { range = { 0.3, 0.4 } }, Speed = { range = { 10, 14 } },
				Size = { seq = { { 0, 0.5 }, { 1, 0.1 } } }, Transparency = { seq = { { 0, 0.6 }, { 0.3, 0 }, { 1, 1 } } },
				LightEmission = 1, LightInfluence = 0, Brightness = 2, ZOffset = 0.2,
			},
		},
		{
			name = "GatherLight", phase = "Telegraph", kind = "Light", start = 0, stop = 17, peak = 0.25, tier = 2,
			color = VIOLET, props = { Brightness = 2, Range = 14 },
		},
		-- Core Focal Point
		{
			name = "VoidCore", phase = "Core", kind = "Mesh", start = 18, stop = 29, peak = 1, tier = 2,
			color = HOT, props = { template = "VoidSphere", from = 0.2, to = 1.6, Material = "Neon" },
		},
		{
			name = "CoreBloom", phase = "Core", kind = "Emitter", start = 18, stop = 21, peak = 0.7, tier = 2,
			count = 6, color = HOT,
			props = {
				texture = "soft_glow", Lifetime = { range = { 0.18, 0.25 } }, Speed = { range = { 0, 0 } },
				Size = { seq = { { 0, 6 }, { 1, 10 } } }, Transparency = { seq = { { 0, 0.3 }, { 1, 1 } } },
				LightEmission = 1, LightInfluence = 0, Brightness = 3, ZOffset = 0.6,
			},
		},
		{
			name = "ImpactFlash", phase = "Core", kind = "Light", start = 18, stop = 20, peak = 0.7, tier = 2, gate = "impact",
			color = HOT, props = { Brightness = 8, Range = 24 },
		},
		-- Ground Projection
		{
			name = "RuneSeal", phase = "Ground", kind = "Decal", start = 4, stop = 60, peak = 0.5, tier = 2,
			color = MAGENTA, props = { texture = "rune_circle", size0 = { 6, 6 }, size1 = { 11, 11 } },
		},
		{
			name = "Ring1", phase = "Ground", kind = "Decal", start = 18, stop = 41, peak = 0.6, tier = 2,
			color = VIOLET, props = { texture = "ring_thin", size0 = { 2, 2 }, size1 = { 16, 16 } },
		},
		{
			name = "Ring2", phase = "Ground", kind = "Decal", start = 22, stop = 45, peak = 0.6, tier = 2,
			color = VIOLET, props = { texture = "ring_thin", size0 = { 2, 2 }, size1 = { 20, 20 } },
		},
		{
			name = "Ring3", phase = "Ground", kind = "Decal", start = 26, stop = 49, peak = 0.6, tier = 2,
			color = VIOLET, props = { texture = "ring_thin", size0 = { 2, 2 }, size1 = { 24, 24 } },
		},
		{
			name = "ScorchCracks", phase = "Ground", kind = "Decal", start = 18, stop = 90, peak = 0.3, tier = 2,
			color = SMOKE, props = { texture = "crack_radial", size0 = { 4, 4 }, size1 = { 12, 12 } },
		},
		-- Secondary Motion
		{
			name = "OrbitArcs", phase = "Secondary", kind = "Beam", start = 20, stop = 58, peak = 0.6, tier = 2, color = MAGENTA,
			props = {
				mode = "arc", arcs = 3, radius = 3.2, height = 1.6, sweep = 70, spin = 220, texture = "arc_beam",
				Width0 = 0.35, Width1 = 0.05, FaceCamera = true, Segments = 12, CurveSize0 = 1.8, CurveSize1 = 1.8,
				Transparency = { seq = { { 0, 0.2 }, { 1, 1 } } }, TextureSpeed = 2,
				LightEmission = 1, LightInfluence = 0, Brightness = 3,
			},
		},
		{
			name = "OrbitTrails", phase = "Secondary", kind = "Trail", start = 20, stop = 62, peak = 0.6, tier = 2, color = VIOLET,
			props = {
				motion = "orbit", orbiters = 3, radius = 4.5, height = 1.2, spin = -300, width = 0.5, texture = "trail_soft",
				Lifetime = 0.35, MinLength = 0.15, MaxLength = 12, FaceCamera = true,
				WidthScale = { seq = { { 0, 1 }, { 1, 0 } } }, Transparency = { seq = { { 0, 0.1 }, { 1, 1 } } },
				LightEmission = 1, LightInfluence = 0, Brightness = 2,
			},
		},
		{
			name = "ShardDebris", phase = "Secondary", kind = "Emitter", start = 18, stop = 22, peak = 0.6, tier = 2,
			count = 18, color = HOT,
			props = {
				texture = "shard", Lifetime = { range = { 0.5, 0.8 } }, Speed = { range = { 18, 34 } },
				SpreadAngle = { vec2 = { 180, 180 } }, Acceleration = { vec = { 0, -40, 0 } }, Drag = 1,
				Size = { seq = { { 0, 0.7 }, { 1, 0.2 } } }, Rotation = { range = { 0, 360 } }, RotSpeed = { range = { -240, 240 } },
				FlipbookLayout = { enum = { "ParticleFlipbookLayout", "Grid2x2" } }, FlipbookStartRandom = true,
				FlipbookFramerate = { range = { 0, 0 } }, -- one random static frame per particle: four shard shapes, one emitter
				LightEmission = 0, LightInfluence = 1, Brightness = 1, ZOffset = 0.2,
			},
		},
		-- Dissipation / Lingering Smoke
		{
			name = "VoidSmoke", phase = "Dissipation", kind = "Emitter", start = 30, stop = 100, peak = 0.3, tier = 4, gate = "ambient",
			rate = 16, color = SMOKE,
			props = {
				texture = "smoke_puff", hostSize = { 4, 1, 4 }, Lifetime = { range = { 1.2, 1.8 } }, Speed = { range = { 1, 2 } },
				Acceleration = { vec = { 0, 1.5, 0 } }, Size = { seq = { { 0, 3 }, { 1, 7 } } },
				Transparency = { seq = { { 0, 0.4 }, { 1, 1 } } },
				FlipbookLayout = { enum = { "ParticleFlipbookLayout", "Grid2x2" } }, FlipbookStartRandom = true,
				FlipbookFramerate = { range = { 0, 0 } },
				LightEmission = 0, LightInfluence = 1, Brightness = 1, ZOffset = -0.5,
			},
		},
		{
			name = "FadingEmbers", phase = "Dissipation", kind = "Emitter", start = 30, stop = 70, peak = 0.3, tier = 4, gate = "ambient",
			rate = 24, color = MAGENTA,
			props = {
				texture = "spark", hostSize = { 5, 1, 5 }, Lifetime = { range = { 0.6, 1.0 } }, Speed = { range = { 2, 5 } },
				Size = { seq = { { 0, 0.4 }, { 1, 0 } } }, Transparency = { seq = { { 0, 0.2 }, { 1, 1 } } },
				LightEmission = 1, LightInfluence = 0, Brightness = 2, ZOffset = 0.1,
			},
		},
	},
}

return VoidRings
