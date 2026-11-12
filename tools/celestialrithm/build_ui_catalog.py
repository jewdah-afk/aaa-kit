#!/usr/bin/env python3
"""Deterministic generation of auditable, non-implemented Celestialrithm UI recipes."""
import json
from pathlib import Path
OUT=Path(__file__).resolve().parents[2]/'docs'/'celestialrithm'/'ui_recipe_catalog.jsonl'
GENRES=['incremental','roguelike','tower-defense','simulator','crafting','racing','collection','survival','social','strategy','platformer','dungeon','tycoon','rpg']
COMPONENTS=['primary-key','secondary-key','nav-rail','currency-meter','xp-meter','health-meter','inventory-slot','shop-card','rarity-frame','tooltip','modal','notification','skill-tree','quest-tracker','hotbar','avatar-stage','reward-reveal','world-select','crafting-slot','settings-toggle']
MATERIALS=['hydroglass','prism-gel','solar-plasma','ice-crystal','slime','holo-foil','void','molten-gold','brushed-steel','neon-ink','pearl','obsidian','biolume','aurora','frosted-glass','ceramic','copper','iridescent','sandstone','pixel-chrome']
MOTION=['spring-press','elastic-rebound','caustic-drift','gradient-travel','masked-shine','rare-edge-trace','number-odometer','reward-stagger','sdf-reveal','mesh-bend','icon-relief','squash-stretch','surface-memory','light-sweep','soft-pulse','fracture-heal','wave-coupling','progress-flow','focus-bracket','depth-parallax']
DEVICES=['low-mobile','mid-mobile','desktop']
BUDGETS={'low-mobile':{'fx_ms':0.7,'ei_px':64,'mesh_vertices':0,'active_hero_fx':1,'background_update_hz':0},'mid-mobile':{'fx_ms':1.5,'ei_px':128,'mesh_vertices':169,'active_hero_fx':1,'background_update_hz':15},'desktop':{'fx_ms':2.5,'ei_px':256,'mesh_vertices':625,'active_hero_fx':2,'background_update_hz':30}}
def recipes():
 for gi,g in enumerate(GENRES):
  for ci,c in enumerate(COMPONENTS):
   for mi,m in enumerate(MATERIALS):
    # One grounded baseline and two optional tiers per combination: 16,800 recipes
    for di,d in enumerate(DEVICES):
     motion=MOTION[(gi*3+ci*5+mi*7+di)%len(MOTION)]
     yield {'id':f'CR-{gi:02d}-{ci:02d}-{mi:02d}-{di}', 'genre':g,'component':c,'material':m,'motion':motion,'device':d,'budget':BUDGETS[d], 'status':'generated_candidate_not_implemented','visual_contract':['squared_silhouette','near_black_outline','flat_readable_face','depth_under_face','protect_text_and_icon','no_cursor_magnetism'],'constraints':{'label_static':True,'only_active_selection_loops':True,'fullscreen_fx_requires_ceremony':True},'qa':['scanpath','APCA','CVD','flash','pixel-ownership','steady-state','device-profiler']}
def main():
 OUT.parent.mkdir(parents=True,exist_ok=True)
 n=0
 with OUT.open('w') as f:
  for entry in recipes():
   f.write(json.dumps(entry,separators=(',',':'))+'\n');n+=1
 print(f'{n} candidate recipes in {OUT}')
if __name__=='__main__': main()
