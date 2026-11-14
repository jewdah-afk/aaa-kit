--!strict
-- StudSocket: builds a HUD v5 socket button as plain Roblox GUI and wires the press into
-- the socket. Layers match the Figma spec board ("HUD v5 · Socket"):
--
--   Well     Frame: dark gradient, UIStroke 1.5 px light, inner shade (ImageLabel, optional)
--   Cap      Frame that moves; holds everything below
--     Rim    Frame ink, UICorner 12
--     Side   Frame, family side colour (the visible depth)
--     Face   Frame + UIGradient (family top -> base), ClipsDescendants
--       Blocks  tiled ImageLabel: studs_checker_blocks.png (the 4x4 on/off pattern)
--       Lights  tiled ImageLabel: studs_checker_light.png  } the map stud, split because
--       Darks   tiled ImageLabel: studs_checker_dark.png   } Roblox has no overlay blend
--       Sheen, Bevel
--     Icon, Label (Montserrat Black + UIStroke, mitred)
--
-- Tiles start at the face's top-left at 96 px (8 studs x 12 px) x UI scale, and faces are
-- whole 4x4 blocks (SocketSpec.isWholeBlocks), so every stud is whole and 1:1 everywhere.

local TweenService = game:GetService("TweenService")
local Socket = require("./SocketSpec")
local Spec = require("./StudPlateSpec")

local StudSocket = {}

export type Assets = {
	blocks: string, -- studs_checker_blocks.png
	lights: string, -- studs_checker_light.png
	darks: string, -- studs_checker_dark.png
}

export type Family = { top: string, base: string, side: string, bevel: string, glow: string }

StudSocket.FAMILIES = {
	lime = { top = "#C8FF3A", base = "#5CC914", side = "#2D7A0A", bevel = "#EFFFB0", glow = "#9BFF2E" },
	ruby = { top = "#FF5C78", base = "#D8143E", side = "#7E0A26", bevel = "#FFB3C1", glow = "#FF3B5C" },
	sky = { top = "#7CC8FF", base = "#2F7BFF", side = "#163E9A", bevel = "#CFEAFF", glow = "#4AA8FF" },
	violet = { top = "#B48CFF", base = "#6A2BE8", side = "#34128A", bevel = "#D9C4FF", glow = "#8A55FF" },
	gold = { top = "#FFE15A", base = "#F29A0E", side = "#8E4A06", bevel = "#FFF3B0", glow = "#FFB020" },
	night = { top = "#3A4378", base = "#222852", side = "#0D1030", bevel = "#6F7BC8", glow = "#3C4A9A" },
	ice = { top = "#EAF6FF", base = "#9ED2F2", side = "#4E86AE", bevel = "#FFFFFF", glow = "#BFEFFF" },
	aurora = { top = "#5FFFE0", base = "#1E86D8", side = "#0E3F72", bevel = "#B8FFF2", glow = "#40F0D0" },
	off = { top = "#8E96B8", base = "#5B6386", side = "#2E3452", bevel = "#C2C8E0", glow = "#000000" },
} :: { [string]: Family }

export type Options = {
	family: string,
	studs: Vector2, -- face size in studs; must be whole 4x4 blocks
	position: UDim2?,
	label: string?,
	labelSize: number?,
	icon: string?,
	iconRect: Rect?, -- px relative to the face; may break out of it
	scale: number?,
	name: string?,
}

export type Button = {
	root: Frame,
	cap: Frame,
	rim: Frame,
	side: Frame,
	face: Frame,
	veil: Frame,
	stroke: UIStroke,
	scale: number,
	studs: Vector2,
	family: Family,
}

local function rgb(h: string): Color3
	local r, g, b = Spec.hex(h)
	return Color3.fromRGB(r, g, b)
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

local function corner(p: Instance, r: number)
	local c = Instance.new("UICorner")
	c.CornerRadius = UDim.new(0, r)
	c.Parent = p
end

local function tile(name: string, face: Frame, image: string, px: number, alpha: number)
	local i = Instance.new("ImageLabel")
	i.Name = name
	i.BackgroundTransparency = 1
	i.Size = UDim2.fromScale(1, 1)
	i.Image = image
	i.ScaleType = Enum.ScaleType.Tile
	i.TileSize = UDim2.fromOffset(px, px)
	i.ImageTransparency = 1 - alpha
	i.ZIndex = face.ZIndex + 1
	i.Parent = face
end

function StudSocket.build(parent: Instance, o: Options, assets: Assets): Button
	local fam = StudSocket.FAMILIES[o.family]
	assert(fam, `unknown socket family {o.family}`)
	local sw, sh = o.studs.X, o.studs.Y
	assert(Socket.isWholeBlocks(sw * Socket.STUD, sh * Socket.STUD), `face {sw}x{sh} studs is not whole 4x4 blocks`)
	local s = o.scale or 1
	local G = Socket.geometry(sw, sh)
	local px = function(v: number): number
		return math.floor(v * s + 0.5)
	end

	local well = frame(o.name or "Socket", parent, "#0B0D22", 1)
	well.Size = UDim2.fromOffset(px(G.wellW), px(G.wellH))
	well.Position = o.position or UDim2.new()
	well.BackgroundTransparency = 0.18
	corner(well, px(Socket.RADIUS.well))
	local wg = Instance.new("UIGradient")
	wg.Rotation = 90
	wg.Color = ColorSequence.new(rgb("#05060F"), rgb("#151937"))
	wg.Parent = well
	local ws = Instance.new("UIStroke")
	ws.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	ws.Color = Color3.new(1, 1, 1)
	ws.Transparency = 0.84
	ws.Thickness = math.max(1, s * 1.5)
	ws.Parent = well

	local cap = frame("Cap", well, nil, 2)
	cap.Position = UDim2.fromOffset(px(Socket.WELL), px(G.capY))
	cap.Size = UDim2.fromOffset(px(G.capW), px(G.capH))

	local rim = frame("Rim", cap, Spec.INK, 2)
	rim.Size = UDim2.fromScale(1, 1)
	corner(rim, px(Socket.RADIUS.rim))
	local glow = Instance.new("UIStroke") -- a soft family-coloured edge stands in for the Figma glow
	glow.Color = rgb(fam.glow)
	glow.Thickness = math.max(1, s * 2)
	glow.Transparency = 1 - Socket.GLOW.rest
	glow.Parent = rim

	local side = frame("Side", cap, fam.side, 3)
	side.AnchorPoint = Vector2.new(0, 1)
	side.Position = UDim2.new(0, px(Socket.RIM), 1, -px(Socket.RIM))
	side.Size = UDim2.fromOffset(px(G.faceW), px(G.side + 10))
	corner(side, px(8))

	local face = frame("Face", cap, "#FFFFFF", 4)
	face.Position = UDim2.fromOffset(px(Socket.RIM), px(Socket.RIM))
	face.Size = UDim2.fromOffset(px(G.faceW), px(G.faceH))
	face.ClipsDescendants = true
	corner(face, px(Socket.RADIUS.face))
	local fg = Instance.new("UIGradient")
	fg.Rotation = 90
	fg.Color = ColorSequence.new(rgb(fam.top), rgb(fam.base))
	fg.Parent = face

	local tpx = px(G.tile)
	tile("Blocks", face, assets.blocks, tpx, 1)
	tile("Lights", face, assets.lights, tpx, Spec.STUD_LIGHT_ALPHA)
	tile("Darks", face, assets.darks, tpx, Spec.STUD_DARK_ALPHA)

	local sheen = frame("Sheen", face, "#FFFFFF", 7)
	sheen.Size = UDim2.fromScale(1, 0.4)
	local sg = Instance.new("UIGradient")
	sg.Rotation = 90
	sg.Transparency = NumberSequence.new(0.76, 1)
	sg.Parent = sheen

	local bevel = frame("Bevel", face, fam.bevel, 7)
	bevel.AnchorPoint = Vector2.new(0, 1)
	bevel.Position = UDim2.new(0, px(4), 1, -px(1))
	bevel.Size = UDim2.new(1, -px(8), 0, math.max(1, px(3)))
	bevel.BackgroundTransparency = 0.1

	if o.label and sw == sh then -- label seat (square faces: tiles and hotbar slots): darkens the bottom of the face so white text reads on studs
		local seat = frame("LabelSeat", face, Spec.INK, 6)
		local seatH = if sh >= 12 then Socket.SEAT.tile else Socket.SEAT.slot
		seat.AnchorPoint = Vector2.new(0, 1)
		seat.Position = UDim2.fromScale(0, 1)
		seat.Size = UDim2.new(1, 0, 0, px(seatH))
		local sg2 = Instance.new("UIGradient")
		sg2.Rotation = 90
		sg2.Transparency = NumberSequence.new(1, 1 - Socket.SEAT.alpha)
		sg2.Parent = seat
	end

	local veil = frame("HoverVeil", face, "#FFFFFF", 8)
	veil.Size = UDim2.fromScale(1, 1)
	veil.BackgroundTransparency = 1

	if o.icon then
		local r = o.iconRect or Rect.new(0, 0, G.faceW, G.faceH)
		local i = Instance.new("ImageLabel")
		i.Name = "Icon"
		i.BackgroundTransparency = 1
		i.Image = o.icon
		i.ScaleType = Enum.ScaleType.Fit
		i.Position = UDim2.fromOffset(px(Socket.RIM + r.Min.X), px(Socket.RIM + r.Min.Y))
		i.Size = UDim2.fromOffset(px(r.Width), px(r.Height))
		i.ZIndex = 9
		i.Parent = cap
	end
	if o.label then
		local size = o.labelSize or 26
		local t = Instance.new("TextLabel")
		t.Name = "Label"
		t.BackgroundTransparency = 1
		t.Text = o.label
		t.FontFace = Font.new("rbxasset://fonts/families/Montserrat.json", Enum.FontWeight.Black)
		t.TextSize = px(size)
		t.TextColor3 = Color3.new(1, 1, 1)
		t.AnchorPoint = Vector2.new(0.5, 1)
		-- bottom edge LABEL_GAP above the face edge, so it never sits on the cap's side
		t.Position = UDim2.new(0.5, 0, 0, px(Socket.RIM + G.faceH - Socket.LABEL_GAP))
		t.Size = UDim2.new(1, 0, 0, px(size * 1.25))
		t.ZIndex = 10
		t.Parent = cap
		local st = Instance.new("UIStroke")
		st.Color = rgb(Spec.INK)
		st.Thickness = math.max(1, math.floor(size * 0.09 * s * 0.5 + 0.5))
		st.LineJoinMode = Enum.LineJoinMode.Miter
		st.Parent = t
	end

	return { root = well, cap = cap, rim = rim, side = side, face = face, veil = veil, stroke = glow, scale = s, studs = o.studs, family = fam }
end

local function info(row: { time: number, style: string, dir: string }): TweenInfo
	return TweenInfo.new(row.time, (Enum.EasingStyle :: any)[row.style], (Enum.EasingDirection :: any)[row.dir])
end

-- The press into the socket: down 40 ms, release 90 ms, then the action. No bounce.
function StudSocket.wire(b: Button, onActivate: (() -> ())?): RBXScriptConnection
	local s = b.scale
	local rest = Socket.geometry(b.studs.X, b.studs.Y, false)
	local down = Socket.geometry(b.studs.X, b.studs.Y, true)
	local function to(g: Socket.Geometry, row, glow: number, veil: number, lift: number)
		local i = info(row)
		TweenService:Create(b.cap, i, { Position = UDim2.fromOffset(math.floor(Socket.WELL * s + 0.5), math.floor((g.capY - lift) * s + 0.5)), Size = UDim2.fromOffset(math.floor(g.capW * s + 0.5), math.floor((g.capH + lift) * s + 0.5)) }):Play()
		TweenService:Create(b.side, i, { Size = UDim2.fromOffset(math.floor(g.faceW * s + 0.5), math.floor((g.side + lift + 10) * s + 0.5)) }):Play()
		TweenService:Create(b.stroke, i, { Transparency = 1 - glow }):Play()
		TweenService:Create(b.veil, i, { BackgroundTransparency = 1 - veil }):Play()
	end
	local M = Socket.MOTION
	local hovering = false
	local hit = Instance.new("TextButton")
	hit.Name = "Hit"
	hit.Text = ""
	hit.BackgroundTransparency = 1
	hit.Size = UDim2.fromScale(1, 1)
	hit.ZIndex = 20
	hit.Parent = b.root
	hit.MouseEnter:Connect(function()
		hovering = true
		to(rest, M.hover, Socket.GLOW.hover, 0.06, Socket.HOVER_LIFT)
	end)
	hit.MouseLeave:Connect(function()
		hovering = false
		to(rest, M.hover, Socket.GLOW.rest, 0, 0)
	end)
	hit.MouseButton1Down:Connect(function()
		to(down, M.down, Socket.GLOW.pressed, 0, 0)
	end)
	return hit.MouseButton1Up:Connect(function()
		to(rest, M.up, if hovering then Socket.GLOW.hover else Socket.GLOW.rest, if hovering then 0.06 else 0, if hovering then Socket.HOVER_LIFT else 0)
		if onActivate then
			onActivate()
		end
	end)
end

-- Held-down look for the selected tab or filter.
function StudSocket.setSelected(b: Button, on: boolean)
	local g = Socket.geometry(b.studs.X, b.studs.Y, on)
	local s = b.scale
	b.cap.Position = UDim2.fromOffset(math.floor(Socket.WELL * s + 0.5), math.floor(g.capY * s + 0.5))
	b.cap.Size = UDim2.fromOffset(math.floor(g.capW * s + 0.5), math.floor(g.capH * s + 0.5))
	b.side.Size = UDim2.fromOffset(math.floor(g.faceW * s + 0.5), math.floor((g.side + 10) * s + 0.5))
end

return StudSocket
