--!strict
local Contrast = require("./Contrast")
local t = require("../../../../tools/lib/t")

t.near("black L", Contrast.lightness(0, 0, 0), 0, 1e-6)
t.near("white L", Contrast.lightness(255, 255, 255), 1, 1e-4)
t.eq("white band", Contrast.bandOf({ 255, 255, 255 }), 7)
t.eq("black band", Contrast.bandOf({ 0, 0, 0 }), 0)

local ok1 = Contrast.gate({ { 120, 120, 120 } }, { { 110, 110, 115 } })
t.ok("grey on grey fails", not ok1)
local ok2, gap = Contrast.gate({ { 240, 220, 180 } }, { { 30, 28, 40 } })
t.ok("bone on night passes", ok2 and gap >= 2)

local ring = Contrast.shiftBands({ 90, 140, 60 }, -2)
t.eq("shift down 2 bands", Contrast.bandOf(ring), Contrast.bandOf({ 90, 140, 60 }) - 2)
t.ok("keeps hue (green stays dominant)", ring[2] >= ring[1] and ring[2] >= ring[3])

t.done()
