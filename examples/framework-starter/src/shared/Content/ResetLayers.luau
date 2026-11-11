--!strict
-- Content: reset (prestige) layers as data. Each layer says what it wipes, what it keeps
-- and what it pays out. Systems/Reset applies them; no service writes its own wipe code.

export type Layer = {
	id: string,
	order: number, -- higher layers also wipe everything lower layers wipe
	requires: { stat: string, atLeast: number },
	wipes: { string }, -- top-level save keys reset to the template value
	keeps: { string }, -- keys explicitly kept even if a lower layer would wipe them
	payout: { currency: string, base: number, exponent: number, from: string }, -- payout = floor(base * (save.stats[from]) ^ exponent)
}

local ResetLayers: { [string]: Layer } = {
	rebirth = {
		id = "rebirth",
		order = 1,
		requires = { stat = "coinsEarned", atLeast = 1e4 },
		wipes = { "coins", "upgrades" },
		keeps = { "gems", "stats", "unlocked" },
		payout = { currency = "gems", base = 1, exponent = 0.5, from = "coinsEarned" },
	},
}

return table.freeze(ResetLayers)
