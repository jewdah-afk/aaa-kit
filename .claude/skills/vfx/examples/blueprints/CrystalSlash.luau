--!strict
-- CrystalSlash: a directional crystal / slash burst (friendly, tier 2). 72 frames (1.2 s), hit on frame 6.
-- Directional: Rig.play orients the effect so "forward" (-Z of the origin CFrame) is the slash direction.
--
--   0-5    Telegraph    a thin aim line and a spark tick: the 6-frame micro-telegraph of a mechanic with no wind-up
--   6      Core         an elongated crescent flash (the one peak-1 layer) and a four-point star
--   6-70   Ground        a crack runs along the line of the slash; a frost ring pops outward
--   6-24   Secondary     a fan of crystal shards sprays forward, and five streak trails shoot out along the cone
--   14-72  Dissipation   cold mist (alpha blended) and glittering dust linger, then fade
--
-- Assets: mesh template "SlashCrescent" (a flat crescent, long axis = X); textures soft_glow, spark, star4, shard, streak,
-- ring_thin, crack_line, trail_soft, mist.
-- Play it: Rig.play(CrystalSlash, origin, Intensity.BUDGET[level])

-- selene: allow(unused_variable)
local Blueprint = require("../Blueprint") -- used for its types only

local ICE = { 0.55, 0.90, 1.0 }
local WHITE = { 0.92, 0.98, 1.0 }
local DEEP_ICE = { 0.12, 0.30, 0.42 }

local CrystalSlash: Blueprint.Blueprint = {
	name = "CrystalSlash",
	hostile = false,
	directional = true,
	hitFrame = 6,
	duration = 72,
	maxParticles = 100,
	layers = {
		-- Telegraph / Anticipation (micro-telegraph: the hit still lands on frame 6)
		{
			name = "AimGlint", phase = "Telegraph", kind = "Beam", start = 0, stop = 5, peak = 0.4, tier = 2, color = ICE,
			props = {
				mode = "straight", length = 10, texture = "streak",
				Width0 = 0.12, Width1 = 0.02, FaceCamera = true, Segments = 1, CurveSize0 = 0, CurveSize1 = 0,
				Transparency = { seq = { { 0, 0.5 }, { 1, 1 } } },
				LightEmission = 1, LightInfluence = 0, Brightness = 3,
			},
		},
		{
			name = "ChargeSpark", phase = "Telegraph", kind = "Emitter", start = 2, stop = 5, peak = 0.35, tier = 2,
			count = 5, color = WHITE,
			props = {
				texture = "spark", Lifetime = { range = { 0.1, 0.18 } }, Speed = { range = { 4, 8 } },
				Size = { seq = { { 0, 0.6 }, { 1, 0 } } }, Transparency = { seq = { { 0, 0 }, { 1, 1 } } },
				LightEmission = 1, LightInfluence = 0, Brightness = 3, ZOffset = 0.3,
			},
		},
		-- Core Focal Point
		{
			name = "SlashFlash", phase = "Core", kind = "Mesh", start = 6, stop = 11, peak = 1, tier = 2,
			color = WHITE, props = { template = "SlashCrescent", from = 0.6, to = 1.4, Material = "Neon", stretch = 2.5 },
		},
		{
			name = "FlashStar", phase = "Core", kind = "Emitter", start = 6, stop = 8, peak = 0.7, tier = 2,
			count = 2, color = WHITE,
			props = {
				texture = "star4", Lifetime = { range = { 0.1, 0.14 } }, Speed = { range = { 0, 0 } },
				Size = { seq = { { 0, 7 }, { 1, 0 } } }, Transparency = { seq = { { 0, 0 }, { 1, 1 } } },
				LightEmission = 1, LightInfluence = 0, Brightness = 4, ZOffset = 0.6,
			},
		},
		-- Ground Projection
		{
			name = "LineCrack", phase = "Ground", kind = "Decal", start = 6, stop = 70, peak = 0.3, tier = 2,
			color = DEEP_ICE, props = { texture = "crack_line", size0 = { 1, 3 }, size1 = { 3, 14 }, offset = { 0, 0, -7 } },
		},
		{
			name = "FrostRing", phase = "Ground", kind = "Decal", start = 6, stop = 29, peak = 0.6, tier = 2,
			color = ICE, props = { texture = "ring_thin", size0 = { 2, 2 }, size1 = { 14, 14 } },
		},
		-- Secondary Motion
		{
			name = "ShardFan", phase = "Secondary", kind = "Emitter", start = 6, stop = 10, peak = 0.6, tier = 2,
			count = 20, color = WHITE,
			props = {
				texture = "shard", Lifetime = { range = { 0.4, 0.7 } }, Speed = { range = { 22, 38 } },
				EmissionDirection = { enum = { "NormalId", "Front" } }, SpreadAngle = { vec2 = { 25, 25 } },
				Acceleration = { vec = { 0, -30, 0 } }, Drag = 0.8,
				Size = { seq = { { 0, 0.8 }, { 1, 0.3 } } }, Rotation = { range = { 0, 360 } }, RotSpeed = { range = { -200, 200 } },
				FlipbookLayout = { enum = { "ParticleFlipbookLayout", "Grid2x2" } }, FlipbookStartRandom = true,
				FlipbookFramerate = { range = { 0, 0 } },
				LightEmission = 0, LightInfluence = 1, Brightness = 1, ZOffset = 0.2,
			},
		},
		{
			name = "ShardStreaks", phase = "Secondary", kind = "Trail", start = 6, stop = 24, peak = 0.6, tier = 2, color = ICE,
			props = {
				motion = "shoot", orbiters = 5, speed = 60, fan = 28, height = 1, width = 0.3, texture = "trail_soft",
				Lifetime = 0.25, MinLength = 0.2, MaxLength = 10, FaceCamera = true,
				WidthScale = { seq = { { 0, 1 }, { 1, 0 } } }, Transparency = { seq = { { 0, 0.1 }, { 1, 1 } } },
				LightEmission = 1, LightInfluence = 0, Brightness = 3,
			},
		},
		-- Dissipation / Lingering Smoke
		{
			name = "ColdMist", phase = "Dissipation", kind = "Emitter", start = 14, stop = 72, peak = 0.3, tier = 4, gate = "ambient",
			rate = 18, color = { 0.55, 0.70, 0.80 },
			props = {
				texture = "mist", hostSize = { 3, 1, 8 }, offset = { 0, 0, -4 }, Lifetime = { range = { 0.9, 1.4 } }, Speed = { range = { 0.5, 1.5 } },
				Size = { seq = { { 0, 2.5 }, { 1, 5 } } }, Transparency = { seq = { { 0, 0.55 }, { 1, 1 } } },
				LightEmission = 0, LightInfluence = 1, Brightness = 1, ZOffset = -0.5,
			},
		},
		{
			name = "CrystalDust", phase = "Dissipation", kind = "Emitter", start = 14, stop = 56, peak = 0.3, tier = 4, gate = "ambient",
			rate = 30, color = WHITE,
			props = {
				texture = "spark", hostSize = { 3, 1, 8 }, offset = { 0, 0, -4 }, Lifetime = { range = { 0.5, 0.9 } }, Speed = { range = { 0.5, 2 } },
				Size = { seq = { { 0, 0.35 }, { 1, 0 } } }, Transparency = { seq = { { 0, 0.2 }, { 1, 1 } } },
				LightEmission = 1, LightInfluence = 0, Brightness = 2, ZOffset = 0.1,
			},
		},
	},
}

return CrystalSlash
