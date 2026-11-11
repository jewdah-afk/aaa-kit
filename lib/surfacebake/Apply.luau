--!strict
-- Apply: the only Roblox-specific file. Reads a MeshPart's geometry through EditableMesh, bakes a
-- recipe, and puts the maps on the part. Everything else in surfacebake is pure Luau.
--
-- Two runtime routes (see docs/playbooks/procedural-textures.md):
--   colour only : MeshPart.TextureContent = Content.fromObject(EditableImage)      (1 image)
--   full PBR    : AssetService:CreateSurfaceAppearanceAsync({ ColorMap, NormalMap, RoughnessMap,
--                 MetalnessMap }) parented to the MeshPart                        (4 images)
-- And the production route: bake in Studio with a plugin and upload with CreateAssetAsync, so
-- players download a normal texture and pay no runtime cost (Apply.toEditableImages gives you the
-- images to upload).
--
-- Rules (from docs/research/20 and 21):
--   * Run on the CLIENT. Content.Object does not replicate; a server-made EditableImage shows as a
--     checkerboard on clients.
--   * Published games need the owner's ID verification + "Enable Mesh / Image APIs".
--   * CreateEditableMeshAsync only opens meshes owned by / shared with the game owner (or the
--     player, client-side). It throws on permission errors: pcall it.
--   * Editable memory is budgeted per device; creation returns nil when it is exhausted. Fall back
--     to the part's authored texture.
--   * SurfaceAppearance maps cannot be swapped after creation: re-bake builds a new one.

local AssetService = game:GetService("AssetService")

local Mesh = require("./Mesh")
local Bake = require("./Bake")
type Mesh = Mesh.Mesh

local Apply = {}

--- Reads an EditableMesh into surfacebake's Mesh (positions welded, per-corner UVs and normals).
--- flipV: set true if a test texture shows upside down on your asset (UV origin convention).
function Apply.fromEditableMesh(em: EditableMesh, flipV: boolean?): Mesh
	local corners = {}
	for _, f in em:GetFaces() do
		local vs = em:GetFaceVertices(f)
		local uvs = em:GetFaceUVs(f)
		local ns = em:GetFaceNormals(f)
		for k = 1, 3 do
			local p = em:GetPosition(vs[k])
			local uv = (uvs[k] and em:GetUV(uvs[k])) or Vector2.zero
			local n = (ns[k] and em:GetNormal(ns[k])) or Vector3.yAxis
			local v = if flipV then 1 - uv.Y else uv.Y
			corners[#corners + 1] = { p.X, p.Y, p.Z, uv.X, v, n.X, n.Y, n.Z }
		end
	end
	return Mesh.fromCorners(corners)
end

--- Creates an EditableImage and uploads one RGBA8 map. Returns nil if the memory budget is full.
function Apply.toEditableImage(rgba: buffer, w: number, h: number): EditableImage?
	local img = AssetService:CreateEditableImage({ Size = Vector2.new(w, h) })
	if not img then
		return nil
	end
	img:WritePixelsBuffer(Vector2.zero, Vector2.new(w, h), rgba)
	return img
end

export type Images = { color: EditableImage, normal: EditableImage?, roughness: EditableImage?, metalness: EditableImage? }

--- All four maps as EditableImages (for a plugin to upload, or to build a SurfaceAppearance).
function Apply.toEditableImages(maps: Bake.Maps, colourOnly: boolean?): Images?
	local color = Apply.toEditableImage(maps.albedo, maps.W, maps.H)
	if not color then
		return nil
	end
	if colourOnly then
		return { color = color }
	end
	local normal = Apply.toEditableImage(maps.normal, maps.W, maps.H)
	local rough = Apply.toEditableImage(maps.roughness, maps.W, maps.H)
	local metal = Apply.toEditableImage(maps.metalness, maps.W, maps.H)
	if not (normal and rough and metal) then
		for _, i in { color, normal, rough, metal } do
			if i then
				i:Destroy()
			end
		end
		return nil
	end
	return { color = color, normal = normal, roughness = rough, metalness = metal }
end

--- Puts baked maps on a MeshPart. Full PBR via a new SurfaceAppearance unless colourOnly.
--- Returns true on success; false (and leaves the part untouched) when memory is short.
function Apply.toMeshPart(part: MeshPart, maps: Bake.Maps, colourOnly: boolean?): boolean
	local imgs = Apply.toEditableImages(maps, colourOnly)
	if not imgs then
		return false
	end
	if colourOnly then
		part.TextureContent = Content.fromObject(imgs.color)
		return true
	end
	local ok, sa = pcall(function()
		return AssetService:CreateSurfaceAppearanceAsync({
			ColorMap = Content.fromObject(imgs.color),
			NormalMap = Content.fromObject(imgs.normal :: EditableImage),
			RoughnessMap = Content.fromObject(imgs.roughness :: EditableImage),
			MetalnessMap = Content.fromObject(imgs.metalness :: EditableImage),
		})
	end)
	if not ok or not sa then
		warn("surfacebake: CreateSurfaceAppearanceAsync failed, falling back to colour only:", sa)
		part.TextureContent = Content.fromObject(imgs.color)
		return true
	end
	local old = part:FindFirstChildOfClass("SurfaceAppearance")
	if old then
		old:Destroy()
	end
	sa.Parent = part
	return true
end

--- One call: open the part's mesh, bake a recipe over several frames, apply the result.
--- Client only. Returns ok, message.
function Apply.bakeMeshPart(part: MeshPart, recipe: any, opts: Bake.Options?): (boolean, string?)
	local ok, em = pcall(function()
		return AssetService:CreateEditableMeshAsync(part.MeshContent)
	end)
	if not ok then
		return false, "mesh not readable (permissions or verification): " .. tostring(em)
	end
	if not em then
		return false, "editable memory budget exhausted"
	end
	local mesh = Apply.fromEditableMesh(em)
	em:Destroy() -- geometry copied; free the budget before allocating images
	local o: Bake.Options = table.clone(opts or {})
	o.yield = o.yield or function()
		task.wait()
	end
	local maps = Bake.run(mesh, recipe, o)
	if not Apply.toMeshPart(part, maps, false) then
		return false, "editable memory budget exhausted (images)"
	end
	return true, string.format("baked %dx%d in %.0f ms", maps.W, maps.H, maps.ms.raster + maps.ms.surface + maps.ms.shade)
end

return Apply
