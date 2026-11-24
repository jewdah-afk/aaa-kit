--!strict
local t = require("../../../../tools/lib/t")
local EffectBudget = require("./EffectBudget")

local function fill(state: EffectBudget.State, count: number, particles: number)
	for i = 1, count do
		EffectBudget.request(state, i, particles, false, i)
	end
end

local function three(): EffectBudget.State
	local s = EffectBudget.new()
	EffectBudget.request(s, 1, 150, false, 0)
	EffectBudget.request(s, 2, 150, false, 1)
	EffectBudget.request(s, 3, 90, false, 2)
	return s
end

do
	local s = EffectBudget.new()
	t.eq("defaults: 6 slots", s.slots, 6)
	t.eq("defaults: 400 particle cap", s.particleCap, 400)
end

do
	local s = EffectBudget.new()
	local all = true
	for i = 1, 6 do
		local ok = EffectBudget.request(s, i, 50, false, i)
		all = all and ok
	end
	t.ok("six friendly effects fit", all)
	local st = EffectBudget.stats(s)
	t.eq("six friendly: friendly count", st.friendly, 6)
	t.eq("six friendly: particles", st.particles, 300)

	local ok, evicted = EffectBudget.request(s, 7, 50, false, 7)
	t.ok("the seventh friendly is skipped", not ok)
	t.eq("a skip evicts nothing", #evicted, 0)
	t.eq("a skip leaves stats unchanged", EffectBudget.stats(s).friendly, 6)
	t.eq("a skip leaves particles unchanged", EffectBudget.stats(s).particles, 300)

	EffectBudget.release(s, 1)
	t.eq("release frees a slot", EffectBudget.stats(s).friendly, 5)
	t.ok("a skipped effect is not queued", s.entries[7] == nil)
	t.ok("after release the seventh is admitted on a new request", (EffectBudget.request(s, 7, 50, false, 8)))
end

do
	local s = EffectBudget.new()
	EffectBudget.request(s, 1, 150, false, 0)
	EffectBudget.request(s, 2, 150, false, 1)
	t.ok("particle cap: 420 is over 400 and skipped", not (EffectBudget.request(s, 3, 120, false, 2)))
	t.ok("particle cap: exactly 400 is admitted", (EffectBudget.request(s, 4, 100, false, 3)))
end

do
	local s = EffectBudget.new()
	t.ok("a friendly effect larger than the cap is never admitted", not (EffectBudget.request(s, 1, 500, false, 0)))
end

do
	local s = EffectBudget.new()
	fill(s, 6, 10)
	local ok = EffectBudget.request(s, 9, 10, true, 10)
	t.ok("hostile ignores the slot limit", ok)
	t.eq("hostile is counted", EffectBudget.stats(s).hostile, 1)
end

do
	local s = three()
	local ok, evicted = EffectBudget.request(s, 9, 160, true, 3)
	t.ok("hostile admitted when over the particle cap", ok)
	t.eq("hostile evicts only the oldest friendly", table.concat(evicted, ","), "1")
	local st = EffectBudget.stats(s)
	t.eq("after eviction: friendly 2", st.friendly, 2)
	t.eq("after eviction: hostile 1", st.hostile, 1)
	t.eq("after eviction: particles 400", st.particles, 400)

	local s2 = three()
	local _, evicted2 = EffectBudget.request(s2, 9, 300, true, 3)
	t.eq("hostile evicts as many as needed", table.concat(evicted2, ","), "1,2")
end

do
	local s = EffectBudget.new()
	local allOk, anyEvicted = true, false
	for i = 1, 3 do
		local ok, evicted = EffectBudget.request(s, i, 200, true, i)
		allOk = allOk and ok
		anyEvicted = anyEvicted or #evicted > 0
	end
	t.ok("hostile effects are always admitted", allOk)
	t.ok("a hostile effect is never evicted", not anyEvicted)
	t.eq("hostile total may exceed the cap", EffectBudget.stats(s).particles, 600)
	t.ok("a friendly effect is skipped while hostile ones fill the cap", not (EffectBudget.request(s, 10, 1, false, 5)))
end

do
	local s = EffectBudget.new()
	EffectBudget.request(s, 5, 200, false, 0)
	EffectBudget.request(s, 2, 150, false, 0)
	local _, evicted = EffectBudget.request(s, 9, 100, true, 1)
	t.eq("tie on start time evicts the smaller id", table.concat(evicted, ","), "2")
end

do
	local s = EffectBudget.new()
	EffectBudget.request(s, 1, 50, false, 0)
	local before = EffectBudget.stats(s)
	local ok, evicted = EffectBudget.request(s, 1, 50, false, 1)
	t.ok("repeat request returns true", ok)
	t.eq("repeat request evicts nothing", #evicted, 0)
	local after = EffectBudget.stats(s)
	t.ok("repeat request changes nothing", before.friendly == after.friendly and before.particles == after.particles)
end

do
	local s = EffectBudget.new()
	EffectBudget.release(s, 99)
	EffectBudget.request(s, 1, 50, false, 0)
	EffectBudget.release(s, 1)
	EffectBudget.release(s, 1)
	local st = EffectBudget.stats(s)
	t.ok("release is safe and counts never go negative", st.friendly == 0 and st.hostile == 0 and st.particles == 0)
end

do
	local s = three()
	local _, evicted = EffectBudget.request(s, 9, 160, true, 3)
	local before = EffectBudget.stats(s)
	EffectBudget.release(s, evicted[1] :: number)
	local after = EffectBudget.stats(s)
	t.ok("releasing an evicted id changes nothing", before.friendly == after.friendly and before.particles == after.particles)
end

do
	local s = EffectBudget.new()
	t.ok("zero-particle friendly is admitted", (EffectBudget.request(s, 1, 0, false, 0)))
	local st = EffectBudget.stats(s)
	t.ok("zero-particle friendly takes a slot and adds no particles", st.friendly == 1 and st.particles == 0)
end

do
	local s = EffectBudget.new()
	local ok = pcall(EffectBudget.request, s, 1, -1, false, 0)
	t.ok("negative particles fail", not ok)
end

t.done()
