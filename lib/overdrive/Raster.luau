--!native
--!optimize 2
-- Raster: draw with memory copies instead of per-pixel loops.
-- Measured (tools/vfxbench, interpreter): a doubling fill clears 480x270 ~140x faster than a writeu32 loop;
-- opaque-run sprite blits are ~9x faster than an alpha test per pixel; row spans fill discs ~7x faster.
-- Every function here draws exactly the pixels the naive loop would (qa/test_raster.luau proves it).
-- Canvases are RGBA8 buffers in EditableImage:WritePixelsBuffer layout (R at +0, A at +3); fields are u8 buffers.

local Raster = {}

local readu8, writeu8, readu32, writeu32 = buffer.readu8, buffer.writeu8, buffer.readu32, buffer.writeu32
local bcopy, bfill, bcreate = buffer.copy, buffer.fill, buffer.create
local min, max, floor, exp = math.min, math.max, math.floor, math.exp

-- Fill `count` pixels starting at pixel `first` with one colour: one write, then log2(count) self-copies.
function Raster.fill(dst: buffer, colour: number, first: number?, count: number?)
	local o = (first or 0) * 4
	local total = (count or (buffer.len(dst) - o) // 4) * 4
	if total <= 0 then
		return
	end
	writeu32(dst, o, colour)
	local done = 4
	while done < total do
		local n = min(done, total - done)
		bcopy(dst, o + done, dst, o, n)
		done += n
	end
end

------------------------------------------------------------------------------------------------
-- Runs: the opaque horizontal spans of a sprite, found once at load. Drawing is one memcpy per span.

export type Runs = {
	w: number,
	h: number,
	src: buffer, -- the sprite, RGBA8, w*h
	list: { number }, -- flat triples: row, x0, length
	count: number, -- number of runs
	opaque: number, -- opaque pixels (for budgeting)
}

-- alphaMin: a pixel counts as opaque when its alpha byte >= alphaMin (default 1).
function Raster.runs(src: buffer, w: number, h: number, alphaMin: number?): Runs
	local amin = alphaMin or 1
	local list = {}
	local opaque = 0
	for y = 0, h - 1 do
		local x = 0
		while x < w do
			if readu8(src, (y * w + x) * 4 + 3) >= amin then
				local x0 = x
				while x < w and readu8(src, (y * w + x) * 4 + 3) >= amin do
					x += 1
				end
				list[#list + 1] = y
				list[#list + 1] = x0
				list[#list + 1] = x - x0
				opaque += x - x0
			else
				x += 1
			end
		end
	end
	return { w = w, h = h, src = src, list = list, count = #list // 3, opaque = opaque }
end

-- Blit at (ox, oy), clipped to the canvas. own/tier: optional owner buffer (1 byte per pixel) to tag,
-- the way cursed-survivors' owner tiers work; tagging a span is one buffer.fill.
function Raster.blitRuns(dst: buffer, dw: number, dh: number, r: Runs, ox: number, oy: number, own: buffer?, tier: number?)
	local list, src, sw = r.list, r.src, r.w
	if ox >= dw or oy >= dh or ox + sw <= 0 or oy + r.h <= 0 then
		return
	end
	local clipped = ox < 0 or oy < 0 or ox + sw > dw or oy + r.h > dh
	for k = 1, #list, 3 do
		local y, x0, len = list[k], list[k + 1], list[k + 2]
		local Y = oy + y
		local X = ox + x0
		if clipped then
			if Y < 0 or Y >= dh then
				continue
			end
			if X < 0 then
				len += X
				x0 -= X
				X = 0
			end
			if X + len > dw then
				len = dw - X
			end
			if len <= 0 then
				continue
			end
		end
		local d = Y * dw + X
		bcopy(dst, d * 4, src, (y * sw + x0) * 4, len * 4)
		if own then
			bfill(own, d, tier or 0, len)
		end
	end
end

------------------------------------------------------------------------------------------------
-- Spans: a filled shape stored as one half-width per row (symmetric shapes: discs, ellipses, diamonds).

-- Half-widths of a disc of radius r: half[dy + r + 1] = largest dx with dx²+dy² <= r² (r is an integer).
function Raster.discSpans(r: number): { number }
	local half = table.create(2 * r + 1)
	for dy = -r, r do
		local h = -1
		for dx = 0, r do
			if dx * dx + dy * dy <= r * r then
				h = dx
			end
		end
		half[dy + r + 1] = h
	end
	return half
end

-- One reusable row of a colour to copy spans from (grown on demand).
local rowBuf = bcreate(4)
local rowColour, rowLen = -1, 1

local function colourRow(colour: number, len: number): buffer
	if colour ~= rowColour or len > rowLen then
		local n = max(len, rowLen)
		if n > rowLen then
			rowBuf = bcreate(n * 4)
			rowLen = n
		end
		Raster.fill(rowBuf, colour, 0, rowLen)
		rowColour = colour
	end
	return rowBuf
end

-- Fill a span shape centred on (cx, cy) with an opaque colour, clipped.
function Raster.fillSpans(dst: buffer, dw: number, dh: number, half: { number }, cx: number, cy: number, colour: number)
	local r = (#half - 1) // 2
	local row = colourRow(colour, 2 * r + 1)
	for dy = -r, r do
		local Y = cy + dy
		local h = half[dy + r + 1]
		if h >= 0 and Y >= 0 and Y < dh then
			local x0, x1 = max(0, cx - h), min(dw - 1, cx + h)
			if x1 >= x0 then
				bcopy(dst, (Y * dw + x0) * 4, row, 0, (x1 - x0 + 1) * 4)
			end
		end
	end
end

-- An annulus (rings, shockwaves) from two disc span tables: up to two spans per row.
function Raster.fillRing(dst: buffer, dw: number, dh: number, outer: { number }, inner: { number }, cx: number, cy: number, colour: number)
	local ro, ri = (#outer - 1) // 2, (#inner - 1) // 2
	local row = colourRow(colour, 2 * ro + 1)
	for dy = -ro, ro do
		local Y = cy + dy
		local ho = outer[dy + ro + 1]
		if ho >= 0 and Y >= 0 and Y < dh then
			local hi = if dy >= -ri and dy <= ri then inner[dy + ri + 1] else -1
			if hi < 0 then
				local x0, x1 = max(0, cx - ho), min(dw - 1, cx + ho)
				if x1 >= x0 then
					bcopy(dst, (Y * dw + x0) * 4, row, 0, (x1 - x0 + 1) * 4)
				end
			else
				-- left span [cx-ho, cx-hi-1], right span [cx+hi+1, cx+ho]
				local a0, a1 = max(0, cx - ho), min(dw - 1, cx - hi - 1)
				if a1 >= a0 then
					bcopy(dst, (Y * dw + a0) * 4, row, 0, (a1 - a0 + 1) * 4)
				end
				local b0, b1 = max(0, cx + hi + 1), min(dw - 1, cx + ho)
				if b1 >= b0 then
					bcopy(dst, (Y * dw + b0) * 4, row, 0, (b1 - b0 + 1) * 4)
				end
			end
		end
	end
end

------------------------------------------------------------------------------------------------
-- Stamps: precomputed soft shapes added into a u8 field (glow, smoke, heat). The exp() runs once at load.

export type Stamp = { r: number, d: number, data: buffer }

-- A gaussian dot: value = floor(peak * exp(-(dx²+dy²) / (spread * r²))).
function Raster.gaussStamp(r: number, peak: number?, spread: number?): Stamp
	local d = 2 * r + 1
	local p, inv = peak or 255, 1 / ((spread or 0.35) * r * r)
	local data = bcreate(d * d)
	for dy = -r, r do
		for dx = -r, r do
			writeu8(data, (dy + r) * d + dx + r, floor(p * exp(-(dx * dx + dy * dy) * inv)))
		end
	end
	return { r = r, d = d, data = data }
end

-- Saturating add of a stamp centred on (cx, cy), clipped. scale (0..256) dims it without a new stamp.
function Raster.stampAdd(field: buffer, fw: number, fh: number, s: Stamp, cx: number, cy: number, scale: number?)
	local r, d, data = s.r, s.d, s.data
	local x0, x1 = max(0, cx - r), min(fw - 1, cx + r)
	local y0, y1 = max(0, cy - r), min(fh - 1, cy + r)
	if x1 < x0 or y1 < y0 then
		return
	end
	local k = scale or 256
	for y = y0, y1 do
		local srow = (y - cy + r) * d - cx + r
		local frow = y * fw
		if k == 256 then
			for x = x0, x1 do
				local i = frow + x
				local v = readu8(field, i) + readu8(data, srow + x)
				writeu8(field, i, if v > 255 then 255 else v)
			end
		else
			for x = x0, x1 do
				local i = frow + x
				local v = readu8(field, i) + (readu8(data, srow + x) * k) // 256
				writeu8(field, i, if v > 255 then 255 else v)
			end
		end
	end
end

-- A motion streak: a 1 px line from (x0,y0) to (x1,y1) whose intensity ramps i0 -> i1, added (saturating).
-- Sparks drawn as streaks read as fast; a dot at 60 fps reads as a stutter.
function Raster.streakAdd(field: buffer, fw: number, fh: number, x0: number, y0: number, x1: number, y1: number, i0: number, i1: number)
	local dx, dy = x1 - x0, y1 - y0
	local n = max(1, floor(max(math.abs(dx), math.abs(dy)) + 0.5))
	local sx, sy, si = dx / n, dy / n, (i1 - i0) / n
	local x, y, i = x0 + 0.5, y0 + 0.5, i0
	for _ = 0, n do
		local ix, iy = floor(x), floor(y)
		if ix >= 0 and ix < fw and iy >= 0 and iy < fh then
			local p = iy * fw + ix
			local v = readu8(field, p) + floor(i)
			writeu8(field, p, if v > 255 then 255 else v)
		end
		x += sx
		y += sy
		i += si
	end
end

return Raster
