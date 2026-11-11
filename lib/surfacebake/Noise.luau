--!strict
-- Noise: 3D fields evaluated on the surface in object space, so they are continuous across UV seams.
-- Built on math.noise (Luau's native 3D Perlin, ~40 ns per call in lune).

local Noise = {}

--- Fractal Brownian motion in about -1..1. lacunarity 2, gain 0.5 are the classic defaults.
function Noise.fbm(x: number, y: number, z: number, octaves: number, lacunarity: number?, gain: number?): number
	local lac, g = lacunarity or 2, gain or 0.5
	local sum, amp, norm = 0, 1, 0
	for _ = 1, octaves do
		sum += math.noise(x, y, z) * amp
		norm += amp
		amp *= g
		x, y, z = x * lac + 17.3, y * lac + 9.1, z * lac + 3.7
	end
	return sum / norm * 1.6 -- math.noise rarely exceeds +-0.6; rescale toward +-1
end

--- Ridged multifractal in 0..1: sharp crests, good for veins, scratches, lava cracks.
function Noise.ridged(x: number, y: number, z: number, octaves: number): number
	local sum, amp, norm = 0, 1, 0
	for _ = 1, octaves do
		local n = 1 - math.abs(math.noise(x, y, z) * 1.6)
		sum += n * n * amp
		norm += amp
		amp *= 0.5
		x, y, z = x * 2 + 17.3, y * 2 + 9.1, z * 2 + 3.7
	end
	return sum / norm
end

--- Domain-warped fBm: the input is offset by another fBm, giving swirled, organic shapes.
function Noise.warped(x: number, y: number, z: number, octaves: number, strength: number): number
	local wx = Noise.fbm(x + 5.2, y + 1.3, z + 2.8, 3)
	local wy = Noise.fbm(x + 1.7, y + 9.2, z + 4.1, 3)
	local wz = Noise.fbm(x + 8.3, y + 2.8, z + 7.7, 3)
	return Noise.fbm(x + wx * strength, y + wy * strength, z + wz * strength, octaves)
end

local function hash3(ix: number, iy: number, iz: number, k: number): number
	local h = bit32.bxor(ix * 73856093, iy * 19349663, iz * 83492791, k * 2654435761)
	h = bit32.bxor(h, bit32.rshift(h, 13))
	h = (h * 1274126177) % 4294967296
	h = bit32.bxor(h, bit32.rshift(h, 16))
	return h / 4294967296
end

--- 3D Voronoi (Worley). Returns F1, F2 (distances to the nearest and second-nearest feature
--- point, in cell units) and a 0..1 id of the nearest cell. F2 - F1 ~ 0 on cell borders: cracks,
--- tiles, scales, cobbles. jitter 0..1 (1 = fully random points).
function Noise.voronoi(x: number, y: number, z: number, jitter: number?): (number, number, number)
	local j = jitter or 1
	local cx, cy, cz = math.floor(x), math.floor(y), math.floor(z)
	local f1, f2, id = 9, 9, 0
	for dx = -1, 1 do
		for dy = -1, 1 do
			for dz = -1, 1 do
				local ix, iy, iz = cx + dx, cy + dy, cz + dz
				local px = ix + 0.5 + (hash3(ix, iy, iz, 1) - 0.5) * j
				local py = iy + 0.5 + (hash3(ix, iy, iz, 2) - 0.5) * j
				local pz = iz + 0.5 + (hash3(ix, iy, iz, 3) - 0.5) * j
				local d = math.sqrt((px - x) ^ 2 + (py - y) ^ 2 + (pz - z) ^ 2)
				if d < f1 then
					f2 = f1
					f1 = d
					id = hash3(ix, iy, iz, 4)
				elseif d < f2 then
					f2 = d
				end
			end
		end
	end
	return f1, f2, id
end

--- Triplanar sample of a tiling RGBA8 image (any 2D algorithm render: reaction-diffusion, cellular
--- automata, a pixelfx frame, a painted tile) projected onto the surface along X, Y and Z and
--- blended by the normal. `sharp` > 1 narrows the blend band. Returns r, g, b, a in 0..1.
function Noise.triplanar(img: buffer, w: number, h: number, px: number, py: number, pz: number, nx: number, ny: number, nz: number, scale: number, sharp: number?): (number, number, number, number)
	local s = sharp or 4
	local ax, ay, az = math.abs(nx) ^ s, math.abs(ny) ^ s, math.abs(nz) ^ s
	local sum = ax + ay + az
	ax, ay, az = ax / sum, ay / sum, az / sum
	local r, g, b, a = 0, 0, 0, 0
	local function tap(u: number, v: number, wgt: number)
		if wgt < 1e-3 then
			return
		end
		local x = math.floor(u * scale * w) % w
		local y = math.floor(v * scale * h) % h
		local o = (y * w + x) * 4
		r += buffer.readu8(img, o) / 255 * wgt
		g += buffer.readu8(img, o + 1) / 255 * wgt
		b += buffer.readu8(img, o + 2) / 255 * wgt
		a += buffer.readu8(img, o + 3) / 255 * wgt
	end
	tap(pz, py, ax)
	tap(px, pz, ay)
	tap(px, py, az)
	return r, g, b, a
end

return Noise
