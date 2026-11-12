--!strict
-- Avatar Hero aura: all tuning in one data table (balance lives in data, never in logic).
-- Hierarchy: tier 2 (combat/status accent), pixel owner = hero (5), never covers UI/threat/ceremony.
-- Intensity rungs: full on rungs 1, 4, 5; peak shortened on rung 2 (surge); suppressed on rung 3 (ceremony).
--
-- The offline renderer (tools/celestialrithm/avatar/render.py) parses the `phases` rows below, so keep
-- one row per line in the exact `{ name = ..., duration = ..., ... }` shape.

export type Range = { number }
export type Phase = {
	name: string,
	duration: number,
	intensity: Range, -- aura brightness 0..1 (from, to)
	shell: Range, -- shell inflation multiplier (from, to)
	orbit: Range, -- orbital angular speed in turns/s (from, to)
	ease: string, -- "linear" | "inCubic" | "outCubic" | "inOutSine" | "outBack"
}

local AuraConfig = {}

AuraConfig.phases = {
	{ name = "idle", duration = 1.40, intensity = { 0.10, 0.10 }, shell = { 1.00, 1.00 }, orbit = { 0.15, 0.15 }, ease = "linear" },
	{ name = "anticipation", duration = 0.80, intensity = { 0.10, 0.04 }, shell = { 1.00, 0.55 }, orbit = { 0.15, 0.60 }, ease = "inCubic" },
	{ name = "activation", duration = 0.25, intensity = { 1.00, 0.85 }, shell = { 0.55, 1.25 }, orbit = { 1.40, 1.00 }, ease = "outCubic" },
	{ name = "peak", duration = 2.00, intensity = { 0.85, 0.75 }, shell = { 1.25, 1.10 }, orbit = { 1.00, 0.80 }, ease = "inOutSine" },
	{ name = "recovery", duration = 1.00, intensity = { 0.75, 0.18 }, shell = { 1.10, 0.95 }, orbit = { 0.80, 0.25 }, ease = "outCubic" },
	{ name = "settle", duration = 1.55, intensity = { 0.18, 0.10 }, shell = { 0.95, 1.00 }, orbit = { 0.25, 0.15 }, ease = "inOutSine" },
} :: { Phase }

-- Onset flash: the activation phase's first frames are the brightest of the whole timeline.
AuraConfig.burst = {
	phase = "activation",
	peak = 1.0,
	decay = 9.0, -- exponential decay rate per second after onset
}

-- Peak pulse: slow breathing on top of the peak plateau (calm, not strobing; < 3 Hz flash rule).
AuraConfig.pulse = { phase = "peak", amplitude = 0.08, hz = 1.2 }

-- Reduced motion: shorter, dimmer, no orbit spin, no onset flash, no anticipation crouch.
AuraConfig.reducedMotion = {
	skip = { anticipation = true },
	intensityCap = 0.45,
	orbitScale = 0.0,
	burstScale = 0.0,
	pulseScale = 0.0,
	timeScale = 1.0,
}

-- Intensity rung (HIERARCHY.md section 4) -> multiplier on intensity and particle counts.
AuraConfig.rungs = {
	[0] = { intensity = 0.6, particles = 0.5 },
	[1] = { intensity = 1.0, particles = 1.0 },
	[2] = { intensity = 0.7, particles = 0.5 },
	[3] = { intensity = 0.0, particles = 0.0 }, -- a ceremony owns the screen
	[4] = { intensity = 1.0, particles = 1.0 },
	[5] = { intensity = 1.0, particles = 1.0 },
}

-- Effect sockets: an Attachment per row, parented to the named R15 part (falls back to R6 names).
AuraConfig.sockets = {
	{ name = "AuraCore", part = "UpperTorso", fallback = "Torso", offset = { 0, 0, 0 } },
	{ name = "AuraFeet", part = "LowerTorso", fallback = "Torso", offset = { 0, -2.1, 0 } },
	{ name = "AuraHandL", part = "LeftHand", fallback = "Left Arm", offset = { 0, -0.2, 0 } },
	{ name = "AuraHandR", part = "RightHand", fallback = "Right Arm", offset = { 0, -0.2, 0 } },
	{ name = "AuraHead", part = "Head", fallback = "Head", offset = { 0, 0.9, 0 } },
	{ name = "OrbitA", part = "UpperTorso", fallback = "Torso", offset = { 1.9, 0, 0 } },
	{ name = "OrbitB", part = "UpperTorso", fallback = "Torso", offset = { -1.9, 0, 0 } },
}

-- Orbitals move their socket around AuraCore. radius in studs, phase offset in turns.
AuraConfig.orbitals = {
	{ socket = "OrbitA", radius = 1.9, height = 0.0, phase = 0.0, tilt = 0.25 },
	{ socket = "OrbitB", radius = 1.9, height = -0.6, phase = 0.5, tilt = -0.2 },
}

-- Instance configs. Plain property values; the client module converts {r,g,b} / {t,v} keypoints.
AuraConfig.effects = {
	trails = {
		{ name = "OrbitTrailA", from = "OrbitA", offsetUp = 0.25, lifetime = 0.35, width = { 0.0, 0.35 }, color = { { 0, 120, 255, 220 }, { 1, 170, 120, 255 } }, transparency = { { 0, 0.1 }, { 1, 1.0 } }, lightEmission = 0.6 },
		{ name = "OrbitTrailB", from = "OrbitB", offsetUp = 0.25, lifetime = 0.35, width = { 0.0, 0.35 }, color = { { 0, 120, 255, 220 }, { 1, 170, 120, 255 } }, transparency = { { 0, 0.1 }, { 1, 1.0 } }, lightEmission = 0.6 },
	},
	beams = {
		{ name = "Spine", from = "AuraFeet", to = "AuraHead", width = { 1.6, 0.6 }, color = { { 0, 90, 230, 200 }, { 1, 150, 110, 255 } }, transparency = { { 0, 0.55 }, { 0.5, 0.75 }, { 1, 1.0 } }, lightEmission = 0.5, textureSpeed = 1.2, segments = 6 },
	},
	particles = {
		-- burst: emitted once at activation onset (Emit), never always-on.
		{ name = "OnsetBurst", socket = "AuraCore", burst = 24, rate = 0, lifetime = { 0.3, 0.6 }, speed = { 6, 10 }, size = { { 0, 0.5 }, { 1, 0.0 } }, color = { 150, 255, 225 }, lightEmission = 0.8, spread = 180 },
		-- rising motes: rate scales with intensity; 0 at idle (calm by default).
		{ name = "Motes", socket = "AuraFeet", burst = 0, rate = 18, lifetime = { 0.6, 1.1 }, speed = { 2, 4 }, size = { { 0, 0.18 }, { 1, 0.0 } }, color = { 120, 255, 200 }, lightEmission = 0.6, spread = 25 },
	},
}

-- Protected region: aura never draws over the face (HIERARCHY.md section 10).
AuraConfig.faceGuard = { part = "Head", maxAlpha = 0.15 }

-- Budgets (per avatar). Exceeding them skips extras; it never delays the onset.
AuraConfig.budget = { maxParticles = 60, maxTrails = 2, maxBeams = 1, maxShellLayers = 2 }

return AuraConfig
