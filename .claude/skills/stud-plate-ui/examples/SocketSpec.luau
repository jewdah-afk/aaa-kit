--!strict
-- SocketSpec: HUD v5 socket buttons, pure numbers (no Instances). A clickable is a cap
-- sitting in a recessed socket; its face wears the map's stud in light/dark 4x4 blocks.
-- The Figma page "HUD v5 · Socket" (spec board "Socket + 4×4 stud checker") uses these
-- same numbers. Info elements (balance, luck, headers, cards) are not socketed.

local Socket = {}

Socket.STUD = 12 -- px per stud at 1080p, always (1:1 rule)
Socket.BLOCK = 4 -- studs per checker block
Socket.TILE_STUDS = 8 -- the map tile holds 8x8 studs = 2x2 blocks
Socket.RIM = 4 -- ink rim around the face
Socket.DEPTH = 10 -- visible cap side at rest
Socket.WELL = 8 -- socket margin around the cap
Socket.PRESS = 8 -- how far the cap sinks on press (side 10 -> 2 px)
Socket.HOVER_LIFT = 2
Socket.RADIUS = { well = 16, rim = 12, face = 8 }
Socket.CHECKER = { lightLift = 0.04, darkDrop = 0.055, overlay = 0.9 } -- soft block mask, then stud overlay
Socket.GLOW = { rest = 0.35, hover = 0.45, pressed = 0.15 }
-- Labels sit on the face, never on the side: bottom LABEL_GAP px above the face edge. No
-- backing plate or shadow behind them. Square-tile icons fill the space from ICON_TOP
-- (breaking the top edge) down to ICON_GAP above the label.
Socket.LABEL_GAP = 10
Socket.ICON_TOP = -26
Socket.ICON_GAP = 4

-- Timings (seconds). Keys press in and never bounce; outcomes carry the juice.
Socket.MOTION = {
	down = { time = 0.04, style = "Quad", dir = "Out" },
	up = { time = 0.09, style = "Quad", dir = "Out" },
	hover = { time = 0.12, style = "Quad", dir = "Out" },
}

-- Face sizes the HUD v5 uses, in studs. Every one is whole blocks.
Socket.FACES = {
	close = { 4, 4 }, -- 1 block: close X, + buy
	buy = { 12, 4 }, -- 3x1: buy, redeem, claim
	tab = { 16, 4 }, -- 4x1: window tabs, equip best
	choice = { 20, 4 }, -- 5x1: purchase options
	slot = { 8, 8 }, -- 2x2: hotbar 1-9, 0
	tile = { 12, 12 }, -- 3x3: Shop, Index, Animals
	daily = { 28, 8 }, -- 7x2: Daily Rewards
}

-- True when a face of w x h px keeps every stud whole and every 4x4 block complete.
function Socket.isWholeBlocks(w: number, h: number): boolean
	local b = Socket.STUD * Socket.BLOCK
	return w > 0 and h > 0 and w % b == 0 and h % b == 0
end

-- Snap a wanted face size (px) to the nearest whole-block size, at least one block.
function Socket.snap(px: number): number
	local b = Socket.STUD * Socket.BLOCK
	return math.max(1, math.floor(px / b + 0.5)) * b
end

export type Geometry = {
	faceW: number,
	faceH: number,
	capW: number,
	capH: number, -- rim + face + side
	wellW: number,
	wellH: number,
	capY: number, -- cap offset inside the well
	side: number, -- visible side (extrusion)
	tile: number, -- TileSize of the stud tile, px
}

-- Layer rects for a face of studsW x studsH studs; pressed sinks the cap into the well.
function Socket.geometry(studsW: number, studsH: number, pressed: boolean?): Geometry
	local fw, fh = studsW * Socket.STUD, studsH * Socket.STUD
	local sink = if pressed then Socket.PRESS else 0
	local capW, capH = fw + Socket.RIM * 2, fh + Socket.RIM * 2 + Socket.DEPTH
	return {
		faceW = fw,
		faceH = fh,
		capW = capW,
		capH = capH - sink,
		wellW = capW + Socket.WELL * 2,
		wellH = capH + Socket.WELL * 2,
		capY = Socket.WELL + sink,
		side = Socket.DEPTH - sink,
		tile = Socket.STUD * Socket.TILE_STUDS,
	}
end

-- Is the stud at (col,row), counted from the face's top-left, on a light block?
function Socket.lightBlock(col: number, row: number): boolean
	return (math.floor(col / Socket.BLOCK) + math.floor(row / Socket.BLOCK)) % 2 == 0
end

return Socket
