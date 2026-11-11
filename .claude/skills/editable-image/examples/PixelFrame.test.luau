--!strict
local PixelFrame = require("./PixelFrame")
local t = require("../../../../tools/lib/t")
local O = PixelFrame.OWNER

local f = PixelFrame.new(32, 18)
f:clear(10, 10, 20)
local r, g, b, own = f:get(0, 0)
t.ok("clear colour + owner", r == 10 and g == 10 and b == 20 and own == O.BACKGROUND)

t.ok("world over background", f:put(5, 5, 50, 80, 50, O.WORLD))
t.ok("threat over world", f:put(5, 5, 255, 60, 60, O.THREAT))
t.ok("hero FX cannot hide threat", not f:put(5, 5, 255, 255, 255, O.HERO))
local _, _, _, o2 = f:get(5, 5)
t.eq("threat kept", o2, O.THREAT)
t.ok("UI covers threat", f:put(5, 5, 240, 230, 200, O.UI))
t.ok("ambient cannot cover UI", not f:put(5, 5, 1, 2, 3, O.AMBIENT))
t.ok("snaps fractional coords", f:put(7.8, 2.2, 1, 1, 1, O.WORLD) and select(4, f:get(7, 2)) == O.WORLD)
t.ok("clips outside", not f:put(-1, 0, 0, 0, 0, O.CEREMONY) and not f:put(32, 0, 0, 0, 0, O.CEREMONY))

f:put(1, 1, 255, 60, 60, O.THREAT)
local landed = f:rect(0, 0, 8, 4, 200, 120, 40, O.REWARD)
t.eq("rect respects owners", landed, 31)
t.near("coverage", f:coverage(O.REWARD), landed / (32 * 18))

t.done()
