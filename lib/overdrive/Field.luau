--!native
--!optimize 2
-- Field: 1-byte-per-pixel scalar fields (glow, smoke density, heat, light) and the passes that make them cheap.
-- A u8 field is 4x less memory than RGBA, so simulate and blur in fields, then colour once with a gradient map.
-- Measured (tools/vfxbench, interpreter): a running-sum blur is ~80x faster than a naive radius-8 box;
-- a palette resolve that reads 4 indices per readu32 is ~2x faster than computing colour per pixel.

local Field = {}

local readu8, writeu8, readu16, writeu16, readu32, writeu32 =
	buffer.readu8, buffer.writeu8, buffer.readu16, buffer.writeu16, buffer.readu32, buffer.writeu32
local band, bor, rshift = bit32.band, bit32.bor, bit32.rshift
local bcreate, bcopy = buffer.create, buffer.copy

-- Scratch buffers keyed by size, so per-frame passes don't allocate.
local scratch: { [number]: buffer } = {}
local function tmp(bytes: number, slot: number): buffer
	local key = bytes * 4 + slot
	local b = scratch[key]
	if not b then
		b = bcreate(bytes)
		scratch[key] = b
	end
	return b
end

-- Box blur, radius r, clamp-to-edge, exact (equals the naive (2r+1)² average, floored). src and dst may be the same.
-- Cost: ~4 reads per pixel per pass whatever the radius.
function Field.boxBlur(src: buffer, dst: buffer, w: number, h: number, r: number)
	if r <= 0 then
		if dst ~= src then
			bcopy(dst, 0, src, 0, w * h)
		end
		return
	end
	local sums = tmp(w * h * 2, 1)
	local wl, hl = w - 1, h - 1
	for y = 0, hl do
		local row = y * w
		local s = 0
		for dx = -r, r do
			s += readu8(src, row + (if dx < 0 then 0 elseif dx > wl then wl else dx))
		end
		for x = 0, wl do
			writeu16(sums, (row + x) * 2, s)
			local outX, inX = x - r, x + r + 1
			s += readu8(src, row + (if inX > wl then wl else inX)) - readu8(src, row + (if outX < 0 then 0 else outX))
		end
	end
	local div = (2 * r + 1) * (2 * r + 1)
	for x = 0, wl do
		local s = 0
		for dy = -r, r do
			s += readu16(sums, ((if dy < 0 then 0 elseif dy > hl then hl else dy) * w + x) * 2)
		end
		for y = 0, hl do
			writeu8(dst, y * w + x, s // div)
			local outY, inY = y - r, y + r + 1
			s += readu16(sums, ((if inY > hl then hl else inY) * w + x) * 2)
				- readu16(sums, ((if outY < 0 then 0 else outY) * w + x) * 2)
		end
	end
end

-- Three box passes approximate a gaussian (central limit); sigma ≈ r * 1.0 for three passes of radius r.
function Field.blur3(src: buffer, dst: buffer, w: number, h: number, r: number)
	Field.boxBlur(src, dst, w, h, r)
	Field.boxBlur(dst, dst, w, h, r)
	Field.boxBlur(dst, dst, w, h, r)
end

-- field[i] = floor(field[i] * k / 256) for every byte, four bytes per step (SWAR). k in 0..256.
function Field.scale(field: buffer, n: number, k: number)
	local n4 = n - n % 4
	for i = 0, n4 - 4, 4 do
		local p = readu32(field, i)
		if p ~= 0 then
			local lo = band(rshift(band(p, 0x00FF00FF) * k, 8), 0x00FF00FF)
			local hi = band(band(rshift(p, 8), 0x00FF00FF) * k, 0xFF00FF00)
			writeu32(field, i, lo + hi)
		end
	end
	for i = n4, n - 1 do
		writeu8(field, i, (readu8(field, i) * k) // 256)
	end
end

-- dst[i] = min(255, dst[i] + src[i]), four bytes per step (SWAR saturating add). Skips all-zero words.
function Field.addSat(dst: buffer, src: buffer, n: number)
	local n4 = n - n % 4
	for i = 0, n4 - 4, 4 do
		local s = readu32(src, i)
		if s ~= 0 then
			local a = readu32(dst, i)
			local lo = band(a, 0x00FF00FF) + band(s, 0x00FF00FF)
			local hi = band(rshift(a, 8), 0x00FF00FF) + band(rshift(s, 8), 0x00FF00FF)
			local olo, ohi = band(lo, 0x01000100), band(hi, 0x01000100)
			lo = band(bor(lo, olo - rshift(olo, 8)), 0x00FF00FF)
			hi = band(bor(hi, ohi - rshift(ohi, 8)), 0x00FF00FF)
			writeu32(dst, i, lo + hi * 256)
		end
	end
	for i = n4, n - 1 do
		local v = readu8(dst, i) + readu8(src, i)
		writeu8(dst, i, if v > 255 then 255 else v)
	end
end

-- 2x2 box downsample: dst is (w//2) x (h//2).
function Field.down2(src: buffer, w: number, h: number, dst: buffer)
	local hw, hh = w // 2, h // 2
	local o = 0
	for y = 0, hh - 1 do
		local r0 = 2 * y * w
		local r1 = r0 + w
		for x = 0, hw - 1 do
			local i = 2 * x
			writeu8(dst, o, (readu8(src, r0 + i) + readu8(src, r0 + i + 1) + readu8(src, r1 + i) + readu8(src, r1 + i + 1)) // 4)
			o += 1
		end
	end
end

-- 2x nearest upsample: each source row is written once, the twin row is one buffer.copy.
function Field.up2(src: buffer, w: number, h: number, dst: buffer)
	local W2 = w * 2
	for y = 0, h - 1 do
		local s, o = y * w, 2 * y * W2
		for x = 0, w - 1 do
			local v = readu8(src, s + x)
			writeu8(dst, o, v)
			writeu8(dst, o + 1, v)
			o += 2
		end
		bcopy(dst, (2 * y + 1) * W2, dst, 2 * y * W2, W2)
	end
end

-- Map every byte through a 256-entry table (a curve: threshold, gamma, bright pass), in place or into dst.
function Field.remap(src: buffer, dst: buffer, n: number, curve: { number })
	for i = 0, n - 1 do
		writeu8(dst, i, curve[readu8(src, i) + 1])
	end
end

-- 256-entry curve helpers.
function Field.curve(f: (v: number) -> number): { number }
	local t = table.create(256)
	for v = 0, 255 do
		local y = math.floor(f(v) + 0.5)
		t[v + 1] = if y < 0 then 0 elseif y > 255 then 255 else y
	end
	return t
end

-- A gradient map (palette ramp): 256 packed RGBA colours from stops { {t, r, g, b, a}, ... }, t in 0..1 ascending.
-- Colouring a grayscale field through a ramp is how AAA effects get rich colour from one channel.
function Field.ramp(stops: { { number } }): { number }
	local pal = table.create(256)
	for v = 0, 255 do
		local t = v / 255
		local k = 1
		while k < #stops - 1 and t > stops[k + 1][1] do
			k += 1
		end
		local a, b = stops[k], stops[math.min(k + 1, #stops)]
		local span = b[1] - a[1]
		local f = if span > 0 then math.clamp((t - a[1]) / span, 0, 1) else 0
		local function ch(i: number): number
			return math.floor(a[i] + (b[i] - a[i]) * f + 0.5)
		end
		pal[v + 1] = ch(2) + ch(3) * 256 + ch(4) * 65536 + ch(5) * 16777216
	end
	return pal
end

-- Resolve a u8 field to RGBA through a palette (gradient map), reading 4 indices per readu32.
function Field.gradientMap(src: buffer, n: number, pal: { number }, dst: buffer)
	local n4 = n - n % 4
	local o = 0
	for i = 0, n4 - 4, 4 do
		local q = readu32(src, i)
		writeu32(dst, o, pal[band(q, 255) + 1])
		writeu32(dst, o + 4, pal[band(rshift(q, 8), 255) + 1])
		writeu32(dst, o + 8, pal[band(rshift(q, 16), 255) + 1])
		writeu32(dst, o + 12, pal[rshift(q, 24) + 1])
		o += 16
	end
	for i = n4, n - 1 do
		writeu32(dst, i * 4, pal[readu8(src, i) + 1])
	end
end

return Field
