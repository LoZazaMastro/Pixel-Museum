"""Recover original-edition packaging even when its regional release year differs."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,re,zipfile,xml.etree.ElementTree as ET,hashlib,io
from urllib.request import Request,urlopen
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
def norm(s):return re.sub('[^a-z0-9]','',s.lower())
TARGETS={
'Final Fantasy XIII-2':2011,'Lightning Returns: Final Fantasy XIII':2013,'Final Fantasy XIV':2013,'Crisis Core: Final Fantasy VII':2007,
'The Legend of Zelda: Oracle of Seasons':2001,'The Legend of Zelda: Oracle of Ages':2001,'Metal Gear: Ghost Babel':2000,
'Gran Turismo 7':2022,'Forza Horizon':2012,'Tekken 5':2004,'Tekken 6':2007,'Super Street Fighter II':1993,
'Ridge Racer 2':1994,'Rave Racer':1995,'Forza Horizon 6':2026}
ALIASES={'granturismo7therealdrivingsimulator':'Gran Turismo 7','finalfantasyxivarealmreborn':'Final Fantasy XIV','finalfantasyxivonlinearealmreborn':'Final Fantasy XIV','supersuperstreetfighterii':'Super Street Fighter II','superstreetfighteriithenewchallengers':'Super Street Fighter II','metalgearsolid':'Metal Gear: Ghost Babel'}
def main():
 wanted={norm(k):k for k in TARGETS};wanted.update(ALIASES);games={};images={}
 with zipfile.ZipFile(ROOT/'build/research/launchbox/Metadata-range.zip') as z,z.open('Metadata.xml') as stream:
  for _,node in ET.iterparse(stream,events=('end',)):
   if node.tag=='Game':
    g={x.tag:x.text or '' for x in node};node.clear();name=norm(g.get('Name',''));target=wanted.get(name)
    if not target:continue
    year=(g.get('ReleaseDate') or g.get('ReleaseYear') or '')[:4]
    if not year.isdigit() and target=='Forza Horizon' and g.get('Platform')=='Microsoft Xbox 360':year='2012'
    if not year.isdigit() or abs(int(year)-TARGETS[target])>2:continue
    if target=='Metal Gear: Ghost Babel' and g.get('Platform')!='Nintendo Game Boy Color':continue
    if target=='Final Fantasy XIV' and int(year)<2013:continue
    if target in ['Ridge Racer 2','Rave Racer'] and g.get('Platform')!='Arcade':continue
    games[g['DatabaseID']]=(target,g)
   elif node.tag=='GameImage':
    i={x.tag:x.text or '' for x in node};node.clear()
    if i.get('DatabaseID') in games and i.get('Type') in ['Box - Front','Advertisement Flyer - Front']:images.setdefault(i['DatabaseID'],[]).append(i)
 candidates={}
 for db,(title,g) in games.items():
  for image in images.get(db,[]):candidates.setdefault(title,[]).append((g,image))
 p=ROOT/'build/research/franchise-mainline/cover-candidates.json';p.write_text(json.dumps(candidates,indent=2),encoding='utf8')
 def recover(item):
  title,year=item;choices=candidates.get(title,[])
  for g,i in sorted(choices,key=lambda pair:(0 if pair[0].get('Platform')=='Arcade' and title in ['Tekken 5','Tekken 6','Super Street Fighter II'] else 1,0 if pair[1].get('Region') in ['North America','Japan'] else 1)):
   f=ROOT/'build/research/launchbox/scans'/i['FileName'];url='https://images.launchbox-app.com/'+i['FileName']
   try:
    if not f.exists():
     with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=20) as r:f.write_bytes(r.read())
    with Image.open(f) as im:im.load();w,h=im.size
    if max(w,h)<600 or min(w,h)<300:continue
    return norm(title)+'|'+str(year),{'url':url,'title':title+' — original-edition '+i['Type'].lower()+' ('+g['Platform']+')','creator':g.get('Publisher','Original publisher'),'credit':g.get('Publisher','Original publisher')+' / original packaging scan','source_page':'https://gamesdb.launchbox-app.com/games/details/'+g['DatabaseID'],'license':'Original publisher and artwork rights retained; historical packaging illustration','license_url':'','width':w,'height':h,'cover_art':True,'story_paragraph':0,'recovery_local_source':f.relative_to(ROOT).as_posix(),'identity_evidence':{'name':g['Name'],'database_id':g['DatabaseID'],'platform':g['Platform'],'year':g.get('ReleaseDate') or g.get('ReleaseYear'),'image_type':i['Type'],'wikipedia_url':g.get('WikipediaURL')},'verification':{'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'native_dimensions':[w,h]}}
   except Exception:continue
  return title,None
 prior=HERE/'franchise-cover-recoveries.json'
 output=json.loads(prior.read_text(encoding='utf8')).get('entries',{}) if prior.exists() else {};held=[]
 with ThreadPoolExecutor(max_workers=6) as pool:
  for key,image in pool.map(recover,TARGETS.items()):
   if image:output[key]=image
   elif norm(key)+'|'+str(TARGETS[key]) not in output:held.append(key)
 path=HERE/'franchise-cover-recoveries.json';path.write_text(json.dumps({'schema_version':1,'entries':output,'held':held},indent=2)+'\n',encoding='utf8');print('COVERS',len(output),'HELD',held)
if __name__=='__main__':main()
