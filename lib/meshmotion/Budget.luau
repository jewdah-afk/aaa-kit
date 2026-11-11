--!native
--!optimize 2
-- Budget: the two engine costs that hurt creature meshes, kept off the hot path.
--
-- 1. Build queue. `AssetService:CreateMeshPartAsync` costs ~22 ms + ~0.27 ms per 1k triangles
--    (docs/research/41-editablemesh-technique-cookbook.md). Jobs are queued and released only while the
--    estimated cost fits this frame's budget, so a reveal that spawns five creatures spreads over frames
--    instead of one 120 ms hitch. One job always runs per frame when the queue is non-empty, so a single job
--    bigger than the budget still makes progress.
-- 2. Dynamic pool. A non-FixedSize EditableMesh reserves the 60k-vertex worst case; keep about 8 live per
--    client. Creatures ask for a dynamic slot by priority (lower = closer/more important); when the pool is
--    full the lowest-priority holder is evicted (it falls back to its FixedSize/static mesh).
-- Pure Luau: jobs are plain functions, so lune tests run them headless.

local Budget = {}

Budget.BUILD_FIXED_MS = 22
Budget.BUILD_MS_PER_KTRI = 0.27

function Budget.buildCost(tris: number): number
	return Budget.BUILD_FIXED_MS + Budget.BUILD_MS_PER_KTRI * tris / 1000
end

-- Build queue ----------------------------------------------------------------------------------------------

export type Job = { tris: number, run: () -> (), priority: number }

function Budget.newQueue(frameMs: number?)
	return { frameMs = frameMs or 8, jobs = {} :: { Job }, built = 0 }
end

function Budget.push(q, job: Job)
	table.insert(q.jobs, job)
	table.sort(q.jobs, function(a, b)
		return a.priority < b.priority
	end)
end

-- Run jobs that fit this frame. Returns the estimated ms spent and the number of jobs run.
function Budget.stepQueue(q): (number, number)
	local spent, ran = 0, 0
	while #q.jobs > 0 do
		local c = Budget.buildCost(q.jobs[1].tris)
		if ran > 0 and spent + c > q.frameMs then
			break
		end
		local job = table.remove(q.jobs, 1)
		job.run()
		spent += c
		ran += 1
		q.built += 1
	end
	return spent, ran
end

-- Dynamic pool ---------------------------------------------------------------------------------------------

function Budget.newPool(max: number?)
	return { max = max or 8, holders = {} :: { [any]: number } }
end

function Budget.count(pool): number
	local n = 0
	for _ in pool.holders do
		n += 1
	end
	return n
end

-- Ask for a slot. Returns (granted, evicted?) — the caller downgrades `evicted` to its static mesh.
function Budget.acquire(pool, who: any, priority: number): (boolean, any?)
	if pool.holders[who] then
		pool.holders[who] = priority
		return true, nil
	end
	if Budget.count(pool) < pool.max then
		pool.holders[who] = priority
		return true, nil
	end
	local worst, worstP = nil, -math.huge
	for h, p in pool.holders do
		if p > worstP then
			worst, worstP = h, p
		end
	end
	if worst ~= nil and worstP > priority then
		pool.holders[worst] = nil
		pool.holders[who] = priority
		return true, worst
	end
	return false, nil
end

function Budget.release(pool, who: any)
	pool.holders[who] = nil
end

return Budget
