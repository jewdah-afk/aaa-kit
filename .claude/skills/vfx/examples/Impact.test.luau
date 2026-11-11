--!strict
local Impact = require("./Impact")
local t = require("../../../../tools/lib/t")

local fx = Impact.new(3)
fx:hit(1, true)
t.ok("flash on hit", fx:flashing())
local game = 0
for _ = 1, 6 do
	game += fx:step(1 / 60)
end
t.near("6-frame hit-stop on a full hit", game, 0, 1e-9)
t.near("time resumes", fx:step(1 / 60), 1 / 60, 1e-9)

local calm = Impact.new()
calm:hit(1, false)
t.near("no hit-stop at calm", calm:step(1 / 60), 1 / 60, 1e-9)

local s = Impact.new(5)
s:hit(1, true)
s:step(0.01)
local x, y = s:shake()
t.ok("shakes", math.abs(x) + math.abs(y) > 0)
local rx = s:shake(true)
t.ok("reduced motion is smaller", math.abs(rx) <= math.abs(x) + 1e-9)
for _ = 1, 60 do
	s:step(1 / 60)
end
local x2, y2 = s:shake()
t.near("trauma decays to rest", math.abs(x2) + math.abs(y2), 0, 1e-9)

t.done()
