--!strict
local Odometer = require("./Odometer")
local t = require("../../../../tools/lib/t")

t.eq("format small", Odometer.format(999), "999")
t.eq("format K floors", Odometer.format(1999), "1.99K")
t.eq("format M", Odometer.format(45_600_000), "45.6M")
t.eq("format T", Odometer.format(3.2e12), "3.20T")
t.eq("format NaN safe", Odometer.format(0 / 0), "0")

local o = Odometer.new(6)
o:set(1234)
local text = ""
for _, s in o.slots do
	text ..= s.cur
end
t.eq("right aligned", text, " 1.23K")
t.ok("rolling after set", o:step(0.01))
for _ = 1, 30 do
	o:step(1 / 60)
end
t.ok("settles", not o:step(1 / 60))
o:set(1234)
t.ok("same value stays still", not o:step(1 / 60))
o:set(1240)
local changed = 0
for _, s in o.slots do
	if s.p < 1 then
		changed += 1
	end
end
t.eq("only changed digits roll", changed, 1)
local a, b = Odometer.offsets({ cur = "1", prev = "0", p = 0 })
t.eq("offsets start", a + b, 1)
t.ok("suffix detect", Odometer.isSuffix("K") and not Odometer.isSuffix("7"))

t.done()
