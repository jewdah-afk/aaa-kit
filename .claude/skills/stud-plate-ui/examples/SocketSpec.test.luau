--!strict
local Socket = require("./SocketSpec")
local t = require("../../../../tools/lib/t")

for name, f in Socket.FACES do
	t.ok(`{name} face is whole 4x4 blocks`, Socket.isWholeBlocks(f[1] * Socket.STUD, f[2] * Socket.STUD))
end
t.ok("100 px is not whole blocks", not Socket.isWholeBlocks(100, 48))
t.eq("snap 100 -> 96", Socket.snap(100), 96)
t.eq("snap 10 -> one block", Socket.snap(10), 48)
t.eq("snap 150 -> 144", Socket.snap(150), 144)

local g = Socket.geometry(12, 12)
t.eq("tile face 144", g.faceW, 144)
t.eq("cap = face + rim", g.capW, 152)
t.eq("cap height includes the side", g.capH, 144 + 8 + 10)
t.eq("well = cap + 8 each side", g.wellW, 168)
t.eq("well height", g.wellH, 162 + 16)
t.eq("stud tile is 8 studs", g.tile, 96)
t.eq("rest side", g.side, 10)

local p = Socket.geometry(12, 12, true)
t.eq("pressed cap sinks 8", p.capY - g.capY, 8)
t.eq("pressed side 2 px", p.side, 2)
t.eq("pressed well unchanged", p.wellH, g.wellH)
t.eq("pressed cap bottom stays on the well floor", p.capY + p.capH, g.capY + g.capH)

t.ok("stud (0,0) light", Socket.lightBlock(0, 0))
t.ok("stud (4,0) dark", not Socket.lightBlock(4, 0))
t.ok("stud (4,4) light", Socket.lightBlock(4, 4))
t.ok("stud (3,7) dark", not Socket.lightBlock(3, 7))

local tile = Socket.geometry(12, 12)
t.ok("label clears the side (bottom above face edge)", Socket.LABEL_GAP > 0 and Socket.RIM + tile.faceH - Socket.LABEL_GAP < Socket.RIM + tile.faceH)
t.ok("checker stays soft", Socket.CHECKER.darkDrop < 0.08 and Socket.CHECKER.lightLift < 0.08)

t.done()
