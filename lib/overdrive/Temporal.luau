--!native
--!optimize 2
-- Temporal: spend work over time instead of every frame.
-- Measured (tools/vfxbench, warped fBm at 256², interpreter): every pixel 70 ms; checkerboard 33 ms;
-- one row in four 20 ms. Pair with feedback/history so the untouched pixels keep last frame's value.
--
-- Perception: smooth, low-frequency content (smoke, glow, energy fields) reads as continuous at 15-30 Hz;
-- hard edges and the player's own feedback want 60 Hz. Anime effects are held on twos/threes (12-20 fps) on
-- purpose: holds read as power, and they cost half or a third.

local Temporal = {}

-- Checkerboard: pixel (x, y) is drawn on frames where (x + y + frame) is even. Returns the first x for row y.
function Temporal.checkerStart(y: number, frame: number): number
	return (y + frame) % 2
end

-- Interlace: rows y where y % phases == frame % phases are drawn this frame.
function Temporal.rowStart(frame: number, phases: number): number
	return frame % phases
end

-- Hold time on a lower frame rate (on twos at 60 fps = 30, on threes = 20, anime 12): returns the quantised time
-- and whether the held frame changed since `lastT` (redraw only then).
function Temporal.hold(t: number, fps: number, lastT: number?): (number, boolean)
	local q = math.floor(t * fps) / fps
	return q, q ~= lastT
end

-- Stagger: spread effects over frames so a 20 Hz effect doesn't land on the same frame as every other 20 Hz
-- effect. Each effect gets a period (frames between updates: 1 = 60 Hz, 2 = 30 Hz, 3 = 20 Hz, 4 = 15 Hz) and the
-- phase with the least load so far. Load per frame is then level instead of spiking.
export type Stagger = { load: { number }, slots: { [string]: { period: number, phase: number, cost: number } }, span: number }

function Temporal.stagger(span: number?): Stagger
	local s = span or 12 -- lcm of 1, 2, 3, 4, 6, 12
	return { load = table.create(s, 0), slots = {}, span = s }
end

function Temporal.add(st: Stagger, name: string, period: number, cost: number?)
	local c = cost or 1
	local best, bestLoad = 0, math.huge
	for phase = 0, period - 1 do
		local worst = 0
		for f = phase, st.span - 1, period do
			worst = math.max(worst, st.load[f + 1] + c)
		end
		if worst < bestLoad then
			best, bestLoad = phase, worst
		end
	end
	for f = best, st.span - 1, period do
		st.load[f + 1] += c
	end
	st.slots[name] = { period = period, phase = best, cost = c }
end

-- Is `name` due on this frame?
function Temporal.due(st: Stagger, name: string, frame: number): boolean
	local s = st.slots[name]
	return s ~= nil and frame % s.period == s.phase
end

-- The worst frame's total cost (what the stagger buys you vs everything on frame 0).
function Temporal.peak(st: Stagger): number
	local m = 0
	for _, v in st.load do
		m = math.max(m, v)
	end
	return m
end

-- Exponential history: history = history + (new - history) * k, frame-rate independent: k = 1 - 0.5^(dt/halfLife).
function Temporal.blendFactor(dt: number, halfLife: number): number
	return 1 - 0.5 ^ (dt / halfLife)
end

return Temporal
