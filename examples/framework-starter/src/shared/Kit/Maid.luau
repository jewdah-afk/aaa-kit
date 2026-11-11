--!strict
-- Maid: collects anything that needs cleaning up and cleans it in one call.
-- Accepts functions, RBXScriptConnections, Instances, threads and objects with :Destroy().
-- Always store it as `self._maid` (lower case) so a grep finds every one.

export type Task = any

local Maid = {}
Maid.__index = Maid

export type Maid = typeof(setmetatable({} :: { _tasks: { Task } }, Maid))

function Maid.new(): Maid
	return setmetatable({ _tasks = {} }, Maid)
end

-- Adds a task and returns it, so `local conn = maid:give(signal:Connect(fn))` reads naturally.
function Maid.give<T>(self: Maid, task: T): T
	table.insert(self._tasks, task)
	return task
end

local function clean(task: Task)
	local kind = typeof(task)
	if kind == "function" then
		task()
	elseif kind == "thread" then
		pcall(task.cancel or coroutine.close, task)
	elseif kind == "RBXScriptConnection" then
		task:Disconnect()
	elseif kind == "Instance" then
		task:Destroy()
	elseif type(task) == "table" then
		if type(task.Destroy) == "function" then
			task:Destroy()
		elseif type(task.Disconnect) == "function" then
			task:Disconnect()
		end
	end
end

-- Cleans every task in reverse order (last given, first cleaned) and empties the list.
function Maid.clean(self: Maid)
	local tasks = self._tasks
	self._tasks = {}
	for i = #tasks, 1, -1 do
		clean(tasks[i])
	end
end

Maid.Destroy = Maid.clean

return Maid
