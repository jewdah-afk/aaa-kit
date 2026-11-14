--!strict
-- OddsLadder: the "1 in N" climb shown during a reveal. The server has already rolled the
-- result; this only builds the counting sequence that lands exactly on it.

export type Tier = { Name: string, MinOdds: number, Colour: { number }, Word: string? }
export type Step = { Odds: number, Tier: number, TierUp: boolean }

local OddsLadder = {}

function OddsLadder.tierOf(tiers: { Tier }, odds: number): number
	local idx = 1
	for i, t in tiers do
		if odds >= t.MinOdds then
			idx = i
		end
	end
	return idx
end

-- `count` displayed values from 2 up to `final`, spaced geometrically (slow start, fast end),
-- rounded to whole numbers, strictly increasing, last one == final. TierUp marks where a
-- slam word and edge flash fire.
function OddsLadder.steps(tiers: { Tier }, final: number, count: number): { Step }
	final = math.max(2, math.floor(final))
	count = math.max(1, math.min(count, final - 1))
	local out: { Step } = {}
	local prevOdds, prevTier = 1, OddsLadder.tierOf(tiers, 2)
	for i = 1, count do
		local p = if count == 1 then 1 else (i - 1) / (count - 1)
		local v = math.floor(2 * (final / 2) ^ p + 0.5)
		if i == count then
			v = final
		end
		v = math.max(v, prevOdds + 1)
		local tier = OddsLadder.tierOf(tiers, v)
		table.insert(out, { Odds = v, Tier = tier, TierUp = i > 1 and tier > prevTier })
		prevOdds, prevTier = v, tier
	end
	return out
end

-- Slam word timing in frames at 60 fps: in (scale 2.2 -> 1) then shrink to park scale.
function OddsLadder.slamScale(frame: number): number
	if frame <= 2 then
		return 2.2 - 1.2 * (frame / 2)
	elseif frame <= 5 then
		return 1 - 0.6 * ((frame - 2) / 3)
	end
	return 0.4
end

return OddsLadder
