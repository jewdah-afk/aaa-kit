--!strict
-- StudPlateSpec: the HUD v4 Stud Plate tokens and layout maths, with no Instances.
-- StudPlate.luau builds GUI from it, and the Figma spec board ("1 · Colour tokens",
-- "2 · Plate anatomy") shows the same numbers. Balance-free: this is look data only.

local Spec = {}

export type Family = {
	top: string?, -- face gradient top (nil when the face is a texture)
	base: string?, -- face gradient bottom
	tex: string?, -- texture key for algorithm faces (frost, aurora, galaxy)
	sill: string,
	bevel: string,
	glow: string,
}

Spec.INK = "#0B0C1A"
Spec.RIM = 4 -- ink rim, px at 1080p
Spec.RADIUS = 12
Spec.SILL = 0.075 -- sill height as a share of plate height
Spec.SILL_MIN = 8
Spec.STUD_PITCH = 22 -- one stud every 22 px; the map tile holds 8 studs, so it tiles every 176 px
Spec.STUDS_PER_TILE = 8
Spec.STUD_OPACITY = 0.85 -- Figma: the UI stud tile as an OVERLAY fill at 85%
-- Roblox has no overlay blend: studs_light + studs_dark (tools/lookdev/stud_overlay_split.py)
-- at these opacities match the Figma overlay to ~5/255 mean error across the HUD face colours
Spec.STUD_LIGHT_ALPHA = 0.3
Spec.STUD_DARK_ALPHA = 0.2
Spec.SHEEN = 0.4 -- top share of the face
Spec.SHEEN_ALPHA = 0.26
Spec.BEVEL = 3
Spec.GLOW_RADIUS = 22
Spec.GLOW_ALPHA = 0.55
Spec.LABEL_STROKE = 0.14 -- of font size
Spec.LABEL_DROP = 0.08 -- of font size

Spec.FAMILIES = {
	lime = { top = "#D6FF4A", base = "#62CC12", sill = "#2F7A08", bevel = "#EFFFB0", glow = "#9BFF2E" },
	ruby = { top = "#FF6C82", base = "#DD1640", sill = "#8A0B27", bevel = "#FFB3C1", glow = "#FF3B5C" },
	frost = { tex = "frost", sill = "#4F98C8", bevel = "#FFFFFF", glow = "#8FDCFF" },
	violet = { top = "#B48CFF", base = "#6A2BE8", sill = "#3B1696", bevel = "#D9C4FF", glow = "#8A55FF" },
	ice = { top = "#FFFFFF", base = "#BEE6FA", sill = "#5F9CC4", bevel = "#FFFFFF", glow = "#BFEFFF" },
	aurora = { tex = "aurora", sill = "#0B2F4A", bevel = "#7DFFE6", glow = "#40F0D0" },
	night = { top = "#3B4475", base = "#1A1F3D", sill = "#0B0E24", bevel = "#8A96FF", glow = "#5B6CFF" },
	galaxy = { tex = "galaxy", sill = "#2E0F5E", bevel = "#E79BFF", glow = "#B45CFF" },
	disabled = { top = "#9AA3C0", base = "#5E6788", sill = "#3A4060", bevel = "#C9CFE6", glow = "#000000" },
} :: { [string]: Family }

-- Which family each HUD button wears. Upgrades is off for release.
Spec.BUTTONS = {
	Daily = { family = "lime", visible = true },
	Shop = { family = "ruby", visible = true },
	Index = { family = "frost", visible = true },
	Animals = { family = "violet", visible = true },
	Upgrades = { family = "galaxy", visible = false },
}

function Spec.hex(h: string): (number, number, number)
	local r = tonumber(string.sub(h, 2, 3), 16) or 0
	local g = tonumber(string.sub(h, 4, 5), 16) or 0
	local b = tonumber(string.sub(h, 6, 7), 16) or 0
	return r, g, b
end

export type Layout = {
	sill: number,
	faceX: number,
	faceY: number,
	faceW: number,
	faceH: number,
	sheenH: number,
	tile: number, -- TileSize of the stud tile, px
	pressDrop: number, -- how far face, icon and label drop on press
}

-- Layer rects for a w x h plate (px). The studs are one tiled image that starts at the
-- face's top-left corner and runs edge to edge: no centring, no per-stud instances.
function Spec.layout(w: number, h: number): Layout
	local sill = math.max(Spec.SILL_MIN, math.floor(h * Spec.SILL + 0.5))
	local faceW = w - Spec.RIM * 2
	local faceH = h - Spec.RIM * 2 - sill
	return {
		sill = sill,
		faceX = Spec.RIM,
		faceY = Spec.RIM,
		faceW = faceW,
		faceH = faceH,
		sheenH = math.floor(faceH * Spec.SHEEN + 0.5),
		tile = Spec.STUD_PITCH * Spec.STUDS_PER_TILE,
		pressDrop = sill, -- face, icon and label sink onto the sill (the sill hides)
	}
end

-- Label ink stroke and hard drop for a font size, rounded to whole pixels.
function Spec.labelInk(fontSize: number): (number, number)
	return math.max(3, math.floor(fontSize * Spec.LABEL_STROKE + 0.5)), math.max(2, math.floor(fontSize * Spec.LABEL_DROP + 0.5))
end

-- Scale every px value for a smaller screen (phone landscape is ~0.62 of 1080p height).
function Spec.scaleFor(viewportHeight: number): number
	return math.clamp(viewportHeight / 1080, 0.5, 1.25)
end

return Spec
