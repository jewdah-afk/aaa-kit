--!strict
-- Pure intensity/ownership gate for an EXISTING flat Stud UI face.
-- Tiers here refer to importance of button events, not new tiers beyond HIERARCHY.md's 1..6.
local Physics = require('./FlatKeyPhysics')
local H={}
H.EVENT={idle=0,focus=1,press=2,confirm=3,ceremony=4}
H.MATERIAL={shop='coral',upgrades='prism',index='hydro',animals='solar',daily='green'}
-- one nominated UI button owns the attention; all others are quiet.
function H.weight(buttonId:string,ownerId:string?,event:number,reducedMotion:boolean?):number
 if event<=0 or reducedMotion then return 0 end
 if buttonId~=ownerId then return 0 end
 return ({[1]=0.18,[2]=0.5,[3]=0.75,[4]=1.0})[event] or 0
end
-- Reserves the center text+icon zone and the perimeter ink from field writes.
function H.mask(u:number,v:number):number
 if u<0.065 or u>0.935 or v<0.07 or v>0.93 then return 0 end
 -- image art/icon lives in the upper body; label lives at the foot.
 if v>0.68 then return 0 end
 if u>0.12 and u<0.88 and v>0.12 and v<0.67 then return 0.1 end
 return 1
end
function H.optical(s:any,u:number,v:number,ownerWeight:number,baseBrightness:number):number
 local amp=H.mask(u,v)*ownerWeight
 -- Safety: brighten at most ~16% when the underlying surface is already very bright.
 local headroom=math.max(0,1-baseBrightness)
 return math.min(0.24,headroom*0.65)*amp*Physics.caustic(s,u,v)
end
return H
