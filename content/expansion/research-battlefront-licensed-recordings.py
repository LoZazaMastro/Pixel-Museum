import importlib.util,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];s=importlib.util.spec_from_file_location('p',R/'content/expansion/soundtrack-broad-pipeline.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p);D=p.RESEARCH/'battlefront-classics'
queries=[('clash','John Williams The Clash of Lightsabers official soundtrack'),('imperial','John Williams The Imperial March official soundtrack original'),('heroes','John Williams Battle of the Heroes original soundtrack'),('fates','John Williams Duel of the Fates original soundtrack')]
for key,q in queries:
 rows=[]
 for r in p.search(q)[:3]:
  try:rows.append({'youtube_id':r['id'],'actual_publication':p.watch(r['id'])})
  except Exception as ex:rows.append({'youtube_id':r['id'],'error':str(ex)})
 p.write(D/(key+'-licensed-search.json'),{'query':q,'candidates':rows});print(key,[(a['youtube_id'],a.get('actual_publication',{}).get('title')) for a in rows],flush=True)
