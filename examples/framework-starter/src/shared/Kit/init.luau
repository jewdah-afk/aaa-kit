--!strict
-- Kit: the one module every script requires. It exposes shared utilities and nothing
-- game-specific. No mutable globals live here: services register themselves explicitly
-- with a Registry they own, so load order is visible and testable.

local Kit = {
	Maid = require("@self/Maid"),
	Signal = require("@self/Signal"),
	Guard = require("@self/Guard"),
	Format = require("@self/Format"),
	Registry = require("@self/Registry"),
}

return table.freeze(Kit)
