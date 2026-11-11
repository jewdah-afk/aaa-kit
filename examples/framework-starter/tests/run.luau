--!strict
-- Headless tests for every pure module. Run from the repo root:
--   lune run examples/framework-starter/tests/run.luau
-- Exits non-zero on the first failing check.

local process = require("@lune/process")

local Kit = require("../src/shared/Kit")
local Economy = require("../src/shared/Systems/Economy")
local Save = require("../src/shared/Systems/Save")
local Automations = require("../src/shared/Systems/Automations")
local Unlocks = require("../src/shared/Systems/Unlocks")
local Reset = require("../src/shared/Systems/Reset")
local Intensity = require("../src/shared/Systems/Intensity")
local Upgrades = require("../src/shared/Content/Upgrades")

local passed, failed = 0, 0
local function check(name: string, cond: boolean)
	if cond then
		passed += 1
	else
		failed += 1
		print("FAIL", name)
	end
end

-- Format
check("short <1000", Kit.Format.short(999) == "999")
check("short K", Kit.Format.short(1234) == "1.23K")
check("short floors", Kit.Format.short(1999) == "1.99K")
check("short M", Kit.Format.short(12_340_000) == "12.3M")
check("short B", Kit.Format.short(1.5e9) == "1.50B")
check("short neg", Kit.Format.short(-2500) == "-2.50K")
check("commas", Kit.Format.commas(1234567) == "1,234,567")
check("commas small", Kit.Format.commas(12) == "12")
check("duration", Kit.Format.duration(3725) == "1h 02m")

-- Guard
check("finite NaN", not Kit.Guard.finite(0 / 0))
check("finite inf", not Kit.Guard.finite(math.huge))
check("finite ok", Kit.Guard.finite(3.5))
check("count rejects 0", not Kit.Guard.count(0, 10))
check("count rejects frac", not Kit.Guard.count(1.5, 10))
check("count ok", Kit.Guard.count(3, 10))
check("oneOf", Kit.Guard.oneOf("click_power", Upgrades) and not Kit.Guard.oneOf("__index", Upgrades))
local t = 0
local lim = Kit.Guard.rate(1, function()
	return t
end)
check("rate first", lim("p"))
check("rate blocked", not lim("p"))
t = 1.01
check("rate after", lim("p"))

-- Maid + Signal
local sig = Kit.Signal.new()
local hits = 0
local maid = Kit.Maid.new()
maid:give(sig:connect(function(n: number)
	hits += n
end))
sig:fire(2)
maid:clean()
sig:fire(5)
check("maid disconnects", hits == 2)
local onceHits = 0
sig:once(function()
	onceHits += 1
end)
sig:fire()
sig:fire()
check("once", onceHits == 1)

-- Registry order
local order = {}
local reg = Kit.Registry.new()
reg:add({ name = "A", init = function() table.insert(order, "A.init") end, start = function() table.insert(order, "A.start") end })
reg:add({ name = "B", init = function() table.insert(order, "B.init") end, playerRemoving = function() table.insert(order, "B.rm") end })
reg:add({ name = "C", playerRemoving = function() table.insert(order, "C.rm") end })
reg:boot()
reg:playerRemoving({})
check("registry order", table.concat(order, ",") == "A.init,B.init,A.start,C.rm,B.rm")

-- Economy
local u = Upgrades.click_power
check("cost lvl0", Economy.cost(u, 0) == 10)
local sum = 0
for i = 0, 9 do
	sum += u.baseCost * u.growth ^ i
end
check("costOf closed form", math.abs(Economy.costOf(u, 0, 10) - math.floor(sum)) <= 1)
local n = Economy.maxAffordable(u, 0, 1000)
check("maxAffordable fits", Economy.costOf(u, 0, n) <= 1000 and Economy.costOf(u, 0, n + 1) > 1000)
check("maxAffordable cap", Economy.maxAffordable(u, u.maxLevel, 1e300) == 0)

local save = Save.new()
save.coins = 100
local r = Economy.buy(save, "click_power", 1000, function()
	return false
end)
check("buy ok", r.ok and (r.bought :: number) > 0 and save.coins >= 0)
check("buy locked", not Economy.buy(save, "auto_miner", 1, function() return false end).ok)
check("buy unknown", not Economy.buy(save, "nope", 1, function() return true end).ok)

-- Save reconcile
local old = { coins = 5, stats = { coinsEarned = 7 }, extra = "kept" }
local fixed = Save.reconcile(old)
check("reconcile fills", fixed.gems == 0 and fixed.stats.resets == 0 and fixed.settings.music == 0.8)
check("reconcile keeps", fixed.coins == 5 and fixed.stats.coinsEarned == 7 and fixed.extra == "kept")
check("reconcile type fix", Save.reconcile({ coins = "x" }).coins == 0)
check("template untouched", Save.TEMPLATE.coins == 0)

-- Automations
local auto = Automations.new()
local runs = 0
auto:add({ id = "a", interval = 1, maxCatchUp = 3, run = function(_, e) runs += e end })
local s2 = Save.new()
auto:tick(s2, 0.5)
check("auto waits", runs == 0)
auto:tick(s2, 0.6)
check("auto fires", runs == 1)
auto:tick(s2, 100)
check("auto catch-up cap", runs == 4)

-- Unlocks
local s3 = Save.new()
s3.stats.coinsEarned = 150
local fresh = Unlocks.refresh(s3)
check("unlock fresh", #fresh == 1 and fresh[1] == "first_hundred")
check("unlock once", #Unlocks.refresh(s3) == 0)

-- Reset
local s4 = Save.new()
s4.coins = 999
s4.upgrades.click_power = 10
s4.stats.coinsEarned = 1e4
local gain = Reset.apply(s4, "rebirth")
check("reset payout", gain == 100)
check("reset wipes", s4.coins == 0 and next(s4.upgrades) == nil)
check("reset keeps", s4.gems == 100 and s4.stats.resets == 1)
check("reset gate", Reset.apply(s4, "rebirth") == nil)

-- Intensity
local st = Intensity.new()
check("calm", Intensity.observe(st, {}, 0.1) == 0)
check("boss jumps", Intensity.observe(st, { boss = true }, 0.1) == 4)
check("falls slowly", Intensity.observe(st, {}, 1.0) == 4)
check("falls one rung", Intensity.observe(st, {}, 0.6) == 3)
local hy = Intensity.new()
Intensity.observe(hy, { onScreen = 40 }, 0.1)
check("crowd on", hy.crowd)
Intensity.observe(hy, { onScreen = 35 }, 0.1)
check("crowd hysteresis", hy.crowd)

print(`{passed} passed, {failed} failed`)
process.exit(failed == 0 and 0 or 1)
