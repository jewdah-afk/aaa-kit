--!strict
-- Curves: the standard pricing and reward curves for incremental and progression games,
-- plus the payback check that keeps them honest. All pure; rows in Content pick a curve
-- by name and parameters, so a designer tunes numbers without touching code.

local Curves = {}

-- Geometric (the default for upgrade costs): base * growth^level.
function Curves.geometric(base: number, growth: number, level: number): number
	return base * growth ^ level
end

-- Polynomial (gentler, good for XP to next level): base * (level + 1)^power.
function Curves.polynomial(base: number, power: number, level: number): number
	return base * (level + 1) ^ power
end

-- Soft cap: linear until `cap`, then logarithmic. The slope is 1 at the cap (no kink)
-- and keeps shrinking after it, so a stat has diminishing returns without a hard wall.
function Curves.softCap(value: number, cap: number): number
	if value <= cap then
		return value
	end
	return cap + cap * math.log(1 + (value - cap) / cap)
end

-- Prestige payout: floor(k * total^exp). exp < 1 so doubling the run gives < 2x currency.
function Curves.prestige(total: number, k: number, exp: number): number
	return math.floor(k * math.max(0, total) ^ exp)
end

-- Seconds of income needed to pay back an upgrade's cost (lower = better buy).
-- cost: price now; gain: income per second the upgrade adds.
function Curves.payback(cost: number, gain: number): number
	return if gain <= 0 then math.huge else cost / gain
end

-- Checks that the time to afford each next level grows smoothly (no wall, no free ride).
-- incomeAt(level) is income per second when you own `level` levels. Returns the
-- worst jump ratio between consecutive wait times; flag anything above `maxJump`.
function Curves.pacing(costAt: (number) -> number, incomeAt: (number) -> number, levels: number): (number, number)
	local worst, worstLevel = 0, 0
	local prev: number? = nil
	for l = 0, levels - 1 do
		local wait = costAt(l) / math.max(incomeAt(l), 1e-9)
		if prev and prev > 0 then
			local jump = wait / prev
			if jump > worst then
				worst, worstLevel = jump, l
			end
		end
		prev = wait
	end
	return worst, worstLevel
end

-- Offline earnings: capped hours, reduced rate (rewards returning without punishing play).
function Curves.offline(perSecond: number, secondsAway: number, capHours: number, rate: number): number
	return perSecond * math.min(secondsAway, capHours * 3600) * rate
end

return Curves
