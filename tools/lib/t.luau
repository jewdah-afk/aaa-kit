--!strict
-- Minimal test helper for lune. t.ok(name, cond), t.eq(name, got, want), t.near(name, a, b, eps), t.done()
local process = require("@lune/process")

local t = {}
local passed, failed = 0, 0

function t.ok(name: string, cond: any)
	if cond then
		passed += 1
	else
		failed += 1
		print("FAIL", name)
	end
end

function t.eq(name: string, got: any, want: any)
	if got == want then
		passed += 1
	else
		failed += 1
		print("FAIL", name, "got", tostring(got), "want", tostring(want))
	end
end

function t.near(name: string, a: number, b: number, eps: number?)
	t.ok(name .. ` ({a} ~ {b})`, math.abs(a - b) <= (eps or 1e-6))
end

function t.done()
	print(`{passed} passed, {failed} failed`)
	process.exit(failed == 0 and 0 or 1)
end

return t
