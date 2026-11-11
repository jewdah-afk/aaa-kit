--!strict
-- PixelFrame: a hard-pixel frame with a colour buffer and an owner buffer (HIERARCHY.md §3).
-- Colour: RGBA8 in one buffer (4 bytes per pixel), the layout WritePixelsBuffer expects.
-- Owner: u8 per pixel, cleared every frame. A write only lands if the writer's rank may
-- cover the pixel's current owner (CAN table). Pure Luau buffers, so lune can test it.
--
-- In Roblox:
--   local img = AssetService:CreateEditableImage({ Size = Vector2.new(W, H) })
--   imageLabel.ImageContent = Content.fromObject(img)        -- ResampleMode = Pixelated
--   ... draw into frame ...
--   img:WritePixelsBuffer(Vector2.zero, Vector2.new(W, H), frame.color)  -- once per frame

local PixelFrame = {}
PixelFrame.__index = PixelFrame

PixelFrame.OWNER = table.freeze({
	BACKGROUND = 0, AMBIENT = 1, WORLD = 2, REWARD = 3, THREAT = 4, HERO = 5, UI = 6, CEREMONY = 7,
})
local O = PixelFrame.OWNER

-- CAN[writer][dest] = true when a writer of that rank may paint over that owner.
-- Default: anything at or above the destination. Hero FX never cover threat / UI / ceremony
-- (they're the same rank as hero, which is above threat, so that rule is explicit here).
local CAN: { { boolean } } = {}
for w = 0, 7 do
	CAN[w + 1] = {}
	for d = 0, 7 do
		CAN[w + 1][d + 1] = w >= d
	end
end
CAN[O.HERO + 1][O.THREAT + 1] = false -- friendly FX never hide a threat (§8)
PixelFrame.CAN = CAN

export type Frame = typeof(setmetatable({} :: { w: number, h: number, color: buffer, owner: buffer }, PixelFrame))

function PixelFrame.new(w: number, h: number): Frame
	return setmetatable({ w = w, h = h, color = buffer.create(w * h * 4), owner = buffer.create(w * h) }, PixelFrame)
end

-- Clears colour to one RGB value and owner to background. One fill each.
function PixelFrame.clear(self: Frame, r: number, g: number, b: number)
	local packed = bit32.bor(r, bit32.lshift(g, 8), bit32.lshift(b, 16), bit32.lshift(255, 24))
	local n = self.w * self.h
	for i = 0, n - 1 do
		buffer.writeu32(self.color, i * 4, packed)
	end
	buffer.fill(self.owner, 0, O.BACKGROUND)
end

-- Writes one pixel if the owner rule allows it. Returns true if it landed.
function PixelFrame.put(self: Frame, x: number, y: number, r: number, g: number, b: number, rank: number): boolean
	x, y = x // 1, y // 1 -- pixel snapping: integer coordinates only
	if x < 0 or y < 0 or x >= self.w or y >= self.h then
		return false
	end
	local i = y * self.w + x
	local dest = buffer.readu8(self.owner, i)
	if not CAN[rank + 1][dest + 1] then
		return false
	end
	buffer.writeu8(self.owner, i, rank)
	buffer.writeu32(self.color, i * 4, bit32.bor(r, bit32.lshift(g, 8), bit32.lshift(b, 16), 0xFF000000))
	return true
end

-- Filled rectangle through the same rule (clipped).
function PixelFrame.rect(self: Frame, x0: number, y0: number, w: number, h: number, r: number, g: number, b: number, rank: number): number
	local landed = 0
	for y = math.max(0, y0 // 1), math.min(self.h - 1, (y0 + h - 1) // 1) do
		for x = math.max(0, x0 // 1), math.min(self.w - 1, (x0 + w - 1) // 1) do
			if self:put(x, y, r, g, b, rank) then
				landed += 1
			end
		end
	end
	return landed
end

function PixelFrame.get(self: Frame, x: number, y: number): (number, number, number, number)
	local i = y * self.w + x
	local c = buffer.readu32(self.color, i * 4)
	return bit32.band(c, 0xFF), bit32.band(bit32.rshift(c, 8), 0xFF), bit32.band(bit32.rshift(c, 16), 0xFF), buffer.readu8(self.owner, i)
end

-- Fraction of the frame owned by a rank (for budgets like "friendly FX ≤ 40% of the play area").
function PixelFrame.coverage(self: Frame, rank: number): number
	local n, hit = self.w * self.h, 0
	for i = 0, n - 1 do
		if buffer.readu8(self.owner, i) == rank then
			hit += 1
		end
	end
	return hit / n
end

return PixelFrame
