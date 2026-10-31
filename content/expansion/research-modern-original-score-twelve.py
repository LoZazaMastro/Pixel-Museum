import json,importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2];s=importlib.util.spec_from_file_location('p',R/'content/expansion/soundtrack-broad-pipeline.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p);D=p.RESEARCH/'modern-original-twelve';D.mkdir(exist_ok=True)
queries=[
 ('Stardew Valley',2016,'Stardew Valley Overture ConcernedApe official soundtrack'),('Stardew Valley',2016,'Stardew Valley Spring Wild Horseradish Jam ConcernedApe soundtrack'),
 ('Dying Light',2015,'Dying Light Horizon Pawel Blaszczak soundtrack official'),('Dying Light',2015,'Dying Light Main Theme Pawel Blaszczak soundtrack official'),
 ('Half-Life: Alyx',2020,'Half Life Alyx Anti Citizen Valve soundtrack'),('Half-Life: Alyx',2020,'Half Life Alyx Ending Triumph Valve soundtrack'),
 ('Dishonored 2',2016,'Dishonored 2 Main Theme Daniel Licht Bethesda soundtrack'),('Dishonored 2',2016,'Dishonored 2 The Dreadful Wale Daniel Licht soundtrack'),
 ('The Last Guardian',2016,'The Last Guardian Overture Takeshi Furukawa soundtrack official'),('The Last Guardian',2016,'The Last Guardian Finale Escape Takeshi Furukawa soundtrack'),
 ('The Witcher 3: Wild Hunt',2015,'The Witcher 3 Geralt of Rivia official soundtrack'),('The Witcher 3: Wild Hunt',2015,'The Witcher 3 The Trail official soundtrack'),
 ('Return of the Obra Dinn',2018,'Return of the Obra Dinn soundtrack Lucas Pope Soldiers of the Sea'),('Return of the Obra Dinn',2018,'Return of the Obra Dinn main theme Lucas Pope soundtrack'),
 ('SteamWorld Heist',2015,'Steam Powered Giraffe SteamWorld Heist Honeybee soundtrack'),('SteamWorld Heist',2015,'Steam Powered Giraffe SteamWorld Heist The Stars soundtrack'),
 ('Nuclear Throne',2015,'Nuclear Throne The Wasteland Jukio Kallio soundtrack'),('Nuclear Throne',2015,'Nuclear Throne Legend of the Throne Jukio Kallio soundtrack'),
 ('Life Is Strange',2015,'Life Is Strange Golden Hour Jonathan Morali soundtrack'),('Life Is Strange',2015,'Life Is Strange Max Chloe Jonathan Morali soundtrack'),
 ('INSIDE',2016,'INSIDE Martin Stig Andersen Sos Gunver Ryberg soundtrack'),('INSIDE',2016,'INSIDE original soundtrack Martin Stig Andersen game 2016'),
 ('Fire Emblem: Three Houses',2019,'Fire Emblem Three Houses Fodlan Winds original soundtrack'),('Fire Emblem: Three Houses',2019,'Fire Emblem Three Houses The Edge of Dawn English soundtrack'),
]
for i,(game,year,query) in enumerate(queries,1):
 f=D/(str(i).zfill(2)+'-'+p.norm(game)+'.json')
 if f.exists():continue
 rows=[];errors=[]
 for result in p.search(query)[:3]:
  try:w=p.watch(result['id']);rows.append({'youtube_id':result['id'],'actual_publication':w})
  except Exception as ex:errors.append({'youtube_id':result['id'],'error':str(ex)})
 p.write(f,{'publication_status':'research_only_needs_actual_identity_role_review','game':game,'year':year,'query':query,'candidates':rows,'errors':errors});print(i,game,len(rows),flush=True)
