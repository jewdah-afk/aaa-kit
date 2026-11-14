--!strict
local Clip = require("./Clip")
local Spring = require("./Spring")
local t = require("../../../../tools/lib/t")

-- A two-channel throw: hand forward distance and torso twist.
local throw: Clip.Clip = {
	Keys = {
		{ Time = 0, Values = { 0, -16 } },
		{ Time = 0.30, Values = { -0.9, -52 }, Ease = "Smooth" }, -- wind-up
		{ Time = 0.46, Values = { 1.2, 28 }, Ease = "In" }, -- release: speeds up into it
		{ Time = 0.61, Values = { 1.5, 46 }, Ease = "Out" }, -- follow-through: slows down
		{ Time = 0.93, Values = { 0, 0 }, Ease = "Smooth" },
	},
}
local out = {}
Clip.sample(throw, 0.46, out)
t.near("hits the release key", out[1], 1.2, 1e-9)
Clip.sample(throw, 99, out)
t.near("clamps past the end", out[1], 0, 1e-9)
Clip.sample(throw, 0 / 0, out)
t.ok("ignores NaN", out[1] == out[1])
Clip.sample(throw, 0.30, out, { [2] = 1.5 })
t.near("drive scales one channel", out[2], -78, 1e-9)
t.near("and leaves the others", out[1], -0.9, 1e-9)

local before, after = {}, {}
Clip.sample(throw, 0.44, before)
Clip.sample(throw, 0.46, after)
local intoRelease = after[1] - before[1]
Clip.sample(throw, 0.48, before)
t.ok("fastest at the release, not before it", intoRelease > 0.3 and before[1] - after[1] < intoRelease)

local held = { -0.5, -30 }
Clip.from(held, Clip.sample(throw, 0, out), 0, 0.1)
t.near("first frame equals the held pose", out[1], -0.5, 1e-9)
Clip.from(held, Clip.sample(throw, 0.1, out), 0.1, 0.1)
Clip.sample(throw, 0.1, before)
t.near("blend is over after its time", out[1], before[1], 1e-9)

t.ok("nothing snaps between 1 ms samples", Clip.maxStep(throw, 0.001, { 1, 1 / 60 }) < 0.04)
t.near("smoother ends flat", Clip.smoother(0.001), 0, 1e-6)

-- Spring
local x, v, over = 0, 0, false
for _ = 1, 600 do
	x, v = Spring.step(x, v, 10, 0, 6, 1 / 60)
	over = over or x > 10 + 1e-9
end
t.near("settles on the target", x, 10, 1e-3)
t.ok("no overshoot from rest", not over)
local a1, b1 = Spring.step(0, 5, 10, 0, 4, 1 / 30)
local a2, b2 = Spring.step(0, 5, 10, 0, 4, 1 / 60)
a2, b2 = Spring.step(a2, b2, 10, 0, 4, 1 / 60)
t.near("same path at 30 and 60 fps", a1, a2, 1e-9)
t.near("same speed at 30 and 60 fps", b1, b2, 1e-9)
local _, kept = Spring.step(0, 25, 0, 0, 3, 1 / 60)
t.ok("keeps the speed it is handed", kept > 21 and kept <= 25)

-- Hand-off: a camera drifting at 9 studs/s is handed a target moving at 120 studs/s.
local function handoff(useSpring: boolean): number
	local path, pos, speed, target = {}, 0, 9, 30
	for i = 1, 60 do
		table.insert(path, pos)
		pos += 9 / 60
	end
	for i = 1, 90 do
		target += 120 / 60
		if useSpring then
			pos, speed = Spring.step(pos, speed, target, 120, Spring.tighten(i / 60, 3.2, 6, 0.6), 1 / 60, 0.5)
		else
			pos += (target - pos) * math.clamp(6 / 60, 0, 1) -- the usual lerp-to-target
		end
		table.insert(path, pos)
	end
	return Spring.maxAccel(path, 1 / 60)
end
local lerpAccel, springAccel = handoff(false), handoff(true)
t.ok(`spring hand-off is at least 5x gentler than a lerp ({math.floor(lerpAccel)} vs {math.floor(springAccel)})`, springAccel * 5 < lerpAccel)

local p, s, target = 0, 0, 0
for _ = 1, 900 do
	target += 2
	p, s = Spring.step(p, s, target, 120, 6, 1 / 60, 0.5)
end
t.near("trails a fast target by a steady distance", target - p, 2 * 0.5 * 120 / 6, 2)
t.eq("kick is zero before and after", Spring.kick(0, 0.14, 0.75) + Spring.kick(2, 0.14, 0.75), 0)
t.near("kick peaks at 1", Spring.kick(0.14, 0.14, 0.75), 1, 1e-9)
t.done()
