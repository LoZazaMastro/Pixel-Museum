"""Regional original packaging recovery for explicitly requested games (not remasters)."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from urllib.request import Request,urlopen
import importlib.util,json,hashlib,re,xml.etree.ElementTree as ET,zipfile
from urllib.parse import unquote
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'content/expansion';CACHE=ROOT/'build/research/user-requested-games'
s=importlib.util.spec_from_file_location('usergames',HERE/'user-requested-game-additions.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
rows=json.loads((HERE/'user-soundtrack-priorities.json').read_text(encoding='utf8'))['entries'];targets={m.m.norm(r['title']):r for r in rows}
for y,t in m.EXTRA:targets[m.m.norm(t)]={'title':t,'year':y}
# Conventional regional title variants retain the same original edition.
alias={'crashbandicoot3warped':'crashbandicootwarped','spyro2gatewaytoglimmer':'spyro2riptosrage','007fromrussiawithlove':'fromrussiawithlove','jamesbond007fromrussiawithlove':'fromrussiawithlove','slyraccoon':'slycooperandthethieviusraccoonus','marvelsspidermanmilesmorales':'marvelsspidermanmilesmorales','spidermanmilesmorales':'marvelsspidermanmilesmorales'}
wiki_targets={}
for row in rows:
 article=unquote(row.get('source_page','').split('/wiki/')[-1]).replace('_',' ') if '/wiki/' in row.get('source_page','') else m.ALIAS.get(row['title'],row['title'])
 wiki_targets[m.m.norm(article)]=row
for y,t in m.EXTRA:wiki_targets[m.m.norm(t)]={'title':t,'year':y}
games={};images={}
with zipfile.ZipFile(ROOT/'build/research/launchbox/Metadata-range.zip') as z,z.open('Metadata.xml') as stream:
 for _,node in ET.iterparse(stream,events=('end',)):
  if node.tag=='Game':
   g={x.tag:x.text or '' for x in node};node.clear();key=m.m.norm(g.get('Name',''));key=alias.get(key,key);t=targets.get(key) or wiki_targets.get(m.m.norm(unquote(g.get('WikipediaURL','').split('/wiki/')[-1]).replace('_',' ')))
   date=g.get('ReleaseDate') or g.get('ReleaseYear') or '';year=int(date[:4]) if date[:4].isdigit() else 0
   if not t or not year or abs(year-t['year'])>2:continue
   if g.get('ReleaseType') in ['Unreleased','ROM Hack','Homebrew']:continue
   games[g['DatabaseID']]=(t,g)
  elif node.tag=='GameImage':
   i={x.tag:x.text or '' for x in node};node.clear()
   if i.get('DatabaseID') in games and i.get('Type')=='Box - Front':images.setdefault(i['DatabaseID'],[]).append(i)
candidates={}
for db,(t,g) in games.items():
 for image in images.get(db,[]):candidates.setdefault(m.m.norm(t['title'])+'|'+str(t['year']),[]).append((t,g,image))
m.m.atomic(CACHE/'regional-cover-candidates.json',candidates)
previous=HERE/'user-requested-cover-recoveries.json'
outputs=json.loads(previous.read_text(encoding='utf8')).get('entries',{}) if previous.exists() else {};held=[]
def acquire(item):
 key,choices=item;valid=[]
 if key in outputs:return key,outputs[key]
 def score(c):
  t,g,i=c;year=int((g.get('ReleaseDate') or g.get('ReleaseYear'))[:4]);return(abs(year-t['year']),0 if i.get('Region') in ['North America','Japan','Europe'] else 1)
 for t,g,i in sorted(choices,key=score)[:10]:
  f=ROOT/'build/research/launchbox/scans'/i['FileName'];url='https://images.launchbox-app.com/'+i['FileName']
  try:
   if not f.exists():
    with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=8) as response:f.write_bytes(response.read(24<<20))
   with Image.open(f) as im:im.load();w,h=im.size
   if max(w,h)<800 or min(w,h)<300:continue
   row={'url':url,'title':t['title']+' - original '+g['Platform']+' packaging ('+i.get('Region','unspecified region')+')','creator':g.get('Publisher') or g.get('Developer') or 'Original publisher','credit':(g.get('Publisher') or 'Original publisher')+' / original packaging scan','source_page':'https://gamesdb.launchbox-app.com/games/details/'+g['DatabaseID'],'license':'Original publisher and artwork rights retained; authentic historical packaging','license_url':'','width':w,'height':h,'cover_art':True,'story_paragraph':0,'recovery_local_source':f.relative_to(ROOT).as_posix(),'identity_evidence':{'name':g['Name'],'database_id':g['DatabaseID'],'platform':g['Platform'],'year':g.get('ReleaseDate') or g.get('ReleaseYear'),'image_type':i['Type'],'wikipedia_url':g.get('WikipediaURL')},'verification':{'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'native_dimensions':[w,h]}}
   valid.append(row)
   if max(w,h)>=1200:break
  except Exception:continue
 return key,max(valid,key=lambda r:r['width']*r['height']) if valid else None
with ThreadPoolExecutor(max_workers=6) as pool:
 for n,f in enumerate(as_completed([pool.submit(acquire,i) for i in candidates.items()]),1):
  key,row=f.result()
  if row:outputs[key]=row
  else:held.append(key)
  m.m.atomic(HERE/'user-requested-cover-recoveries.json',{'schema_version':1,'entries':outputs,'held':held})
  print('REGIONAL ORIGINALS',n,'/',len(candidates),'ADMITTED',len(outputs),flush=True)
