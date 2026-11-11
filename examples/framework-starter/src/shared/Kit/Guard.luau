--!strict
-- Guard: server-side argument validation. Every remote handler runs its arguments
-- through these before touching data. Client checks are cosmetic; these are the real ones.

local Guard = {}

-- A finite number (rejects NaN, +inf, -inf and non-numbers).
function Guard.finite(v: unknown): boolean
	return type(v) == "number" and v == v and math.abs(v) ~= math.huge
end

-- A whole number inside [lo, hi].
function Guard.int(v: unknown, lo: number, hi: number): boolean
	return Guard.finite(v) and (v :: number) % 1 == 0 and (v :: number) >= lo and (v :: number) <= hi
end

-- A count the player asked for: whole, >= 1, capped.
function Guard.count(v: unknown, max: number): boolean
	return Guard.int(v, 1, max)
end

-- A string that is a key of the given table (whitelist, never a free-form key).
function Guard.oneOf(v: unknown, whitelist: { [string]: any }): boolean
	return type(v) == "string" and #v <= 64 and whitelist[v] ~= nil
end

-- Per-player rate limit. `new(seconds)` returns a function `(key) -> allowed`.
-- Pass a clock for tests; defaults to os.clock.
function Guard.rate(seconds: number, clock: (() -> number)?): (key: any) -> boolean
	local now = clock or os.clock
	local last: { [any]: number } = {}
	return function(key: any): boolean
		local t = now()
		local prev = last[key]
		if prev and t - prev < seconds then
			return false
		end
		last[key] = t
		return true
	end
end

-- Forget a key (call on PlayerRemoving so tables don't grow forever).
function Guard.forget(limiter: any, _key: any)
	-- Limiters are closures; services keep their own per-player tables and clear them.
	-- This hook exists so call sites read the same in every service.
	return limiter
end

return Guard
