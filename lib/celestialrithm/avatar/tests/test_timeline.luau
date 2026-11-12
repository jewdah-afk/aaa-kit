--!strict
-- lune run lib/celestialrithm/avatar/tests/test_timeline.luau
-- Pure tests for AuraTimeline + AuraConfig: phase order, transitions, onset brightness,
-- determinism, reduced-motion path, input guards and allocation-free stepping.

local AuraConfig = require("../AuraConfig")
local AuraTimeline = require("../AuraTimeline")
local process = require("@lune/process")

local passed, failed = 0, 0
local function check(name: string, ok: boolean, detail: string?)
	if ok then
		passed += 1
		print("ok   " .. name)
	else
		failed += 1
		print("FAIL " .. name .. "  " .. (detail or ""))
	end
end

local DT = 1 / 60
local EXPECTED = { "idle", "anticipation", "activation", "peak", "recovery", "settle" }

-- 1. Phase order and boundaries --------------------------------------------------------------------
do
	local tl = AuraTimeline.new(AuraConfig)
	local seen: { string } = {}
	local last = ""
	local frames = 0
	while not tl.out.done and frames < 10000 do
		local out = tl:step(DT)
		if out.phaseName ~= last then
			table.insert(seen, out.phaseName)
			last = out.phaseName
		end
		frames += 1
	end
	check("phases.order", table.concat(seen, ",") == table.concat(EXPECTED, ","), table.concat(seen, ","))
	local total = 0
	for _, p in AuraConfig.phases do
		total += p.duration
	end
	check("phases.total_duration", math.abs(tl:duration() - total) < 1e-9, tostring(tl:duration()))
	check("phases.frame_count", frames == math.ceil(total / DT - 1e-6), `{frames} frames`)
	check("phases.ends_done", tl.out.done and tl.out.phaseName == "settle" and tl.out.alpha == 1)

	-- boundaries: just before / at each phase end
	local acc = 0
	local okb = true
	for i, p in AuraConfig.phases do
		local before = tl:sample(acc + p.duration * 0.5)
		if before.phase ~= i then
			okb = false
		end
		acc += p.duration
		if i < #AuraConfig.phases then
			local at = tl:sample(acc + 1e-6)
			if at.phase ~= i + 1 or at.alpha > 0.01 then
				okb = false
			end
		end
	end
	check("phases.boundaries", okb)
end

-- 2. Onset is the brightest moment; idle is calm ----------------------------------------------------
do
	local tl = AuraTimeline.new(AuraConfig)
	local maxI, maxPhase, idleMax = -1, "", 0
	while not tl.out.done do
		local out = tl:step(DT)
		if out.intensity > maxI then
			maxI, maxPhase = out.intensity, out.phaseName
		end
		if out.phaseName == "idle" then
			idleMax = math.max(idleMax, out.intensity)
		end
	end
	check("onset.brightest_in_activation", maxPhase == "activation" and maxI >= 0.95, `{maxPhase} {maxI}`)
	check("idle.calm", idleMax <= 0.12, tostring(idleMax))
	local lastI = tl.out.intensity
	check("settle.returns_to_idle", math.abs(lastI - 0.10) < 1e-6, tostring(lastI))
end

-- 3. Determinism: same inputs -> bit-identical outputs; sample(t) agrees with step ------------------
do
	local a = AuraTimeline.new(AuraConfig)
	local b = AuraTimeline.new(AuraConfig)
	local same = true
	local agree = true
	local t = 0
	for _ = 1, 500 do
		local oa = a:step(DT)
		local ob = b:step(DT)
		t = oa.time
		if oa.intensity ~= ob.intensity or oa.orbitAngle ~= ob.orbitAngle or oa.shell ~= ob.shell or oa.phase ~= ob.phase then
			same = false
		end
	end
	check("determinism.identical_runs", same)
	-- a fresh timeline sampled directly at the same time gives the same non-integrated channels
	local c = AuraTimeline.new(AuraConfig)
	local probe = { 0.3, 1.9, 2.25, 2.3, 3.7, 5.2, 6.4 }
	for _, pt in probe do
		local s = c:sample(pt)
		local ref = AuraTimeline.new(AuraConfig)
		local r = ref:sample(pt)
		if s.intensity ~= r.intensity or s.shell ~= r.shell or s.phase ~= r.phase then
			agree = false
		end
	end
	check("determinism.sample_random_access", agree)
	check("determinism.time_clamped", t <= a:duration() + 1e-9, tostring(t))
end

-- 4. Reduced motion ---------------------------------------------------------------------------------
do
	local tl = AuraTimeline.new(AuraConfig, { reducedMotion = true })
	local hasAnticipation, maxI, maxOrbit, maxBurst = false, 0, 0, 0
	local angle0 = tl.out.orbitAngle
	while not tl.out.done do
		local out = tl:step(DT)
		if out.phaseName == "anticipation" then
			hasAnticipation = true
		end
		maxI = math.max(maxI, out.intensity)
		maxOrbit = math.max(maxOrbit, out.orbit)
		maxBurst = math.max(maxBurst, out.burst)
	end
	check("reduced.skips_anticipation", not hasAnticipation)
	check("reduced.intensity_cap", maxI <= AuraConfig.reducedMotion.intensityCap + 1e-9, tostring(maxI))
	check("reduced.no_orbit", maxOrbit == 0 and tl.out.orbitAngle == angle0, tostring(maxOrbit))
	check("reduced.no_burst", maxBurst == 0, tostring(maxBurst))
	local full = AuraTimeline.new(AuraConfig)
	check("reduced.shorter", tl:duration() < full:duration(), `{tl:duration()} vs {full:duration()}`)
end

-- 5. Rungs and guards -------------------------------------------------------------------------------
do
	local ceremony = AuraTimeline.new(AuraConfig, { rung = 3 })
	local maxI = 0
	while not ceremony.out.done do
		maxI = math.max(maxI, ceremony:step(DT).intensity)
	end
	check("rung.ceremony_suppresses", maxI == 0, tostring(maxI))

	local tl = AuraTimeline.new(AuraConfig)
	tl:step(0 / 0) -- NaN
	check("guard.nan_dt", tl.out.time == 0, tostring(tl.out.time))
	tl:step(-1)
	check("guard.negative_dt", tl.out.time == 0, tostring(tl.out.time))
	tl:step(10)
	check("guard.huge_dt_clamped", math.abs(tl.out.time - 0.25) < 1e-9, tostring(tl.out.time))
	local s = tl:sample(math.huge)
	check("guard.inf_sample_done", s.done and s.intensity == s.intensity, tostring(s.intensity))
	tl:restart()
	check("restart.resets", tl.out.time == 0 and tl.out.phaseName == "idle" and not tl.out.done)

	local okBad = pcall(function()
		AuraTimeline.new({
			phases = { { name = "x", duration = 1, intensity = { 0, 1 }, shell = { 1, 1 }, orbit = { 0, 0 }, ease = "wobble" } },
			reducedMotion = AuraConfig.reducedMotion,
			rungs = AuraConfig.rungs,
			burst = AuraConfig.burst,
			pulse = AuraConfig.pulse,
		})
	end)
	check("guard.unknown_ease_rejected", not okBad)
end

-- 6. Hot path returns the same table (no per-frame allocation of outputs) ---------------------------
do
	local tl = AuraTimeline.new(AuraConfig)
	local first = tl:step(DT)
	local sameTable = true
	for _ = 1, 300 do
		if tl:step(DT) ~= first then
			sameTable = false
		end
	end
	check("alloc.same_out_table", sameTable)
end

-- 7. Config sanity: every orbital/effect references a declared socket ------------------------------
do
	local sockets: { [string]: boolean } = {}
	for _, s in AuraConfig.sockets do
		sockets[s.name] = true
	end
	local ok = true
	for _, o in AuraConfig.orbitals do
		ok = ok and sockets[o.socket] == true
	end
	for _, tr in AuraConfig.effects.trails do
		ok = ok and sockets[tr.from] == true
	end
	for _, bm in AuraConfig.effects.beams do
		ok = ok and sockets[bm.from] == true and sockets[bm.to] == true
	end
	for _, p in AuraConfig.effects.particles do
		ok = ok and sockets[p.socket] == true
	end
	check("config.sockets_resolve", ok)
	local burstTotal = 0
	for _, p in AuraConfig.effects.particles do
		burstTotal += p.burst
	end
	check("config.particle_budget", burstTotal <= AuraConfig.budget.maxParticles, tostring(burstTotal))
end

print(`{passed} passed, {failed} failed`)
process.exit(if failed == 0 then 0 else 1)
