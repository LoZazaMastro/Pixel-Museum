import json,importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2];s=importlib.util.spec_from_file_location('p',R/'content/expansion/soundtrack-broad-pipeline.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p);D=p.RESEARCH/'final-user-score-priorities/retries';D.mkdir(exist_ok=True)
queries=[('The Getaway',2002,'The Getaway 2002 original soundtrack full'),('The Simpsons: Hit & Run',2003,'The Simpsons Hit and Run original soundtrack volume 1'),('The Simpsons: Hit & Run',2003,'The Simpsons Hit and Run original soundtrack volume 2'),('The Simpsons: Hit & Run',2003,'The Simpsons Hit and Run original soundtrack volume 3'),('Onimusha 3: Demon Siege',2004,'Onimusha 3 opening Masamichi Amano soundtrack'),('Onimusha: Warlords',2001,'Onimusha Hama no Hibiki 2018 soundtrack'),('The Simpsons: Hit & Run',2003,'Marc Baril Homers Tuba original audio')]
for i,(game,year,query) in enumerate(queries,1):
 f=D/(str(i).zfill(2)+'.json')
 if f.exists():continue
 rows=[];errors=[]
 for result in p.search(query)[:3]:
  try:w=p.watch(result['id']);rows.append({'youtube_id':result['id'],'actual_publication':w})
  except Exception as ex:errors.append({'youtube_id':result['id'],'error':str(ex)})
 p.write(f,{'publication_status':'research_only_unreviewed','game':game,'year':year,'query':query,'candidates':rows,'errors':errors});print(i,game,len(rows),flush=True)
for vid in ['HpSkRSKRtAA']:
 try:p.write(D/('watch-'+vid+'.json'),p.watch(vid));print(vid,'actualwatch',flush=True)
 except Exception as ex:print(vid,str(ex),flush=True)
