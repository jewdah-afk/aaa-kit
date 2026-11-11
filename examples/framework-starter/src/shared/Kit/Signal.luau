--!strict
-- Signal: a typed, dependency-free event. Works in Roblox and in lune tests.
-- Handlers run in order of connection; a handler that errors does not stop the others.

local Signal = {}
Signal.__index = Signal

export type Connection = { connected: boolean, Disconnect: (Connection) -> () }
export type Signal<T...> = {
	connect: (self: Signal<T...>, fn: (T...) -> ()) -> Connection,
	fire: (self: Signal<T...>, T...) -> (),
	once: (self: Signal<T...>, fn: (T...) -> ()) -> Connection,
	destroy: (self: Signal<T...>) -> (),
}

function Signal.new<T...>(): Signal<T...>
	return (setmetatable({ _handlers = {} :: { any } }, Signal) :: any) :: Signal<T...>
end

function Signal.connect(self: any, fn: (...any) -> ()): Connection
	local entry = { fn = fn, connected = true }
	local conn = {
		connected = true,
		Disconnect = function(c: any)
			c.connected = false
			entry.connected = false
		end,
	}
	table.insert(self._handlers, entry)
	return conn
end

function Signal.once(self: any, fn: (...any) -> ()): Connection
	local conn: Connection
	conn = Signal.connect(self, function(...)
		conn:Disconnect()
		fn(...)
	end)
	return conn
end

function Signal.fire(self: any, ...: any)
	-- copy so handlers may connect or disconnect while firing
	local snapshot = table.clone(self._handlers)
	for _, entry in snapshot do
		if entry.connected then
			local ok, err = pcall(entry.fn, ...)
			if not ok then
				warn(`[Signal] handler failed: {err}`)
			end
		end
	end
	-- drop dead entries
	local live = {}
	for _, entry in self._handlers do
		if entry.connected then
			table.insert(live, entry)
		end
	end
	self._handlers = live
end

function Signal.destroy(self: any)
	for _, entry in self._handlers do
		entry.connected = false
	end
	self._handlers = {}
end

-- Maid compatibility
Signal.Destroy = Signal.destroy

return Signal
