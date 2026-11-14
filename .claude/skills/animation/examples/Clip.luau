--!strict
-- Clip: an animation as data. Keys are rows of numbers (one column per channel), each with a
-- time and the ease used to move into it. The sampler is pure, so the same clip runs in the
-- game, in a lune test and in an offline render.

export type Ease = "Smooth" | "In" | "Out" | "Linear"
export type Key = { Time: number, Values: { number }, Ease: Ease? }
export type Clip = { Keys: { Key }, EasePower: number? }

local Clip = {}

function Clip.smooth(u: number): number
	u = math.clamp(u, 0, 1)
	return u * u * (3 - 2 * u)
end

-- No speed and no acceleration at either end: use it for blends that must start and stop clean.
function Clip.smoother(u: number): number
	u = math.clamp(u, 0, 1)
	return u * u * u * (u * (u * 6 - 15) + 10)
end

local function ease(kind: Ease?, u: number, power: number): number
	if kind == "In" then
		return u ^ power -- speeds up into the key: carries momentum through a hit or release
	elseif kind == "Out" then
		return 1 - (1 - u) ^ power -- slows down into the key: a follow-through settling
	elseif kind == "Linear" then
		return u
	end
	return Clip.smooth(u)
end

local function finite(v: number): number
	return if v ~= v or math.abs(v) == math.huge then 0 else v
end

function Clip.length(clip: Clip): number
	return clip.Keys[#clip.Keys].Time
end

-- Writes the pose at `time` into `out` (reused, so sampling allocates nothing) and returns it.
-- `scale` multiplies channels: { [channel] = factor }, e.g. a stronger throw twists further.
function Clip.sample(clip: Clip, time: number, out: { number }, scale: { [number]: number }?): { number }
	local keys = clip.Keys
	time = math.clamp(finite(time), keys[1].Time, keys[#keys].Time)
	local from, to = keys[#keys - 1], keys[#keys]
	for i = 2, #keys do
		if time <= keys[i].Time then
			from, to = keys[i - 1], keys[i]
			break
		end
	end
	local a = ease(to.Ease, math.clamp((time - from.Time) / (to.Time - from.Time), 0, 1), clip.EasePower or 1.6)
	for c = 1, #to.Values do
		local v = from.Values[c] + (to.Values[c] - from.Values[c]) * a
		out[c] = if scale and scale[c] then v * scale[c] else v
	end
	return out
end

-- Leaves from a pose that was being held (a charge, an idle) over `blend` seconds, so the first
-- frame of the clip equals the held pose exactly. Call after Clip.sample with the same `out`.
function Clip.from(held: { number }, out: { number }, time: number, blend: number): { number }
	if time < blend then
		local b = Clip.smooth(finite(time) / blend)
		for c = 1, #out do
			out[c] = held[c] + (out[c] - held[c]) * b
		end
	end
	return out
end

-- Largest change of any channel between two samples `step` seconds apart. A test asserts this
-- stays small, which is how "nothing snaps" becomes a number.
function Clip.maxStep(clip: Clip, step: number, weights: { number }?): number
	local a, b = {}, {}
	local worst = 0
	Clip.sample(clip, clip.Keys[1].Time, a)
	local t = clip.Keys[1].Time
	while t < Clip.length(clip) do
		t += step
		Clip.sample(clip, t, b)
		for c = 1, #b do
			worst = math.max(worst, math.abs(b[c] - a[c]) * (if weights then weights[c] else 1))
		end
		a, b = b, a
	end
	return worst
end

return Clip
