--!native
--!optimize 2
-- Animator: keyframe clips on segments plus a distance-LOD scheduler for many animated creatures.
--
-- Clip = { length = seconds, loop = true?, tracks = { [segName] = { {t, rx?, ry?, rz?, tx?, ty?, tz?, s?}, ... } } }
-- Keys are sorted by t; missing channels are 0 (scale 1). Interpolation is smoothstep between keys, and a
-- looping clip wraps its last key back to the first.
--
-- Scheduler: each frame decides which instances re-skin. Tiers by camera distance (studs):
--   near  < 40   every frame
--   mid   < 100  every 2nd frame
--   far   < 200  every 4th frame
--   beyond 200 or off-screen: frozen (keeps its last pose)
-- Instances in the same tier are phase-spread (id mod interval) so they do not all land on one frame, and a
-- per-frame vertex budget caps the total skinned work; whatever is over budget waits, least recently served first.
-- Pure Luau.

local Animator = {}

local CHANNELS = { "rx", "ry", "rz", "tx", "ty", "tz", "s" }
local DEFAULT = { rx = 0, ry = 0, rz = 0, tx = 0, ty = 0, tz = 0, s = 1 }

Animator.TIERS = {
	{ dist = 40, every = 1 },
	{ dist = 100, every = 2 },
	{ dist = 200, every = 4 },
}

local function smooth(x: number): number
	return x * x * (3 - 2 * x)
end

local function keyValue(k, ch: string): number
	local v = k[ch]
	return if v == nil then DEFAULT[ch] else v
end

-- Write a clip's pose at time t into rig.pose (segments without a track are left untouched).
function Animator.sample(clip, rig, t: number)
	local len = clip.length
	if clip.loop ~= false then
		t = t % len
	else
		t = math.clamp(t, 0, len)
	end
	for segName, keys in clip.tracks do
		local p = rig:segment(segName)
		local n = #keys
		if n == 1 then
			for _, ch in CHANNELS do
				p[ch] = keyValue(keys[1], ch)
			end
			continue
		end
		-- find the key pair around t
		local a, b, u
		if t < keys[1].t then
			if clip.loop ~= false then
				a, b = keys[n], keys[1]
				local span = keys[1].t + len - keys[n].t
				u = (t + len - keys[n].t) / span
			else
				a, b, u = keys[1], keys[1], 0
			end
		elseif t >= keys[n].t then
			if clip.loop ~= false then
				a, b = keys[n], keys[1]
				local span = keys[1].t + len - keys[n].t
				u = if span > 0 then (t - keys[n].t) / span else 0
			else
				a, b, u = keys[n], keys[n], 0
			end
		else
			for i = 1, n - 1 do
				if t < keys[i + 1].t then
					a, b = keys[i], keys[i + 1]
					u = (t - a.t) / (b.t - a.t)
					break
				end
			end
		end
		u = smooth(math.clamp(u, 0, 1))
		for _, ch in CHANNELS do
			local va, vb = keyValue(a, ch), keyValue(b, ch)
			p[ch] = va + (vb - va) * u
		end
	end
end

-- Scheduler ------------------------------------------------------------------------------------------------

export type Entry = {
	id: number,
	verts: number,
	dist: number,
	visible: boolean,
	lastFrame: number, -- frame it last updated (-1 = never)
	lastTime: number,
	serial: number, -- order it was last served in (-1 = never)
}

function Animator.newScheduler(o: { vertexBudget: number? }?)
	return {
		budget = (o and o.vertexBudget) or 60000,
		frame = 0,
		entries = {} :: { Entry },
		nextId = 1,
		serial = 0,
	}
end

function Animator.add(sched, verts: number): Entry
	local e = { id = sched.nextId, verts = verts, dist = 0, visible = true, lastFrame = -1, lastTime = 0, serial = -1 }
	sched.nextId += 1
	table.insert(sched.entries, e)
	return e
end

function Animator.remove(sched, e: Entry)
	local i = table.find(sched.entries, e)
	if i then
		table.remove(sched.entries, i)
	end
end

function Animator.interval(dist: number, visible: boolean): number?
	if not visible then
		return nil
	end
	for _, tier in Animator.TIERS do
		if dist < tier.dist then
			return tier.every
		end
	end
	return nil
end

-- Returns the entries to update this frame (reused table), closest-overdue first, within the vertex budget.
-- The caller runs rig:update(now, now - e.lastTime) on each and the scheduler stamps lastTime.
local due: { Entry } = {}
function Animator.step(sched, now: number): { Entry }
	table.clear(due)
	local f = sched.frame
	for _, e in sched.entries do
		local every = Animator.interval(e.dist, e.visible)
		-- first update waits for its phase slot (spreads a tier across frames); after that, every `every` frames
		local isDue = if e.lastFrame < 0 then every ~= nil and (f + e.id) % every == 0 else every ~= nil and f - e.lastFrame >= every
		if isDue then
			table.insert(due, e)
		end
	end
	-- least recently served first (true round robin under the budget); never-served by distance
	table.sort(due, function(a, b)
		if a.serial ~= b.serial then
			return a.serial < b.serial
		end
		if a.dist ~= b.dist then
			return a.dist < b.dist
		end
		return a.id < b.id
	end)
	local used, keep = 0, 0
	for i = 1, #due do
		local e = due[i]
		if used + e.verts > sched.budget and keep > 0 then
			continue
		end
		used += e.verts
		keep += 1
		due[keep] = e
		e.lastFrame = f
		e.lastTime = now
		sched.serial += 1
		e.serial = sched.serial
	end
	for i = #due, keep + 1, -1 do
		due[i] = nil
	end
	sched.frame = f + 1
	return due
end

return Animator
