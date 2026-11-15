--!strict
-- ZoneLadder: which zone a flying projectile is in, and how far through the crossfade.
-- Zones are content (a plain table); this module only reads them.

export type Zone = { Name: string, Start: number, Colour: { number } }

local ZoneLadder = {}

-- Returns the zone index at distance `d` and a 0..1 blend toward that zone over `fade` studs
-- after its start (1 = fully in). Zones must be sorted by Start, first Start = 0.
function ZoneLadder.at(zones: { Zone }, d: number, fade: number): (number, number)
	local idx = 1
	for i = #zones, 1, -1 do
		if d >= zones[i].Start then
			idx = i
			break
		end
	end
	if idx == 1 or fade <= 0 then
		return idx, 1
	end
	return idx, math.clamp((d - zones[idx].Start) / fade, 0, 1)
end

-- Builds evenly paced zones so each one is on screen for `seconds` at projectile speed `speed`.
function ZoneLadder.paced(names: { string }, speed: number, seconds: number): { Zone }
	local out = {}
	for i, n in names do
		out[i] = { Name = n, Start = (i - 1) * speed * seconds, Colour = { 1, 1, 1 } }
	end
	return out
end

-- Luck at distance: starts at `base`, adds `perZone` each zone entered (the "+0.09×" chip).
function ZoneLadder.luck(zones: { Zone }, d: number, base: number, perZone: number): number
	local idx = ZoneLadder.at(zones, d, 0)
	return base + (idx - 1) * perZone
end

return ZoneLadder
