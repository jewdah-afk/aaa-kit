--!strict
-- GridMesh: builds a heightfield grid (vertices, normals, triangles) as plain arrays, then
-- an adapter pushes it into a Roblox EditableMesh. The pure half is testable in lune; the
-- adapter only runs in Roblox. LOD = the same builder at a coarser `step`.

local GridMesh = {}

export type Data = {
	positions: { { number } }, -- {x, y, z}
	normals: { { number } },
	uvs: { { number } },
	tris: { { number } }, -- 1-based vertex indices, counter-clockwise seen from +Y
}

-- size: world width/depth; cells: quads per side; height(x, z) -> y
function GridMesh.build(size: number, cells: number, height: (number, number) -> number): Data
	local n = cells + 1
	local positions, normals, uvs, tris = {}, {}, {}, {}
	local step = size / cells
	local function h(ix: number, iz: number): number
		return height(-size / 2 + ix * step, -size / 2 + iz * step)
	end
	for iz = 0, cells do
		for ix = 0, cells do
			local x, z = -size / 2 + ix * step, -size / 2 + iz * step
			table.insert(positions, { x, h(ix, iz), z })
			table.insert(uvs, { ix / cells, iz / cells })
			-- central differences (clamped at the border) for smooth normals
			local dx = h(math.min(ix + 1, cells), iz) - h(math.max(ix - 1, 0), iz)
			local dz = h(ix, math.min(iz + 1, cells)) - h(ix, math.max(iz - 1, 0))
			local nx, ny, nz = -dx, 2 * step, -dz
			local len = math.sqrt(nx * nx + ny * ny + nz * nz)
			table.insert(normals, { nx / len, ny / len, nz / len })
		end
	end
	for iz = 0, cells - 1 do
		for ix = 0, cells - 1 do
			local a = iz * n + ix + 1
			local b, c, d = a + 1, a + n, a + n + 1
			table.insert(tris, { a, c, b })
			table.insert(tris, { b, c, d })
		end
	end
	return { positions = positions, normals = normals, uvs = uvs, tris = tris }
end

-- Triangle budget per LOD ring: full detail near, quarter and sixteenth further out.
function GridMesh.cellsForDistance(baseCells: number, distance: number, nearDist: number): number
	if distance < nearDist then
		return baseCells
	elseif distance < nearDist * 3 then
		return math.max(1, baseCells // 2)
	end
	return math.max(1, baseCells // 4)
end

-- Roblox adapter (not run in lune). Creates one EditableMesh and a MeshPart showing it.
-- EditableMesh is client-side by default; the vertex/triangle budget is engine-limited,
-- so build big terrain from several chunks rather than one mesh.
function GridMesh.toRoblox(data: Data, parent: Instance): any
	local AssetService = (game :: any):GetService("AssetService")
	local em = AssetService:CreateEditableMesh()
	local vids = table.create(#data.positions)
	local nids = table.create(#data.normals)
	local uids = table.create(#data.uvs)
	for i, p in data.positions do
		vids[i] = em:AddVertex(Vector3.new(p[1], p[2], p[3]))
		local nn = data.normals[i]
		nids[i] = em:AddNormal(Vector3.new(nn[1], nn[2], nn[3]))
		local uv = data.uvs[i]
		uids[i] = em:AddUV(Vector2.new(uv[1], uv[2]))
	end
	for _, t in data.tris do
		local fid = em:AddTriangle(vids[t[1]], vids[t[2]], vids[t[3]])
		em:SetFaceNormals(fid, { nids[t[1]], nids[t[2]], nids[t[3]] })
		em:SetFaceUVs(fid, { uids[t[1]], uids[t[2]], uids[t[3]] })
	end
	local part = AssetService:CreateMeshPartAsync(Content.fromObject(em))
	part.Anchored = true
	part.Parent = parent
	return part, em
end

return GridMesh
