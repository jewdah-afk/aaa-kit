--!strict
local t = require("../../../../tools/lib/t")
local Flipbook = require("./Flipbook")

local CELL, GRID, FRAMES = 32, 4, 16
local sheet = Flipbook.bake(CELL, GRID, FRAMES, Flipbook.ring)

t.eq("sheet is an exact multiple of the layout", sheet.size % GRID, 0)
t.eq("buffer is RGBA8", buffer.len(sheet.buf), sheet.size * sheet.size * 4)
t.eq("Grid4x4 holds 16 frames", Flipbook.GRIDS[16], 4)

-- frame rects
do
	local x0, y0 = Flipbook.rect(0, CELL, GRID)
	local x5, y5 = Flipbook.rect(5, CELL, GRID)
	local x15, y15 = Flipbook.rect(15, CELL, GRID)
	t.ok("frame 0 at the origin", x0 == 0 and y0 == 0)
	t.ok("frame 5 is column 1, row 1", x5 == CELL and y5 == CELL)
	t.ok("frame 15 is the last cell", x15 == 3 * CELL and y15 == 3 * CELL)
end

-- frame 0 reads on its own (low-memory phones show only that frame)
t.ok("frame 0 covers at least 5% of the cell", Flipbook.coverage(sheet, 0) >= 0.05)
t.ok("every frame but the last is visible (a one-shot ends empty)", (function()
	for f = 0, FRAMES - 2 do
		if Flipbook.coverage(sheet, f) <= 0 then
			return false
		end
	end
	return true
end)())

-- the 1 px margin of every cell is transparent, so filtering cannot bleed neighbouring frames
do
	local clean = true
	for f = 0, FRAMES - 1 do
		local ox, oy = Flipbook.rect(f, CELL, GRID)
		for i = 0, CELL - 1 do
			for _, p in { { i, 0 }, { i, CELL - 1 }, { 0, i }, { CELL - 1, i } } do
				if buffer.readu8(sheet.buf, ((oy + p[2]) * sheet.size + (ox + p[1])) * 4 + 3) ~= 0 then
					clean = false
				end
			end
		end
	end
	t.ok("cell margins are fully transparent", clean)
end

-- no residual alpha under 3/255 anywhere
do
	local residual = 0
	for i = 0, sheet.size * sheet.size - 1 do
		local a = buffer.readu8(sheet.buf, i * 4 + 3)
		if a > 0 and a < 3 then
			residual += 1
		end
	end
	t.eq("no residual alpha", residual, 0)
end

-- deterministic: same inputs, same bytes
do
	local again = Flipbook.bake(CELL, GRID, FRAMES, Flipbook.ring)
	t.ok("deterministic", buffer.tostring(again.buf) == buffer.tostring(sheet.buf))
end

-- the ring expands and thins: the late frame is dimmer than the middle one
t.ok("the effect fades by the last frame", Flipbook.coverage(sheet, FRAMES - 1) < Flipbook.coverage(sheet, 5))

-- frame stepping for ImageRectOffset
t.eq("Loop wraps", Flipbook.frameAt(16 / 24, 24, 16, "Loop"), 0)
t.eq("OneShot holds the last frame", Flipbook.frameAt(10, 24, 16, "OneShot"), 15)
t.eq("OneShot starts at 0", Flipbook.frameAt(0, 24, 16, "OneShot"), 0)
t.eq("PingPong turns round", Flipbook.frameAt(17 / 24, 24, 16, "PingPong"), 13)
t.eq("fps is capped at 30", Flipbook.frameAt(1, 120, 64, "OneShot"), 30)

t.done()
