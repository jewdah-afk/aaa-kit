--!strict
-- Central system: the intensity ladder (HIERARCHY.md §4). One number 0..5 owned by game
-- state, read by every visual layer. Rising is immediate; falling steps down one rung per
-- FALL_HOLD seconds; each trigger has separate enter and exit thresholds.

local Intensity = {}

Intensity.NAMES = table.freeze({ [0] = "calm", "build", "surge", "ceremony", "boss", "finale" })
Intensity.CROWD_ON, Intensity.CROWD_OFF = 40, 30 -- entities on screen
Intensity.NEAR_ON, Intensity.NEAR_OFF = 12, 8 -- entities within reach of the player
Intensity.LOW_ON, Intensity.LOW_OFF = 0.30, 0.40 -- HP fraction
Intensity.FALL_HOLD = 1.5

-- What each rung allows. Visual systems read these knobs; they never decide loudness alone.
Intensity.BUDGET = table.freeze({
	[0] = table.freeze({ impact = false, ambient = true, particles = 0.5, bloom = 0.3, musicDb = -2.5 }),
	[1] = table.freeze({ impact = false, ambient = true, particles = 0.8, bloom = 0.5, musicDb = -1.5 }),
	[2] = table.freeze({ impact = true, ambient = false, particles = 0.6, bloom = 0.6, musicDb = -0.5 }),
	[3] = table.freeze({ impact = true, ambient = true, particles = 1.0, bloom = 0.8, musicDb = -0.5 }),
	[4] = table.freeze({ impact = true, ambient = false, particles = 0.7, bloom = 0.8, musicDb = 0 }),
	[5] = table.freeze({ impact = true, ambient = false, particles = 1.0, bloom = 1.0, musicDb = 1 }),
})

export type Obs = { finale: boolean?, boss: boolean?, screen: boolean?, onScreen: number?, near: number?, shotNear: boolean?, hp: number? }
export type State = { level: number, hold: number, crowd: boolean, near: boolean, low: boolean }

function Intensity.new(): State
	return { level = 0, hold = 0, crowd = false, near = false, low = false }
end

function Intensity.target(s: State, o: Obs): number
	local on, near, hp = o.onScreen or 0, o.near or 0, o.hp or 1
	s.crowd = if s.crowd then on > Intensity.CROWD_OFF else on >= Intensity.CROWD_ON
	s.near = if s.near then near > Intensity.NEAR_OFF else near >= Intensity.NEAR_ON
	s.low = if s.low then hp < Intensity.LOW_OFF else hp < Intensity.LOW_ON
	if o.finale then
		return 5
	elseif o.boss then
		return 4
	elseif o.screen then
		return 3
	elseif s.near or s.low or o.shotNear then
		return 2
	elseif s.crowd then
		return 1
	end
	return 0
end

function Intensity.observe(s: State, o: Obs, dt: number): number
	local want = Intensity.target(s, o)
	if want >= s.level then
		s.level, s.hold = want, 0
	else
		s.hold += dt
		if s.hold >= Intensity.FALL_HOLD then
			s.level -= 1
			s.hold = 0
		end
	end
	return s.level
end

function Intensity.budget(level: number)
	return Intensity.BUDGET[math.clamp(math.floor(level), 0, 5)]
end

return Intensity
