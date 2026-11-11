--!strict
-- Central system: upgrade maths. Pure functions over Content rows and a save table,
-- so the server and lune tests run the exact same code.

local Upgrades = require("../Content/Upgrades")

local Economy = {}

-- Cost of the next level (level = current level, 0-based).
function Economy.cost(u: Upgrades.Upgrade, level: number): number
	return math.floor(u.baseCost * u.growth ^ level)
end

-- Total cost of buying `n` levels starting at `level`, in closed form (geometric series).
function Economy.costOf(u: Upgrades.Upgrade, level: number, n: number): number
	if n <= 0 then
		return 0
	end
	local r = u.growth
	return math.floor(u.baseCost * r ^ level * (r ^ n - 1) / (r - 1))
end

-- Most levels affordable with `money`, capped by maxLevel. O(1).
function Economy.maxAffordable(u: Upgrades.Upgrade, level: number, money: number): number
	local room = u.maxLevel - level
	if room <= 0 or money < Economy.cost(u, level) then
		return 0
	end
	local r = u.growth
	local n = math.floor(math.log(money * (r - 1) / (u.baseCost * r ^ level) + 1) / math.log(r))
	n = math.clamp(n, 0, room)
	-- guard against float error at the boundary
	while n > 0 and Economy.costOf(u, level, n) > money do
		n -= 1
	end
	return n
end

-- Sum of an effect across every owned upgrade.
function Economy.effect(save: any, effect: string): number
	local total = 0
	for id, level in save.upgrades do
		local u = Upgrades[id]
		if u and u.effect == effect then
			total += u.perLevel * level
		end
	end
	return total
end

-- Coins per tap and per second, the two numbers the HUD shows.
function Economy.rates(save: any): (number, number)
	local mult = 1 + Economy.effect(save, "multiplier")
	local tap = (1 + Economy.effect(save, "clickPower")) * mult
	local perSecond = Economy.effect(save, "autoPerSecond") * mult
	return tap, perSecond
end

export type BuyResult = { ok: boolean, reason: string?, bought: number?, spent: number? }

-- Validated purchase. Mutates `save` only on success. The caller has already checked
-- that `id` is a whitelisted key and `n` is a sane whole number (Kit.Guard).
function Economy.buy(save: any, id: string, n: number, isUnlocked: (string) -> boolean): BuyResult
	local u = Upgrades[id]
	if not u then
		return { ok = false, reason = "unknown upgrade" }
	end
	if u.unlock and not isUnlocked(u.unlock) then
		return { ok = false, reason = "locked" }
	end
	local level = save.upgrades[id] or 0
	local count = math.min(n, Economy.maxAffordable(u, level, save[u.currency]))
	if count <= 0 then
		return { ok = false, reason = level >= u.maxLevel and "maxed" or "cannot afford" }
	end
	local spent = Economy.costOf(u, level, count)
	save[u.currency] -= spent
	save.upgrades[id] = level + count
	if u.currency == "coins" then
		save.stats.coinsSpent += spent
	end
	return { ok = true, bought = count, spent = spent }
end

return Economy
