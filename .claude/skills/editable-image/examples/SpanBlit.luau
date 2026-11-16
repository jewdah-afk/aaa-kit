--!strict
-- SpanBlit: the two cheapest moves in an interpreted EditableImage renderer.
--
-- 1. Sprites as precomputed opaque row spans. At load, each sprite row becomes a list of
--    (x0, length) runs of opaque pixels. Drawing copies long runs with buffer.copy and writes
--    short runs pixel by pixel: in the interpreter buffer.copy/fill cost ~50 ns per call while
--    readu32/writeu32 cost ~5-10 ns, so runs of SHORT_RUN pixels or fewer are cheaper written directly.
-- 2. Dirty rows. Track the min/max row touched this frame and upload only that band with
--    WritePixelsBuffer(Vector2.new(0, y0), Vector2.new(W, rows), bandBuffer).
--
-- Pure Luau, no Roblox calls, so it runs under lune. Pixels are RGBA8 straight alpha (WritePixelsBuffer layout).

local SpanBlit = {}

SpanBlit.SHORT_RUN = 7 -- measured crossover in the interpreter; re-measure on your target

export type Sprite = {
	w: number,
	h: number,
	pixels: buffer, -- w*h*4 RGBA8
	spans: { { number } }, -- spans[row+1] = { x0, len, x0, len, ... }
	opaque: number, -- opaque pixel count (for coverage budgets)
}

-- Bake spans once at load. Alpha < 128 counts as empty (hard-pixel art has no partial alpha).
function SpanBlit.sprite(w: number, h: number, pixels: buffer): Sprite
	local spans = table.create(h)
	local opaque = 0
	for y = 0, h - 1 do
		local row = {}
		local x = 0
		while x < w do
			while x < w and buffer.readu8(pixels, (y * w + x) * 4 + 3) < 128 do
				x += 1
			end
			local x0 = x
			while x < w and buffer.readu8(pixels, (y * w + x) * 4 + 3) >= 128 do
				x += 1
			end
			if x > x0 then
				table.insert(row, x0)
				table.insert(row, x - x0)
				opaque += x - x0
			end
		end
		spans[y + 1] = row
	end
	return { w = w, h = h, pixels = pixels, spans = spans, opaque = opaque }
end

-- Draw a sprite at integer (px, py) into dst (dw x dh RGBA8), clipped. Returns pixels written.
function SpanBlit.draw(dst: buffer, dw: number, dh: number, s: Sprite, px: number, py: number): number
	px, py = px // 1, py // 1
	local src, sw = s.pixels, s.w
	local readu32, writeu32, copy = buffer.readu32, buffer.writeu32, buffer.copy
	local short = SpanBlit.SHORT_RUN
	local written = 0
	local y0 = math.max(0, -py)
	local y1 = math.min(s.h - 1, dh - 1 - py)
	for sy = y0, y1 do
		local row = s.spans[sy + 1]
		local dy = py + sy
		for i = 1, #row, 2 do
			local a = row[i]
			local b = a + row[i + 1] -- exclusive
			-- clip the run against the destination
			if px + a < 0 then
				a = -px
			end
			if px + b > dw then
				b = dw - px
			end
			local n = b - a
			if n > 0 then
				local so = (sy * sw + a) * 4
				local d = (dy * dw + px + a) * 4
				if n <= short then
					for k = 0, n - 1 do
						writeu32(dst, d + k * 4, readu32(src, so + k * 4))
					end
				else
					copy(dst, d, src, so, n * 4)
				end
				written += n
			end
		end
	end
	return written
end

-- Dirty-row tracker for partial uploads.
export type Dirty = { y0: number, y1: number }

function SpanBlit.dirty(): Dirty
	return { y0 = math.huge, y1 = -1 }
end

function SpanBlit.mark(d: Dirty, y: number, h: number, dh: number)
	d.y0 = math.max(0, math.min(d.y0, y // 1))
	d.y1 = math.min(dh - 1, math.max(d.y1, (y + h - 1) // 1))
end

-- Copies the dirty band into `band` (reused, sized dw*dh*4) and returns (y0, rows), or nil when clean.
-- Roblox: img:WritePixelsBuffer(Vector2.new(0, y0), Vector2.new(dw, rows), band)
-- (WritePixelsBuffer reads the buffer from offset 0, so the band must start at byte 0.)
function SpanBlit.band(d: Dirty, src: buffer, dw: number, band: buffer): (number?, number?)
	if d.y1 < d.y0 then
		return nil, nil
	end
	local y0, rows = d.y0, d.y1 - d.y0 + 1
	buffer.copy(band, 0, src, y0 * dw * 4, rows * dw * 4)
	d.y0, d.y1 = math.huge, -1
	return y0, rows
end

return SpanBlit
