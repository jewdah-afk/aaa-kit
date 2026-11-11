--!strict
-- Reel: a weighted RNG reel that is decided first and animated second.
-- 1. The server rolls the result (weighted, seeded). 2. The client builds a strip of
-- filler items that ends on the result (any RNG: Random.new(seed) wrapped as
-- `function() return rng:NextNumber() end` in Roblox). 3. An ease-out curve with a small overshoot
-- lands the strip on it. The animation never decides anything.

local Reel = {}

export type Entry = { id: string, weight: number, tier: number }

-- Weighted pick. `r` is a uniform number in [0, 1) from the server's RNG.
function Reel.pick(entries: { Entry }, r: number): Entry
	local total = 0
	for _, e in entries do
		total += e.weight
	end
	local x = r * total
	for _, e in entries do
		x -= e.weight
		if x < 0 then
			return e
		end
	end
	return entries[#entries]
end

-- Builds a strip of `length` items whose item at `landIndex` is the result.
-- Fillers come from the same table (so the strip "looks honest"), with one near-miss:
-- the slot right after the landing shows a higher tier when one exists.
function Reel.strip(entries: { Entry }, result: Entry, length: number, landIndex: number, rand: () -> number): { Entry }
	local strip = table.create(length) :: { Entry }
	for i = 1, length do
		strip[i] = Reel.pick(entries, rand())
	end
	strip[landIndex] = result
	local best: Entry? = nil
	for _, e in entries do
		if e.tier > result.tier and (best == nil or e.tier < (best :: Entry).tier) then
			best = e
		end
	end
	if best and landIndex < length then
		strip[landIndex + 1] = best
	end
	return strip
end

-- Position along the strip at time t (seconds), in item widths.
-- Ease-out quint to `target`, overshooting by `over` items, then settling back by `duration`.
function Reel.position(t: number, duration: number, target: number, over: number?): number
	local o = over or 0.18
	local settle = 0.18 -- last 18% of the time is the settle-back
	local u = math.clamp(t / duration, 0, 1)
	if u < 1 - settle then
		local k = u / (1 - settle)
		local e = 1 - (1 - k) ^ 5
		return e * (target + o)
	end
	local k = (u - (1 - settle)) / settle
	local e = k * k * (3 - 2 * k) -- smoothstep back
	return target + o * (1 - e)
end

-- Seconds until the reel "ticks" past the next item (for a click sound / small shake).
-- Returns item indices crossed between t0 and t1.
function Reel.crossed(t0: number, t1: number, duration: number, target: number): { number }
	local a = math.floor(Reel.position(t0, duration, target))
	local b = math.floor(Reel.position(t1, duration, target))
	local out = {}
	for i = a + 1, b do
		table.insert(out, i)
	end
	return out
end

return Reel
