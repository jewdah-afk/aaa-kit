-- VFX inner-loop benchmarks: the naive way vs the fast way, for the kernels every
-- EditableImage effect is built from. Every pair is checked for the same output
-- (checksum), so a "fast" variant can't win by doing different work.
--
-- Run (Luau CLI 0.740, the version pinned in cursed-survivors/rokit.toml):
--   luau -O2 tools/vfxbench/bench.luau              -- interpreter (what the Roblox client runs today)
--   luau -O2 --codegen tools/vfxbench/bench.luau    -- native codegen (server; client if Roblox enables it)
--   luau -O2 tools/vfxbench/bench.luau -a quick     -- fewer repetitions
-- Output: a Markdown table (group, variant, ms per call, ns per pixel, speed-up vs the group's first row).
--
-- Numbers are desktop-class CPU timings of the same VM Roblox ships. Engine calls
-- (WritePixelsBuffer, DrawImage, upload) don't exist here: Studio's lib/frontier/studio/Bench measures those.

local args = { ... }
local QUICK = args[1] == "quick"
local MIN_TIME = if QUICK then 0.08 else 0.30 -- seconds of repetitions per case
local MAX_REPS = if QUICK then 20 else 200

local clock = os.clock
local floor, min, max, sqrt, sin, cos, atan2, exp = math.floor, math.min, math.max, math.sqrt, math.sin, math.cos, math.atan2, math.exp
local band, bor, rshift, lshift = bit32.band, bit32.bor, bit32.rshift, bit32.lshift
local readu8, writeu8, readu32, writeu32 = buffer.readu8, buffer.writeu8, buffer.readu32, buffer.writeu32
local readf32, writef32 = buffer.readf32, buffer.writef32
local bcopy, bfill, bcreate, blen = buffer.copy, buffer.fill, buffer.create, buffer.len

-- deterministic pseudo-random (xorshift32), so every run draws the same scene
local seed = 2463534242
local function rnd(): number
	seed = bit32.bxor(seed, lshift(seed, 13))
	seed = bit32.bxor(seed, rshift(seed, 17))
	seed = bit32.bxor(seed, lshift(seed, 5))
	return seed / 4294967296
end

local function checksum(b: buffer): number
	-- position-weighted sum of every byte, exact in doubles for these sizes
	local s = 0
	local n = blen(b)
	for i = 0, n - 1, 4 do
		s = (s * 31 + readu32(b, i)) % 2147483647
	end
	return s
end

local function meanByte(b: buffer): number
	local s, n = 0, blen(b)
	for i = 0, n - 1 do
		s += readu8(b, i)
	end
	return s / n
end

local results = {}
local groups: { [string]: { exact: boolean, first: number?, ref: number? } } = {}
local startGroup: (group: string, exact: boolean?) -> ()

-- case(group, variant, pixels, fn, check): fn() runs one "frame"; check() returns a
-- comparable value after fn has run. exact=false groups compare meanByte within 1%.
local function case(group: string, variant: string, pixels: number, fn: () -> (), check: () -> number?)
	fn() -- warm-up (also builds any lazy tables)
	local times = {}
	local t0 = clock()
	local reps = 0
	while reps < MAX_REPS and (clock() - t0) < MIN_TIME or reps < 3 do
		local a = clock()
		fn()
		times[#times + 1] = clock() - a
		reps += 1
	end
	table.sort(times)
	local med = times[(#times + 1) // 2]
	local g = groups[group]
	local value = check()
	local status = "reference"
	if value == nil then
		status = "n/a"
		if g.first == nil then
			g.first = med
		end
	elseif g.first == nil then
		g.first, g.ref = med, value
	elseif g.exact then
		status = if value == g.ref then "same" else "DIFFERENT"
	else
		status = if math.abs(value - g.ref) <= 0.01 * math.max(1, g.ref) then "≈same" else "DIFFERENT"
	end
	results[#results + 1] = {
		group = group,
		variant = variant,
		ms = med * 1000,
		ns = med * 1e9 / pixels,
		speed = g.first / med,
		status = status,
	}
end

-- Every group starts here. exact = false: variants may differ by float rounding
-- (incremental stepping, interpolated grids, fewer pixels per frame), so outputs are
-- compared by mean byte within 1% instead of by checksum.
function startGroup(group: string, exact: boolean?)
	groups[group] = { exact = exact ~= false, first = nil, ref = nil }
end

---------------------------------------------------------------------------
-- Canvas sizes
local W, H = 480, 270 -- cursed-survivors' per-frame canvas
local N = W * H
local SW, SH = 256, 256 -- square effect canvas
local SN = SW * SH

---------------------------------------------------------------------------
-- 1. Clear a canvas to one colour
do
	local G = "01 clear 480x270 to a colour"
	startGroup(G)
	local b = bcreate(N * 4)
	local colour = 0xFF20100A
	case(G, "writeu32 per pixel", N, function()
		for i = 0, N * 4 - 4, 4 do
			writeu32(b, i, colour)
		end
	end, function()
		return checksum(b)
	end)
	case(G, "doubling buffer.copy (log2 N copies)", N, function()
		writeu32(b, 0, colour)
		local filled, total = 4, N * 4
		while filled < total do
			local n = min(filled, total - filled)
			bcopy(b, filled, b, 0, n)
			filled += n
		end
	end, function()
		return checksum(b)
	end)
	-- the clear image is built once at load; one memcpy per frame
	local template = bcreate(N * 4)
	for i = 0, N * 4 - 4, 4 do
		writeu32(template, i, colour)
	end
	case(G, "copy from a prebuilt clear buffer", N, function()
		bcopy(b, 0, template, 0)
	end, function()
		return checksum(b)
	end)
end

do
	local G = "02 clear 480x270 to transparent black"
	startGroup(G)
	local b = bcreate(N * 4)
	case(G, "writeu32 per pixel", N, function()
		for i = 0, N * 4 - 4, 4 do
			writeu32(b, i, 0)
		end
	end, function()
		return checksum(b)
	end)
	case(G, "buffer.fill(b, 0, 0)", N, function()
		bfill(b, 0, 0)
	end, function()
		return checksum(b)
	end)
end

---------------------------------------------------------------------------
-- 3. Writing a computed pixel
do
	local G = "03 write a gradient pixel (pack)"
	startGroup(G)
	local b = bcreate(N * 4)
	case(G, "4x writeu8", N, function()
		local i = 0
		for y = 0, H - 1 do
			for x = 0, W - 1 do
				writeu8(b, i, x % 256)
				writeu8(b, i + 1, y % 256)
				writeu8(b, i + 2, (x + y) % 256)
				writeu8(b, i + 3, 255)
				i += 4
			end
		end
	end, function()
		return checksum(b)
	end)
	case(G, "1x writeu32, arithmetic pack", N, function()
		local i = 0
		for y = 0, H - 1 do
			local gy = (y % 256) * 256 + 0xFF000000
			for x = 0, W - 1 do
				writeu32(b, i, x % 256 + gy + ((x + y) % 256) * 65536)
				i += 4
			end
		end
	end, function()
		return checksum(b)
	end)
	case(G, "1x writeu32, bit32 pack", N, function()
		local i = 0
		for y = 0, H - 1 do
			for x = 0, W - 1 do
				writeu32(b, i, bor(band(x, 255), lshift(band(y, 255), 8), lshift(band(x + y, 255), 16), 0xFF000000))
				i += 4
			end
		end
	end, function()
		return checksum(b)
	end)
end

---------------------------------------------------------------------------
-- 4. Additive blend (glow over the scene), saturating, all four channels
do
	local G = "04 additive blend 256x256 (saturating)"
	startGroup(G)
	local src, dst, base = bcreate(SN * 4), bcreate(SN * 4), bcreate(SN * 4)
	for i = 0, SN * 4 - 1 do
		writeu8(src, i, floor(rnd() * 256))
		writeu8(base, i, floor(rnd() * 256))
	end
	case(G, "per channel: readu8 + math.min", SN, function()
		bcopy(dst, 0, base, 0)
		for i = 0, SN * 4 - 1 do
			writeu8(dst, i, min(255, readu8(dst, i) + readu8(src, i)))
		end
	end, function()
		return checksum(dst)
	end)
	local sat = table.create(511)
	for v = 0, 510 do
		sat[v + 1] = min(255, v)
	end
	case(G, "per channel: saturation LUT", SN, function()
		bcopy(dst, 0, base, 0)
		for i = 0, SN * 4 - 1 do
			writeu8(dst, i, sat[readu8(dst, i) + readu8(src, i) + 1])
		end
	end, function()
		return checksum(dst)
	end)
	case(G, "SWAR: 2 channels per add (bit32)", SN, function()
		bcopy(dst, 0, base, 0)
		for i = 0, SN * 4 - 4, 4 do
			local a, s = readu32(dst, i), readu32(src, i)
			local lo = band(a, 0x00FF00FF) + band(s, 0x00FF00FF)
			local hi = band(rshift(a, 8), 0x00FF00FF) + band(rshift(s, 8), 0x00FF00FF)
			local olo, ohi = band(lo, 0x01000100), band(hi, 0x01000100)
			lo = band(bor(lo, olo - rshift(olo, 8)), 0x00FF00FF)
			hi = band(bor(hi, ohi - rshift(ohi, 8)), 0x00FF00FF)
			writeu32(dst, i, lo + hi * 256)
		end
	end, function()
		return checksum(dst)
	end)
	case(G, "SWAR, skip where glow is 0 (sparse)", SN, function()
		-- same maths; a real glow layer is mostly empty, so test the early-out cost on dense data
		bcopy(dst, 0, base, 0)
		for i = 0, SN * 4 - 4, 4 do
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
	end, function()
		return checksum(dst)
	end)
end

---------------------------------------------------------------------------
-- 5. Alpha-over blend with one layer opacity (out = (s*a + d*(256-a)) >> 8 per channel)
do
	local G = "05 alpha blend 256x256 (layer opacity)"
	startGroup(G)
	local src, dst, base = bcreate(SN * 4), bcreate(SN * 4), bcreate(SN * 4)
	for i = 0, SN * 4 - 1 do
		writeu8(src, i, floor(rnd() * 256))
		writeu8(base, i, floor(rnd() * 256))
	end
	local A = 150
	case(G, "per channel: readu8 x2, writeu8", SN, function()
		bcopy(dst, 0, base, 0)
		local ia = 256 - A
		for i = 0, SN * 4 - 1 do
			writeu8(dst, i, (readu8(src, i) * A + readu8(dst, i) * ia) // 256)
		end
	end, function()
		return checksum(dst)
	end)
	case(G, "SWAR: 2 channels per multiply", SN, function()
		bcopy(dst, 0, base, 0)
		local ia = 256 - A
		for i = 0, SN * 4 - 4, 4 do
			local s, d = readu32(src, i), readu32(dst, i)
			local rb = band(rshift(band(s, 0x00FF00FF) * A + band(d, 0x00FF00FF) * ia, 8), 0x00FF00FF)
			local ag = band(band(rshift(s, 8), 0x00FF00FF) * A + band(rshift(d, 8), 0x00FF00FF) * ia, 0xFF00FF00)
			writeu32(dst, i, rb + ag)
		end
	end, function()
		return checksum(dst)
	end)
end

---------------------------------------------------------------------------
-- 6. Palette-indexed resolve (1 byte per pixel -> RGBA), the colour-cycling base
do
	local G = "06 index->RGBA resolve 480x270"
	startGroup(G)
	local idx, out = bcreate(N), bcreate(N * 4)
	for i = 0, N - 1 do
		writeu8(idx, i, floor(rnd() * 256))
	end
	local pal = table.create(256)
	local palBuf = bcreate(1024)
	for c = 0, 255 do
		local r, g, bl = c, 255 - c, (c * 7) % 256
		local v = r + g * 256 + bl * 65536 + 0xFF000000
		pal[c + 1] = v
		writeu32(palBuf, c * 4, v)
	end
	case(G, "compute colour per pixel", N, function()
		for i = 0, N - 1 do
			local c = readu8(idx, i)
			writeu32(out, i * 4, c + (255 - c) * 256 + ((c * 7) % 256) * 65536 + 0xFF000000)
		end
	end, function()
		return checksum(out)
	end)
	case(G, "palette in a Luau table", N, function()
		local o = 0
		for i = 0, N - 1 do
			writeu32(out, o, pal[readu8(idx, i) + 1])
			o += 4
		end
	end, function()
		return checksum(out)
	end)
	case(G, "palette in a buffer (readu32)", N, function()
		local o = 0
		for i = 0, N - 1 do
			writeu32(out, o, readu32(palBuf, readu8(idx, i) * 4))
			o += 4
		end
	end, function()
		return checksum(out)
	end)
	case(G, "4 indices per readu32", N, function()
		local o = 0
		for i = 0, N - 4, 4 do
			local q = readu32(idx, i)
			writeu32(out, o, pal[band(q, 255) + 1])
			writeu32(out, o + 4, pal[band(rshift(q, 8), 255) + 1])
			writeu32(out, o + 8, pal[band(rshift(q, 16), 255) + 1])
			writeu32(out, o + 12, pal[rshift(q, 24) + 1])
			o += 16
		end
	end, function()
		return checksum(out)
	end)
end

---------------------------------------------------------------------------
-- 7. Box blur of a 1-byte field (light, heat, smoke density), radius 8, clamp-to-edge
do
	local G = "07 box blur 256x256 u8, radius 8"
	startGroup(G)
	local R = 8
	local D = 2 * R + 1
	local src, tmp, out = bcreate(SN), bcreate(SN), bcreate(SN)
	for i = 0, SN - 1 do
		writeu8(src, i, floor(rnd() * 256))
	end
	local function cl(v: number, hi: number): number
		return if v < 0 then 0 elseif v > hi then hi else v
	end
	case(G, "naive 2D (289 taps/px)", SN, function()
		for y = 0, SH - 1 do
			for x = 0, SW - 1 do
				local s = 0
				for dy = -R, R do
					local row = cl(y + dy, SH - 1) * SW
					for dx = -R, R do
						s += readu8(src, row + cl(x + dx, SW - 1))
					end
				end
				writeu8(out, y * SW + x, s // (D * D))
			end
		end
	end, function()
		return checksum(out)
	end)
	-- separable: blur rows into tmp as sums (u16 would be exact; keep the total, divide once)
	local tmpSum = bcreate(SN * 2)
	case(G, "separable naive (34 taps/px)", SN, function()
		for y = 0, SH - 1 do
			local row = y * SW
			for x = 0, SW - 1 do
				local s = 0
				for dx = -R, R do
					s += readu8(src, row + cl(x + dx, SW - 1))
				end
				buffer.writeu16(tmpSum, (row + x) * 2, s)
			end
		end
		for x = 0, SW - 1 do
			for y = 0, SH - 1 do
				local s = 0
				for dy = -R, R do
					s += buffer.readu16(tmpSum, (cl(y + dy, SH - 1) * SW + x) * 2)
				end
				writeu8(out, y * SW + x, s // (D * D))
			end
		end
	end, function()
		return checksum(out)
	end)
	case(G, "separable running sum (O(1)/px)", SN, function()
		local readu16, writeu16 = buffer.readu16, buffer.writeu16
		for y = 0, SH - 1 do
			local row = y * SW
			local s = 0
			for dx = -R, R do
				s += readu8(src, row + cl(dx, SW - 1))
			end
			for x = 0, SW - 1 do
				writeu16(tmpSum, (row + x) * 2, s)
				local outX, inX = x - R, x + R + 1
				s += readu8(src, row + (if inX > SW - 1 then SW - 1 else inX)) - readu8(src, row + (if outX < 0 then 0 else outX))
			end
		end
		local div = D * D
		for x = 0, SW - 1 do
			local s = 0
			for dy = -R, R do
				s += readu16(tmpSum, (cl(dy, SH - 1) * SW + x) * 2)
			end
			for y = 0, SH - 1 do
				writeu8(out, y * SW + x, s // div)
				local outY, inY = y - R, y + R + 1
				s += readu16(tmpSum, ((if inY > SH - 1 then SH - 1 else inY) * SW + x) * 2)
					- readu16(tmpSum, ((if outY < 0 then 0 else outY) * SW + x) * 2)
			end
		end
	end, function()
		return checksum(out)
	end)
	local _ = tmp
end

---------------------------------------------------------------------------
-- 8. Gaussian splats: 400 soft particles (radius 6) added into a u8 heat field
do
	local G = "08 400 soft splats r=6 into 256x256 u8"
	startGroup(G)
	local R = 6
	local field = bcreate(SN)
	local px, py = table.create(400), table.create(400)
	for i = 1, 400 do
		px[i] = R + floor(rnd() * (SW - 2 * R))
		py[i] = R + floor(rnd() * (SH - 2 * R))
	end
	local inv = 1 / (0.35 * R * R)
	case(G, "exp() per covered pixel", 400 * (2 * R + 1) ^ 2, function()
		bfill(field, 0, 0)
		for p = 1, 400 do
			local cx, cy = px[p], py[p]
			for dy = -R, R do
				local row = (cy + dy) * SW
				for dx = -R, R do
					local v = floor(255 * exp(-(dx * dx + dy * dy) * inv))
					local i = row + cx + dx
					writeu8(field, i, min(255, readu8(field, i) + v))
				end
			end
		end
	end, function()
		return checksum(field)
	end)
	local D = 2 * R + 1
	local stamp = table.create(D * D)
	for dy = -R, R do
		for dx = -R, R do
			stamp[(dy + R) * D + dx + R + 1] = floor(255 * exp(-(dx * dx + dy * dy) * inv))
		end
	end
	case(G, "precomputed stamp table", 400 * D * D, function()
		bfill(field, 0, 0)
		for p = 1, 400 do
			local base = (py[p] - R) * SW + px[p] - R
			local k = 1
			for _ = 1, D do
				for i = base, base + D - 1 do
					writeu8(field, i, min(255, readu8(field, i) + stamp[k]))
					k += 1
				end
				base += SW
			end
		end
	end, function()
		return checksum(field)
	end)
end

---------------------------------------------------------------------------
-- 9. Tunnel effect (demoscene): per-pixel atan2/sqrt vs a precomputed (u,v) table
do
	local G = "09 tunnel 256x256 (texture lookup)"
	startGroup(G)
	local tex = bcreate(256 * 256 * 4)
	for i = 0, 256 * 256 - 1 do
		local x, y = i % 256, i // 256
		writeu32(tex, i * 4, bor(bit32.bxor(x, y), lshift(x, 8), lshift(y, 16), 0xFF000000))
	end
	local out = bcreate(SN * 4)
	local T = 37
	local cx, cy = SW / 2, SH / 2
	case(G, "atan2 + sqrt per pixel", SN, function()
		local o = 0
		for y = 0, SH - 1 do
			for x = 0, SW - 1 do
				local dx, dy = x - cx + 0.5, y - cy + 0.5
				local d = floor(32 * 256 / sqrt(dx * dx + dy * dy)) % 256
				local a = floor(256 * (atan2(dy, dx) / (2 * math.pi) + 0.5)) % 256
				writeu32(out, o, readu32(tex, (((d + T) % 256) * 256 + (a + T) % 256) * 4))
				o += 4
			end
		end
	end, function()
		return checksum(out)
	end)
	local uv = bcreate(SN * 2)
	do
		local i = 0
		for y = 0, SH - 1 do
			for x = 0, SW - 1 do
				local dx, dy = x - cx + 0.5, y - cy + 0.5
				writeu8(uv, i, floor(32 * 256 / sqrt(dx * dx + dy * dy)) % 256)
				writeu8(uv, i + 1, floor(256 * (atan2(dy, dx) / (2 * math.pi) + 0.5)) % 256)
				i += 2
			end
		end
	end
	case(G, "precomputed (u,v) table", SN, function()
		local o = 0
		for i = 0, SN * 2 - 2, 2 do
			local d, a = readu8(uv, i), readu8(uv, i + 1)
			writeu32(out, o, readu32(tex, (band(d + T, 255) * 256 + band(a + T, 255)) * 4))
			o += 4
		end
	end, function()
		return checksum(out)
	end)
	case(G, "table, one readu16 for (u,v)", SN, function()
		local o = 0
		local readu16 = buffer.readu16
		for i = 0, SN * 2 - 2, 2 do
			local q = readu16(uv, i) -- d in the low byte, a in the high byte
			writeu32(out, o, readu32(tex, (band(q + T, 255) * 256 + band(rshift(q, 8) + T, 255)) * 4))
			o += 4
		end
	end, function()
		return checksum(out)
	end)
end

---------------------------------------------------------------------------
-- 10. Plasma: math.sin per pixel vs separable sine terms + a table
do
	local G = "10 plasma 256x256"
	startGroup(G)
	local out = bcreate(SN * 4)
	local t = 1.7
	local function q(v: number): number -- quantise sin to 0..63 so both variants are exact
		return floor((v + 1) * 31.5)
	end
	case(G, "3x math.sin per pixel", SN, function()
		local o = 0
		for y = 0, SH - 1 do
			for x = 0, SW - 1 do
				local v = q(sin(x * 0.061 + t)) + q(sin(y * 0.047 - t)) + q(sin((x + y) * 0.033 + t * 2))
				writeu32(out, o, v + v * 256 + 0xFF000000)
				o += 4
			end
		end
	end, function()
		return checksum(out)
	end)
	local sx, sy, sxy = table.create(SW), table.create(SH), table.create(SW + SH)
	case(G, "row/col tables (sin once per row/col)", SN, function()
		for x = 0, SW - 1 do
			sx[x + 1] = q(sin(x * 0.061 + t))
		end
		for y = 0, SH - 1 do
			sy[y + 1] = q(sin(y * 0.047 - t))
		end
		for k = 0, SW + SH - 2 do
			sxy[k + 1] = q(sin(k * 0.033 + t * 2))
		end
		local o = 0
		for y = 0, SH - 1 do
			local vy = sy[y + 1]
			for x = 0, SW - 1 do
				local v = sx[x + 1] + vy + sxy[x + y + 1]
				writeu32(out, o, v + v * 256 + 0xFF000000)
				o += 4
			end
		end
	end, function()
		return checksum(out)
	end)
end

---------------------------------------------------------------------------
-- 11. Feedback zoom-rotate of the previous frame (trails, smoke, portals)
do
	local G = "11 rotozoom feedback 256x256 (nearest)"
	startGroup(G, false)
	local prev, out = bcreate(SN * 4), bcreate(SN * 4)
	for i = 0, SN - 1 do
		writeu32(prev, i * 4, floor(rnd() * 0xFFFFFF) + 0xFF000000)
	end
	local ang, zoom = 0.02, 0.985
	local ca, sa = cos(ang) * zoom, sin(ang) * zoom
	local cx, cy = SW / 2, SH / 2
	case(G, "rotate each pixel (mul per pixel)", SN, function()
		local o = 0
		for y = 0, SH - 1 do
			local ry = y - cy
			for x = 0, SW - 1 do
				local rx = x - cx
				local u = floor(rx * ca - ry * sa + cx)
				local v = floor(rx * sa + ry * ca + cy)
				if u >= 0 and u < SW and v >= 0 and v < SH then
					writeu32(out, o, readu32(prev, (v * SW + u) * 4))
				else
					writeu32(out, o, 0xFF000000)
				end
				o += 4
			end
		end
	end, function()
		return meanByte(out)
	end)
	case(G, "incremental (u,v) step along the row", SN, function()
		local o = 0
		for y = 0, SH - 1 do
			local ry = y - cy
			local u = -cx * ca - ry * sa + cx
			local v = -cx * sa + ry * ca + cy
			for _ = 0, SW - 1 do
				local iu, iv = floor(u), floor(v)
				if iu >= 0 and iu < SW and iv >= 0 and iv < SH then
					writeu32(out, o, readu32(prev, (iv * SW + iu) * 4))
				else
					writeu32(out, o, 0xFF000000)
				end
				u += ca
				v += sa
				o += 4
			end
		end
	end, function()
		return meanByte(out)
	end)
end

---------------------------------------------------------------------------
-- 12. Arbitrary warp field (swirl): per-pixel trig vs a coarse 8x8 grid, interpolated (Milkdrop mesh)
do
	local G = "12 swirl warp 256x256: per-pixel vs 8px grid"
	startGroup(G, false)
	local prev, out = bcreate(SN * 4), bcreate(SN * 4)
	for i = 0, SN - 1 do
		local x, y = i % SW, i // SW
		writeu32(prev, i * 4, bor((x * 3) % 256, lshift((y * 5) % 256, 8), 0xFF000000))
	end
	local cx, cy = SW / 2, SH / 2
	local function warp(x: number, y: number): (number, number)
		local dx, dy = x - cx, y - cy
		local r = sqrt(dx * dx + dy * dy)
		local a = 0.6 * exp(-r * 0.02)
		local c, s = cos(a), sin(a)
		return dx * c - dy * s + cx, dx * s + dy * c + cy
	end
	case(G, "exp+cos+sin+sqrt per pixel", SN, function()
		local o = 0
		for y = 0, SH - 1 do
			for x = 0, SW - 1 do
				local u, v = warp(x, y)
				local iu, iv = floor(u), floor(v)
				if iu >= 0 and iu < SW and iv >= 0 and iv < SH then
					writeu32(out, o, readu32(prev, (iv * SW + iu) * 4))
				else
					writeu32(out, o, 0xFF000000)
				end
				o += 4
			end
		end
	end, function()
		return meanByte(out)
	end)
	local CELL = 8
	local GW, GH = SW // CELL + 1, SH // CELL + 1
	local gu, gv = table.create(GW * GH), table.create(GW * GH)
	case(G, "warp at grid nodes, bilinear in between", SN, function()
		for gy = 0, GH - 1 do
			for gx = 0, GW - 1 do
				local u, v = warp(gx * CELL, gy * CELL)
				gu[gy * GW + gx + 1], gv[gy * GW + gx + 1] = u, v
			end
		end
		for gy = 0, GH - 2 do
			for gx = 0, GW - 2 do
				local k = gy * GW + gx + 1
				local u00, v00, u10, v10 = gu[k], gv[k], gu[k + 1], gv[k + 1]
				local u01, v01, u11, v11 = gu[k + GW], gv[k + GW], gu[k + GW + 1], gv[k + GW + 1]
				for j = 0, CELL - 1 do
					local fy = j / CELL
					local ul, vl = u00 + (u01 - u00) * fy, v00 + (v01 - v00) * fy
					local ur, vr = u10 + (u11 - u10) * fy, v10 + (v11 - v10) * fy
					local du, dv = (ur - ul) / CELL, (vr - vl) / CELL
					local o = ((gy * CELL + j) * SW + gx * CELL) * 4
					for _ = 0, CELL - 1 do
						local iu, iv = floor(ul), floor(vl)
						if iu >= 0 and iu < SW and iv >= 0 and iv < SH then
							writeu32(out, o, readu32(prev, (iv * SW + iu) * 4))
						else
							writeu32(out, o, 0xFF000000)
						end
						ul += du
						vl += dv
						o += 4
					end
				end
			end
		end
	end, function()
		return meanByte(out)
	end)
end

---------------------------------------------------------------------------
-- 13. One function call per pixel vs the same maths inline
do
	local G = "13 shade() call per pixel vs inline"
	startGroup(G)
	local out = bcreate(SN * 4)
	local function shade(x: number, y: number): number
		local v = (x * x + y * y) % 256
		return v + (255 - v) * 256 + 0xFF000000
	end
	case(G, "local function per pixel", SN, function()
		local o = 0
		for y = 0, SH - 1 do
			for x = 0, SW - 1 do
				writeu32(out, o, shade(x, y))
				o += 4
			end
		end
	end, function()
		return checksum(out)
	end)
	local shadeVar: any = shade -- an indirect call can't be inlined by -O2
	case(G, "indirect call (stored function)", SN, function()
		local f = shadeVar
		local o = 0
		for y = 0, SH - 1 do
			for x = 0, SW - 1 do
				writeu32(out, o, f(x, y))
				o += 4
			end
		end
	end, function()
		return checksum(out)
	end)
	case(G, "inline maths", SN, function()
		local o = 0
		for y = 0, SH - 1 do
			local yy = y * y
			for x = 0, SW - 1 do
				local v = (x * x + yy) % 256
				writeu32(out, o, v + (255 - v) * 256 + 0xFF000000)
				o += 4
			end
		end
	end, function()
		return checksum(out)
	end)
end

---------------------------------------------------------------------------
-- 14. Unpacking a pixel into channels
do
	local G = "14 unpack RGBA, sum channels 256x256"
	startGroup(G)
	local src = bcreate(SN * 4)
	for i = 0, SN * 4 - 1 do
		writeu8(src, i, floor(rnd() * 256))
	end
	local acc = bcreate(8)
	case(G, "4x readu8", SN, function()
		local s = 0
		for i = 0, SN * 4 - 4, 4 do
			s += readu8(src, i) + readu8(src, i + 1) + readu8(src, i + 2) + readu8(src, i + 3)
		end
		buffer.writef64(acc, 0, s)
	end, function()
		return buffer.readf64(acc, 0)
	end)
	case(G, "readu32 + bit32 band/rshift", SN, function()
		local s = 0
		for i = 0, SN * 4 - 4, 4 do
			local p = readu32(src, i)
			s += band(p, 255) + band(rshift(p, 8), 255) + band(rshift(p, 16), 255) + rshift(p, 24)
		end
		buffer.writef64(acc, 0, s)
	end, function()
		return buffer.readf64(acc, 0)
	end)
	case(G, "readu32 + // and %", SN, function()
		local s = 0
		for i = 0, SN * 4 - 4, 4 do
			local p = readu32(src, i)
			s += p % 256 + (p // 256) % 256 + (p // 65536) % 256 + p // 16777216
		end
		buffer.writef64(acc, 0, s)
	end, function()
		return buffer.readf64(acc, 0)
	end)
end

---------------------------------------------------------------------------
-- 15. Particle update: 20,000 particles, p += v*dt, v *= drag, bounce in a box
do
	local G = "15 update 20k particles"
	startGroup(G)
	local P = 20000
	local dt, drag = 1 / 60, 0.995
	local init = table.create(P * 4)
	for i = 1, P * 4 do
		init[i] = rnd() * 200
	end
	-- array of tables
	local aos = table.create(P)
	for i = 1, P do
		aos[i] = { x = init[i * 4 - 3], y = init[i * 4 - 2], vx = init[i * 4 - 1] - 100, vy = init[i * 4] - 100 }
	end
	local accA = bcreate(8)
	case(G, "array of {x,y,vx,vy} tables", P, function()
		for i = 1, P do
			local p = aos[i]
			local vx, vy = p.vx * drag, p.vy * drag
			local x, y = p.x + vx * dt, p.y + vy * dt
			if x < 0 or x > 200 then
				vx = -vx
			end
			if y < 0 or y > 200 then
				vy = -vy
			end
			p.x, p.y, p.vx, p.vy = x, y, vx, vy
		end
		buffer.writef64(accA, 0, aos[1].x)
	end, function()
		return nil
	end)
	local X, Y, VX, VY = table.create(P), table.create(P), table.create(P), table.create(P)
	for i = 1, P do
		X[i], Y[i], VX[i], VY[i] = init[i * 4 - 3], init[i * 4 - 2], init[i * 4 - 1] - 100, init[i * 4] - 100
	end
	case(G, "4 parallel arrays (SoA)", P, function()
		for i = 1, P do
			local vx, vy = VX[i] * drag, VY[i] * drag
			local x, y = X[i] + vx * dt, Y[i] + vy * dt
			if x < 0 or x > 200 then
				vx = -vx
			end
			if y < 0 or y > 200 then
				vy = -vy
			end
			X[i], Y[i], VX[i], VY[i] = x, y, vx, vy
		end
	end, function()
		return nil
	end)
	local pb = bcreate(P * 16)
	for i = 0, P - 1 do
		writef32(pb, i * 16, init[i * 4 + 1])
		writef32(pb, i * 16 + 4, init[i * 4 + 2])
		writef32(pb, i * 16 + 8, init[i * 4 + 3] - 100)
		writef32(pb, i * 16 + 12, init[i * 4 + 4] - 100)
	end
	case(G, "one f32 buffer (interleaved)", P, function()
		for o = 0, P * 16 - 16, 16 do
			local vx, vy = readf32(pb, o + 8) * drag, readf32(pb, o + 12) * drag
			local x, y = readf32(pb, o) + vx * dt, readf32(pb, o + 4) + vy * dt
			if x < 0 or x > 200 then
				vx = -vx
			end
			if y < 0 or y > 200 then
				vy = -vy
			end
			writef32(pb, o, x)
			writef32(pb, o + 4, y)
			writef32(pb, o + 8, vx)
			writef32(pb, o + 12, vy)
		end
	end, function()
		return nil
	end)
	local VP, VV = table.create(P), table.create(P)
	for i = 1, P do
		VP[i] = vector.create(init[i * 4 - 3], init[i * 4 - 2], 0)
		VV[i] = vector.create(init[i * 4 - 1] - 100, init[i * 4] - 100, 0)
	end
	case(G, "vector type (p += v*dt in one op)", P, function()
		for i = 1, P do
			local v = VV[i] * drag
			local p = VP[i] + v * dt
			if p.x < 0 or p.x > 200 or p.y < 0 or p.y > 200 then
				v = vector.create(if p.x < 0 or p.x > 200 then -v.x else v.x, if p.y < 0 or p.y > 200 then -v.y else v.y, 0)
			end
			VP[i], VV[i] = p, v
		end
	end, function()
		return nil
	end)
end

---------------------------------------------------------------------------
-- 16. Copy a dirty rectangle out of the canvas (for a partial WritePixelsBuffer)
do
	local G = "16 pack a 96x96 dirty rect from 480x270"
	startGroup(G)
	local canvas = bcreate(N * 4)
	for i = 0, N - 1 do
		writeu32(canvas, i * 4, floor(rnd() * 0xFFFFFF) + 0xFF000000)
	end
	local RW, RH, RX, RY = 96, 96, 200, 100
	local rect = bcreate(RW * RH * 4)
	case(G, "per pixel readu32/writeu32", RW * RH, function()
		local o = 0
		for y = RY, RY + RH - 1 do
			for x = RX, RX + RW - 1 do
				writeu32(rect, o, readu32(canvas, (y * W + x) * 4))
				o += 4
			end
		end
	end, function()
		return checksum(rect)
	end)
	case(G, "one buffer.copy per row", RW * RH, function()
		for r = 0, RH - 1 do
			bcopy(rect, r * RW * 4, canvas, ((RY + r) * W + RX) * 4, RW * 4)
		end
	end, function()
		return checksum(rect)
	end)
end

---------------------------------------------------------------------------
-- 17. Composite a half-res effect layer into the full canvas (2x nearest upscale)
do
	local G = "17 2x nearest upscale 240x135 -> 480x270"
	startGroup(G)
	local HW, HH = W // 2, H // 2
	local half, full = bcreate(HW * HH * 4), bcreate(N * 4)
	for i = 0, HW * HH - 1 do
		writeu32(half, i * 4, floor(rnd() * 0xFFFFFF) + 0xFF000000)
	end
	case(G, "per output pixel", N, function()
		local o = 0
		for y = 0, H - 1 do
			local srow = (y // 2) * HW
			for x = 0, W - 1 do
				writeu32(full, o, readu32(half, (srow + x // 2) * 4))
				o += 4
			end
		end
	end, function()
		return checksum(full)
	end)
	case(G, "write each row once, buffer.copy the twin row", N, function()
		for y = 0, HH - 1 do
			local o = y * 2 * W * 4
			local s = y * HW * 4
			for x = 0, HW - 1 do
				local p = readu32(half, s)
				writeu32(full, o, p)
				writeu32(full, o + 4, p)
				s += 4
				o += 8
			end
			bcopy(full, (y * 2 + 1) * W * 4, full, y * 2 * W * 4, W * 4)
		end
	end, function()
		return checksum(full)
	end)
end

---------------------------------------------------------------------------
-- 18. An expensive field (domain-warped value noise, 3 octaves): full, checkerboard, quarter-res
do
	local G = "18 warped fBm field: resolution & temporal levers"
	startGroup(G, false)
	local perm = table.create(512)
	for i = 1, 256 do
		perm[i] = i - 1
	end
	for i = 256, 2, -1 do
		local j = floor(rnd() * i) + 1
		perm[i], perm[j] = perm[j], perm[i]
	end
	for i = 1, 256 do
		perm[i + 256] = perm[i]
	end
	local function vnoise(x: number, y: number): number
		local xi, yi = floor(x), floor(y)
		local xf, yf = x - xi, y - yi
		xi, yi = band(xi, 255), band(yi, 255)
		local a, b = perm[perm[xi + 1] + yi + 1], perm[perm[xi + 2] + yi + 1]
		local c, d = perm[perm[xi + 1] + yi + 2], perm[perm[xi + 2] + yi + 2]
		local u, v = xf * xf * (3 - 2 * xf), yf * yf * (3 - 2 * yf)
		local top = a + (b - a) * u
		return (top + (c + (d - c) * u - top) * v) / 255
	end
	local function fbm(x: number, y: number): number
		return vnoise(x, y) * 0.5 + vnoise(x * 2.03, y * 2.03) * 0.25 + vnoise(x * 4.01, y * 4.01) * 0.125
	end
	local function field(x: number, y: number, t: number): number
		local s = 0.02
		local wx = fbm(x * s + t, y * s)
		local wy = fbm(x * s, y * s - t)
		return fbm(x * s + 4 * wx, y * s + 4 * wy)
	end
	local out = bcreate(SN * 4)
	local t = 0.4
	local function px(o: number, v: number)
		local c = floor(v * 290) % 256
		writeu32(out, o, c + c * 256 + 0xFF000000)
	end
	case(G, "full res, every pixel every frame", SN, function()
		local o = 0
		for y = 0, SH - 1 do
			for x = 0, SW - 1 do
				px(o, field(x, y, t))
				o += 4
			end
		end
	end, function()
		return meanByte(out)
	end)
	local frame = 0
	case(G, "checkerboard (half the pixels per frame)", SN, function()
		frame += 1
		local parity = frame % 2
		for y = 0, SH - 1 do
			for x = (y + parity) % 2, SW - 1, 2 do
				px((y * SW + x) * 4, field(x, y, t))
			end
		end
	end, function()
		return meanByte(out)
	end)
	case(G, "interlaced 1 row in 4 per frame", SN, function()
		frame += 1
		for y = frame % 4, SH - 1, 4 do
			local o = y * SW * 4
			for x = 0, SW - 1 do
				px(o, field(x, y, t))
				o += 4
			end
		end
	end, function()
		return meanByte(out)
	end)
	local q = bcreate((SW // 2) * (SH // 2) * 4)
	local q4 = bcreate((SW // 4) * (SH // 4) * 4)
	case(G, "half res 128x128 (GPU bilinear does the upscale)", SN, function()
		local o = 0
		for y = 0, SH - 1, 2 do
			for x = 0, SW - 1, 2 do
				local c = floor(field(x, y, t) * 290) % 256
				writeu32(q, o, c + c * 256 + 0xFF000000)
				o += 4
			end
		end
	end, function()
		return meanByte(q)
	end)
	case(G, "quarter res 64x64", SN, function()
		local o = 0
		for y = 0, SH - 1, 4 do
			for x = 0, SW - 1, 4 do
				local c = floor(field(x, y, t) * 290) % 256
				writeu32(q4, o, c + c * 256 + 0xFF000000)
				o += 4
			end
		end
	end, function()
		return meanByte(q4)
	end)
end

---------------------------------------------------------------------------
-- 19. Type annotations (matter for native codegen, not the interpreter)
do
	local G = "19 same kernel, typed vs untyped params"
	startGroup(G)
	local src, dst = bcreate(SN * 4), bcreate(SN * 4)
	for i = 0, SN * 4 - 1 do
		writeu8(src, i, floor(rnd() * 256))
	end
	local function untyped(s, d, n, k)
		for i = 0, n - 4, 4 do
			local p = readu32(s, i)
			writeu32(d, i, band(p, 0xFF00FF00) + band(rshift(band(p, 0x00FF00FF) * k, 8), 0x00FF00FF))
		end
	end
	local function typed(s: buffer, d: buffer, n: number, k: number)
		for i = 0, n - 4, 4 do
			local p = readu32(s, i)
			writeu32(d, i, band(p, 0xFF00FF00) + band(rshift(band(p, 0x00FF00FF) * k, 8), 0x00FF00FF))
		end
	end
	local anyU: any, anyT: any = untyped, typed
	case(G, "untyped params", SN, function()
		anyU(src, dst, SN * 4, 200)
	end, function()
		return checksum(dst)
	end)
	case(G, "params annotated buffer/number", SN, function()
		anyT(src, dst, SN * 4, 200)
	end, function()
		return checksum(dst)
	end)
end

---------------------------------------------------------------------------
-- 20. A realistic glow layer is mostly empty: 30 glows of 24x24 on 480x270 (~13% lit)
do
	local G = "20 sparse glow composite 480x270 (30 blobs)"
	startGroup(G)
	local glow, dst, base = bcreate(N * 4), bcreate(N * 4), bcreate(N * 4)
	for i = 0, N - 1 do
		writeu32(base, i * 4, floor(rnd() * 0xFFFFFF) + 0xFF000000)
	end
	local TILE = 16
	local TW, TH = math.ceil(W / TILE), math.ceil(H / TILE)
	local tileLit = table.create(TW * TH, false)
	for _ = 1, 30 do
		local bx, by = floor(rnd() * (W - 24)), floor(rnd() * (H - 24))
		for y = by, by + 23 do
			for x = bx, bx + 23 do
				local dx, dy = x - bx - 11.5, y - by - 11.5
				local v = max(0, 120 - floor((dx * dx + dy * dy) * 0.8))
				if v > 0 then
					writeu32(glow, (y * W + x) * 4, v + v * 256 + (v // 2) * 65536)
					tileLit[(y // TILE) * TW + x // TILE + 1] = true
				end
			end
		end
	end
	local function addPixel(i: number)
		local s = readu32(glow, i)
		local a = readu32(dst, i)
		local lo = band(a, 0x00FF00FF) + band(s, 0x00FF00FF)
		local hi = band(rshift(a, 8), 0x00FF00FF) + band(rshift(s, 8), 0x00FF00FF)
		local olo, ohi = band(lo, 0x01000100), band(hi, 0x01000100)
		lo = band(bor(lo, olo - rshift(olo, 8)), 0x00FF00FF)
		hi = band(bor(hi, ohi - rshift(ohi, 8)), 0x00FF00FF)
		writeu32(dst, i, lo + hi * 256)
	end
	case(G, "blend every pixel", N, function()
		bcopy(dst, 0, base, 0)
		for i = 0, N * 4 - 4, 4 do
			addPixel(i)
		end
	end, function()
		return checksum(dst)
	end)
	case(G, "skip pixels where glow == 0", N, function()
		bcopy(dst, 0, base, 0)
		for i = 0, N * 4 - 4, 4 do
			if readu32(glow, i) ~= 0 then
				addPixel(i)
			end
		end
	end, function()
		return checksum(dst)
	end)
	case(G, "only 16x16 tiles marked lit", N, function()
		bcopy(dst, 0, base, 0)
		for ty = 0, TH - 1 do
			for tx = 0, TW - 1 do
				if tileLit[ty * TW + tx + 1] then
					local x1 = min(W, tx * TILE + TILE) - 1
					for y = ty * TILE, min(H, ty * TILE + TILE) - 1 do
						local row = y * W
						for x = tx * TILE, x1 do
							addPixel((row + x) * 4)
						end
					end
				end
			end
		end
	end, function()
		return checksum(dst)
	end)
end

---------------------------------------------------------------------------
-- 21. 50% transparency: true blend vs ordered-dither coverage (write-or-skip, no read)
do
	local G = "21 50% overlay 256x256: blend vs dither"
	startGroup(G, false)
	local src, dst, base = bcreate(SN * 4), bcreate(SN * 4), bcreate(SN * 4)
	for i = 0, SN - 1 do
		writeu32(src, i * 4, 0xFF8040C0)
		writeu32(base, i * 4, 0xFF204060)
	end
	case(G, "SWAR alpha blend (read both, write)", SN, function()
		bcopy(dst, 0, base, 0)
		for i = 0, SN * 4 - 4, 4 do
			local s, d = readu32(src, i), readu32(dst, i)
			local rb = band(rshift(band(s, 0x00FF00FF) * 128 + band(d, 0x00FF00FF) * 128, 8), 0x00FF00FF)
			local ag = band(band(rshift(s, 8), 0x00FF00FF) * 128 + band(rshift(d, 8), 0x00FF00FF) * 128, 0xFF00FF00)
			writeu32(dst, i, rb + ag)
		end
	end, function()
		return meanByte(dst)
	end)
	case(G, "checker dither: copy every other pixel", SN, function()
		bcopy(dst, 0, base, 0)
		for y = 0, SH - 1 do
			local o = (y * SW + (y % 2)) * 4
			for _ = 0, SW // 2 - 1 do
				writeu32(dst, o, readu32(src, o))
				o += 8
			end
		end
	end, function()
		return meanByte(dst)
	end)
end

---------------------------------------------------------------------------
-- 22. Sprite blit with transparent pixels: alpha test per pixel vs precomputed opaque runs
do
	local G = "22 blit 300 sprites 24x24 (60% opaque)"
	startGroup(G)
	local S = 24
	local sprite = bcreate(S * S * 4)
	for y = 0, S - 1 do
		for x = 0, S - 1 do
			local dx, dy = x - 11.5, y - 11.5
			if dx * dx * 1.3 + dy * dy < 120 then -- an opaque blob, transparent corners
				writeu32(sprite, (y * S + x) * 4, 0xFF000000 + floor(rnd() * 0xFFFFFF))
			end
		end
	end
	-- runs: { row, x0, length } for every opaque span, built once at load
	local runs = {}
	for y = 0, S - 1 do
		local x = 0
		while x < S do
			if readu32(sprite, (y * S + x) * 4) ~= 0 then
				local x0 = x
				while x < S and readu32(sprite, (y * S + x) * 4) ~= 0 do
					x += 1
				end
				runs[#runs + 1] = y
				runs[#runs + 1] = x0
				runs[#runs + 1] = x - x0
			else
				x += 1
			end
		end
	end
	local canvas = bcreate(N * 4)
	local sx, sy = table.create(300), table.create(300)
	for i = 1, 300 do
		sx[i], sy[i] = floor(rnd() * (W - S)), floor(rnd() * (H - S))
	end
	case(G, "per pixel: read, test alpha, write", 300 * S * S, function()
		bfill(canvas, 0, 0)
		for k = 1, 300 do
			local ox, oy = sx[k], sy[k]
			for y = 0, S - 1 do
				local d = ((oy + y) * W + ox) * 4
				local s = y * S * 4
				for _ = 0, S - 1 do
					local p = readu32(sprite, s)
					if p ~= 0 then
						writeu32(canvas, d, p)
					end
					s += 4
					d += 4
				end
			end
		end
	end, function()
		return checksum(canvas)
	end)
	local nr = #runs
	case(G, "opaque runs: one buffer.copy per run", 300 * S * S, function()
		bfill(canvas, 0, 0)
		for k = 1, 300 do
			local ox, oy = sx[k], sy[k]
			for r = 1, nr, 3 do
				local y, x0, len = runs[r], runs[r + 1], runs[r + 2]
				bcopy(canvas, ((oy + y) * W + ox + x0) * 4, sprite, (y * S + x0) * 4, len * 4)
			end
		end
	end, function()
		return checksum(canvas)
	end)
end

---------------------------------------------------------------------------
-- 23. Filled discs (shockwave cores, pickups, bullets): distance test per pixel vs row spans
do
	local G = "23 fill 200 discs r=10 on 480x270"
	startGroup(G)
	local R = 10
	local canvas = bcreate(N * 4)
	local cxs, cys = table.create(200), table.create(200)
	for i = 1, 200 do
		cxs[i], cys[i] = R + floor(rnd() * (W - 2 * R)), R + floor(rnd() * (H - 2 * R))
	end
	local colour = 0xFF30C0FF
	case(G, "bounding box, test dx²+dy² per pixel", 200 * (2 * R + 1) ^ 2, function()
		bfill(canvas, 0, 0)
		for k = 1, 200 do
			local cx, cy = cxs[k], cys[k]
			for dy = -R, R do
				local row = (cy + dy) * W
				for dx = -R, R do
					if dx * dx + dy * dy <= R * R then
						writeu32(canvas, (row + cx + dx) * 4, colour)
					end
				end
			end
		end
	end, function()
		return checksum(canvas)
	end)
	-- half-widths per row, computed once (any shape can be stored this way)
	local half = table.create(2 * R + 1)
	for dy = -R, R do
		local h = -1
		for dx = 0, R do
			if dx * dx + dy * dy <= R * R then
				h = dx
			end
		end
		half[dy + R + 1] = h
	end
	-- one row of the colour, to copy spans from
	local row = bcreate((2 * R + 1) * 4)
	for i = 0, 2 * R do
		writeu32(row, i * 4, colour)
	end
	case(G, "row spans: one buffer.copy per row", 200 * (2 * R + 1) ^ 2, function()
		bfill(canvas, 0, 0)
		for k = 1, 200 do
			local cx, cy = cxs[k], cys[k]
			for dy = -R, R do
				local h = half[dy + R + 1]
				if h >= 0 then
					bcopy(canvas, ((cy + dy) * W + cx - h) * 4, row, 0, (2 * h + 1) * 4)
				end
			end
		end
	end, function()
		return checksum(canvas)
	end)
end

---------------------------------------------------------------------------
-- 24. Bilinear vs nearest sampling in Luau (why upscaling belongs to the GPU)
do
	local G = "24 resample 128x128 -> 256x256"
	startGroup(G, false)
	local SRC = 128
	local src, out = bcreate(SRC * SRC), bcreate(SN)
	for i = 0, SRC * SRC - 1 do
		writeu8(src, i, (i * 7) % 256)
	end
	case(G, "bilinear (4 taps) in Luau", SN, function()
		local o = 0
		local sc = (SRC - 1) / (SW - 1)
		for y = 0, SH - 1 do
			local fy = y * sc
			local y0 = floor(fy)
			local ty = fy - y0
			local y1 = min(y0 + 1, SRC - 1)
			for x = 0, SW - 1 do
				local fx = x * sc
				local x0 = floor(fx)
				local tx = fx - x0
				local x1 = min(x0 + 1, SRC - 1)
				local a, b = readu8(src, y0 * SRC + x0), readu8(src, y0 * SRC + x1)
				local c, d = readu8(src, y1 * SRC + x0), readu8(src, y1 * SRC + x1)
				local top = a + (b - a) * tx
				writeu8(out, o, floor(top + (c + (d - c) * tx - top) * ty))
				o += 1
			end
		end
	end, function()
		return meanByte(out)
	end)
	case(G, "nearest in Luau", SN, function()
		local o = 0
		for y = 0, SH - 1 do
			local srow = (y // 2) * SRC
			for x = 0, SW - 1 do
				writeu8(out, o, readu8(src, srow + x // 2))
				o += 1
			end
		end
	end, function()
		return meanByte(out)
	end)
end

---------------------------------------------------------------------------
-- Report
local codegen = "interpreter"
do
	-- the CLI doesn't expose the mode; time a tight loop and let the caller label the run
	local mode = args[2]
	if mode then
		codegen = mode
	end
end
print(`# vfxbench ({_VERSION}, {codegen}, {if QUICK then "quick" else "full"})`)
print("")
print("| Group | Variant | ms/call | ns/px | x vs first | output |")
print("|---|---|---:|---:|---:|---|")
local lastGroup = ""
for _, r in results do
	local g = if r.group == lastGroup then "" else r.group
	lastGroup = r.group
	print(string.format("| %s | %s | %.3f | %.1f | %.2f | %s |", g, r.variant, r.ms, r.ns, r.speed, r.status))
end
local bad = 0
for _, r in results do
	if r.status == "DIFFERENT" then
		bad += 1
	end
end
print("")
print(`@@DONE {bad}`)
