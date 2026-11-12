--!strict
-- lune run lib/celestialrithm/qa/test_director.luau   (from the repo root or this folder)
local H = require("../HierarchyDirector")

local failed = 0
local function check(name: string, ok: boolean)
	print(("@@CHECK %s %s"):format(ok and "PASS" or "FAIL", name))
	if not ok then
		failed += 1
	end
end
local function near(a: number, b: number): boolean
	return math.abs(a - b) < 1e-6
end

local d = H.new({ verdant_coral = 0.5 })
local c, e = table.create(3, 0), table.create(3, 0)

H.attention(d, { 0, 0, 0 }, c, e)
check("calm board: all multipliers are 1", near(c[1], 1) and near(c[3], 1) and near(e[2], 1))

H.attention(d, { 0, 1, 0 }, c, e)
check("owner gains contrast and exposure", near(c[2], 1.45) and near(e[2], 1.30))
check("others sink by the same envelope", near(c[1], 0.55) and near(e[3], 0.70))
check("owner strictly louder than everyone else", c[2] > c[1] and c[2] > c[3])

H.attention(d, { 0.3, 0.3, 0 }, c, e)
check("tied presses share ownership, idle surface dips", near(c[1], c[2]) and c[3] < 1)

H.attention(d, { 2, -1, 0 }, c, e)
check("press levels are clamped to 0..1", near(c[1], 1.45) and near(c[2], 0.55))

check("calibrated gain read from data", near(H.gain(d, "verdant_coral"), 0.5) and near(H.gain(d, "opal"), 1))
check("grade keeps the mean fixed", near(H.grade(0.4, 0.4, 0.5, 1.45, 1), 0.4))
check("grade clamps to 0..1", H.grade(1, 0.2, 1.6, 1.45, 1.3) == 1 and H.grade(0, 0.8, 1.6, 1.45, 1) == 0)

local ev = { id = "a", priority = 1, start = 0, duration = 1, reducedMotion = false }
check("offer accepts the first event", H.offer(d, ev, 0))
check("equal priority cannot interrupt", not H.offer(d, { id = "b", priority = 1, start = 0.2, duration = 1, reducedMotion = false }, 0.2))
check("higher priority interrupts", H.offer(d, { id = "c", priority = 2, start = 0.3, duration = 1, reducedMotion = false }, 0.3))
check("intensity peaks mid-event", near(H.intensity(d, "c", 0.8), 1) and H.intensity(d, "c", 0.35) < 1)
check("reduced motion gives no intensity", (function()
	local r = H.new()
	H.offer(r, { id = "x", priority = 1, start = 0, duration = 1, reducedMotion = true }, 0)
	return H.intensity(r, "x", 0.5) == 0
end)())

print(("@@DONE %d"):format(failed))
