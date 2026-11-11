--!strict
--# selene: allow(multiple_statements)
-- lune run examples/bignum/test.luau
local process = require("@lune/process")
local EN = require("./EternityNum")

local passed, failed = 0, 0
local function check(name: string, cond: boolean)
	if cond then passed += 1 else failed += 1; print("FAIL", name) end
end
local function near(a: number, b: number, rel: number?): boolean
	return math.abs(a - b) <= (rel or 1e-9) * math.max(1, math.abs(b))
end

check("add small", EN.toNumber(EN.add(2, 3)) == 5)
check("mul small", EN.toNumber(EN.mul(1e10, 1e5)) == 1e15)
check("past double", EN.toString(EN.mul("1e300", "1e300")) ~= "inf")
check("cmp huge", EN.me("1e1000", "1e999") and EN.le("1e999", "1e1000"))
check("cmp layers", EN.me("1ee20", "1e1000000"))
check("pow", near(EN.toNumber(EN.log10(EN.pow(10, 500))), 500))
check("sub to zero", EN.isZero(EN.sub("1e50", "1e50")))
check("short K", EN.short(1234) == "1.23K")
check("short big uses suffix or sci", #EN.short("1e40") > 0)

local s = EN.toString(EN.mul("1.2345e777", 3))
check("save roundtrip", EN.eq(EN.fromSave(s), EN.mul("1.2345e777", 3)))

-- closed-form buy-all agrees with the sum it promises
local n = EN.geomAfford(1e6, 10, 1.15, 0)
check("afford fits", EN.leeq(EN.geomSum(10, 1.15, 0, n), 1e6))
check("afford max", EN.me(EN.geomSum(10, 1.15, 0, n + 1), 1e6))

-- leaderboard encoding keeps order
local prev = -math.huge
local ok = true
for _, v in { 0, 1, 999, 1e6, 1e15, "1e100", "1e1000", "1ee10" } do
	local e = EN.lbencode(v)
	if e <= prev then ok = false end
	prev = e
end
check("lbencode monotonic", ok)

print(`{passed} passed, {failed} failed`)
process.exit(failed == 0 and 0 or 1)
