--!strict
-- Content: plain data only. No requires, no logic beyond tiny pure cost/effect curves.
-- Add an upgrade by copying a row and changing numbers. Balance lives here, never in a service.

export type Upgrade = {
	id: string,
	name: string,
	currency: "coins" | "gems",
	baseCost: number,
	growth: number, -- cost multiplier per level (geometric)
	maxLevel: number,
	effect: "clickPower" | "autoPerSecond" | "multiplier",
	perLevel: number, -- effect added per level
	unlock: string?, -- id in Content/Unlocks, nil = always available
}

local Upgrades: { [string]: Upgrade } = {
	click_power = {
		id = "click_power",
		name = "Sharper Tap",
		currency = "coins",
		baseCost = 10,
		growth = 1.15,
		maxLevel = 200,
		effect = "clickPower",
		perLevel = 1,
	},
	auto_miner = {
		id = "auto_miner",
		name = "Auto Miner",
		currency = "coins",
		baseCost = 50,
		growth = 1.18,
		maxLevel = 150,
		effect = "autoPerSecond",
		perLevel = 2,
		unlock = "first_hundred",
	},
	gem_lens = {
		id = "gem_lens",
		name = "Gem Lens",
		currency = "gems",
		baseCost = 5,
		growth = 1.6,
		maxLevel = 25,
		effect = "multiplier",
		perLevel = 0.1,
		unlock = "first_reset",
	},
}

return table.freeze(Upgrades)
