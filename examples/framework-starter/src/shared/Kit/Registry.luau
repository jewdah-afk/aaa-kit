--!strict
-- Registry: explicit service lifecycle. Each service is a table with optional
-- init(registry) and start(registry) functions plus playerAdded/playerRemoving.
-- All inits run (in registration order) before any start, so services may look each
-- other up in init and only begin work in start.

export type Service = {
	name: string,
	init: ((Registry) -> ())?,
	start: ((Registry) -> ())?,
	playerAdded: ((player: any) -> ())?,
	playerRemoving: ((player: any) -> ())?,
}

export type Registry = {
	add: (self: Registry, service: Service) -> Service,
	get: (self: Registry, name: string) -> Service,
	boot: (self: Registry) -> (),
	playerAdded: (self: Registry, player: any) -> (),
	playerRemoving: (self: Registry, player: any) -> (),
	_list: { Service },
	_byName: { [string]: Service },
	_booted: boolean,
}

local Registry = {}
Registry.__index = Registry

function Registry.new(): Registry
	return (setmetatable({ _list = {}, _byName = {}, _booted = false }, Registry) :: any) :: Registry
end

function Registry.add(self: Registry, service: Service): Service
	assert(not self._booted, `cannot add {service.name} after boot`)
	assert(self._byName[service.name] == nil, `duplicate service {service.name}`)
	table.insert(self._list, service)
	self._byName[service.name] = service
	return service
end

function Registry.get(self: Registry, name: string): Service
	local s = self._byName[name]
	assert(s, `unknown service {name}`)
	return s
end

function Registry.boot(self: Registry)
	assert(not self._booted, "boot called twice")
	self._booted = true
	for _, s in self._list do
		if s.init then
			s.init(self)
		end
	end
	for _, s in self._list do
		if s.start then
			s.start(self)
		end
	end
end

function Registry.playerAdded(self: Registry, player: any)
	for _, s in self._list do
		if s.playerAdded then
			s.playerAdded(player)
		end
	end
end

-- Runs in reverse order so later services clean up before the ones they depend on.
function Registry.playerRemoving(self: Registry, player: any)
	for i = #self._list, 1, -1 do
		local s = self._list[i]
		if s.playerRemoving then
			s.playerRemoving(player)
		end
	end
end

return Registry
