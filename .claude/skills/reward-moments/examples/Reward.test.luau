--!strict
local Reel = require("./Reel")
local RewardSequence = require("./RewardSequence")
local t = require("../../../../tools/lib/t")

local entries = {
	{ id = "common", weight = 70, tier = 1 },
	{ id = "rare", weight = 25, tier = 3 },
	{ id = "mythic", weight = 5, tier = 6 },
}
t.eq("pick low", Reel.pick(entries, 0).id, "common")
t.eq("pick mid", Reel.pick(entries, 0.8).id, "rare")
t.eq("pick top", Reel.pick(entries, 0.999).id, "mythic")

-- distribution sanity over a seeded RNG
local function lcg(seed: number): () -> number
	local x = seed
	return function()
		x = (x * 1103515245 + 12345) % 2147483648
		return x / 2147483648
	end
end
local rng = lcg(7)
local counts = { common = 0, rare = 0, mythic = 0 }
for _ = 1, 20000 do
	local e = Reel.pick(entries, rng())
	counts[e.id] += 1
end
t.near("weights", counts.mythic / 20000, 0.05, 0.01)

local strip = Reel.strip(entries, entries[1], 40, 34, lcg(1))
t.eq("strip lands", strip[34].id, "common")
t.eq("near miss after", strip[35].id, "rare")

t.near("starts at 0", Reel.position(0, 4, 34), 0)
t.ok("overshoots", Reel.position(4 * 0.82, 4, 34) > 34)
t.near("settles exactly", Reel.position(4, 4, 34), 34)
t.ok("ticks crossed", #Reel.crossed(0, 1, 4, 34) > 0)

local beats = {}
local seq = RewardSequence.new(1, function(b)
	table.insert(beats, b)
end)
for _ = 1, 120 do
	seq:step(1 / 60)
end
t.eq("common reaches continue", seq:beat(), "continue")
t.eq("beats in order", table.concat(beats, ","), "container,item,identity,delta,continue")
seq:press()
t.eq("press finishes", seq:beat(), "done")

local mythic = RewardSequence.new(6)
mythic:step(0.1)
mythic:press()
t.ok("skip jumps to continue", mythic:beat() == "continue" and mythic.skipped)
t.ok("mythic is longer", RewardSequence.new(6):length("identity") > RewardSequence.new(1):length("identity"))

t.done()
