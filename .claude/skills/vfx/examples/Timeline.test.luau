--!strict
local t = require("../../../../tools/lib/t")
local Timeline = require("./Timeline")

local layers = {
	{ name = "A", start = 0, stop = 17 },
	{ name = "B", start = 18, stop = 29 },
	{ name = "C", start = 18, stop = 40 },
}

local function names(cues: { Timeline.Cue }): string
	local out = {}
	for _, c in cues do
		table.insert(out, `{c.kind}{if c.layer then ":" .. c.layer else ""}@{c.frame}`)
	end
	return table.concat(out, " ")
end

-- 60 fps steps: a cue at frame N fires on step N, never earlier, never later
do
	local tl = Timeline.new(layers, 18, 60)
	local firedAt: { [string]: number } = {}
	for step = 1, 70 do
		for _, c in tl:step(1 / 60) do
			firedAt[`{c.kind}{c.layer or ""}`] = step
		end
	end
	t.eq("A starts on step 1 (frame 0 is due at once)", firedAt.startA, 1)
	t.eq("A stops on frame 18", firedAt.stopA, 18)
	t.eq("hit fires on frame 18", firedAt.hit, 18)
	t.eq("B starts on frame 18", firedAt.startB, 18)
	t.eq("C stops on frame 41", firedAt.stopC, 41)
	t.eq("done fires on frame 61", firedAt.done, 61)
	t.ok("finished", tl:isDone())
end

-- Same frame: stop, then start, then hit
do
	local tl = Timeline.new(layers, 18, 60)
	local seen = ""
	for _ = 1, 18 do
		local cues = tl:step(1 / 60)
		if #cues > 0 then
			seen = names(cues)
		end
	end
	t.eq("order inside frame 18", seen, "stop:A@18 start:B@18 start:C@18 hit@18")
end

-- Cues never fire early or more than one step late at any frame rate
for _, fps in { 30, 60, 144, 240 } do
	local tl = Timeline.new(layers, 18, 60)
	local dt = 1 / fps
	local step, hitStep = 0, -1
	while not tl:isDone() and step < 100000 do
		step += 1
		for _, c in tl:step(dt) do
			if c.kind == "hit" then
				hitStep = step
			end
		end
	end
	local due = 18 / 60 -- seconds
	t.ok(`{fps} fps: hit not early`, hitStep * dt >= due - 1e-6)
	t.ok(`{fps} fps: hit within one step`, hitStep * dt <= due + dt + 1e-6)
end

-- A hitch fires every skipped cue, in order, in one step
do
	local tl = Timeline.new(layers, 18, 60)
	local cues = tl:step(2)
	t.eq("2 s hitch fires all cues", #cues, 2 * #layers + 2)
	t.eq("sorted by frame", cues[#cues].kind, "done")
	t.ok("done after a hitch", tl:isDone())
	t.eq("nothing fires after done", #tl:step(1 / 60), 0)
end

-- Hit-stop: timeScale 0 freezes the effect and resumes where it stopped
do
	local tl = Timeline.new(layers, 18, 60)
	for _ = 1, 10 do
		tl:step(1 / 60)
	end
	tl.timeScale = 0
	for _ = 1, 30 do
		t.eq("frozen: no cues", #tl:step(1 / 60), 0)
	end
	t.near("frozen at frame 10", tl.frame, 10, 1e-6)
	tl.timeScale = 1
	local hitStep = 0
	for step = 1, 20 do
		for _, c in tl:step(1 / 60) do
			if c.kind == "hit" then
				hitStep = step
			end
		end
	end
	t.eq("hit lands 8 steps after resume", hitStep, 8)
end

-- Bad dt is ignored, quiet frames allocate nothing
do
	local tl = Timeline.new(layers, 18, 60)
	tl:step(1 / 60)
	t.eq("negative dt ignored", #tl:step(-1), 0)
	t.eq("NaN dt ignored", #tl:step(math.huge - math.huge), 0)
	t.ok("quiet frames share one empty table", rawequal(tl:step(1 / 60), tl:step(1 / 60)))
end

t.near("seconds", Timeline.toSeconds(30), 0.5, 1e-9)
t.near("frames", Timeline.toFrames(0.5), 30, 1e-9)
t.done()
