--!strict
-- StudPlate: builds a HUD v4 Stud Plate as plain Roblox GUI, the hand-built replacement
-- for a FrameWisp import. Layer for layer it matches the Figma spec board:
--
--   Glow      ImageLabel, soft 9-slice (glow_9slice.png) tinted the family glow colour
--   Rim       Frame, ink, UICorner 12
--   Sill      Frame, family sill colour, bottom 7.5%
--   Face      Frame + UIGradient (top -> base), or an ImageLabel texture for frost/aurora/galaxy
--   Studs     two tiled ImageLabels: studs_light (white) + studs_dark (black). Roblox has no
--             overlay blend, so the map tile is split into its lights and darks once
--             (tools/lookdev/stud_overlay_split.py); stacked, they tint any face like overlay.
--   Sheen     Frame, white, UIGradient transparency 0.74 -> 1 over the top 40%
--   Bevel     Frame, 3 px, family bevel colour
--   Icon      ImageLabel (voxel render), may break the top edge
--   Label     TextLabel, Fredoka One, white, UIStroke ink
--
-- Asset ids come from the game (`assets` below), never hard-coded here.

local Spec = require("./StudPlateSpec")

local StudPlate = {}

export type Assets = {
	studsLight: string,
	studsDark: string,
	glow: string, -- 9-slice soft rounded rect, white
	textures: { [string]: string }?, -- frost / aurora / galaxy faces
}

export type Options = {
	family: string,
	size: Vector2,
	position: UDim2?,
	label: string?,
	labelSize: number?,
	labelY: number?, -- px from the plate top
	icon: string?,
	iconRect: Rect?, -- px, relative to the plate; may stick out of it
	name: string?,
	scale: number?, -- from Spec.scaleFor(viewport height)
}

export type Plate = {
	root: Frame,
	face: GuiObject,
	sill: Frame,
	glow: ImageLabel,
	icon: ImageLabel?,
	label: TextLabel?,
	veil: Frame,
	layout: Spec.Layout,
	family: Spec.Family,
	scale: number,
}

local function rgb(h: string): Color3
	local r, g, b = Spec.hex(h)
	return Color3.fromRGB(r, g, b)
end

local function px(x: number, y: number, s: number): UDim2
	return UDim2.fromOffset(math.floor(x * s + 0.5), math.floor(y * s + 0.5))
end

local function frame(name: string, parent: Instance, color: string?, z: number): Frame
	local f = Instance.new("Frame")
	f.Name = name
	f.BorderSizePixel = 0
	f.BackgroundColor3 = if color then rgb(color) else Color3.new(1, 1, 1)
	f.BackgroundTransparency = if color then 0 else 1
	f.ZIndex = z
	f.Parent = parent
	return f
end

local function corner(parent: Instance, r: number)
	local c = Instance.new("UICorner")
	c.CornerRadius = UDim.new(0, r)
	c.Parent = parent
end

local function tiled(name: string, parent: Instance, image: string, tile: number, alpha: number, z: number): ImageLabel
	local i = Instance.new("ImageLabel")
	i.Name = name
	i.BackgroundTransparency = 1
	i.Size = UDim2.fromScale(1, 1)
	i.Image = image
	i.ScaleType = Enum.ScaleType.Tile
	i.TileSize = UDim2.fromOffset(tile, tile) -- starts at the face's top-left: edge to edge, no centring
	i.ImageTransparency = 1 - alpha
	i.ZIndex = z
	i.Parent = parent
	return i
end

function StudPlate.build(parent: Instance, o: Options, assets: Assets): Plate
	local fam = Spec.FAMILIES[o.family]
	assert(fam, `unknown Stud Plate family {o.family}`)
	local s = o.scale or 1
	local w, h = o.size.X, o.size.Y
	local L = Spec.layout(w, h)

	local root = frame(o.name or "StudPlate", parent, nil, 1)
	root.Size = px(w, h, s)
	root.Position = o.position or UDim2.new()

	local glow = Instance.new("ImageLabel")
	glow.Name = "Glow"
	glow.BackgroundTransparency = 1
	glow.Image = assets.glow
	glow.ImageColor3 = rgb(fam.glow)
	glow.ImageTransparency = 1 - Spec.GLOW_ALPHA
	glow.ScaleType = Enum.ScaleType.Slice
	glow.SliceCenter = Rect.new(64, 64, 64, 64)
	glow.Size = UDim2.new(1, math.floor(Spec.GLOW_RADIUS * 2 * s), 1, math.floor(Spec.GLOW_RADIUS * 2 * s))
	glow.Position = px(-Spec.GLOW_RADIUS, -Spec.GLOW_RADIUS, s)
	glow.ZIndex = 1
	glow.Parent = root

	local rim = frame("Rim", root, Spec.INK, 2)
	rim.Size = UDim2.fromScale(1, 1)
	corner(rim, math.floor(Spec.RADIUS * s))

	local sill = frame("Sill", root, fam.sill, 3)
	sill.Position = px(Spec.RIM, h - Spec.RIM - L.sill - 6, s)
	sill.Size = px(w - Spec.RIM * 2, L.sill + 6, s)
	corner(sill, math.floor(8 * s))

	local face: GuiObject
	if fam.tex and assets.textures and assets.textures[fam.tex] then
		local img = Instance.new("ImageLabel")
		img.Image = assets.textures[fam.tex]
		img.ScaleType = Enum.ScaleType.Crop
		img.BackgroundTransparency = 1
		face = img
	else
		local f = frame("Face", root, "#FFFFFF", 4)
		local g = Instance.new("UIGradient")
		g.Rotation = 90
		g.Color = ColorSequence.new(rgb(fam.top or "#FFFFFF"), rgb(fam.base or "#FFFFFF"))
		g.Parent = f
		face = f
	end
	face.Name = "Face"
	face.ZIndex = 4
	face.ClipsDescendants = true
	face.Position = px(L.faceX, L.faceY, s)
	face.Size = px(L.faceW, L.faceH, s)
	face.Parent = root
	corner(face, math.floor(8 * s))

	local tile = math.floor(L.tile * s + 0.5)
	tiled("StudsLight", face, assets.studsLight, tile, Spec.STUD_LIGHT_ALPHA, 5)
	tiled("StudsDark", face, assets.studsDark, tile, Spec.STUD_DARK_ALPHA, 5)

	local sheen = frame("Sheen", face, "#FFFFFF", 6)
	sheen.Size = UDim2.new(1, 0, Spec.SHEEN, 0)
	local sg = Instance.new("UIGradient")
	sg.Rotation = 90
	sg.Transparency = NumberSequence.new(1 - Spec.SHEEN_ALPHA, 1)
	sg.Parent = sheen

	local bevel = frame("Bevel", face, fam.bevel, 6)
	bevel.AnchorPoint = Vector2.new(0, 1)
	bevel.Position = UDim2.new(0, math.floor(3 * s), 1, -math.floor(1 * s))
	bevel.Size = UDim2.new(1, -math.floor(6 * s), 0, math.max(1, math.floor(Spec.BEVEL * s)))
	corner(bevel, 2)

	local veil = frame("HoverVeil", face, "#FFFFFF", 7)
	veil.Size = UDim2.fromScale(1, 1)
	veil.BackgroundTransparency = 1

	local icon: ImageLabel? = nil
	if o.icon then
		local r = o.iconRect or Rect.new(0, 0, w, w)
		local i = Instance.new("ImageLabel")
		i.Name = "Icon"
		i.BackgroundTransparency = 1
		i.Image = o.icon
		i.ScaleType = Enum.ScaleType.Fit
		i.Position = px(r.Min.X, r.Min.Y, s)
		i.Size = px(r.Width, r.Height, s)
		i.ZIndex = 8
		i.Parent = root
		icon = i
	end

	local label: TextLabel? = nil
	if o.label then
		local size = o.labelSize or 40
		local stroke, _ = Spec.labelInk(size)
		local t = Instance.new("TextLabel")
		t.Name = "Label"
		t.BackgroundTransparency = 1
		t.Text = o.label
		t.FontFace = Font.fromEnum(Enum.Font.FredokaOne)
		t.TextSize = math.floor(size * s)
		t.TextColor3 = Color3.new(1, 1, 1)
		t.Size = UDim2.new(1, 0, 0, math.floor(size * 1.2 * s))
		t.Position = px(0, o.labelY or (h - size * 1.6), s)
		t.ZIndex = 9
		t.Parent = root
		local st = Instance.new("UIStroke")
		st.Color = rgb(Spec.INK)
		st.Thickness = math.max(1, math.floor(stroke * s * 0.5 + 0.5)) -- UIStroke grows both ways; half reads like Figma OUTSIDE
		st.LineJoinMode = Enum.LineJoinMode.Round
		st.Parent = t
		label = t
	end

	return { root = root, face = face, sill = sill, glow = glow, icon = icon, label = label, veil = veil, layout = L, family = fam, scale = s }
end

return StudPlate
