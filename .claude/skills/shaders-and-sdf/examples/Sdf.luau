--!strict
-- Sdf: 2D signed distance functions and a rasteriser with 1-pixel anti-aliasing.
-- Negative inside, positive outside, in pixels. The same maths runs in GLSL (see the
-- SKILL.md table) and on the CPU for EditableImage UI: rounded panels, rings, glows.

local Sdf = {}

function Sdf.circle(px: number, py: number, r: number): number
	return math.sqrt(px * px + py * py) - r
end

-- Box centred at the origin with half-size (bx, by) and corner radius r.
function Sdf.roundBox(px: number, py: number, bx: number, by: number, r: number): number
	local qx, qy = math.abs(px) - bx + r, math.abs(py) - by + r
	local ox, oy = math.max(qx, 0), math.max(qy, 0)
	return math.sqrt(ox * ox + oy * oy) + math.min(math.max(qx, qy), 0) - r
end

-- Ring of radius r and thickness w.
function Sdf.ring(px: number, py: number, r: number, w: number): number
	return math.abs(Sdf.circle(px, py, r)) - w / 2
end

function Sdf.union(a: number, b: number): number
	return math.min(a, b)
end

function Sdf.subtract(a: number, b: number): number
	return math.max(a, -b)
end

-- Polynomial smooth min (k = blend radius in px). Blobs merge like liquid.
function Sdf.smoothUnion(a: number, b: number, k: number): number
	local h = math.clamp(0.5 + 0.5 * (b - a) / k, 0, 1)
	return b + (a - b) * h - k * h * (1 - h)
end

-- Coverage 0..1 for a pixel: a 1 px linear ramp across the edge (cheap analytic AA).
function Sdf.coverage(d: number): number
	return math.clamp(0.5 - d, 0, 1)
end

-- Glow falloff outside the shape: 1 at the edge, fading to 0 at `radius` px.
function Sdf.glow(d: number, radius: number): number
	if d <= 0 then
		return 1
	end
	local x = math.clamp(1 - d / radius, 0, 1)
	return x * x
end

-- Rasterise a distance function into an 8-bit alpha buffer (w*h bytes), sampled at pixel centres.
function Sdf.rasterize(w: number, h: number, dist: (number, number) -> number): buffer
	local out = buffer.create(w * h)
	for y = 0, h - 1 do
		for x = 0, w - 1 do
			local a = Sdf.coverage(dist(x + 0.5, y + 0.5))
			buffer.writeu8(out, y * w + x, math.floor(a * 255 + 0.5))
		end
	end
	return out
end

return Sdf
