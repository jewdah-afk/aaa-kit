--!strict
--!optimize 2
-- Pure, deterministic phase timeline for the Avatar Hero aura (no Roblox APIs; runs in lune).
-- idle -> anticipation -> activation -> peak -> recovery -> settle, driven by AuraConfig data.
--
-- Hot path: `step` and `sample` write into `self.out` and allocate nothing.
-- Cosmetic only: the server decides *whether* a power-up happens (cooldown, ownership, rate limit)
-- and broadcasts it; clients only run this timeline for the look.

local AuraTimeline = {}
AuraTimeline.__index = AuraTimeline

export type Out = {
	phase: number, -- index into the active phase list (1-based)
	phaseName: string,
	alpha: number, -- 0..1 progress inside the phase
	intensity: number, -- 0..1 final brightness (rung, pulse, burst, reduced-motion cap applied)
	shell: number, -- shell inflation multiplier
	orbit: number, -- orbital speed, turns/s
	orbitAngle: number, -- accumulated orbit angle, turns (wrapped to [0, 1))
	burst: number, -- onset flash 0..1
	time: number, -- seconds since start
	done: boolean,
}

type PhaseRow = {
	name: string,
	duration: number,
	intensity: { number },
	shell: { number },
	orbit: { number },
	ease: string,
}

export type Options = { reducedMotion: boolean?, rung: number? }

local MAX_DT = 0.25

local EASE: { [string]: (number) -> number } = {
	linear = function(t: number): number
		return t
	end,
	inCubic = function(t: number): number
		return t * t * t
	end,
	outCubic = function(t: number): number
		local u = 1 - t
		return 1 - u * u * u
	end,
	inOutSine = function(t: number): number
		return 0.5 - 0.5 * math.cos(math.pi * t)
	end,
	outBack = function(t: number): number
		local c1 = 1.70158
		local u = t - 1
		return 1 + (c1 + 1) * u * u * u + c1 * u * u
	end,
}

local function clamp01(v: number): number
	if v ~= v then
		return 0 -- NaN guard
	end
	return if v < 0 then 0 elseif v > 1 then 1 else v
end

function AuraTimeline.new(config: any, options: Options?)
	local opts: Options = options or {}
	local reduced = opts.reducedMotion == true
	local rm = config.reducedMotion
	local rungRow = config.rungs[opts.rung or 1] or config.rungs[1]

	local phases: { PhaseRow } = {}
	local ends: { number } = {}
	local total = 0
	for _, row in config.phases do
		if not (reduced and rm.skip[row.name]) then
			assert(EASE[row.ease], `AuraTimeline: unknown ease '{row.ease}' in phase '{row.name}'`)
			assert(row.duration > 0, `AuraTimeline: phase '{row.name}' needs a positive duration`)
			table.insert(phases, row)
			total += row.duration
			table.insert(ends, total)
		end
	end
	assert(#phases > 0, "AuraTimeline: no phases")

	local self = setmetatable({
		phases = phases,
		ends = ends,
		total = total,
		reduced = reduced,
		intensityCap = if reduced then rm.intensityCap else 1,
		orbitScale = if reduced then rm.orbitScale else 1,
		burstScale = if reduced then rm.burstScale else 1,
		pulseScale = if reduced then rm.pulseScale else 1,
		timeScale = if reduced then rm.timeScale else 1,
		rungIntensity = rungRow.intensity,
		burstPhase = config.burst.phase,
		burstPeak = config.burst.peak,
		burstDecay = config.burst.decay,
		pulsePhase = config.pulse.phase,
		pulseAmp = config.pulse.amplitude,
		pulseHz = config.pulse.hz,
		cursor = 1,
		out = {
			phase = 1,
			phaseName = phases[1].name,
			alpha = 0,
			intensity = 0,
			shell = 1,
			orbit = 0,
			orbitAngle = 0,
			burst = 0,
			time = 0,
			done = false,
		} :: Out,
	}, AuraTimeline)
	self:sample(0)
	return self
end

export type Timeline = typeof(AuraTimeline.new({} :: any))

-- Total duration of the active phase list (seconds).
function AuraTimeline.duration(self: Timeline): number
	return self.total
end

-- Restart from t = 0 (orbit angle kept continuous so orbitals don't jump).
function AuraTimeline.restart(self: Timeline)
	self.cursor = 1
	self.out.done = false
	self:sample(0)
end

-- Pure evaluation of every channel except orbitAngle at absolute time t. Writes self.out.
function AuraTimeline.sample(self: Timeline, t: number): Out
	local out = self.out
	if t ~= t or t < 0 then
		t = 0
	end
	local phases, ends = self.phases, self.ends
	local n = #phases
	-- the cursor only moves forward during normal playback; reset it when sampling backwards
	local i = self.cursor
	if i > n or (i > 1 and t < ends[i - 1]) then
		i = 1
	end
	while i < n and t >= ends[i] do
		i += 1
	end
	self.cursor = i
	local row = phases[i]
	local start = if i > 1 then ends[i - 1] else 0
	local a = clamp01((t - start) / row.duration)
	local done = t >= self.total
	if done then
		a = 1
	end
	local e = EASE[row.ease](a)

	local intensity = row.intensity[1] + (row.intensity[2] - row.intensity[1]) * e
	if row.name == self.pulsePhase then
		intensity += self.pulseAmp * self.pulseScale * math.sin(2 * math.pi * self.pulseHz * (t - start))
	end
	local burst = 0
	if row.name == self.burstPhase then
		burst = self.burstPeak * self.burstScale * math.exp(-self.burstDecay * (t - start))
	end
	intensity = math.max(intensity, burst)
	intensity = math.min(clamp01(intensity * self.rungIntensity), self.intensityCap)

	out.phase = i
	out.phaseName = row.name
	out.alpha = a
	out.intensity = intensity
	out.shell = row.shell[1] + (row.shell[2] - row.shell[1]) * e
	out.orbit = (row.orbit[1] + (row.orbit[2] - row.orbit[1]) * e) * self.orbitScale
	out.burst = burst
	out.time = t
	out.done = done
	return out
end

-- Advance by dt seconds (clamped to [0, 0.25]); integrates orbitAngle. Allocation-free.
function AuraTimeline.step(self: Timeline, dt: number): Out
	if dt ~= dt or dt < 0 then
		dt = 0
	elseif dt > MAX_DT then
		dt = MAX_DT
	end
	local out = self.out
	local t = math.min(out.time + dt * self.timeScale, self.total)
	if self.total - t < 1e-9 then
		t = self.total -- absorb float drift so a 7.00 s timeline is exactly 420 steps at 60 Hz
	end
	local speed0 = out.orbit
	self:sample(t)
	local angle = out.orbitAngle + 0.5 * (speed0 + out.orbit) * dt -- trapezoid rule
	out.orbitAngle = angle - math.floor(angle)
	return out
end

return AuraTimeline
