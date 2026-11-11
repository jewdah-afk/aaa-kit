--!strict
local Receipts = require("./Receipts")
local t = require("../../../../tools/lib/t")

local products = {
	[111] = function(save)
		save.gems += 100
	end,
}
local save = { gems = 0 }
t.eq("grants", Receipts.decide(save, products, 111, "p1"), "granted")
t.eq("dedupes", Receipts.decide(save, products, 111, "p1"), "duplicate")
t.eq("granted once", save.gems, 100)
t.eq("retry when not loaded", Receipts.decide(nil, products, 111, "p2"), "retry")
t.eq("unknown product", Receipts.decide(save, products, 999, "p3"), "unknown")
save.receipts.old = 0
save.receipts.p1 = 35 * 86400
Receipts.prune(save, 30, 40 * 86400)
t.ok("prunes old receipts", save.receipts.old == nil)
t.ok("keeps recent receipts", save.receipts.p1 ~= nil)
t.done()
