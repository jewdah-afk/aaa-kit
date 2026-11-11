--!strict
-- Impact: the three timing tools behind a hit that "feels" heavy.
--   hit-stop: freeze gameplay time for a few frames on contact
--   trauma shake: camera offset = maxOffset * trauma^2 * noise, trauma decays linearly
--   flash: a 1–2 frame white overlay on the hit target
-- All pure; the caller applies the numbers to the camera / sprite / sim clock.
-- The budget comes from the intensity rung (HIERARCHY.md §4): no impact frames at calm.

local Impact = {}
Impact.__index = Impact

export type Impact = typeof(setmetatable({} :: {
	stopLeft: number,
	trauma: number,
	flashLeft: number,
	seed: number,
	time: number,
}, Impact))

Impact.MAX_OFFSET = 6 -- px (or studs * 0.1 for a 3D camera)
Impact.MAX_ROLL = 1.5 -- degrees
Impact.DECAY = 1 / 0.45 -- trauma per second (full trauma fades in 450 ms)

function Impact.new(seed: number?): Impact
	return setmetatable({ stopLeft = 0, trauma = 0, flashLeft = 0, seed = seed or 1, time = 0 }, Impact)
end

-- Register a hit. strength 0..1. allowImpact comes from Intensity.budget(level).impact.
function Impact.hit(self: Impact, strength: number, allowImpact: boolean)
	self.trauma = math.min(1, self.trauma + 0.35 * strength)
	self.flashLeft = math.max(self.flashLeft, 2 / 60)
	if allowImpact then
		-- 2 frames for a normal hit, up to 6 for a kill / crit
		self.stopLeft = math.max(self.stopLeft, (2 + 4 * strength) / 60)
	end
end

-- Returns the gameplay dt after hit-stop (0 while frozen). Effects keep using real dt.
function Impact.step(self: Impact, dt: number): number
	self.time += dt
	self.trauma = math.max(0, self.trauma - Impact.DECAY * dt)
	self.flashLeft = math.max(0, self.flashLeft - dt)
	if self.stopLeft > 0 then
		local used = math.min(self.stopLeft, dt)
		self.stopLeft -= used
		return dt - used
	end
	return dt
end

-- Smooth value noise in [-1, 1] (no RNG per frame, so shake is continuous, not jittery).
local function noise(x: number, seed: number): number
	local i = math.floor(x)
	local f = x - i
	local function h(n: number): number
		local s = math.sin((n + seed * 57.13) * 12.9898) * 43758.5453
		return (s - math.floor(s)) * 2 - 1
	end
	local u = f * f * (3 - 2 * f)
	return h(i) * (1 - u) + h(i + 1) * u
end

-- Camera offset (x, y in px) and roll (degrees) for this frame.
function Impact.shake(self: Impact, reducedMotion: boolean?): (number, number, number)
	local s = self.trauma * self.trauma
	if reducedMotion then
		s *= 0.25
	end
	local f = self.time * 28 -- noise frequency
	return Impact.MAX_OFFSET * s * noise(f, self.seed), Impact.MAX_OFFSET * s * noise(f, self.seed + 1), Impact.MAX_ROLL * s * noise(f, self.seed + 2)
end

function Impact.flashing(self: Impact): boolean
	return self.flashLeft > 0
end

return Impact
