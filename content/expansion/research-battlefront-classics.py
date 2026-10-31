import importlib.util,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];s=importlib.util.spec_from_file_location('p',R/'content/expansion/soundtrack-broad-pipeline.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p);D=p.RESEARCH/'battlefront-classics';D.mkdir(exist_ok=True)
queries=[(2004,'Star Wars Battlefront 2004 main menu soundtrack John Williams'),(2004,'Star Wars Battlefront 2004 soundtrack galactic conquest'),(2004,'Star Wars Battlefront 2004 soundtrack battle Hoth'),(2005,'Star Wars Battlefront II 2005 main menu soundtrack John Williams'),(2005,'Star Wars Battlefront II 2005 Galactic Conquest map soundtrack'),(2005,'Star Wars Battlefront II 2005 soundtrack victory')]
for i,(year,q) in enumerate(queries,1):
 f=D/f'{i}-{year}-discover.json'
 if f.exists():continue
 rows=[]
 for r in p.search(q)[:3]:
  try:rows.append({'youtube_id':r['id'],'actual_publication':p.watch(r['id'])})
  except Exception as ex:rows.append({'youtube_id':r['id'],'error':str(ex)})
 p.write(f,{'year':year,'query':q,'candidates':rows});print(i,[(a['youtube_id'],a.get('actual_publication',{}).get('title')) for a in rows],flush=True)
