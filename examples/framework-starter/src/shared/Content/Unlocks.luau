--!strict
-- Content: unlock conditions as data. Systems/Unlocks evaluates them; nothing else decides gating.

export type Unlock = {
	id: string,
	stat: string, -- a key in the save's `stats` table
	atLeast: number,
}

local Unlocks: { [string]: Unlock } = {
	first_hundred = { id = "first_hundred", stat = "coinsEarned", atLeast = 100 },
	first_reset = { id = "first_reset", stat = "resets", atLeast = 1 },
	big_spender = { id = "big_spender", stat = "coinsSpent", atLeast = 1e6 },
}

return table.freeze(Unlocks)
