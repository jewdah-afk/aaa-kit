--!strict
-- Pure Luau, deterministic UI UX motion choreography. No engine dependencies.
-- R&D scheduler: explicit focus owner; no pointer attraction / magnetic cursor motion.
local M = {}
local profiles = {
  press={duration=.26,priority=3,amp=.12}, select={duration=.34,priority=2,amp=.07},
  purchase={duration=.62,priority=4,amp=.16}, reward={duration=1.25,priority=6,amp=.22},
  alert={duration=.42,priority=5,amp=.10}, idle={duration=0,priority=0,amp=0},
}
local function clamp(v,lo,hi) return math.max(lo,math.min(hi,v)) end
function M.easeOutBack(t,over)
 t=clamp(t,0,1)-1; local c=1.70158*(over or 1)
 return 1+(c+1)*t*t*t+c*t*t
end
function M.new()
 return {time=0,owner=nil,events={},cooldowns={},settings={intensity=1,reducedMotion=false},stats={rejected=0,accepted=0}}
end
function M.emit(self,id,kind,tier)
 assert(type(id)=='string' and profiles[kind], 'invalid motion event')
 local pr=profiles[kind]
 local effective=math.max(pr.priority,tier or 0)
 if self.owner and self.owner.priority>effective and self.owner.untilTime>self.time then
   self.stats.rejected+=1; return false
 end
 if self.cooldowns[id] and self.time-self.cooldowns[id]<.075 then
   self.stats.rejected+=1; return false
 end
 self.cooldowns[id]=self.time
 local e={id=id,kind=kind,start=self.time,duration=pr.duration,priority=effective,untilTime=self.time+pr.duration}
 self.owner=e; table.insert(self.events,e); self.stats.accepted+=1; return true
end
function M.step(self,dt)
 self.time+=math.max(0,math.min(dt,.05))
 if self.owner and self.time>=self.owner.untilTime then self.owner=nil end
 for i=#self.events,1,-1 do if self.time>self.events[i].untilTime then table.remove(self.events,i) end end
end
function M.sample(self,id)
 local owner=self.owner
 if not owner or owner.id~=id then return {scaleX=1,scaleY=1,depth=0,shine=0,burst=0,fxWeight=0} end
 local p=profiles[owner.kind]
 local u=clamp((self.time-owner.start)/math.max(.001,owner.duration),0,1)
 local w=math.sin(math.pi*u)^2
 local amp=p.amp*clamp(self.settings.intensity,0,2)
 if self.settings.reducedMotion then amp=0 end
 local press=owner.kind=='press' or owner.kind=='purchase'
 local phase=press and -1 or 1
 return {scaleX=1+phase*amp*.6*w,scaleY=1-phase*amp*w,
   depth=(press and amp or 0)*w,
   shine=clamp((u-.10)*2.8,0,1)*clamp((.95-u)*5,0,1),
   burst=owner.kind=='reward' and math.sin(math.pi*u)^4 or 0,
   fxWeight=w}
end
function M.profile(kind) return profiles[kind] end
return M
