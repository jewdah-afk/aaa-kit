--!strict
local Spec = require("./StudPlateSpec")
local t = require("../../../../tools/lib/t")

local L = Spec.layout(168, 176) -- the Shop / Index / Animals tile
t.eq("sill 7.5% of 176", L.sill, 13)
t.eq("face width", L.faceW, 160)
t.eq("face height", L.faceH, 176 - 8 - 13)
t.eq("press drops by the sill", L.pressDrop, 13)
t.eq("stud tile = 8 studs x 22 px", L.tile, 176)
t.eq("face starts at the rim (studs run edge to edge)", L.faceX, Spec.RIM)

local small = Spec.layout(48, 48)
t.eq("sill never below the minimum", small.sill, Spec.SILL_MIN)

local s, d = Spec.labelInk(40)
t.eq("label stroke 14%", s, 6)
t.eq("label drop 8%", d, 3)

local r, g, b = Spec.hex("#DD1640")
t.ok("hex parse", r == 221 and g == 22 and b == 64)

for name, f in Spec.FAMILIES do
	t.ok(`{name} has a face`, (f.top ~= nil and f.base ~= nil) or f.tex ~= nil)
end
t.eq("Upgrades hidden for release", Spec.BUTTONS.Upgrades.visible, false)
t.eq("Animals is violet (orange paw pops)", Spec.BUTTONS.Animals.family, "violet")
t.eq("phone landscape clamps to half size", Spec.scaleFor(390), 0.5)
t.near("720p", Spec.scaleFor(720), 720 / 1080, 1e-9)
t.eq("scale clamps", Spec.scaleFor(4000), 1.25)

t.done()
