--!strict
-- Mesh: the plain triangle data the baker works on, plus procedural test meshes.
--
--   P    {x,y,z, ...}             shared (welded) vertex positions, 3 per vertex
--   tris {a,b,c, ...}             1-based vertex indices, 3 per triangle
--   UV   {u,v, ...}               per-corner UVs, 6 per triangle (0..1, v down like EditableImage rows)
--   N    {x,y,z, ...}             per-corner normals, 9 per triangle (split normals = hard edges)
--
-- Positions are shared so curvature and AO can see neighbours; UVs and normals are per corner so
-- seams and hard edges work exactly like EditableMesh (positions per vertex, attributes per face corner).
-- Roblox adapter: SurfaceBake.Apply.fromEditableMesh builds this from an EditableMesh.

export type Mesh = { P: { number }, tris: { number }, UV: { number }, N: { number } }

local Mesh = {}

function Mesh.new(): Mesh
	return { P = {}, tris = {}, UV = {}, N = {} }
end

function Mesh.vertexCount(m: Mesh): number
	return #m.P // 3
end

function Mesh.triCount(m: Mesh): number
	return #m.tris // 3
end

-- Adds a vertex, welding to an existing one at the same position (within 1e-5).
local function addVertex(m: Mesh, weld: { [string]: number }, x: number, y: number, z: number): number
	-- integer grid key (1e-5) so -0.0 and 0.0 weld together
	local key = string.format("%d,%d,%d", math.floor(x * 1e5 + 0.5), math.floor(y * 1e5 + 0.5), math.floor(z * 1e5 + 0.5))
	local id = weld[key]
	if id then
		return id
	end
	local P = m.P
	P[#P + 1], P[#P + 2], P[#P + 3] = x, y, z
	id = #P // 3
	weld[key] = id
	return id
end

-- Appends one triangle: corners are {x,y,z, u,v, nx,ny,nz}.
local function addTri(m: Mesh, weld, a: { number }, b: { number }, c: { number })
	local tris, UV, N = m.tris, m.UV, m.N
	for _, k in { a, b, c } do
		tris[#tris + 1] = addVertex(m, weld, k[1], k[2], k[3])
		UV[#UV + 1], UV[#UV + 2] = k[4], k[5]
		N[#N + 1], N[#N + 2], N[#N + 3] = k[6], k[7], k[8]
	end
end

--- UV sphere of radius r: one UV island with a seam at u = 0/1 and poles at v = 0 and 1.
function Mesh.sphere(r: number, segs: number, rings: number): Mesh
	local m, weld = Mesh.new(), {}
	local function corner(i: number, j: number)
		local u, v = i / segs, j / rings
		local th, ph = u * 2 * math.pi, v * math.pi
		local nx, ny, nz = math.sin(ph) * math.cos(th), math.cos(ph), math.sin(ph) * math.sin(th)
		return { nx * r, ny * r, nz * r, u, v, nx, ny, nz }
	end
	for j = 0, rings - 1 do
		for i = 0, segs - 1 do
			local a, b, c, d = corner(i, j), corner(i + 1, j), corner(i + 1, j + 1), corner(i, j + 1)
			if j > 0 then
				addTri(m, weld, a, c, b)
			end
			if j < rings - 1 then
				addTri(m, weld, a, d, c)
			end
		end
	end
	return m
end

--- Box with half-extents hx, hy, hz and a 3x2 UV atlas (one cell per face, 2-texel-safe margins).
--- Normals are split per face (hard edges), positions welded (so edges have curvature).
function Mesh.box(hx: number, hy: number, hz: number, div: number?): Mesh
	local m, weld = Mesh.new(), {}
	local n = div or 4
	local faces = {
		-- normal, u axis, v axis, atlas cell (col,row)
		{ { 1, 0, 0 }, { 0, 0, -1 }, { 0, -1, 0 }, 0, 0 },
		{ { -1, 0, 0 }, { 0, 0, 1 }, { 0, -1, 0 }, 1, 0 },
		{ { 0, 1, 0 }, { 1, 0, 0 }, { 0, 0, 1 }, 2, 0 },
		{ { 0, -1, 0 }, { 1, 0, 0 }, { 0, 0, -1 }, 0, 1 },
		{ { 0, 0, 1 }, { 1, 0, 0 }, { 0, -1, 0 }, 1, 1 },
		{ { 0, 0, -1 }, { -1, 0, 0 }, { 0, -1, 0 }, 2, 1 },
	}
	local H = { hx, hy, hz }
	local margin = 0.02
	for _, f in faces do
		local nrm, ua, va, col, row = f[1], f[2], f[3], f[4], f[5]
		local function corner(s: number, t: number)
			-- s, t in -1..1 across the face
			local p = {}
			for k = 1, 3 do
				p[k] = (nrm[k] + ua[k] * s + va[k] * t) * H[k]
			end
			local u = (col + margin + (s + 1) / 2 * (1 - 2 * margin)) / 3
			local v = (row + margin + (t + 1) / 2 * (1 - 2 * margin)) / 2
			return { p[1], p[2], p[3], u, v, nrm[1], nrm[2], nrm[3] }
		end
		for i = 0, n - 1 do
			for j = 0, n - 1 do
				local s0, s1 = -1 + 2 * i / n, -1 + 2 * (i + 1) / n
				local t0, t1 = -1 + 2 * j / n, -1 + 2 * (j + 1) / n
				local a, b, c, d = corner(s0, t0), corner(s1, t0), corner(s1, t1), corner(s0, t1)
				addTri(m, weld, a, b, c)
				addTri(m, weld, a, c, d)
			end
		end
	end
	return m
end

--- Torus (ring radius R, tube radius r): concave on the inside, convex on the outside.
function Mesh.torus(R: number, r: number, segs: number, sides: number): Mesh
	local m, weld = Mesh.new(), {}
	local function corner(i: number, j: number)
		local u, v = i / segs, j / sides
		local th, ph = u * 2 * math.pi, v * 2 * math.pi
		local cx, cz = math.cos(th), math.sin(th)
		local nx, ny, nz = math.cos(ph) * cx, math.sin(ph), math.cos(ph) * cz
		return { cx * R + nx * r, ny * r, cz * R + nz * r, u, v, nx, ny, nz }
	end
	for j = 0, sides - 1 do
		for i = 0, segs - 1 do
			local a, b, c, d = corner(i, j), corner(i + 1, j), corner(i + 1, j + 1), corner(i, j + 1)
			addTri(m, weld, a, b, c)
			addTri(m, weld, a, c, d)
		end
	end
	return m
end

--- Builds a Mesh from triangle corners given as {x,y,z,u,v,nx,ny,nz} triples (welds positions).
function Mesh.fromCorners(corners: { { number } }): Mesh
	local m, weld = Mesh.new(), {}
	for i = 1, #corners, 3 do
		addTri(m, weld, corners[i], corners[i + 1], corners[i + 2])
	end
	return m
end

return Mesh
