import importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('p',R/'content/expansion/soundtrack-broad-pipeline.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
D=p.RESEARCH/'rhythm-priorities'
queries=[
 ('beatmania-u-gotta','beatmania original soundtrack u gotta groove DJ nagureo'),
 ('beatmania20single','beatmania 1997 soundtrack 20 november single mix'),
 ('solo-paranoia','PARANOIA EVOLUTION 200 original soundtrack DDR Solo Bass Mix'),
 ('solo-hysteria','NAOKI 190 HYSTERIA original soundtrack DDR Solo Bass'),
 ('lumines-shake-official','MONDO GROSSO Shake Ya Body Sony Music official audio'),
 ('greenday-jesus-delivery','Green Day Jesus of Suburbia Provided to YouTube by Reprise American Idiot')]
for slug,query in queries:
 f=D/(slug+'-discovery.json')
 if f.exists():continue
 rows=[]
 for x in p.search(query)[:3]:
  try: rows.append({'youtube_id':x['id'],'actual':p.watch(x['id'])})
  except Exception as ex:rows.append({'youtube_id':x['id'],'error':str(ex)})
 p.write(f,{'publication_status':'research_only','query':query,'candidates':rows})
 print(slug,[(r['youtube_id'],r.get('actual',{}).get('title')) for r in rows],flush=True)
