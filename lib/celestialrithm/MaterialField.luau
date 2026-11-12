--!strict
-- Pure repeatable surface field; base for atlas-backed EditableImage adapter.
local M = {}
local abs,cos,sin,sqrt,exp = math.abs,math.cos,math.sin,math.sqrt,math.exp
function M.sample(kind: string, u: number, v: number, t: number, pressure: number): number
    local x,y = 2*u-1,2*v-1
    local radius = sqrt(x*x+y*y)
    local shock = sin(17*radius - 8*t)*exp(-2*radius)*pressure
    if kind=="hydro" then
        return .58*cos(11*x+4*sin(3*y+1.8*t))*cos(10*y-5*sin(2*x+1.2*t))+.42*shock
    elseif kind=="prism" then return sin(10*x+5*y+2*t)+.6*cos(12*y-3*t)+.35*shock
    elseif kind=="solar" then return .6*sin(16*x-9*t)+.75*shock
    elseif kind=="bio" then return sin(12*(x+y)+3*sin(8*y-t))*cos(8*x-4*t)
    elseif kind=="frost" then return cos(16*math.max(abs(x),abs(y))-2*t)+.35*shock
    elseif kind=="void" then return sin(11*x+8*t)*cos(12*y-3*t)+.8*shock
    elseif kind=="holo" then return sin(7*x+8*y+3*t)+cos(14*(x-y)-t)
    else return sin(12*x+5*t)*sin(8*y-3*t) end
end
return M
