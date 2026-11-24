--!strict
-- Timeline: frame-accurate cues for one effect, driven by ONE per-frame callback (RunService.PreRender).
--
-- Why not task.wait / task.delay chains or tween.Completed hops: each hop resumes on a later frame than asked, the error
-- adds up along the chain, and the order of two cues in the same frame is up to the scheduler. Here the effect owns one
-- clock counted in 60 fps FRAMES, so a cue at frame 18 fires on the first step whose clock reaches 18, whatever dt is:
--   * a hitch fires every cue it skipped, in order, in one step (catch-up, nothing is lost or reordered);
--   * timeScale = 0 freezes the effect (hit-stop) and resumes exactly where it stopped;
--   * at one frame, "stop" cues fire before "start" cues, then "hit", then "done".
--
-- A layer is visible on frames start..stop, so its "stop" cue fires on frame stop + 1.

local Timeline = {}
Timeline.__index = Timeline

export type Cue = { frame: number, kind: "stop" | "start" | "hit" | "done", layer: string? }
export type Timed = { name: string, start: number, stop: number }

export type Timeline = typeof(setmetatable({} :: {
	cues: { Cue },
	nextCue: number,
	frame: number,
	timeScale: number,
}, Timeline))

Timeline.FPS = 60
local EPS = 1e-6 -- frames; absorbs float error from summing many dt values
local NONE: { Cue } = table.freeze({})
local RANK = { stop = 1, start = 2, hit = 3, done = 4 }

function Timeline.toFrames(seconds: number): number
	return seconds * Timeline.FPS
end

function Timeline.toSeconds(frames: number): number
	return frames / Timeline.FPS
end

function Timeline.new(layers: { Timed }, hitFrame: number, duration: number): Timeline
	local cues: { Cue } = {}
	for _, L in layers do
		table.insert(cues, { frame = L.start, kind = "start", layer = L.name })
		table.insert(cues, { frame = L.stop + 1, kind = "stop", layer = L.name })
	end
	table.insert(cues, { frame = hitFrame, kind = "hit" })
	table.insert(cues, { frame = duration + 1, kind = "done" })
	local order: { [Cue]: number } = {}
	for i, c in cues do
		order[c] = i
	end
	table.sort(cues, function(a: Cue, b: Cue): boolean
		if a.frame ~= b.frame then
			return a.frame < b.frame
		end
		if a.kind ~= b.kind then
			return RANK[a.kind] < RANK[b.kind]
		end
		return order[a] < order[b]
	end)
	return setmetatable({ cues = cues, nextCue = 1, frame = 0, timeScale = 1 }, Timeline)
end

-- Advance by dt real seconds. Returns the cues that came due (a shared empty table when none did, so a quiet frame
-- allocates nothing). Effects keep real dt; scale it down only for hit-stop (HIERARCHY.md §9).
function Timeline.step(self: Timeline, dt: number): { Cue }
	if not (dt > 0) or self.nextCue > #self.cues then
		return NONE
	end
	self.frame += dt * Timeline.FPS * self.timeScale
	local due: { Cue }? = nil
	while self.nextCue <= #self.cues and self.cues[self.nextCue].frame <= self.frame + EPS do
		due = due or {}
		table.insert(due :: { Cue }, self.cues[self.nextCue])
		self.nextCue += 1
	end
	return due or NONE
end

function Timeline.isDone(self: Timeline): boolean
	return self.nextCue > #self.cues
end

-- Seconds of effect time elapsed (frames / 60), for tween lengths and audio offsets.
function Timeline.seconds(self: Timeline): number
	return self.frame / Timeline.FPS
end

return Timeline
