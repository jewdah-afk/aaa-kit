--!strict
-- Separate loudness tiers 1-6 from research milestone labels T12+.
local H = {}
export type Event = {id:string, priority:number, start:number, duration:number, reducedMotion:boolean}
function H.new()
    return {active = nil :: Event?, calmUntil = 0, maxFX = 1}
end
function H.offer(self, event:Event, now:number): boolean
    if self.active and now < (self.active.start+self.active.duration) and self.active.priority >= event.priority then
        return false
    end
    self.active = event
    self.calmUntil = now + event.duration + .2
    return true
end
function H.intensity(self, id:string, now:number): number
    local e = self.active
    if not e or e.id ~= id or e.reducedMotion or now >= e.start+e.duration then return 0 end
    local x = math.clamp((now-e.start)/e.duration,0,1)
    return math.min(1,4*x,4*(1-x))
end
return H
