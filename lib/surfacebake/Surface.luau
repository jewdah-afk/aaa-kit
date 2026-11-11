--!strict
-- Surface: geometry-aware masks that make procedural textures look like real wear.
--   curvature  0.5 = flat, > 0.5 convex (edges: chipped paint, polish), < 0.5 concave (creases: dirt)
--   ao         1 = open sky, 0 = fully enclosed (crevices collect grime, moss, dust)
-- Both are computed per vertex on the welded mesh, then interpolated per texel through the
-- G-buffer's barycentrics. Per-vertex is cheap (vertices << texels) and smooth; detail on top of
-- it comes from noise in Layers.

local Mesh = require("./Mesh")
local Raster = require("./Raster")
type Mesh = Mesh.Mesh
type GBuffer = Raster.GBuffer

local Surface = {}

local function norm3(x: number, y: number, z: number): (number, number, number)
	local l = math.sqrt(x * x + y * y + z * z)
	if l < 1e-12 then
		return 0, 1, 0
	end
	return x / l, y / l, z / l
end

--- Smooth per-vertex normals {x,y,z,...}: the average of the authored corner normals at each
--- welded vertex (hard edges average to the bisector). Authored normals are exact on curved
--- surfaces, where area-weighted face normals skew with the triangulation.
function Surface.vertexNormals(m: Mesh): { number }
	local P, tris, N = m.P, m.tris, m.N
	local VN = table.create(#P, 0)
	for t = 1, #tris // 3 do
		for k = 0, 2 do
			local v = tris[t * 3 - 2 + k]
			local o = t * 9 - 8 + k * 3
			VN[v * 3 - 2] += N[o]
			VN[v * 3 - 1] += N[o + 1]
			VN[v * 3] += N[o + 2]
		end
	end
	for v = 1, #P // 3 do
		VN[v * 3 - 2], VN[v * 3 - 1], VN[v * 3] = norm3(VN[v * 3 - 2], VN[v * 3 - 1], VN[v * 3])
	end
	return VN
end

--- Per-vertex convexity from a discrete mean curvature: for each edge neighbour q of p,
--- k = -2 n.(q - p) / |q - p|^2 is the curvature of the circle through p and q tangent to the
--- surface at p (1/studs). The mean over neighbours, times the mesh's mean edge length, is
--- tessellation-independent and dimensionless; it maps to 0..1 with 0.5 = flat.
--- `gain` sharpens it (1-3 suits game meshes).
function Surface.vertexCurvature(m: Mesh, gain: number?): { number }
	local P, tris = m.P, m.tris
	local nv = #P // 3
	local VN = Surface.vertexNormals(m)
	local sum, cnt = table.create(nv, 0), table.create(nv, 0)
	local seen: { [number]: boolean } = {}
	local edgeLen, edges = 0, 0
	local function edge(a: number, b: number)
		local key = if a < b then a * 1e7 + b else b * 1e7 + a
		if seen[key] then
			return
		end
		seen[key] = true
		local dx, dy, dz = P[b * 3 - 2] - P[a * 3 - 2], P[b * 3 - 1] - P[a * 3 - 1], P[b * 3] - P[a * 3]
		local l2 = dx * dx + dy * dy + dz * dz
		if l2 < 1e-12 then
			return
		end
		edgeLen += math.sqrt(l2)
		edges += 1
		sum[a] += -2 * (VN[a * 3 - 2] * dx + VN[a * 3 - 1] * dy + VN[a * 3] * dz) / l2
		cnt[a] += 1
		sum[b] += 2 * (VN[b * 3 - 2] * dx + VN[b * 3 - 1] * dy + VN[b * 3] * dz) / l2
		cnt[b] += 1
	end
	for t = 1, #tris // 3 do
		local a, b, c = tris[t * 3 - 2], tris[t * 3 - 1], tris[t * 3]
		edge(a, b)
		edge(b, c)
		edge(c, a)
	end
	local L = if edges > 0 then edgeLen / edges else 1
	local k = gain or 1
	local out = table.create(nv, 0.5)
	for v = 1, nv do
		if cnt[v] > 0 then
			out[v] = math.clamp(0.5 + (sum[v] / cnt[v]) * L * k * 0.5, 0, 1)
		end
	end
	return out
end

-- Möller-Trumbore; returns hit distance or nil.
local function rayTri(ox, oy, oz, dx, dy, dz, P, a, b, c, tmax): number?
	local ax, ay, az = P[a * 3 - 2], P[a * 3 - 1], P[a * 3]
	local e1x, e1y, e1z = P[b * 3 - 2] - ax, P[b * 3 - 1] - ay, P[b * 3] - az
	local e2x, e2y, e2z = P[c * 3 - 2] - ax, P[c * 3 - 1] - ay, P[c * 3] - az
	local px, py, pz = dy * e2z - dz * e2y, dz * e2x - dx * e2z, dx * e2y - dy * e2x
	local det = e1x * px + e1y * py + e1z * pz
	if math.abs(det) < 1e-12 then
		return nil
	end
	local inv = 1 / det
	local sx, sy, sz = ox - ax, oy - ay, oz - az
	local u = (sx * px + sy * py + sz * pz) * inv
	if u < 0 or u > 1 then
		return nil
	end
	local qx, qy, qz = sy * e1z - sz * e1y, sz * e1x - sx * e1z, sx * e1y - sy * e1x
	local v = (dx * qx + dy * qy + dz * qz) * inv
	if v < 0 or u + v > 1 then
		return nil
	end
	local t = (e2x * qx + e2y * qy + e2z * qz) * inv
	if t > 1e-4 and t < tmax then
		return t
	end
	return nil
end

--- Per-vertex ambient occlusion: `rays` cosine-weighted hemisphere rays (deterministic spiral),
--- each blocked if it hits any triangle within `radius`. Triangles are bucketed in a uniform grid
--- of cell = radius, so each vertex only tests triangles near it. Cost ~ verts x rays x local tris.
function Surface.vertexAO(m: Mesh, radius: number, rays: number?): { number }
	local P, tris = m.P, m.tris
	local nv, nt = #P // 3, #tris // 3
	local VN = Surface.vertexNormals(m)
	local R = rays or 24
	local cell = radius
	local grid: { [number]: { number } } = {}
	local function key(ix: number, iy: number, iz: number): number
		return (ix + 512) * 1048576 + (iy + 512) * 1024 + (iz + 512)
	end
	for t = 1, nt do
		local a, b, c = tris[t * 3 - 2], tris[t * 3 - 1], tris[t * 3]
		local minx = math.min(P[a * 3 - 2], P[b * 3 - 2], P[c * 3 - 2])
		local maxx = math.max(P[a * 3 - 2], P[b * 3 - 2], P[c * 3 - 2])
		local miny = math.min(P[a * 3 - 1], P[b * 3 - 1], P[c * 3 - 1])
		local maxy = math.max(P[a * 3 - 1], P[b * 3 - 1], P[c * 3 - 1])
		local minz = math.min(P[a * 3], P[b * 3], P[c * 3])
		local maxz = math.max(P[a * 3], P[b * 3], P[c * 3])
		for ix = math.floor(minx / cell), math.floor(maxx / cell) do
			for iy = math.floor(miny / cell), math.floor(maxy / cell) do
				for iz = math.floor(minz / cell), math.floor(maxz / cell) do
					local k = key(ix, iy, iz)
					local list = grid[k]
					if not list then
						list = {}
						grid[k] = list
					end
					list[#list + 1] = t
				end
			end
		end
	end
	-- hemisphere directions around +Z (cosine-weighted spiral), rotated per vertex
	local dirs = {}
	local golden = math.pi * (3 - math.sqrt(5))
	for i = 0, R - 1 do
		local r = math.sqrt((i + 0.5) / R)
		local th = i * golden
		dirs[#dirs + 1] = { r * math.cos(th), r * math.sin(th), math.sqrt(1 - r * r) }
	end
	local out = table.create(nv, 1)
	for v = 1, nv do
		local nx, ny, nz = VN[v * 3 - 2], VN[v * 3 - 1], VN[v * 3]
		-- orthonormal basis around n
		local tx, ty, tz
		if math.abs(nx) < 0.9 then
			tx, ty, tz = norm3(0, nz, -ny) -- n x X
		else
			tx, ty, tz = norm3(-nz, 0, nx) -- n x Y
		end
		local bx, by, bz = ny * tz - nz * ty, nz * tx - nx * tz, nx * ty - ny * tx
		local ox, oy, oz = P[v * 3 - 2] + nx * radius * 0.01, P[v * 3 - 1] + ny * radius * 0.01, P[v * 3] + nz * radius * 0.01
		-- candidate triangles from the 27 neighbouring cells
		local cx, cy, cz = math.floor(ox / cell), math.floor(oy / cell), math.floor(oz / cell)
		local cand: { number } = {}
		local mark: { [number]: boolean } = {}
		for ix = cx - 1, cx + 1 do
			for iy = cy - 1, cy + 1 do
				for iz = cz - 1, cz + 1 do
					local list = grid[key(ix, iy, iz)]
					if list then
						for _, t in list do
							if not mark[t] then
								mark[t] = true
								cand[#cand + 1] = t
							end
						end
					end
				end
			end
		end
		local hits = 0
		for _, d in dirs do
			local dx = tx * d[1] + bx * d[2] + nx * d[3]
			local dy = ty * d[1] + by * d[2] + ny * d[3]
			local dz = tz * d[1] + bz * d[2] + nz * d[3]
			for _, t in cand do
				local a, b, c = tris[t * 3 - 2], tris[t * 3 - 1], tris[t * 3]
				if a ~= v and b ~= v and c ~= v and rayTri(ox, oy, oz, dx, dy, dz, P, a, b, c, radius) then
					hits += 1
					break
				end
			end
		end
		out[v] = 1 - hits / R
	end
	return out
end

--- Sharp edges: welded edges whose two faces meet at more than `angleDeg` (default 30), plus open
--- boundary edges. Returns a flat list {ax,ay,az, bx,by,bz, ...} of segments.
function Surface.sharpEdges(m: Mesh, angleDeg: number?): { number }
	local P, tris = m.P, m.tris
	local cosMax = math.cos(math.rad(angleDeg or 30))
	local faces: { [number]: { number } } = {}
	local fn = {}
	for t = 1, #tris // 3 do
		local a, b, c = tris[t * 3 - 2], tris[t * 3 - 1], tris[t * 3]
		local e1x, e1y, e1z = P[b * 3 - 2] - P[a * 3 - 2], P[b * 3 - 1] - P[a * 3 - 1], P[b * 3] - P[a * 3]
		local e2x, e2y, e2z = P[c * 3 - 2] - P[a * 3 - 2], P[c * 3 - 1] - P[a * 3 - 1], P[c * 3] - P[a * 3]
		local x, y, z = norm3(e1y * e2z - e1z * e2y, e1z * e2x - e1x * e2z, e1x * e2y - e1y * e2x)
		fn[t] = { x, y, z }
		for _, e in { { a, b }, { b, c }, { c, a } } do
			local lo, hi = math.min(e[1], e[2]), math.max(e[1], e[2])
			local key = lo * 1e7 + hi
			local list = faces[key]
			if not list then
				list = {}
				faces[key] = list
			end
			list[#list + 1] = t
		end
	end
	local out = {}
	for key, list in faces do
		local sharp = #list == 1
		if not sharp then
			for i = 2, #list do
				local p, q = fn[list[1]], fn[list[i]]
				-- winding may differ between faces, so compare unsigned
				if math.abs(p[1] * q[1] + p[2] * q[2] + p[3] * q[3]) < cosMax then
					sharp = true
				end
			end
		end
		if sharp then
			local hi = key % 1e7
			local lo = (key - hi) // 1e7
			out[#out + 1], out[#out + 2], out[#out + 3] = P[lo * 3 - 2], P[lo * 3 - 1], P[lo * 3]
			out[#out + 1], out[#out + 2], out[#out + 3] = P[hi * 3 - 2], P[hi * 3 - 1], P[hi * 3]
		end
	end
	return out
end

--- Per-texel distance (studs) from the surface point to the nearest sharp edge, capped at maxDist.
--- Edge wear, chipped paint and polished rims keyed on this have the same width in studs on any
--- tessellation. Segments are bucketed in a grid of cell = maxDist.
function Surface.edgeDistance(G: GBuffer, m: Mesh, maxDist: number, angleDeg: number?): buffer
	local S = Surface.sharpEdges(m, angleDeg)
	local cell = maxDist
	local grid: { [number]: { number } } = {}
	local function key(ix: number, iy: number, iz: number): number
		return (ix + 512) * 1048576 + (iy + 512) * 1024 + (iz + 512)
	end
	for s = 1, #S // 6 do
		local o = s * 6 - 5
		for ix = math.floor(math.min(S[o], S[o + 3]) / cell), math.floor(math.max(S[o], S[o + 3]) / cell) do
			for iy = math.floor(math.min(S[o + 1], S[o + 4]) / cell), math.floor(math.max(S[o + 1], S[o + 4]) / cell) do
				for iz = math.floor(math.min(S[o + 2], S[o + 5]) / cell), math.floor(math.max(S[o + 2], S[o + 5]) / cell) do
					local k = key(ix, iy, iz)
					local list = grid[k]
					if not list then
						list = {}
						grid[k] = list
					end
					list[#list + 1] = o
				end
			end
		end
	end
	local n = G.W * G.H
	local out = buffer.create(n * 4)
	for i = 0, n - 1 do
		local best = maxDist
		if buffer.readu8(G.cover, i) ~= 0 then
			local px, py, pz = Raster.readVec(G.pos, i)
			local cx, cy, cz = math.floor(px / cell), math.floor(py / cell), math.floor(pz / cell)
			for ix = cx - 1, cx + 1 do
				for iy = cy - 1, cy + 1 do
					for iz = cz - 1, cz + 1 do
						local list = grid[key(ix, iy, iz)]
						if list then
							for _, o in list do
								local ax, ay, az = S[o], S[o + 1], S[o + 2]
								local dx, dy, dz = S[o + 3] - ax, S[o + 4] - ay, S[o + 5] - az
								local l2 = dx * dx + dy * dy + dz * dz
								local t = if l2 > 0 then math.clamp(((px - ax) * dx + (py - ay) * dy + (pz - az) * dz) / l2, 0, 1) else 0
								local qx, qy, qz = ax + dx * t - px, ay + dy * t - py, az + dz * t - pz
								local d = math.sqrt(qx * qx + qy * qy + qz * qz)
								if d < best then
									best = d
								end
							end
						end
					end
				end
			end
		end
		buffer.writef32(out, i * 4, best)
	end
	return out
end

--- Interpolates a per-vertex scalar into a per-texel f32 buffer through the G-buffer.
function Surface.toTexels(G: GBuffer, m: Mesh, perVertex: { number }): buffer
	local n = G.W * G.H
	local out = buffer.create(n * 4)
	local tris = m.tris
	for i = 0, n - 1 do
		local t = buffer.readi32(G.tri, i * 4)
		if t > 0 then
			local b0, b1, b2 = Raster.readVec(G.bar, i)
			local v = b0 * perVertex[tris[t * 3 - 2]] + b1 * perVertex[tris[t * 3 - 1]] + b2 * perVertex[tris[t * 3]]
			buffer.writef32(out, i * 4, v)
		end
	end
	return out
end

return Surface
