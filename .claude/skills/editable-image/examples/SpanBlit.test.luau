--!strict
local SpanBlit = require("./SpanBlit")
local t = require("../../../../tools/lib/t")

-- 10x2 sprite. Row 0: a 2-px run then an 8-px run. Row 1: fully empty.
local W, H = 10, 2
local px = buffer.create(W * H * 4)
local function set(x: number, y: number, c: number)
	buffer.writeu32(px, (y * W + x) * 4, c)
end
set(0, 0, 0xFF0000FF)
set(1, 0, 0xFF0000FF)
for x = 2, 9 do
	set(x, 0, 0xFF00FF00)
end
-- x=2..9 opaque, but break it at x=2 with transparency so runs are [0,2) and [3,10)
set(2, 0, 0x00000000)

local s = SpanBlit.sprite(W, H, px)
t.eq("row 0 has two runs", #s.spans[1], 4)
t.eq("first run", s.spans[1][1] * 100 + s.spans[1][2], 2)
t.eq("second run", s.spans[1][3] * 100 + s.spans[1][4], 307)
t.eq("empty row has no runs", #s.spans[2], 0)
t.eq("opaque count", s.opaque, 9)

local DW, DH = 16, 4
local dst = buffer.create(DW * DH * 4)
local n = SpanBlit.draw(dst, DW, DH, s, 3.7, 1.2) -- snaps to (3, 1)
t.eq("all opaque pixels written", n, 9)
t.eq("short run pixel", buffer.readu32(dst, (1 * DW + 3) * 4), 0xFF0000FF)
t.eq("gap left untouched", buffer.readu32(dst, (1 * DW + 5) * 4), 0)
t.eq("long run (buffer.copy) pixel", buffer.readu32(dst, (1 * DW + 12) * 4), 0xFF00FF00)

local dst2 = buffer.create(DW * DH * 4)
t.eq("clips left edge", SpanBlit.draw(dst2, DW, DH, s, -4, 0), 6)
t.eq("clips right edge", SpanBlit.draw(dst2, DW, DH, s, 12, 0), 3)
t.eq("fully off-screen", SpanBlit.draw(dst2, DW, DH, s, 0, 9), 0)

local d = SpanBlit.dirty()
local band = buffer.create(DW * DH * 4)
t.ok("clean frame uploads nothing", SpanBlit.band(d, dst, DW, band) == nil)
SpanBlit.mark(d, 1, 1, DH)
SpanBlit.mark(d, 2, 5, DH) -- clamps to last row
local y0, rows = SpanBlit.band(d, dst, DW, band)
t.eq("band start", y0, 1)
t.eq("band rows", rows, 3)
t.eq("band holds row 1 at offset 0", buffer.readu32(band, 3 * 4), 0xFF0000FF)
t.ok("tracker resets", SpanBlit.band(d, dst, DW, band) == nil)

t.done()
