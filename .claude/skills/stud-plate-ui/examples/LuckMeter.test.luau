--!strict
local LuckMeter = require("./LuckMeter")
local t = require("../../../../tools/lib/t")

t.eq("x1 is CALM", LuckMeter.rung(1).name, "CALM")
t.eq("x2 is WARM (inclusive)", LuckMeter.rung(2).name, "WARM")
t.eq("x7.2 is LUCKY", LuckMeter.rung(7.2).name, "LUCKY")
t.eq("x12.84 is HOT", LuckMeter.rung(12.84).name, "HOT")
t.eq("x31.5 is MYTHIC", LuckMeter.rung(31.5).name, "MYTHIC")
t.eq("NaN reads CALM", LuckMeter.rungIndex(0 / 0), 1)
t.eq("inf reads CALM", LuckMeter.rungIndex(math.huge), 1)
t.eq("negative reads CALM", LuckMeter.rungIndex(-4), 1)

local prev = 0
local ok = true
for _, r in LuckMeter.RUNGS do
	ok = ok and r.scale > prev
	prev = r.scale
end
t.ok("rungs grow monotonically", ok)

t.eq("format x12.84", LuckMeter.format(12.849), "×12.84")
t.eq("format floors", LuckMeter.format(1.999), "×1.99")
t.eq("format hundreds", LuckMeter.format(123.45), "×123.4")
t.eq("format thousands", LuckMeter.format(4321.9), "×4321")
t.eq("format NaN", LuckMeter.format(0 / 0), "×0.00")

t.near("countUp starts at from", LuckMeter.countUp(1, 10, 0), 1, 1e-9)
t.near("countUp ends at to", LuckMeter.countUp(1, 10, 1), 10, 1e-9)
t.ok("countUp is past the log midpoint by t=0.15", LuckMeter.countUp(1, 100, 0.15) > 10)
t.near("countUp clamps t", LuckMeter.countUp(2, 8, 5), 8, 1e-9)

t.eq("punch rests at 1", LuckMeter.punch(0), 1)
t.near("punch peaks", LuckMeter.punch(LuckMeter.PUNCH_UP), LuckMeter.PUNCH_PEAK, 1e-6)
t.eq("punch done", LuckMeter.punch(1), 1)
local overshoot = false
for i = 1, 40 do
	if LuckMeter.punch(LuckMeter.PUNCH_UP + LuckMeter.PUNCH_SETTLE * i / 40) < 1 then
		overshoot = true
	end
end
t.ok("settle overshoots below 1 (back out)", overshoot)
t.near("spin peaks at -12", LuckMeter.spin(LuckMeter.PUNCH_UP), -12, 1e-6)

t.eq("crossing up", LuckMeter.crossed(4.9, 5.1), 3)
t.eq("crossing two rungs", LuckMeter.crossed(1, 11), 4)
t.eq("same rung", LuckMeter.crossed(5.5, 9.9), nil)
t.eq("falling never punches", LuckMeter.crossed(30, 1), nil)

t.done()
