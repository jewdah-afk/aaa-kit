--!strict
-- Flipbook: a procedural flipbook sheet baked into an RGBA8 buffer, ready for EditableImage:WritePixelsBuffer.
--
-- WHERE IT CAN BE USED. ParticleEmitter / Beam / Trail .TextureContent are NOT documented to accept an EditableImage
-- (docs/research/20, §5.4-5.5: only a URI is known to render). So a runtime sheet goes on surfaces that DO accept one,
-- stepped by rect: ImageLabel.ImageContent (+ ImageRectOffset / ImageRectSize), Decal.TextureContent, MeshPart.TextureContent.
-- For a ParticleEmitter, bake the same sheet offline (or in Studio), upload the PNG, and set FlipbookLayout.
--
-- Rules baked in (docs/research/45 §1.6): a sheet is grid x grid cells so its size is an exact multiple of the layout;
-- a 1 px transparent margin per cell keeps frames from bleeding when the sheet is filtered; residual alpha under 3/255 is
-- zeroed (it shows as a faint box under alpha blending); frame 0 must read on its own, because low-memory phones turn
-- flipbooks off and show only that frame.

local Flipbook = {}

export type Sheet = { buf: buffer, size: number, cell: number, grid: number, frames: number }
export type Shade = (t: number, u: number, v: number) -> (number, number, number, number)

Flipbook.MAX_FPS = 30 -- Roblox's FlipbookFramerate cap; use the same for ImageRect stepping
Flipbook.GRIDS = table.freeze({ [4] = 2, [16] = 4, [64] = 8 }) -- frame count -> grid side (Grid2x2, Grid4x4, Grid8x8)
local KILL_ALPHA = 3 / 255

-- Pixel offset of frame `index` (0-based) inside the sheet, reading order, for ImageRectOffset.
function Flipbook.rect(index: number, cell: number, grid: number): (number, number)
	return (index % grid) * cell, (index // grid) * cell
end

-- Which frame to show `elapsed` seconds after the effect starts.
function Flipbook.frameAt(elapsed: number, fps: number, frames: number, mode: "Loop" | "OneShot" | "PingPong"): number
	local i = math.floor(elapsed * math.min(fps, Flipbook.MAX_FPS))
	if mode == "OneShot" then
		return math.clamp(i, 0, frames - 1)
	elseif mode == "PingPong" then
		local period = math.max(1, 2 * (frames - 1))
		local k = i % period
		return if k < frames then k else period - k
	end
	return i % frames
end

-- Small integer hash for grain: deterministic, products stay far below 2^53 so the doubles are exact.
local function hash(x: number, y: number, seed: number): number
	local h = (x * 73 + y * 151 + seed * 997) % 65536
	h = (bit32.bxor(h, bit32.rshift(h, 7)) * 40503) % 65536
	h = bit32.bxor(h, bit32.rshift(h, 5))
	return ((h * 31) % 65536) / 65536
end

-- Bake `frames` cells of `cell` px into a grid x grid sheet. shade(t, u, v): t = 0..1 across the animation,
-- u, v = -1..1 across the cell; returns r, g, b, a in 0..1 (not premultiplied).
function Flipbook.bake(cell: number, grid: number, frames: number, shade: Shade): Sheet
	assert(frames >= 1 and frames <= grid * grid, "frames must fit the grid")
	local size = cell * grid
	local buf = buffer.create(size * size * 4) -- zero-filled: fully transparent
	for f = 0, frames - 1 do
		local ox, oy = Flipbook.rect(f, cell, grid)
		local t = if frames > 1 then f / (frames - 1) else 0
		for py = 1, cell - 2 do -- the outer 1 px of every cell stays transparent
			for px = 1, cell - 2 do
				local u, v = (px + 0.5) / cell * 2 - 1, (py + 0.5) / cell * 2 - 1
				local r, g, b, a = shade(t, u, v)
				if a >= KILL_ALPHA then
					local at = ((oy + py) * size + (ox + px)) * 4
					buffer.writeu8(buf, at, math.floor(math.clamp(r, 0, 1) * 255 + 0.5))
					buffer.writeu8(buf, at + 1, math.floor(math.clamp(g, 0, 1) * 255 + 0.5))
					buffer.writeu8(buf, at + 2, math.floor(math.clamp(b, 0, 1) * 255 + 0.5))
					buffer.writeu8(buf, at + 3, math.floor(math.clamp(a, 0, 1) * 255 + 0.5))
				end
			end
		end
	end
	return { buf = buf, size = size, cell = cell, grid = grid, frames = frames }
end

-- Fraction of a cell's pixels that are visible (alpha > 0): "does this frame read?"
function Flipbook.coverage(sheet: Sheet, index: number): number
	local ox, oy = Flipbook.rect(index, sheet.cell, sheet.grid)
	local n = 0
	for y = 0, sheet.cell - 1 do
		for x = 0, sheet.cell - 1 do
			if buffer.readu8(sheet.buf, ((oy + y) * sheet.size + (ox + x)) * 4 + 3) > 0 then
				n += 1
			end
		end
	end
	return n / (sheet.cell * sheet.cell)
end

-- A ring shockwave that expands, thins and cools from white-hot to violet. Frame 0 is already a visible disc.
function Flipbook.ring(t: number, u: number, v: number): (number, number, number, number)
	local d = math.sqrt(u * u + v * v)
	local eased = 1 - (1 - t) * (1 - t)
	local radius = 0.30 + 0.62 * eased
	local width = 0.20 * (1 - t) + 0.04
	local edge = math.abs(d - radius) / width
	local grain = 0.85 + 0.15 * hash(math.floor((u + 1) * 16), math.floor((v + 1) * 16), 7)
	local a = math.max(0, 1 - edge) * (1 - t * t) * grain
	if t == 0 then
		a = math.max(a, math.max(0, 1 - d / 0.55)) -- frame 0 also carries a soft core so it reads alone
	end
	local heat = 1 - eased
	return 0.55 + 0.45 * heat, 0.25 + 0.60 * heat, 0.95, a
end

return Flipbook
