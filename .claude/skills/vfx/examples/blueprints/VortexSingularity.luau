--!strict
-- VortexSingularity: a vertical vortex that erupts at a point (HOSTILE boss attack, tier 2). 168 frames (2.8 s), hit on frame 48.
--
--   0-47    Telegraph    a red ring closes inward on the floor, dust is drawn in, a red light pulses (0.8 s of warning)
--   48      Core         a white-cyan collapse flash (the one peak-1 layer), a dark event-horizon sphere and a light column
--   40-150  Ground       a spiral scorch burns in; contracting runes pull toward the centre
--   52-120  Secondary    three helix trails climb the column while the floor debris lifts
--   100-168 Dissipation  grey dust drifts down and a few cyan motes hang, then fade
--
-- Because it is hostile, the Telegraph is a critical cue: Blueprint.plan never gates it or scales its particle counts, at any rung
-- (HIERARCHY.md §9, §10), and red is allowed. The lingering dust is gated "ambient", so surge, boss and finale drop it.
--
-- Assets: mesh template "VoidSphere"; textures soft_glow, mote, ring_thin, rune_circle, spiral_scorch, trail_soft, streak, smoke_puff, spark.
-- Play it: Rig.play(VortexSingularity, origin, Intensity.BUDGET[level])

-- selene: allow(unused_variable)
local Blueprint = require("../Blueprint") -- used for its types only

local WARN = { 1.0, 0.25, 0.15 }
local CYAN = { 0.20, 0.85, 1.0 }
local FLASH = { 0.85, 0.97, 1.0 }
local DEEP = { 0.05, 0.05, 0.12 }
local DUST = { 0.45, 0.42, 0.40 }

local VortexSingularity: Blueprint.Blueprint = {
	name = "VortexSingularity",
	hostile = true,
	directional = false,
	hitFrame = 48,
	duration = 168,
	maxParticles = 160,
	layers = {
		-- Telegraph / Anticipation (critical cue: never gated, never scaled)
		{
			name = "SuctionRing", phase = "Telegraph", kind = "Decal", start = 0, stop = 47, peak = 0.6, tier = 2,
			color = WARN, props = { texture = "ring_thin", size0 = { 22, 22 }, size1 = { 10, 10 } },
		},
		{
			name = "DustDraw", phase = "Telegraph", kind = "Emitter", start = 0, stop = 47, peak = 0.35, tier = 2,
			rate = 60, color = DUST,
			props = {
				texture = "smoke_puff", hostSize = { 22, 0.5, 22 },
				Shape = { enum = { "ParticleEmitterShape", "Cylinder" } }, ShapeInOut = { enum = { "ParticleEmitterShapeInOut", "Inward" } },
				Lifetime = { range = { 0.6, 0.9 } }, Speed = { range = { 8, 12 } },
				Size = { seq = { { 0, 1.5 }, { 1, 0.4 } } }, Transparency = { seq = { { 0, 0.7 }, { 0.3, 0.3 }, { 1, 1 } } },
				LightEmission = 0, LightInfluence = 1, Brightness = 1, ZOffset = -0.2,
			},
		},
		{
			name = "WarnPulse", phase = "Telegraph", kind = "Light", start = 0, stop = 47, peak = 0.3, tier = 2,
			color = WARN, props = { Brightness = 3, Range = 20 },
		},
		-- Core Focal Point
		{
			name = "CollapseFlash", phase = "Core", kind = "Mesh", start = 48, stop = 55, peak = 1, tier = 2,
			color = FLASH, props = { template = "VoidSphere", from = 0.5, to = 3, Material = "Neon" },
		},
		{
			name = "EventHorizon", phase = "Core", kind = "Mesh", start = 48, stop = 112, peak = 0.35, tier = 2,
			color = DEEP, props = { template = "VoidSphere", from = 0.2, to = 2.4, Material = "SmoothPlastic" },
		},
		{
			name = "LightColumn", phase = "Core", kind = "Beam", start = 48, stop = 107, peak = 0.6, tier = 2, color = CYAN,
			props = {
				mode = "straight", length = 14, texture = "streak",
				Width0 = 2.2, Width1 = 0.6, FaceCamera = true, Segments = 1, CurveSize0 = 0, CurveSize1 = 0,
				Transparency = { seq = { { 0, 0.3 }, { 1, 1 } } }, TextureSpeed = 1.5,
				LightEmission = 1, LightInfluence = 0, Brightness = 4,
			},
		},
		-- Ground Projection
		{
			name = "ScorchSpiral", phase = "Ground", kind = "Decal", start = 40, stop = 150, peak = 0.3, tier = 2,
			color = DEEP, props = { texture = "spiral_scorch", size0 = { 6, 6 }, size1 = { 16, 16 } },
		},
		{
			name = "PullRunes", phase = "Ground", kind = "Decal", start = 48, stop = 100, peak = 0.5, tier = 2,
			color = CYAN, props = { texture = "rune_circle", size0 = { 10, 10 }, size1 = { 8, 8 } },
		},
		-- Secondary Motion
		{
			name = "HelixTrails", phase = "Secondary", kind = "Trail", start = 52, stop = 110, peak = 0.6, tier = 2, color = CYAN,
			props = {
				motion = "orbit", orbiters = 3, radius = 4, height = 0.5, rise = 8, spin = 420, width = 0.6, texture = "trail_soft",
				Lifetime = 0.5, MinLength = 0.2, MaxLength = 16, FaceCamera = true,
				WidthScale = { seq = { { 0, 1 }, { 1, 0 } } }, Transparency = { seq = { { 0, 0.1 }, { 1, 1 } } },
				LightEmission = 1, LightInfluence = 0, Brightness = 3,
			},
		},
		{
			name = "LiftedDebris", phase = "Secondary", kind = "Emitter", start = 52, stop = 120, peak = 0.35, tier = 2,
			rate = 21, color = DUST,
			props = {
				texture = "smoke_puff", hostSize = { 14, 0.5, 14 }, Lifetime = { range = { 0.8, 1.2 } }, Speed = { range = { 1, 3 } },
				Acceleration = { vec = { 0, 6, 0 } }, Size = { seq = { { 0, 0.8 }, { 1, 0.3 } } },
				Transparency = { seq = { { 0, 0.2 }, { 1, 1 } } },
				LightEmission = 0, LightInfluence = 1, Brightness = 1, ZOffset = 0.2,
			},
		},
		-- Dissipation / Lingering Smoke
		{
			name = "VortexDust", phase = "Dissipation", kind = "Emitter", start = 100, stop = 168, peak = 0.3, tier = 4, gate = "ambient",
			rate = 22, color = DUST,
			props = {
				texture = "smoke_puff", hostSize = { 10, 1, 10 }, Lifetime = { range = { 1.4, 2.0 } }, Speed = { range = { 0.5, 1.5 } },
				Acceleration = { vec = { 0, -0.5, 0 } }, Size = { seq = { { 0, 4 }, { 1, 8 } } },
				Transparency = { seq = { { 0, 0.5 }, { 1, 1 } } },
				LightEmission = 0, LightInfluence = 1, Brightness = 1, ZOffset = -0.5,
			},
		},
		{
			name = "DriftMotes", phase = "Dissipation", kind = "Emitter", start = 100, stop = 150, peak = 0.3, tier = 4, gate = "ambient",
			rate = 30, color = CYAN,
			props = {
				texture = "mote", hostSize = { 8, 4, 8 }, Lifetime = { range = { 1.0, 1.6 } }, Speed = { range = { 0.5, 2 } },
				Size = { seq = { { 0, 0.3 }, { 1, 0 } } }, Transparency = { seq = { { 0, 0.3 }, { 1, 1 } } },
				LightEmission = 1, LightInfluence = 0, Brightness = 2, ZOffset = 0.1,
			},
		},
	},
}

return VortexSingularity
