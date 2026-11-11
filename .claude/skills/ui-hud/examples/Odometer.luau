--!strict
-- Odometer: a rolling-digit counter model. Pure (no Instances), so the same code drives
-- a TextLabel row in Roblox, an EditableImage HUD, or a lune test.
--
-- Each slot holds the character it shows now, the one it is leaving and a 0..1 roll
-- progress. A slot only animates when its character changes, so a steady number is
-- perfectly still (HIERARCHY.md §6: calm frames stay calm).

local Odometer = {}
Odometer.__index = Odometer

local SUFFIXES = { "", "K", "M", "B", "T", "Qa", "Qi", "Sx", "Sp", "Oc", "No", "Dc" }

export type Slot = { cur: string, prev: string, p: number }
export type Odometer = typeof(setmetatable({} :: { width: number, speed: number, slots: { Slot } }, Odometer))

-- Three significant digits plus suffix, floored (never show more than the player has).
function Odometer.format(n: number): string
	if n ~= n or n < 0 then
		return "0"
	end
	if n < 1000 then
		return tostring(math.floor(n))
	end
	local i = 1
	while n >= 1000 and i < #SUFFIXES do
		n /= 1000
		i += 1
	end
	local s
	if n >= 100 then
		s = string.format("%d", math.floor(n))
	elseif n >= 10 then
		s = string.format("%.1f", math.floor(n * 10) / 10)
	else
		s = string.format("%.2f", math.floor(n * 100) / 100)
	end
	return s .. SUFFIXES[i]
end

-- width = number of character slots (right-aligned); speed = rolls per second (7 ≈ 140 ms)
function Odometer.new(width: number, speed: number?): Odometer
	local slots = {}
	for i = 1, width do
		slots[i] = { cur = " ", prev = " ", p = 1 }
	end
	return setmetatable({ width = width, speed = speed or 7, slots = slots }, Odometer)
end

-- Set the value; slots whose character changed restart their roll.
function Odometer.set(self: Odometer, value: number)
	local s = Odometer.format(value)
	s = string.rep(" ", math.max(0, self.width - #s)) .. s:sub(-self.width)
	for i = 1, self.width do
		local ch = s:sub(i, i)
		local slot = self.slots[i]
		if slot.cur ~= ch then
			slot.prev, slot.cur, slot.p = slot.cur, ch, 0
		end
	end
end

-- Advance the rolls. Returns true while anything is still moving (skip drawing when false).
function Odometer.step(self: Odometer, dt: number): boolean
	local moving = false
	for _, slot in self.slots do
		if slot.p < 1 then
			slot.p = math.min(1, slot.p + dt * self.speed)
			moving = moving or slot.p < 1
		end
	end
	return moving
end

-- Ease-out cubic for drawing: the new glyph slides up from below, the old one leaves upward.
-- Returns (prevOffset, curOffset) in glyph heights: draw prev at y - e, cur at y + (1 - e).
function Odometer.offsets(slot: Slot): (number, number)
	local e = 1 - (1 - slot.p) ^ 3
	return -e, 1 - e
end

-- Suffix letters get the currency colour; digits stay neutral (colour has one job).
function Odometer.isSuffix(ch: string): boolean
	return ch:match("%a") ~= nil
end

return Odometer
