import importlib.util,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];s=importlib.util.spec_from_file_location('p',R/'content/expansion/soundtrack-broad-pipeline.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p);D=p.RESEARCH/'rhythm-priorities';D.mkdir(exist_ok=True)
queries=[
 ('PaRappa the Rapper',1996,'PaRappa Rapper Chop Chop Master Onion original soundtrack'),
 ('PaRappa the Rapper',1996,'PaRappa Rapper Instructor Mooselini original soundtrack'),
 ('PaRappa the Rapper 2',2002,'PaRappa Rapper 2 Toasty Buns original soundtrack'),
 ('PaRappa the Rapper 2',2002,'PaRappa Rapper 2 Noodles original soundtrack'),
 ('Beatmania',1997,'beatmania first mix 20 november original soundtrack DJ Nagureo'),
 ('Beatmania',1997,'beatmania first mix u gotta groove DJ Nagureo'),
 ('Dance Dance Revolution',1998,'Smile dk Butterfly official original 1998'),
 ('Dance Dance Revolution',1998,'DDR 1998 AM 3P kTz original soundtrack'),
 ('Dance Dance Revolution Solo Bass Mix',1999,'DDR Solo Bass Mix 1999 songlist Together Forever Captain Jack'),
 ('Rez',2001,'Rez OST Buggie Running Beeps Keiichi Sugiyama'),
 ('Rez',2001,'Rez OST Protocol Rain Mist'),
 ('Lumines',2004,'Lumines PSP original soundtrack Shinin Mondo Grosso'),
 ('Lumines',2004,'Lumines PSP original soundtrack Shake Your Body Mondo Grosso'),
 ('Guitar Hero',2005,'Shaimus All Of This official'),
 ('Guitar Hero',2005,'The Slip Even Rats official'),
 ('Green Day: Rock Band',2010,'Green Day Basket Case official audio'),
 ('Green Day: Rock Band',2010,'Green Day Jesus Of Suburbia official audio'),
 ('Rock Band 3',2010,'Queen Bohemian Rhapsody official audio'),
 ('Rock Band 3',2010,'The Doors Break On Through To The Other Side official audio'),
]
for i,(game,year,q) in enumerate(queries,1):
 f=D/(str(i).zfill(2)+'-'+p.norm(game)+'.json')
 if f.exists():continue
 rows=[]
 for r in p.search(q)[:3]:
  try:rows.append({'youtube_id':r['id'],'actual_publication':p.watch(r['id'])})
  except Exception as ex:rows.append({'youtube_id':r['id'],'error':str(ex)})
 p.write(f,{'publication_status':'research_only_needs_exact_game_recording_and_roles','game':game,'year':year,'query':q,'candidates':rows});print(i,game,[(a['youtube_id'],a.get('actual_publication',{}).get('title')) for a in rows],flush=True)
