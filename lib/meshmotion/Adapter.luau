-- Adapter: the only Roblox-API file in meshmotion. Cannot run headless; compile-checked only.
-- Two ways to show a Rig, pick per creature:
--   * Parts mode (cheapest): each segment is its own MeshPart, and `segmentCFrame` drives its CFrame.
--     Zero vertex writes. Use it for rigid-only motion (cookbook: "vertex churn that is really rigid motion
--     should always be hoisted into the CFrame").
--   * Editable mode: one EditableMesh made from the uploaded MeshPart (keeps its UVs and texture), and
--     `push` writes rig.out with one BatchSetValues. Use it when deformers run (squash, wave, twist, jiggle).
-- [UNVERIFIED in Studio from this repo] the vertex matching in `bind`: Roblox may split vertices on UV and
--   normal seams, so several EditableMesh vertices map onto one blueprint vertex. Matching uses rounded
--   positions after aligning the two bounding-box centres (CreateMeshPartAsync re-centres geometry).

local AssetService = game:GetService("AssetService")

local Adapter = {}

local rf = buffer.readf32

export type Binding = { em: EditableMesh, ids: { number }, map: { number }, vals: { Vector3 }, offset: Vector3 }

local function key(x: number, y: number, z: number, q: number): string
	return string.format("%d,%d,%d", math.round(x / q), math.round(y / q), math.round(z / q))
end

-- Make an editable copy of an uploaded MeshPart and map its vertices onto the rig's blueprint.
-- `tolerance` is the matching grid in studs (default 0.01).
function Adapter.bind(meshPart: MeshPart, data: any, tolerance: number?): Binding
	local q = tolerance or 0.01
	local em = AssetService:CreateEditableMeshAsync(meshPart.MeshContent)
	local ids = em:GetVertices()
	local positions = em:BatchGetValues(ids) :: { Vector3 }

	-- align centres
	local emMin, emMax = Vector3.one * math.huge, -Vector3.one * math.huge
	for _, p in positions do
		emMin, emMax = emMin:Min(p), emMax:Max(p)
	end
	local b = data.bounds
	local bpCentre = Vector3.new((b.min[1] + b.max[1]) / 2, (b.min[2] + b.max[2]) / 2, (b.min[3] + b.max[3]) / 2)
	local offset = (emMin + emMax) / 2 - bpCentre

	local lookup = {}
	for v = 0, data.n - 1 do
		local o = v * 12
		lookup[key(rf(data.rest, o), rf(data.rest, o + 4), rf(data.rest, o + 8), q)] = v
	end
	local map, missing = table.create(#ids), 0
	for i, p in positions do
		local lp = p - offset
		local v = lookup[key(lp.X, lp.Y, lp.Z, q)]
		if v == nil then
			missing += 1
			v = -1
		end
		map[i] = v
	end
	if missing > 0 then
		warn(`meshmotion: {missing}/{#ids} vertices of {meshPart.Name} did not match {data.name}`)
	end
	return { em = em, ids = ids, map = map, vals = table.create(#ids), offset = offset }
end

-- Show the editable copy on a part (once). Returns the new MeshPart; the caller positions it.
function Adapter.show(bnd: Binding, template: MeshPart): MeshPart
	local part = AssetService:CreateMeshPartAsync(Content.fromObject(bnd.em))
	part.TextureContent = template.TextureContent
	part.Anchored, part.CanCollide, part.CanQuery, part.CanTouch = true, false, false, false
	return part
end

-- Push rig.out to the EditableMesh in one batch call. Unmatched vertices keep their position.
function Adapter.push(bnd: Binding, rig: any)
	local out, ids, map, vals, off = rig.out, bnd.ids, bnd.map, bnd.vals, bnd.offset
	local pushIds = ids
	for i = 1, #ids do
		local v = map[i]
		if v >= 0 then
			local o = v * 12
			vals[i] = Vector3.new(rf(out, o), rf(out, o + 4), rf(out, o + 8)) + off
		else
			vals[i] = bnd.em:GetPosition(ids[i])
		end
	end
	bnd.em:BatchSetValues(pushIds, vals)
end

-- Parts mode: CFrame for segment i, relative to the creature's root CFrame. A segment part whose mesh is
-- centred at rest point c goes at segmentCFrame(...) * CFrame.new(c). Scale (pose.s ~= 1) is not
-- representable in a CFrame: parts mode ignores it, so keep scale animation to editable mode.
function Adapter.segmentCFrame(rig: any, i: number, root: CFrame): CFrame
	local w, o = rig.world, (i - 1) * 48
	local local_ = CFrame.new(
		rf(w, o + 12), rf(w, o + 28), rf(w, o + 44),
		rf(w, o), rf(w, o + 4), rf(w, o + 8),
		rf(w, o + 16), rf(w, o + 20), rf(w, o + 24),
		rf(w, o + 32), rf(w, o + 36), rf(w, o + 40)
	)
	return root * local_
end

function Adapter.destroy(bnd: Binding)
	bnd.em:Destroy()
end

return Adapter
