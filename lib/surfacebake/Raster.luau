--!strict
-- Raster: bakes a mesh into a UV-space G-buffer. For every texel the model covers, it stores the
-- object-space position, the shading normal and a tangent frame, so any 3D algorithm can be
-- evaluated "on the surface" and come out seamless across UV islands.
--
--   G.cover  u8   0 empty, 1 inside a triangle, 2 gutter (filled by dilation)
--   G.tri    i32  triangle index (1-based), 0 if empty
--   G.pos    f32  x,y,z            object space
--   G.nrm    f32  x,y,z            unit, interpolated from corner normals
--   G.tan    f32  x,y,z            unit tangent along +u (Gram-Schmidt against the normal)
--   G.bit    f32  x,y,z            unit bitangent along +v (= down the image rows), orthogonal to n and t
--   G.bar    f32  b0,b1,b2         barycentric weights inside G.tri
--
-- Texel (x, y) samples UV ((x + 0.5) / W, (y + 0.5) / H): row 0 is v = 0, matching EditableImage rows.

local Mesh = require("./Mesh")
type Mesh = Mesh.Mesh

export type GBuffer = {
	W: number,
	H: number,
	cover: buffer,
	tri: buffer,
	pos: buffer,
	nrm: buffer,
	tan: buffer,
	bit: buffer,
	bar: buffer,
	covered: number,
}

local Raster = {}

local function norm3(x: number, y: number, z: number): (number, number, number)
	local l = math.sqrt(x * x + y * y + z * z)
	if l < 1e-12 then
		return 0, 0, 1
	end
	return x / l, y / l, z / l
end

-- Per-triangle tangent along +u and bitangent along +v from position and UV deltas.
local function triTangent(m: Mesh, t: number): (number, number, number, number, number, number)
	local P, tris, UV = m.P, m.tris, m.UV
	local ia, ib, ic = tris[t * 3 - 2], tris[t * 3 - 1], tris[t * 3]
	local ax, ay, az = P[ia * 3 - 2], P[ia * 3 - 1], P[ia * 3]
	local e1x, e1y, e1z = P[ib * 3 - 2] - ax, P[ib * 3 - 1] - ay, P[ib * 3] - az
	local e2x, e2y, e2z = P[ic * 3 - 2] - ax, P[ic * 3 - 1] - ay, P[ic * 3] - az
	local u0, v0 = UV[t * 6 - 5], UV[t * 6 - 4]
	local du1, dv1 = UV[t * 6 - 3] - u0, UV[t * 6 - 2] - v0
	local du2, dv2 = UV[t * 6 - 1] - u0, UV[t * 6] - v0
	local det = du1 * dv2 - du2 * dv1
	if math.abs(det) < 1e-14 then
		local ax2, ay2, az2 = norm3(e1x, e1y, e1z)
		local bx2, by2, bz2 = norm3(e2x, e2y, e2z)
		return ax2, ay2, az2, bx2, by2, bz2
	end
	local r = 1 / det
	local tx, ty, tz = norm3((e1x * dv2 - e2x * dv1) * r, (e1y * dv2 - e2y * dv1) * r, (e1z * dv2 - e2z * dv1) * r)
	local bx, by, bz = norm3((e2x * du1 - e1x * du2) * r, (e2y * du1 - e1y * du2) * r, (e2z * du1 - e1z * du2) * r)
	return tx, ty, tz, bx, by, bz
end

local function writeTexel(G: GBuffer, m: Mesh, t: number, i: number, b0: number, b1: number, b2: number, tx: number, ty: number, tz: number, vx: number, vy: number, vz: number)
	local P, tris, N = m.P, m.tris, m.N
	local ia, ib, ic = tris[t * 3 - 2], tris[t * 3 - 1], tris[t * 3]
	local px = b0 * P[ia * 3 - 2] + b1 * P[ib * 3 - 2] + b2 * P[ic * 3 - 2]
	local py = b0 * P[ia * 3 - 1] + b1 * P[ib * 3 - 1] + b2 * P[ic * 3 - 1]
	local pz = b0 * P[ia * 3] + b1 * P[ib * 3] + b2 * P[ic * 3]
	local nx, ny, nz = norm3(
		b0 * N[t * 9 - 8] + b1 * N[t * 9 - 5] + b2 * N[t * 9 - 2],
		b0 * N[t * 9 - 7] + b1 * N[t * 9 - 4] + b2 * N[t * 9 - 1],
		b0 * N[t * 9 - 6] + b1 * N[t * 9 - 3] + b2 * N[t * 9]
	)
	-- Gram-Schmidt the tangent against the interpolated normal
	local d = tx * nx + ty * ny + tz * nz
	local qx, qy, qz = norm3(tx - nx * d, ty - ny * d, tz - nz * d)
	-- bitangent: +v direction made orthogonal to n and the tangent
	local dn, dq = vx * nx + vy * ny + vz * nz, vx * qx + vy * qy + vz * qz
	local wx, wy, wz = norm3(vx - nx * dn - qx * dq, vy - ny * dn - qy * dq, vz - nz * dn - qz * dq)
	local o = i * 12
	buffer.writef32(G.pos, o, px)
	buffer.writef32(G.pos, o + 4, py)
	buffer.writef32(G.pos, o + 8, pz)
	buffer.writef32(G.nrm, o, nx)
	buffer.writef32(G.nrm, o + 4, ny)
	buffer.writef32(G.nrm, o + 8, nz)
	buffer.writef32(G.tan, o, qx)
	buffer.writef32(G.tan, o + 4, qy)
	buffer.writef32(G.tan, o + 8, qz)
	buffer.writef32(G.bit, o, wx)
	buffer.writef32(G.bit, o + 4, wy)
	buffer.writef32(G.bit, o + 8, wz)
	buffer.writef32(G.bar, o, b0)
	buffer.writef32(G.bar, o + 4, b1)
	buffer.writef32(G.bar, o + 8, b2)
	buffer.writei32(G.tri, i * 4, t)
end

--- Rasterises every triangle into UV space. Texels whose centre lies inside a triangle (with a
--- tiny tolerance so shared edges never leave cracks) are covered.
function Raster.bake(m: Mesh, W: number, H: number): GBuffer
	local n = W * H
	local G: GBuffer = {
		W = W,
		H = H,
		cover = buffer.create(n),
		tri = buffer.create(n * 4),
		pos = buffer.create(n * 12),
		nrm = buffer.create(n * 12),
		tan = buffer.create(n * 12),
		bit = buffer.create(n * 12),
		bar = buffer.create(n * 12),
		covered = 0,
	}
	local UV = m.UV
	local eps = 1e-7
	for t = 1, #m.tris // 3 do
		local ax, ay = UV[t * 6 - 5] * W, UV[t * 6 - 4] * H
		local bx, by = UV[t * 6 - 3] * W, UV[t * 6 - 2] * H
		local cx, cy = UV[t * 6 - 1] * W, UV[t * 6] * H
		local area = (bx - ax) * (cy - ay) - (cx - ax) * (by - ay)
		if math.abs(area) > 1e-12 then
			local tx, ty, tz, vx, vy, vz = triTangent(m, t)
			local x0 = math.max(0, math.floor(math.min(ax, bx, cx) - 0.5))
			local x1 = math.min(W - 1, math.ceil(math.max(ax, bx, cx) - 0.5))
			local y0 = math.max(0, math.floor(math.min(ay, by, cy) - 0.5))
			local y1 = math.min(H - 1, math.ceil(math.max(ay, by, cy) - 0.5))
			local inv = 1 / area
			for y = y0, y1 do
				local py = y + 0.5
				for x = x0, x1 do
					local px = x + 0.5
					local w0 = ((bx - px) * (cy - py) - (cx - px) * (by - py)) * inv
					local w1 = ((cx - px) * (ay - py) - (ax - px) * (cy - py)) * inv
					local w2 = 1 - w0 - w1
					if w0 >= -eps and w1 >= -eps and w2 >= -eps then
						local i = y * W + x
						if buffer.readu8(G.cover, i) == 0 then
							G.covered += 1
						end
						buffer.writeu8(G.cover, i, 1)
						writeTexel(G, m, t, i, w0, w1, w2, tx, ty, tz, vx, vy, vz)
					end
				end
			end
		end
	end
	return G
end

--- Grows every island outward by `px` texels, copying the nearest covered texel's attributes, so
--- bilinear filtering and mipmaps never pull the empty background colour into the seams.
--- Industry practice is 2-16 px of padding depending on resolution; 4 px at 512 is a sane default.
function Raster.dilate(G: GBuffer, px: number)
	local W, H = G.W, G.H
	for _ = 1, px do
		local fill = {}
		for y = 0, H - 1 do
			for x = 0, W - 1 do
				local i = y * W + x
				if buffer.readu8(G.cover, i) == 0 then
					-- 4-neighbours first, then diagonals, so growth stays round-ish
					for _, d in { { 1, 0 }, { -1, 0 }, { 0, 1 }, { 0, -1 }, { 1, 1 }, { -1, -1 }, { 1, -1 }, { -1, 1 } } do
						local nx, ny = x + d[1], y + d[2]
						if nx >= 0 and nx < W and ny >= 0 and ny < H then
							local j = ny * W + nx
							if buffer.readu8(G.cover, j) ~= 0 then
								fill[#fill + 1] = i
								fill[#fill + 1] = j
								break
							end
						end
					end
				end
			end
		end
		for k = 1, #fill, 2 do
			local i, j = fill[k], fill[k + 1]
			buffer.writeu8(G.cover, i, 2)
			buffer.writei32(G.tri, i * 4, buffer.readi32(G.tri, j * 4))
			buffer.copy(G.pos, i * 12, G.pos, j * 12, 12)
			buffer.copy(G.nrm, i * 12, G.nrm, j * 12, 12)
			buffer.copy(G.tan, i * 12, G.tan, j * 12, 12)
			buffer.copy(G.bit, i * 12, G.bit, j * 12, 12)
			buffer.copy(G.bar, i * 12, G.bar, j * 12, 12)
		end
	end
end

function Raster.readVec(b: buffer, i: number): (number, number, number)
	local o = i * 12
	return buffer.readf32(b, o), buffer.readf32(b, o + 4), buffer.readf32(b, o + 8)
end

return Raster
