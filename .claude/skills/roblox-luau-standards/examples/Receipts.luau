--!strict
-- Receipts: a developer-product handler that never double-grants and always answers.
-- Rules: dedupe by PurchaseId (persisted in the save), grant only for known product ids,
-- return NotProcessedYet when the player's data isn't loaded so Roblox retries later.
-- The decision logic is pure (testable); `bind` wires it to MarketplaceService.

local Receipts = {}

export type Grant = (save: any) -> ()
export type Decision = "granted" | "duplicate" | "retry" | "unknown"

-- Pure core. `products` maps productId -> grant function. Mutates save on success.
function Receipts.decide(save: any?, products: { [number]: Grant }, productId: number, purchaseId: string): Decision
	if save == nil then
		return "retry" -- player left or data not loaded: Roblox will call again
	end
	save.receipts = save.receipts or {}
	if save.receipts[purchaseId] then
		return "duplicate" -- already granted: still answer PurchaseGranted
	end
	local grant = products[productId]
	if not grant then
		return "unknown"
	end
	grant(save)
	save.receipts[purchaseId] = os.time()
	return "granted"
end

-- Keep the receipts table bounded: drop entries older than `days`.
function Receipts.prune(save: any, days: number, now: number)
	if not save.receipts then
		return
	end
	for id, at in save.receipts do
		if now - at > days * 86400 then
			save.receipts[id] = nil
		end
	end
end

-- Roblox wiring (compile-checked; runs only in a server Script).
function Receipts.bind(getSave: (Player) -> any?, products: { [number]: Grant }, saveNow: (Player) -> boolean)
	local MarketplaceService = (game :: any):GetService("MarketplaceService")
	local Players = (game :: any):GetService("Players")
	MarketplaceService.ProcessReceipt = function(info: any)
		local player = Players:GetPlayerByUserId(info.PlayerId)
		local d = Receipts.decide(player and getSave(player), products, info.ProductId, info.PurchaseId)
		if d == "granted" then
			-- persist before confirming; if the save fails, let Roblox retry
			if not saveNow(player) then
				return Enum.ProductPurchaseDecision.NotProcessedYet
			end
			return Enum.ProductPurchaseDecision.PurchaseGranted
		elseif d == "duplicate" then
			return Enum.ProductPurchaseDecision.PurchaseGranted
		end
		if d == "unknown" then
			warn(`[Receipts] unknown product {info.ProductId}`)
		end
		return Enum.ProductPurchaseDecision.NotProcessedYet
	end
end

return Receipts
