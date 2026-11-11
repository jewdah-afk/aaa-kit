-- meshmotion headless checks + timings. `lune run test_meshmotion.luau` from this folder; last line @@DONE <failures>.
local Out = require("../../frontier/qa/Out")
local Store = require("../Store")
local Rig = require("../Rig")
local Deform = require("../Deform")
local Animator = require("../Animator")
local Budget = require("../Budget")
local Creature = require("../Creature")

local function near(a: number, b: number, eps: number?): boolean
	return math.abs(a - b) <= (eps or 1e-4)
end

-- Synthetic voxel creature: boxes per segment, a 4-link tail chain, fins, a jiggly crystal.
local function box(bp, seg: string, cx, cy, cz, sx, sy, sz, w: number?)
	local base = #bp.verts // 3
	for i = 0, 7 do
		local x = cx + (if bit32.band(i, 1) ~= 0 then sx else -sx) / 2
		local y = cy + (if bit32.band(i, 2) ~= 0 then sy else -sy) / 2
		local z = cz + (if bit32.band(i, 4) ~= 0 then sz else -sz) / 2
		table.insert(bp.verts, x); table.insert(bp.verts, y); table.insert(bp.verts, z)
		table.insert(bp.vseg, seg)
		table.insert(bp.weights, w or 0)
	end
	local faces = { { 0, 2, 3, 1 }, { 4, 5, 7, 6 }, { 0, 1, 5, 4 }, { 2, 6, 7, 3 }, { 0, 4, 6, 2 }, { 1, 3, 7, 5 } }
	for _, f in faces do
		for _, t in { { 1, 2, 3 }, { 1, 3, 4 } } do
			for _, k in t do
				table.insert(bp.tris, base + f[k])
			end
		end
	end
end

local function creatureBlueprint(subdiv: number?)
	local bp = { name = "TestBeast", verts = {}, tris = {}, vseg = {}, weights = {}, segments = {
		-- deliberately out of order: Store must sort parents first
		{ name = "Tail2", parent = "Tail1", pivot = { 0, 1, 4 } },
		{ name = "Body", pivot = { 0, 1, 0 } },
		{ name = "Tail1", parent = "Body", pivot = { 0, 1, 2 } },
		{ name = "Tail3", parent = "Tail2", pivot = { 0, 1, 6 } },
		{ name = "Tail4", parent = "Tail3", pivot = { 0, 1, 8 } },
		{ name = "FinL", parent = "Body", pivot = { -1, 1, 0 } },
		{ name = "FinR", parent = "Body", pivot = { 1, 1, 0 } },
		{ name = "Crystal", parent = "Body", pivot = { 0, 2, 0 } },
	} }
	local reps = subdiv or 1
	for r = 0, reps - 1 do
		local j = r * 0.001
		box(bp, "Body", j, 1, 0, 2, 2, 4)
		for k = 1, 4 do
			box(bp, "Tail" .. k, j, 1, 2 * k + 1, 1, 1, 2)
		end
		box(bp, "FinL", -1.5 + j, 1, 0, 1, 0.25, 1)
		box(bp, "FinR", 1.5 + j, 1, 0, 1, 0.25, 1)
		box(bp, "Crystal", j, 2.5, 0, 0.5, 1, 0.5, 1)
	end
	return bp
end

local data = Store.fromBlueprint(creatureBlueprint())
local rd = buffer.readf32
local function pos(buf: buffer, v: number): (number, number, number)
	return rd(buf, v * 12), rd(buf, v * 12 + 4), rd(buf, v * 12 + 8)
end

-- Store ----------------------------------------------------------------------------------------------------
Out.check("store.counts", data.n == 64 and data.triCount == 96, `{data.n} verts {data.triCount} tris`)
local order = {}
for i, s in data.segments do
	order[s.name] = i
	if s.parent then
		assert(s.parent < i, "parent after child")
	end
end
Out.check("store.parents_first", order.Body < order.Tail1 and order.Tail1 < order.Tail2 and order.Tail3 < order.Tail4)
Out.check("store.rejects_cycle", not pcall(Store.fromBlueprint, {
	verts = { 0, 0, 0 }, tris = {}, vseg = { "A" },
	segments = { { name = "A", parent = "B" }, { name = "B", parent = "A" } },
}))
Out.check("store.rejects_bad_index", not pcall(Store.fromBlueprint, {
	verts = { 0, 0, 0 }, tris = { 0, 0, 5 }, vseg = { "A" }, segments = { { name = "A" } },
}))
local loads = 0
local a1 = Store.acquire("beast", function() loads += 1 return creatureBlueprint() end)
local a2 = Store.acquire("beast", function() loads += 1 return creatureBlueprint() end)
Out.check("store.shared", a1 == a2 and loads == 1 and Store.refs("beast") == 2)
Store.release("beast"); Store.release("beast")
Out.check("store.freed", Store.refs("beast") == 0)

-- Rig ------------------------------------------------------------------------------------------------------
local rig = Rig.new(data)
rig:update(0, 0)
local maxErr = 0
for v = 0, data.n - 1 do
	local x, y, z = pos(rig.out, v)
	local rx, ry, rz = pos(data.rest, v)
	maxErr = math.max(maxErr, math.abs(x - rx), math.abs(y - ry), math.abs(z - rz))
end
Out.check("rig.identity", maxErr < 1e-5, `max err {maxErr}`)

-- pivot stays fixed under its own rotation
rig:segment("FinL").rz = 0.7
rig:solve()
local px, py, pz = rig:transformPoint("FinL", -1, 1, 0)
Out.check("rig.pivot_fixed", near(px, -1) and near(py, 1) and near(pz, 0))

-- hierarchy: rotating Body 90 deg around Y swings the tail tip pivot from +z to +x
rig:resetPose()
rig:segment("Body").ry = math.pi / 2
rig:solve()
local tx, ty, tz = rig:transformPoint("Tail4", 0, 1, 8)
Out.check("rig.parent_chain", near(tx, 8, 1e-3) and near(ty, 1) and near(tz, 0, 1e-3), `{tx},{ty},{tz}`)

-- chained bends accumulate: each tail link bent 0.2 rad -> tip direction 0.8 rad
rig:resetPose()
for k = 1, 4 do
	rig:segment("Tail" .. k).ry = 0.2
end
rig:solve()
local ax, _, az = rig:transformPoint("Tail4", 0, 1, 8)
local bx, _, bz = rig:transformPoint("Tail4", 0, 1, 10)
Out.check("rig.chain_accumulates", near(math.atan2(bx - ax, bz - az), 0.8, 1e-3))

-- translation + scale
rig:resetPose()
rig:segment("Crystal").s = 2
rig:segment("Crystal").ty = 1
rig:solve()
local _, cy = rig:transformPoint("Crystal", 0, 3, 0)
Out.check("rig.scale_about_pivot", near(cy, 2 + 1 + 2), `{cy}`)

-- Deform ---------------------------------------------------------------------------------------------------
local function bboxVolume(buf: buffer): number
	local mn, mx = { math.huge, math.huge, math.huge }, { -math.huge, -math.huge, -math.huge }
	for v = 0, data.n - 1 do
		local p = { pos(buf, v) }
		for k = 1, 3 do
			mn[k], mx[k] = math.min(mn[k], p[k]), math.max(mx[k], p[k])
		end
	end
	return (mx[1] - mn[1]) * (mx[2] - mn[2]) * (mx[3] - mn[3]), mn[2]
end
rig:resetPose()
rig:update(0, 0)
local v0 = bboxVolume(rig.out)
rig:update(0.25, 0, { Deform.squash({ amount = 0.3, freq = 1 }) })
local v1, footY = bboxVolume(rig.out)
Out.check("deform.squash_volume", near(v1 / v0, 1, 1e-3) and near(footY, data.bounds.min[2]), `ratio {v1 / v0}`)

local wave = Deform.wave({ amp = 0.5, wavelength = 4, speed = 1, from = 2, to = 10, segments = { "Tail1", "Tail2", "Tail3", "Tail4" } })
rig:update(0.3, 0, { wave })
local bodyStill, tailMoved = true, false
for v = 0, data.n - 1 do
	local x = pos(rig.out, v)
	local rx = pos(data.rest, v)
	local segName = data.segments[buffer.readu16(data.seg, v * 2)].name
	if segName == "Body" and not near(x, rx) then
		bodyStill = false
	end
	if segName == "Tail4" and math.abs(x - rx) > 0.05 then
		tailMoved = true
	end
end
Out.check("deform.wave_masked", bodyStill and tailMoved)

local tw = Deform.twist({ rate = 0.5, speed = 0.25, segments = { "Crystal" } })
rig:update(1, 0, { tw })
local cv = 58 -- a top Crystal vertex (7th box, corner 2: y = 3)
local x0, _, z0 = pos(data.rest, cv)
local x1, _, z1 = pos(rig.out, cv)
Out.check("deform.twist_keeps_radius", near(x0 * x0 + z0 * z0, x1 * x1 + z1 * z1, 1e-3) and not near(x0, x1))

-- jiggle: crystal (weight 1) lags behind a sudden body move, body (weight 0) does not, then settles
local jr = Rig.new(data)
local jig = Deform.jiggle({ stiffness = 300, damping = 18 })
jr:update(0, 1 / 60, { jig })
jr:segment("Body").tx = 1
jr:update(1 / 60, 1 / 60, { jig })
local bxp = pos(jr.out, 0)
local cxp = pos(jr.out, cv)
local cxr = pos(data.rest, cv)
Out.check("deform.jiggle_lags", near(bxp, pos(data.rest, 0) + 1) and (cxp - cxr) < 0.9, `crystal moved {cxp - cxr}`)
for f = 2, 180 do
	jr:update(f / 60, 1 / 60, { jig })
end
Out.check("deform.jiggle_settles", near(pos(jr.out, cv) - cxr, 1, 1e-2))

-- determinism of the pure deformers
local function snapshot(t: number): string
	local r = Rig.new(data)
	r:update(t, 0, { Deform.bob({ amp = 0.2, freq = 1 }), wave, tw })
	return buffer.tostring(r.out)
end
Out.check("deform.deterministic", snapshot(0.77) == snapshot(0.77))

-- Animator -------------------------------------------------------------------------------------------------
local clip = { length = 2, tracks = {
	FinL = { { t = 0, rz = 0 }, { t = 1, rz = 1 } },
	Body = { { t = 0.5, ty = 0.4 } },
} }
local ar = Rig.new(data)
Animator.sample(clip, ar, 0)
local fin = ar:segment("FinL")
Out.check("anim.key0", near(fin.rz, 0) and near(ar:segment("Body").ty, 0.4))
Animator.sample(clip, ar, 0.5)
Out.check("anim.mid_smooth", near(fin.rz, 0.5))
Animator.sample(clip, ar, 1.5)
Out.check("anim.loop_wraps", near(fin.rz, 0.5), `{fin.rz}`)
Animator.sample(clip, ar, 2)
Out.check("anim.loop_period", near(fin.rz, 0))
Animator.sample({ length = 2, loop = false, tracks = clip.tracks }, ar, 5)
Out.check("anim.clamp", near(fin.rz, 1))

-- scheduler tiers and phase spread
local sched = Animator.newScheduler({ vertexBudget = 1e9 })
local nearE, midE, farE, goneE = Animator.add(sched, 100), Animator.add(sched, 100), Animator.add(sched, 100), Animator.add(sched, 100)
nearE.dist, midE.dist, farE.dist, goneE.dist = 10, 60, 150, 500
local counts = { [nearE] = 0, [midE] = 0, [farE] = 0, [goneE] = 0 }
for f = 1, 400 do
	for _, e in Animator.step(sched, f / 60) do
		counts[e] += 1
	end
end
Out.check("sched.tiers", counts[nearE] == 400 and near(counts[midE], 200, 1) and near(counts[farE], 100, 1) and counts[goneE] == 0,
	`{counts[nearE]} {counts[midE]} {counts[farE]} {counts[goneE]}`)

-- 40 far creatures spread evenly: no frame updates more than ceil(40/4)+1
local s2 = Animator.newScheduler({ vertexBudget = 1e9 })
for _ = 1, 40 do
	Animator.add(s2, 100).dist = 150
end
local peak = 0
for f = 1, 64 do
	peak = math.max(peak, #Animator.step(s2, f / 60))
end
Out.check("sched.phase_spread", peak <= 11, `peak {peak}`)

-- vertex budget: 10 near creatures of 10k verts with a 30k budget -> 3 per frame, everyone served in turn
local s3 = Animator.newScheduler({ vertexBudget = 30000 })
local served = {}
for i = 1, 10 do
	local e = Animator.add(s3, 10000)
	e.dist = 5
	served[e] = 0
end
local over = false
for f = 1, 100 do
	local due = Animator.step(s3, f / 60)
	local sum = 0
	for _, e in due do
		sum += e.verts
		served[e] += 1
	end
	over = over or sum > 30000
end
local minS, maxS = math.huge, 0
for _, c in served do
	minS, maxS = math.min(minS, c), math.max(maxS, c)
end
Out.check("sched.budget_fair", not over and maxS - minS <= 1, `min {minS} max {maxS}`)

-- Budget ---------------------------------------------------------------------------------------------------
Out.check("budget.cost_model", near(Budget.buildCost(10000), 24.7))
local q = Budget.newQueue(30)
local done = 0
for i = 1, 5 do
	Budget.push(q, { tris = 2000, priority = i, run = function() done += 1 end })
end
local frames = 0
while #q.jobs > 0 do
	local spent = Budget.stepQueue(q)
	frames += 1
	assert(spent <= 30 or frames == 1, "queue over budget")
end
Out.check("budget.queue_spreads", done == 5 and frames == 5, `{frames} frames`)
local big = Budget.newQueue(8)
Budget.push(big, { tris = 20000, priority = 0, run = function() end })
local _, ran = Budget.stepQueue(big)
Out.check("budget.queue_progress", ran == 1)

local pool = Budget.newPool(8)
for i = 1, 8 do
	assert(Budget.acquire(pool, "c" .. i, i), "pool slot")
end
local okFar = Budget.acquire(pool, "far", 99)
local okNear, evicted = Budget.acquire(pool, "near", 0)
Out.check("budget.pool_cap", not okFar and okNear and evicted == "c8" and Budget.count(pool) == 8)

-- Creature + hooks -----------------------------------------------------------------------------------------
local presented, hookT = 0, -1
local cr = Creature.new(data, { clip = clip, deformers = { Deform.bob({ amp = 0.1, freq = 2 }) }, present = function() presented += 1 end })
cr:onFrame(function(t) hookT = t end)
for _ = 1, 10 do
	cr:step(1 / 60)
end
Out.check("creature.step", presented == 10 and near(hookT, 10 / 60))

-- Timings --------------------------------------------------------------------------------------------------
local bigData = Store.fromBlueprint(creatureBlueprint(80)) -- 5120 verts, 7680 tris
local br = Rig.new(bigData)
local stack = { Deform.squash({ amount = 0.05, freq = 1 }), Deform.wave({ amp = 0.3, wavelength = 4, speed = 1, segments = { "Tail1", "Tail2", "Tail3", "Tail4" } }), Deform.jiggle({ stiffness = 300, damping = 18 }) }
local t = 0
Out.time("meshmotion.skin_5k", 200, function()
	t += 1 / 60
	br:update(t, 0)
end)
Out.time("meshmotion.skin_deform_5k", 200, function()
	t += 1 / 60
	br:update(t, 1 / 60, stack)
end)
local s4 = Animator.newScheduler()
for i = 1, 200 do
	Animator.add(s4, 2000).dist = i
end
Out.time("meshmotion.schedule_200", 500, function()
	Animator.step(s4, 0)
end)

Out.done()
