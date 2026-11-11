--!strict
local C = require("./Perceptual")
local t = require("../../../../tools/lib/t")
local hex = C.hex

-- APCA reference values (apca-w3 0.0.98G), same as tools/hierarchy/test_hierarchy.py
t.near("black on white", C.apcaLc(hex("#000"), hex("#fff")), 106.04, 0.05)
t.near("white on black", C.apcaLc(hex("#fff"), hex("#000")), -107.88, 0.05)
t.near("#888 on white", C.apcaLc(hex("#888"), hex("#fff")), 63.06, 0.05)
t.near("white on #888", C.apcaLc(hex("#fff"), hex("#888")), -68.54, 0.05)
t.eq("same colour is 0", C.apcaLc(hex("#777"), hex("#777")), 0)

t.near("wcag 21:1", C.wcagRatio(hex("#000"), hex("#fff")), 21, 1e-6)
t.near("wcag #767676", C.wcagRatio(hex("#767676"), hex("#fff")), 4.54, 0.01)

local w = C.oklab(hex("#fff"))
t.near("oklab white L", w.L, 1, 1e-3)
t.near("oklab white chroma", math.abs(w.a) + math.abs(w.b), 0, 1e-3)

local orange = hex("#ff8800")
local back = C.fromOklab(C.oklab(orange))
t.near("oklab round trip r", back.r, orange.r, 1e-4)
t.near("oklab round trip g", back.g, orange.g, 1e-4)
t.near("oklab round trip b", back.b, orange.b, 1e-4)

local mid = C.mixOklab(hex("#0000ff"), hex("#ffff00"), 0.5)
t.ok("oklab midpoint of blue/yellow is not grey mud", C.oklab(mid).L > 0.5)

local red, green = hex("#cc3333"), hex("#59a033")
t.ok("deutan pulls red and green together",
	C.deltaE(C.simulateCvd(red, "deutan"), C.simulateCvd(green, "deutan")) < C.deltaE(red, green) * 0.6)
local g = C.simulateCvd(hex("#808080"), "protan")
t.near("greys stay grey", g.r, g.g, 0.01)

t.eq("audit passes good pairs", #C.audit({ { name = "coins", fg = hex("#fff"), bg = hex("#1a1a2e"), floor = 75 } }), 0)
local bad = C.audit({ { name = "hint", fg = hex("#666"), bg = hex("#444"), floor = 60 } })
t.eq("audit flags weak pair", #bad, 1)
t.eq("audit names it", bad[1].name, "hint")

-- a ladder that only changes hue (same OKLab L and chroma) fails
local function lch(L: number, c: number, hDeg: number)
	local h = math.rad(hDeg)
	return C.fromOklab({ L = L, a = c * math.cos(h), b = c * math.sin(h) })
end
local _, greyWarn = C.ladder({ lch(0.6, 0.12, 30), lch(0.6, 0.12, 140) })
t.ok("hue-only ladder warned as close in grey", #greyWarn > 0)
-- the classic rare -> epic trap: a light blue and a light purple collapse under deuteranopia
local trap = C.ladder({ hex("#3d8bff"), hex("#b44dff") })
t.eq("blue -> light purple collapses under deutan", #trap, 1)
t.ok("names the deutan collapse", (trap[1] or ""):find("deutan") ~= nil)
-- fix: make the purple darker than the blue so the step survives in lightness
t.eq("value ladder passes", #C.ladder({ hex("#6b6b6b"), hex("#3d8bff"), hex("#8a2be2"), hex("#ffb000") }), 0)

-- regression: the shipped rarity ladder (materials/RarityStyle.TIERS, = HIERARCHY.md 7) stays CVD-safe
local RarityStyle = require("../../materials/examples/RarityStyle")
local cols = {}
for i, tier in RarityStyle.TIERS do
	cols[i] = { r = tier.color[1] / 255, g = tier.color[2] / 255, b = tier.color[3] / 255 }
end
t.ok("ladder has every tier", #cols >= 6)
local problems, warnings = C.ladder(cols)
t.eq("rarity ladder is colour-blind safe: " .. table.concat(problems, "; "), #problems, 0)
-- known and accepted: Uncommon and Rare are close in grey; frame behaviour (HIERARCHY 7) separates them
t.eq("only the known grey-close step", table.concat(warnings, "; "):match("^step 2%->3") ~= nil and #warnings, 1)

t.done()
