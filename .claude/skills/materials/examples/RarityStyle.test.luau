--!strict
--# selene: allow(multiple_statements)
local RarityStyle = require("./RarityStyle")
local t = require("../../../../tools/lib/t")

t.eq("seven tiers", #RarityStyle.TIERS, 7)
-- each tier adds at most one motion behaviour, and never removes one
local ok = true
for i = 2, #RarityStyle.TIERS do
	local a, b = RarityStyle.TIERS[i - 1], RarityStyle.TIERS[i]
	local d = RarityStyle.behaviours(b) - RarityStyle.behaviours(a)
	if d < 0 or d > 1 then ok = false end
end
t.ok("ladder adds one at a time", ok)
t.eq("common is still", RarityStyle.behaviours(RarityStyle.TIERS[1]), 0)
t.ok("motion starts at Rare", RarityStyle.behaviours(RarityStyle.TIERS[2]) == 0 and RarityStyle.TIERS[3].sweep)
-- no rarity uses danger red (pure red family)
local redFree = true
for _, s in RarityStyle.TIERS do
	if s.color[1] > 200 and s.color[2] < 70 and s.color[3] < 70 then redFree = false end
end
t.ok("no rarity borrows danger red", redFree)
t.eq("clamps tier", RarityStyle.get(99).name, "Secret")
t.done()
