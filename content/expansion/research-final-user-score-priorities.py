"""Bounded resumable discovery only. A title/composer query is not admission evidence."""
import json,importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2];s=importlib.util.spec_from_file_location('p',R/'content/expansion/soundtrack-broad-pipeline.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
D=p.RESEARCH/'final-user-score-priorities';D.mkdir(exist_ok=True)
queries=[
 ('Auto Modellista',2002,'Auto Modellista Upper Opening Tetsuya Shibata soundtrack'),
 ('Auto Modellista',2002,'Auto Modellista Full Scaled Tetsuya Shibata soundtrack'),
 ('Auto Modellista',2002,'Auto Modellista Main Menu Garage Life soundtrack'),
 ('The Simpsons: Hit & Run',2003,'The Simpsons Hit Run Homer Tuba Marc Baril soundtrack'),
 ('The Simpsons: Hit & Run',2003,'The Simpsons Hit Run Bart Guitar soundtrack official'),
 ('The Simpsons: Hit & Run',2003,'The Simpsons Hit Run Simpsons Cola soundtrack'),
 ('The Getaway',2002,'The Getaway 2002 Andrew Hale Shawn Lee main theme soundtrack'),
 ('The Getaway',2002,'The Getaway 2002 soundtrack track 1 2'),
 ('Enter the Matrix',2003,'Enter the Matrix 2003 Don Davis soundtrack original'),
 ('Enter the Matrix',2003,'Enter the Matrix Erik Lundborg soundtrack'),
 ('The Matrix: Path of Neo',2005,'The Matrix Path of Neo 2005 soundtrack Tobias Enhus original'),
 ('The Matrix: Path of Neo',2005,'The Matrix Path of Neo 2005 soundtrack Main Menu'),
 ('Need for Speed III: Hot Pursuit',1998,'Rom Di Prisco Aquila 303 Need For Speed III soundtrack'),
 ('Need for Speed III: Hot Pursuit',1998,'Saki Kaskas Knockout Need For Speed III soundtrack'),
 ('Need for Speed III: Hot Pursuit',1998,'Matt Ragan Romulus 3 Need For Speed III soundtrack'),
 ('Onimusha 2: Samurai\'s Destiny',2002,'Onimusha 2 Taro Iwashiro Main Theme soundtrack'),
 ('Onimusha 2: Samurai\'s Destiny',2002,'Onimusha 2 Taro Iwashiro Truth of Resolution'),
 ('Onimusha 3: Demon Siege',2004,'Onimusha 3 Demon Siege soundtrack Nobuyoshi Suzuki'),
 ('Onimusha 3: Demon Siege',2004,'Onimusha 3 Akari Kaida Main Theme soundtrack'),
 ('Onimusha: Dawn of Dreams',2006,'Onimusha Dawn of Dreams Hideyuki Fukasawa soundtrack'),
 ('Onimusha: Dawn of Dreams',2006,'Onimusha Dawn of Dreams Jamie Christopherson soundtrack'),
 ('Onimusha: Warlords',2001,'Onimusha Warlords 2019 remastered soundtrack composer'),
 ('Onimusha: Warlords',2001,'Onimusha Warlords 2019 remaster Main Theme soundtrack'),
]
for i,(game,year,query) in enumerate(queries,1):
 f=D/(str(i).zfill(2)+'-'+p.norm(game)+'.json')
 if f.exists():continue
 rows=[];errors=[]
 for result in p.search(query)[:3]:
  try:actual=p.watch(result['id']);rows.append({'youtube_id':result['id'],'actual_publication':actual})
  except Exception as ex:errors.append({'youtube_id':result['id'],'error':str(ex)})
 p.write(f,{'publication_status':'research_only_unreviewed','game':game,'year':year,'query':query,'candidates':rows,'errors':errors});print(i,game,len(rows),flush=True)
