--!strict
-- Attention director for animated material surfaces (EditableImage faces, keycaps, slots).
--
-- Loudness tiers 1-6 (HIERARCHY.md) are separate from research milestone labels (T12+).
-- Two jobs, both measured on the offline board (tools/celestialrithm/foundry/hierarchy_pass.py):
--   1. Rest calibration: each material has a contrast gain solved from a salience model so no
--      material accidentally owns a calm screen (data: tools/celestialrithm/foundry/loudness.json).
--   2. Handoff: one owner per moment. While a surface activates, it gains contrast and exposure and
--      every other surface sinks toward calm by the same envelope.
-- Pure Luau: no Roblox APIs, no allocation in Attention (writes into caller-owned arrays).

local H = {}

export type Event = { id: string, priority: number, start: number, duration: number, reducedMotion: boolean }

export type Shape = {
	ownerContrast: number,
	ownerExposure: number,
	othersContrast: number,
	othersExposure: number,
}

-- Same numbers as director.py (data, not logic).
H.DefaultShape = table.freeze({
	ownerContrast = 0.45,
	ownerExposure = 0.30,
	othersContrast = 0.45,
	othersExposure = 0.30,
}) :: Shape

export type Director = {
	active: Event?,
	calmUntil: number,
	maxFX: number,
	shape: Shape,
	gains: { [string]: number },
}

function H.new(gains: { [string]: number }?, shape: Shape?): Director
	return { active = nil, calmUntil = 0, maxFX = 1, shape = shape or H.DefaultShape, gains = gains or {} }
end

-- Offer an event; a lower-or-equal priority event cannot interrupt an active one.
function H.offer(self: Director, event: Event, now: number): boolean
	local a = self.active
	if a and now < (a.start + a.duration) and a.priority >= event.priority then
		return false
	end
	self.active = event
	self.calmUntil = now + event.duration + 0.2
	return true
end

-- Triangle-ish envelope 0..1 for the active event's own surface.
function H.intensity(self: Director, id: string, now: number): number
	local e = self.active
	if not e or e.id ~= id or e.reducedMotion or now >= e.start + e.duration then
		return 0
	end
	local x = math.clamp((now - e.start) / e.duration, 0, 1)
	return math.min(1, 4 * x, 4 * (1 - x))
end

-- Rest gain for a material id (1 when uncalibrated).
function H.gain(self: Director, materialId: string): number
	return self.gains[materialId] or 1
end

-- presses[i] in 0..1 -> contrastOut[i], exposureOut[i]. Caller owns the output arrays (no allocation).
function H.attention(self: Director, presses: { number }, contrastOut: { number }, exposureOut: { number })
	local s = self.shape
	local top = 0
	for i = 1, #presses do
		local p = math.clamp(presses[i], 0, 1)
		if p > top then
			top = p
		end
	end
	for i = 1, #presses do
		local w = math.clamp(presses[i], 0, 1)
		local other = math.max(top - w, 0)
		contrastOut[i] = (1 + s.ownerContrast * w) * (1 - s.othersContrast * other)
		exposureOut[i] = (1 + s.ownerExposure * w) * (1 - s.othersExposure * other)
	end
end

-- Apply contrast around a precomputed face mean, then exposure, to one linear channel value.
function H.grade(value: number, mean: number, gain: number, contrast: number, exposure: number): number
	return math.clamp((mean + (value - mean) * gain * contrast) * exposure, 0, 1)
end

return H
