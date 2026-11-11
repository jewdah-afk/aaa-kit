--!strict
-- Central system: evaluates Content/Unlocks against a save. Returns newly unlocked ids
-- so the caller can fire one "unlocked" event per id (client shows/hides content).

local UnlockData = require("../Content/Unlocks")

local Unlocks = {}

function Unlocks.isUnlocked(save: any, id: string): boolean
	return save.unlocked[id] == true
end

-- Marks every satisfied unlock and returns the ids that changed this call.
function Unlocks.refresh(save: any): { string }
	local fresh = {}
	for id, u in UnlockData do
		if not save.unlocked[id] and (save.stats[u.stat] or 0) >= u.atLeast then
			save.unlocked[id] = true
			table.insert(fresh, id)
		end
	end
	table.sort(fresh)
	return fresh
end

return Unlocks
