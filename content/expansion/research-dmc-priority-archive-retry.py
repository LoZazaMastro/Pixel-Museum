import json,importlib.util,re
from pathlib import Path
R=Path(__file__).resolve().parents[2];sp=importlib.util.spec_from_file_location('p',R/'content/expansion/soundtrack-broad-pipeline.py');p=importlib.util.module_from_spec(sp);sp.loader.exec_module(p);B=p.RESEARCH/'user-priority/dmc'
queries=[('dmc1-public','Devil May Cry 2001 Public Enemy OST'),('dmc1-cathedral','Devil May Cry 2001 Cathedral OST'),('dmc1-lock','Devil May Cry 2001 Lock Load original OST'),('dmc2-fire','Devil May Cry 2 Fire Away Dante Battle 1 OST'),('dmc2-shoot','Devil May Cry 2 Shoot the Works OST'),('dmc2-wings','Devil May Cry 2 Wings of Guardian OST'),('dmc3-cry','Devil May Cry 3 Devils Never Cry OST original'),('dmc3-cerberus','Devil May Cry 3 Cerberus battle OST original'),('dmc3-vergil','Devil May Cry 3 Vergil Battle 2 OST original'),('dmc4-time','Devil May Cry 4 Time Has Come OST original'),('dmc4-sworn','Devil May Cry 4 Sworn Through Swords OST original'),('dmc5-crimson','Jeff Rona Rachel Fannan Crimson Cloud official audio'),('dmc5-subhuman','Cody Matthew Johnson Subhuman Cliff Lloret official'),('dmc5-silver','Casey Edwards Silver Bullet Devil May Cry 5 official')]
for key,query in queries:
 out=B/(key+'-retry.json')
 if out.exists():continue
 rows=[];errors=[]
 for flat in p.search(query)[:3]:
  try:w=p.watch(flat['id']);rows.append({'youtube_id':flat['id'],'actual_publication':w})
  except Exception as ex:errors.append(str(ex))
 p.write(out,{'query':query,'state':'requires_manual_original_game_version_and_role_review','candidates':rows,'errors':errors});print(key,len(rows),flush=True)
