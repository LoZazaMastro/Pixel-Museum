import json,importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('p',Path('content/expansion/soundtrack-broad-pipeline.py'));p=importlib.util.module_from_spec(s);s.loader.exec_module(p);B=p.RESEARCH/'licensed-priority';queries=[('burnout3takedown',8,'Chronic Future Time And Time Again Lines In My Face'),('burnout3takedown',10,'The Von Bondies Cmon Cmon Pawn Shoppe Heart'),('needforspeedunderground2',2,'Rise Against Give It All Siren Song Of The Counter Culture'),('needforspeedunderground2',3,'Queens Of The Stone Age In My Head Lullabies To Paralyze'),('needforspeedunderground2',4,'Spiderbait Black Betty Tonight Alright'),('needforspeedunderground2',5,'Skindred Nobody Babylon'),('needforspeedunderground2',9,'Helmet Crashing Foreign Cars Size Matters'),('needforspeedunderground2',10,'Killradio Scavenger Raising The Dead'),('needforspeedunderground2',12,'Unwritten Law Celebration Song Heres To The Mourning')]
for folder,n,q in queries:
 out=B/folder/(str(n).zfill(2)+'-retry.json')
 if out.exists():continue
 rows=p.search(q);result=[]
 for r in rows[:4]:
  try:w=p.watch(r['id']);result.append({'youtube_id':r['id'],'metadata':w})
  except Exception as ex:result.append({'youtube_id':r['id'],'error':str(ex)})
 p.write(out,{'query':q,'actual_publications':result});print(folder,n,[(r['youtube_id'],r.get('metadata',{}).get('title')) for r in result],flush=True)
