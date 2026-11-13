--!strict
-- LuckMeter: the top-centre luck counter that replaced the world banner (HUD v4).
-- Pure maths, no Instances: which rung a luck value sits on, how big the clover and
-- number are, the gradient, the glow and how many sparkles, plus the count-up curve and
-- the punch played when luck crosses into a new rung. The Figma spec board
-- ("4 · Luck counter") was drawn from this same table, so keep them in step.

local LuckMeter = {}

export type Rung = {
	name: string,
	min: number, -- luck multiplier where this rung starts
	scale: number, -- clover + number scale
	glow: number, -- 0..1 glow strength
	sparkles: number, -- idle sparkle count while in flight
	stops: { { number | string } }, -- gradient stops: { position, "#RRGGBB" }
}

LuckMeter.RUNGS = {
	{ name = "CALM", min = 0, scale = 0.78, glow = 0, sparkles = 0, stops = { { 0, "#FFFFFF" }, { 1, "#FFE9A0" } } },
	{ name = "WARM", min = 2, scale = 0.86, glow = 0.2, sparkles = 1, stops = { { 0, "#FFF4B0" }, { 1, "#FFC629" } } },
	{ name = "LUCKY", min = 5, scale = 0.93, glow = 0.35, sparkles = 2, stops = { { 0, "#F2FFB0" }, { 1, "#8CFF3A" } } },
	{ name = "HOT", min = 10, scale = 1.0, glow = 0.55, sparkles = 4, stops = { { 0, "#FFFBD0" }, { 0.45, "#FFD93A" }, { 1, "#FF8A12" } } },
	{ name = "MYTHIC", min = 25, scale = 1.1, glow = 0.8, sparkles = 6, stops = { { 0, "#7DFFE6" }, { 0.5, "#B45CFF" }, { 1, "#FF5AC8" } } },
} :: { Rung }

-- Timings (seconds), mirrored in the motion table rows 4-6.
LuckMeter.TICK_TIME = 0.25 -- count-up toward a new target, exponential out
LuckMeter.BUMP_GAP = 0.15 -- at most one +2% bump per this many seconds
LuckMeter.PUNCH_UP = 0.08 -- 1 -> 1.18, quad out
LuckMeter.PUNCH_SETTLE = 0.32 -- 1.18 -> 1, back out
LuckMeter.PUNCH_PEAK = 1.18
LuckMeter.REST_HOLD = 0.6 -- after the ball lands
LuckMeter.REST_TIME = 0.4 -- back to CALM size, quint in-out
LuckMeter.REST_OPACITY = 0.6

local function finite(x: number): number
	if x ~= x or x == math.huge or x == -math.huge then
		return 0
	end
	return x
end

-- Index of the rung a luck value sits on (1..#RUNGS). NaN and negatives read as CALM.
function LuckMeter.rungIndex(luck: number): number
	luck = finite(luck)
	local idx = 1
	for i, r in LuckMeter.RUNGS do
		if luck >= r.min then
			idx = i
		end
	end
	return idx
end

function LuckMeter.rung(luck: number): Rung
	return LuckMeter.RUNGS[LuckMeter.rungIndex(luck)]
end

-- "×12.84": two decimals under 100, one under 1000, then whole numbers. Floored, so the
-- counter never shows more luck than the server granted.
function LuckMeter.format(luck: number): string
	luck = math.max(0, finite(luck))
	if luck < 100 then
		return string.format("×%.2f", math.floor(luck * 100) / 100)
	elseif luck < 1000 then
		return string.format("×%.1f", math.floor(luck * 10) / 10)
	end
	return string.format("×%d", math.floor(luck))
end

-- Exponential-out count-up in log space, so ×1 -> ×10 reads as steadily as ×10 -> ×100.
-- t is 0..1 through TICK_TIME.
function LuckMeter.countUp(from: number, to: number, t: number): number
	t = math.clamp(finite(t), 0, 1)
	local e = if t >= 1 then 1 else 1 - 2 ^ (-10 * t)
	local a, b = math.max(from, 1e-3), math.max(to, 1e-3)
	return math.exp(math.log(a) + (math.log(b) - math.log(a)) * e)
end

local function quadOut(t: number): number
	return 1 - (1 - t) * (1 - t)
end

local function backOut(t: number): number
	local s = 1.70158
	local u = t - 1
	return 1 + u * u * ((s + 1) * u + s)
end

-- Scale multiplier of the rung-up punch at `time` seconds since it started (1 when done).
function LuckMeter.punch(time: number): number
	time = finite(time)
	local up, settle, peak = LuckMeter.PUNCH_UP, LuckMeter.PUNCH_SETTLE, LuckMeter.PUNCH_PEAK
	if time <= 0 then
		return 1
	elseif time < up then
		return 1 + (peak - 1) * quadOut(time / up)
	elseif time < up + settle then
		return peak + (1 - peak) * backOut((time - up) / settle)
	end
	return 1
end

-- Did luck cross into a higher rung? Returns the new rung index or nil. Only upward
-- crossings punch; falling back (a new throw) is handled by the rest animation.
function LuckMeter.crossed(prev: number, nxt: number): number?
	local a, b = LuckMeter.rungIndex(prev), LuckMeter.rungIndex(nxt)
	if b > a then
		return b
	end
	return nil
end

-- Clover spin for the rung-up (degrees): -12 at the peak, back to 0 with the settle.
function LuckMeter.spin(time: number): number
	local p = LuckMeter.punch(time)
	return -12 * (p - 1) / (LuckMeter.PUNCH_PEAK - 1)
end

return LuckMeter
