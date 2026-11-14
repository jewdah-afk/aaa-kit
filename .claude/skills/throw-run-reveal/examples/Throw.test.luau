--!strict
local ZoneLadder = require("./ZoneLadder")
local OddsLadder = require("./OddsLadder")
local t = require("../../../../tools/lib/t")

local zones = ZoneLadder.paced({ "Frosted Pines", "Glacier Gate", "Aurora Ridge" }, 100, 0.3)
t.eq("zone 2 start", zones[2].Start, 30)
local i, b = ZoneLadder.at(zones, 0, 6)
t.eq("first zone", i, 1)
t.eq("first zone full", b, 1)
i, b = ZoneLadder.at(zones, 33, 6)
t.eq("mid fade zone", i, 2)
t.near("mid fade blend", b, 0.5, 1e-9)
i = ZoneLadder.at(zones, 9999, 6)
t.eq("past end", i, 3)
t.near("luck per zone", ZoneLadder.luck(zones, 65, 1, 0.09), 1.18, 1e-9)

local tiers = {
	{ Name = "Common", MinOdds = 1, Colour = { 1, 1, 1 } },
	{ Name = "Uncommon", MinOdds = 10, Colour = { 0.5, 1, 0.5 }, Word = "NICE!" },
	{ Name = "Rare", MinOdds = 50, Colour = { 0.5, 0.8, 1 }, Word = "FROSTY!" },
	{ Name = "Epic", MinOdds = 400, Colour = { 0.8, 0.6, 1 }, Word = "BLIZZARD!" },
	{ Name = "Legendary", MinOdds = 2000, Colour = { 1, 0.7, 0.25 }, Word = "LEGENDARY!" },
}
local s = OddsLadder.steps(tiers, 3809, 24)
t.eq("lands on final", s[#s].Odds, 3809)
t.eq("starts at 2", s[1].Odds, 2)
local inc, ups = true, 0
for k = 2, #s do
	if s[k].Odds <= s[k - 1].Odds then
		inc = false
	end
	if s[k].TierUp then
		ups += 1
	end
end
t.ok("strictly increasing", inc)
t.eq("one slam per tier crossed", ups, 4)
t.eq("final tier", s[#s].Tier, 5)
local small = OddsLadder.steps(tiers, 3, 24)
t.eq("tiny final clamps count", #small, 2)
t.eq("tiny final lands", small[#small].Odds, 3)
t.near("slam in", OddsLadder.slamScale(0), 2.2, 1e-9)
t.near("slam hit", OddsLadder.slamScale(2), 1, 1e-9)
t.near("parked", OddsLadder.slamScale(9), 0.4, 1e-9)
t.done()
