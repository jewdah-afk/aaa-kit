--!strict
-- Parallax: depth illusions Roblox can't do with shaders, done per texel on the CPU into an
-- EditableImage (small images, updated when the camera moves) or with stacked geometry.
--
--   Parallax.pom        parallax occlusion mapping: a height field seen at an angle, with
--                        occlusion, inside a flat surface (portals, grates, gem interiors, cracks)
--   Parallax.interior   interior mapping: rooms with walls, floor and ceiling behind every window
--                        of a flat facade, correct for any view angle
--   Parallax.layers     multi-layer 2D parallax (UI backdrops, skyboxes, depth cards)
--   Parallax.zoom       infinite zoom: octaves of a tile blended over log-scale, so zooming in
--                        never ends and never pops (plus an optional spiral)
--   Parallax.shells     shell texturing: N offset copies of a mesh with alpha masks give fur,
--                        grass and moss real depth and silhouette
--
-- Conventions: images are RGBA8 buffers, row 0 at the top. View directions are in the surface's
-- tangent space: x = +u (right), y = image-up, z = out of the surface toward the eye (z > 0).

local Mesh = require("./Mesh")
local Surface = require("./Surface")
type Mesh = Mesh.Mesh

local Parallax = {}

local function u8(v: number): number
	return math.clamp(math.floor(v * 255 + 0.5), 0, 255)
end

local function hash2(x: number, y: number, k: number): number
	local h = bit32.bxor(x * 73856093, y * 19349663, k * 83492791)
	h = bit32.bxor(h, bit32.rshift(h, 13))
	h = (h * 1274126177) % 4294967296
	h = bit32.bxor(h, bit32.rshift(h, 16))
	return h / 4294967296
end

--- Parallax occlusion mapping.
--- height: f32 buffer (hw x hh) of 0..1 (1 = the top surface), colour: RGBA8 (hw x hh).
--- out: RGBA8 (ow x oh). view: tangent-space vector toward the eye. depth: how deep the field
--- goes, in uv units. steps: layers to march (8 at grazing angles is the floor; 16-32 for close-ups).
--- shade: darken with depth (0..1) to fake the light falloff into the hole.
function Parallax.pom(height: buffer, colour: buffer, hw: number, hh: number, out: buffer, ow: number, oh: number, vx: number, vy: number, vz: number, depth: number, steps: number, shade: number?)
	local sh = shade or 0.5
	vz = math.max(vz, 0.08)
	-- uv change per unit of depth, travelling into the surface away from the eye
	local dU = -vx / vz * depth
	local dV = vy / vz * depth -- image-up is -v (rows), so +vy moves the ray down the rows
	-- more layers at grazing angles (classic POM step interpolation)
	local n = math.floor(steps * (1 + (1 - vz) * 1.5))
	local stepD = 1 / n
	local function hAt(u: number, v: number): number
		local x = math.floor(u * hw) % hw
		local y = math.floor(v * hh) % hh
		return buffer.readf32(height, (y * hw + x) * 4)
	end
	for oy = 0, oh - 1 do
		local v0 = (oy + 0.5) / oh
		for ox = 0, ow - 1 do
			local u0 = (ox + 0.5) / ow
			local d = 0 -- ray depth below the top, 0..1
			local u, v = u0, v0
			local surf = 1 - hAt(u, v) -- depth of the surface at this uv
			local prevD, prevSurf = 0, surf
			while d < surf and d < 1 do
				prevD, prevSurf = d, surf
				d += stepD
				u += dU * stepD
				v += dV * stepD
				surf = 1 - hAt(u, v)
			end
			-- refine between the last two layers (linear intersection)
			local a = prevSurf - prevD
			local b = d - surf
			local f = if a + b > 1e-6 then a / (a + b) else 0
			local fu = u - dU * stepD * (1 - f)
			local fv = v - dV * stepD * (1 - f)
			local hitD = prevD + (d - prevD) * f
			-- bilinear colour fetch: nearest-texel fetch makes thin bright features (cracks, runes)
			-- crawl from frame to frame as the view moves, which can fail the WCAG flash check
			local gx, gy = fu * hw - 0.5, fv * hh - 0.5
			local x0, y0 = math.floor(gx), math.floor(gy)
			local ax, ay = gx - x0, gy - y0
			local r, g, bb = 0, 0, 0
			for k2 = 0, 3 do
				local dx, dy = k2 % 2, k2 // 2
				local w = (if dx == 1 then ax else 1 - ax) * (if dy == 1 then ay else 1 - ay)
				local c = buffer.readu32(colour, (((y0 + dy) % hh) * hw + ((x0 + dx) % hw)) * 4)
				r += (c % 256) * w
				g += ((c // 256) % 256) * w
				bb += ((c // 65536) % 256) * w
			end
			local k = 1 - sh * hitD
			r, g, bb = r * k, g * k, bb * k
			buffer.writeu32(out, (oy * ow + ox) * 4, math.floor(r) + math.floor(g) * 256 + math.floor(bb) * 65536 + 255 * 16777216)
		end
	end
end

--- Interior mapping: a facade of rooms (rx x ry windows) on a flat surface, each a box of depth
--- `roomDepth` (in window widths). Per texel: one ray-box intersection, no textures needed.
--- Rooms get a random wall tint and lights on/off from `seed`; frames are drawn between windows.
function Parallax.interior(out: buffer, ow: number, oh: number, rx: number, ry: number, vx: number, vy: number, vz: number, roomDepth: number, seed: number?)
	local sd = seed or 1
	vz = math.max(vz, 0.05)
	-- ray direction into the room (away from the eye): x right, y up, z into the wall
	local dx, dy, dz = -vx, -vy, vz
	for oy = 0, oh - 1 do
		local gy = (1 - (oy + 0.5) / oh) * ry -- up is +y
		local cy = math.floor(gy)
		local fy = gy - cy
		for ox = 0, ow - 1 do
			local gx = (ox + 0.5) / ow * rx
			local cx = math.floor(gx)
			local fx = gx - cx
			local q = (oy * ow + ox) * 4
			-- window frame / wall between windows
			local mx, my = math.min(fx, 1 - fx), math.min(fy, 1 - fy)
			if mx < 0.08 or my < 0.1 then
				local wall = 0.55 + 0.1 * hash2(cx, cy, sd + 9)
				buffer.writeu32(out, q, u8(wall * 0.72) + u8(wall * 0.66) * 256 + u8(wall * 0.6) * 65536 + 255 * 16777216)
			else
				-- room-local coords: x,y in 0..1 across the window, z depth 0..roomDepth
				local px, py = fx, fy
				local tX = if dx > 0 then (1 - px) / dx elseif dx < 0 then -px / dx else math.huge
				local tY = if dy > 0 then (1 - py) / dy elseif dy < 0 then -py / dy else math.huge
				local tZ = roomDepth / dz
				local t = math.min(tX, tY, tZ)
				local hx, hy, hz = px + dx * t, py + dy * t, dz * t / roomDepth -- hz 0..1 into the room
				local lit = hash2(cx, cy, sd) > 0.35
				local tint = hash2(cx, cy, sd + 1)
				local r, g, b
				if t == tZ then -- back wall, with a "picture" block
					r, g, b = 0.75 - tint * 0.2, 0.68, 0.55 + tint * 0.25
					if math.abs(hx - 0.5) < 0.15 and math.abs(hy - 0.6) < 0.12 then
						r, g, b = 0.25 + tint * 0.5, 0.3, 0.45
					end
				elseif t == tY then
					if dy < 0 then -- floor: checker
						local ch = (math.floor(hx * 4) + math.floor(hz * 4 * roomDepth)) % 2
						r, g, b = 0.45 + ch * 0.12, 0.33 + ch * 0.08, 0.24
					else -- ceiling with a lamp
						r, g, b = 0.85, 0.84, 0.8
						if (hx - 0.5) ^ 2 + (hz - 0.5) ^ 2 < 0.02 then
							r, g, b = 1.6, 1.5, 1.2
						end
					end
				else -- side walls
					r, g, b = 0.68 - tint * 0.15, 0.62 + tint * 0.1, 0.52
				end
				-- depth falloff and lights
				local k = (1 - hz * 0.45) * (if lit then 1.0 else 0.22)
				if lit then
					r, g, b = r * 1.05, g * 0.98, b * 0.85
				end
				-- glass: a faint reflection rising toward the top of the window
				local refl = 0.08 + 0.12 * fy
				buffer.writeu32(out, q, u8(r * k + refl * 0.6) + u8(g * k + refl * 0.7) * 256 + u8(b * k + refl * 0.9) * 65536 + 255 * 16777216)
			end
		end
	end
end

export type Layer = { img: buffer, w: number, h: number, depth: number } -- depth 0 = screen plane, 1 = far

--- Multi-layer 2D parallax: back-to-front composite, each layer offset by view * (1 - depth) and
--- wrapped horizontally. Layers use alpha; layer 1 is the farthest. (ox, oy) is the camera offset.
function Parallax.layers(out: buffer, ow: number, oh: number, layers: { Layer }, camX: number, camY: number)
	for y = 0, oh - 1 do
		for x = 0, ow - 1 do
			local r, g, b = 0, 0, 0
			for _, L in layers do
				local f = 1 - L.depth
				local sx = math.floor((x + camX * f) * L.w / ow) % L.w
				local sy = math.clamp(math.floor((y + camY * f) * L.h / oh), 0, L.h - 1)
				local c = buffer.readu32(L.img, (sy * L.w + sx) * 4)
				local a = (c // 16777216) / 255
				if a > 0 then
					r += ((c % 256) - r) * a
					g += (((c // 256) % 256) - g) * a
					b += (((c // 65536) % 256) - b) * a
				end
			end
			buffer.writeu32(out, (y * ow + x) * 4, math.floor(r) + math.floor(g) * 256 + math.floor(b) * 65536 + 255 * 16777216)
		end
	end
end

--- Infinite zoom. z = log2 of the zoom (increase it every frame; it never needs resetting).
--- K octaves of the tile are drawn at scales 2^(k - frac(z)) and blended with weights that fade
--- in at the small end and out at the large end, so frac(z) -> 1 lands exactly on the next
--- octave: seamless forever. spin (radians per octave) turns it into a spiral. base = tiles
--- across the screen at the coarsest octave.
function Parallax.zoom(out: buffer, ow: number, oh: number, tile: buffer, tw: number, th: number, z: number, K: number, spin: number?, base: number?)
	local f = z - math.floor(z)
	local sp = spin or 0
	local b0 = base or 0.5
	local aspect = ow / oh
	-- per-octave constants
	local scale, cosA, sinA, wgt = {}, {}, {}, {}
	local wsum = 0
	for k = 0, K - 1 do
		local x = k - f -- -1 .. K-1
		scale[k + 1] = b0 * 2 ^ x
		local a = sp * x
		cosA[k + 1], sinA[k + 1] = math.cos(a), math.sin(a)
		local w = math.sin(math.pi * (x + 1) / K)
		wgt[k + 1] = w * w
		wsum += w * w
	end
	for y = 0, oh - 1 do
		local py = ((y + 0.5) / oh - 0.5)
		for x = 0, ow - 1 do
			local px = ((x + 0.5) / ow - 0.5) * aspect
			local r, g, b = 0, 0, 0
			for k = 1, K do
				local s = scale[k]
				local u = (px * cosA[k] - py * sinA[k]) * s
				local v = (px * sinA[k] + py * cosA[k]) * s
				local tx = math.floor(u * tw) % tw
				local ty = math.floor(v * th) % th
				local c = buffer.readu32(tile, (ty * tw + tx) * 4)
				local w = wgt[k]
				r += (c % 256) * w
				g += ((c // 256) % 256) * w
				b += ((c // 65536) % 256) * w
			end
			local vig = 1 - 0.6 * (px * px + py * py)
			buffer.writeu32(out, (y * ow + x) * 4, math.floor(r / wsum * vig) + math.floor(g / wsum * vig) * 256 + math.floor(b / wsum * vig) * 65536 + 255 * 16777216)
		end
	end
end

export type ShellSpec = {
	count: number, -- shells (8-24)
	length: number, -- studs from the base surface to the outermost shell
	density: number, -- strands per UV cell kept (0..1)
	cells: number, -- strand grid cells across the texture
	thickness: number?, -- strand radius at the root, in cells (default 0.45)
	root: { number }, -- colour at the root
	tip: { number }, -- colour at the tip
	gravity: { number }?, -- {x,y,z} droop in studs at the tip (fur sag, grass lean)
}

--- Shell texturing. Returns `count` meshes (the base mesh pushed out along its vertex normals,
--- plus gravity, more at the tips) and `count` RGBA8 masks of size S x S in the mesh's UV space.
--- Strands are a jittered grid in UV; each has a random height and tapers toward its tip, so
--- outer shells show fewer, thinner dots. Alpha 0 = see through.
--- Roblox: one MeshPart per shell (EditableMesh from these positions), each with its mask as the
--- colour map of a SurfaceAppearance using transparency. [UNVERIFIED in Studio: AlphaMode setup.]
function Parallax.shells(m: Mesh, spec: ShellSpec, S: number): ({ Mesh }, { buffer })
	local VN = Surface.vertexNormals(m)
	local n = spec.count
	local meshes, masks = {}, {}
	local grav = spec.gravity or { 0, 0, 0 }
	for i = 1, n do
		local h = i / n
		local P = table.create(#m.P, 0)
		for v = 1, #m.P // 3 do
			local off = spec.length * h
			local droop = h * h -- gravity bends the tips more than the roots
			P[v * 3 - 2] = m.P[v * 3 - 2] + VN[v * 3 - 2] * off + grav[1] * droop
			P[v * 3 - 1] = m.P[v * 3 - 1] + VN[v * 3 - 1] * off + grav[2] * droop
			P[v * 3] = m.P[v * 3] + VN[v * 3] * off + grav[3] * droop
		end
		meshes[i] = { P = P, tris = m.tris, UV = m.UV, N = m.N }
		local buf = buffer.create(S * S * 4)
		local cells = spec.cells
		local rad0 = spec.thickness or 0.45
		local r1, g1, b1 = spec.root[1], spec.root[2], spec.root[3]
		local r2, g2, b2 = spec.tip[1], spec.tip[2], spec.tip[3]
		local cr, cg, cb = r1 + (r2 - r1) * h, g1 + (g2 - g1) * h, b1 + (b2 - b1) * h
		local col = u8(cr) + u8(cg) * 256 + u8(cb) * 65536
		for y = 0, S - 1 do
			local gy = (y + 0.5) / S * cells
			local cy = math.floor(gy)
			for x = 0, S - 1 do
				local gx = (x + 0.5) / S * cells
				local cx = math.floor(gx)
				local keep = hash2(cx, cy, 1) < spec.density
				local alpha = 0
				if i == 1 then
					alpha = 255 -- the innermost shell is solid: it is the "skin"
				elseif keep then
					local hgt = 0.35 + 0.65 * hash2(cx, cy, 2)
					if h <= hgt then
						local jx = 0.5 + (hash2(cx, cy, 3) - 0.5) * 0.4
						local jy = 0.5 + (hash2(cx, cy, 4) - 0.5) * 0.4
						local d = math.sqrt((gx - cx - jx) ^ 2 + (gy - cy - jy) ^ 2)
						local rad = rad0 * (1 - h / hgt) -- taper to a point at the strand's tip
						if d < rad then
							alpha = 255
						end
					end
				end
				buffer.writeu32(buf, (y * S + x) * 4, col + alpha * 16777216)
			end
		end
		masks[i] = buf
	end
	return meshes, masks
end

return Parallax
