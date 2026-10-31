"""Recover explicitly audited main instalments without changing their editions."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen
import hashlib, importlib.util, json, re, unicodedata, xml.etree.ElementTree as ET, zipfile
from PIL import Image

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('major_source_helpers',HERE/'major-release-additions.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
CACHE=ROOT/'build/research/franchise-mainline';CACHE.mkdir(parents=True,exist_ok=True)

# This is a finite mainline audit, not a claim to enumerate every AAA game.
SERIES={
 'Standalone releases':[(2013,'The Stanley Parable')],
 'Halo':[(2009,'Halo 3: ODST'),(2015,'Halo 5: Guardians'),(2021,'Halo Infinite')],
 'Grand Theft Auto':[(1997,'Grand Theft Auto (video game)'),(2006,'Grand Theft Auto: Vice City Stories')],
 'Final Fantasy':[(1992,'Final Fantasy V'),(2003,'Final Fantasy X-2'),(2011,'Final Fantasy XIII-2'),(2013,'Lightning Returns: Final Fantasy XIII'),(2013,'Final Fantasy XIV'),(2007,'Crisis Core: Final Fantasy VII')],
 'The Legend of Zelda':[(2000,"The Legend of Zelda: Majora's Mask"),(2001,'The Legend of Zelda: Oracle of Seasons'),(2001,'The Legend of Zelda: Oracle of Ages'),(2004,'The Legend of Zelda: Four Swords Adventures'),(2007,'The Legend of Zelda: Phantom Hourglass'),(2009,'The Legend of Zelda: Spirit Tracks'),(2011,'The Legend of Zelda: Skyward Sword'),(2015,'The Legend of Zelda: Tri Force Heroes'),(2024,'The Legend of Zelda: Echoes of Wisdom')],
 'Super Mario':[(1988,'Super Mario Bros. 2'),(1992,'Super Mario Land 2: 6 Golden Coins'),(2009,'New Super Mario Bros. Wii'),(2012,'New Super Mario Bros. U'),(2016,'Super Mario Run'),(2015,'Super Mario Maker'),(2019,'Super Mario Maker 2')],
 'Mario Kart':[(2001,'Mario Kart: Super Circuit'),(2011,'Mario Kart 7'),(2019,'Mario Kart Tour'),(2025,'Mario Kart World')],
 'Metroid':[(1991,'Metroid II: Return of Samus'),(2007,'Metroid Prime 3: Corruption'),(2006,'Metroid Prime Hunters'),(2010,'Metroid: Other M'),(2025,'Metroid Prime 4: Beyond')],
 'Metal Gear':[(1990,'Metal Gear 2: Solid Snake'),(2006,'Metal Gear Solid: Portable Ops'),(2010,'Metal Gear Solid: Peace Walker'),(2000,'Metal Gear: Ghost Babel')],
 'Resident Evil':[(2000,'Resident Evil – Code: Veronica'),(2012,'Resident Evil 6'),(2012,'Resident Evil: Revelations'),(2015,'Resident Evil: Revelations 2'),(2004,'Resident Evil Outbreak: File 2')],
 'Gran Turismo':[(1999,'Gran Turismo 2'),(2010,'Gran Turismo 5'),(2013,'Gran Turismo 6'),(2017,'Gran Turismo Sport'),(2022,'Gran Turismo 7'),(2009,'Gran Turismo (2009 video game)')],
 'Forza':[(2007,'Forza Motorsport 2'),(2009,'Forza Motorsport 3'),(2011,'Forza Motorsport 4'),(2013,'Forza Motorsport 5'),(2015,'Forza Motorsport 6'),(2023,'Forza Motorsport (2023 video game)'),(2012,'Forza Horizon'),(2014,'Forza Horizon 2'),(2026,'Forza Horizon 6')],
 'Uncharted':[(2011,'Uncharted: Golden Abyss')],
 'Gears of War':[(2011,'Gears of War 3'),(2016,'Gears of War 4'),(2019,'Gears 5'),(2020,'Gears Tactics')],
 'God of War':[(2007,'God of War II'),(2008,'God of War: Chains of Olympus'),(2010,'God of War: Ghost of Sparta'),(2013,'God of War: Ascension')],
 'Tekken':[(2001,'Tekken 4'),(2004,'Tekken 5'),(2007,'Tekken 6'),(2015,'Tekken 7'),(1999,'Tekken Tag Tournament'),(2011,'Tekken Tag Tournament 2')],
 'Street Fighter':[(1995,'Street Fighter Alpha'),(1996,'Street Fighter Alpha 2'),(1997,'Street Fighter III'),(2008,'Street Fighter IV'),(1993,'Super Street Fighter II'),(1994,'Super Street Fighter II Turbo')],
 'Ridge Racer':[(1993,'Ridge Racer (1993 video game)'),(1994,'Ridge Racer 2'),(1995,'Rave Racer'),(1996,'Rage Racer'),(2000,'Ridge Racer V'),(2005,'Ridge Racer 6'),(2006,'Ridge Racer 7'),(2011,'Ridge Racer 3D'),(2011,'Ridge Racer (2011 video game)'),(2000,'Ridge Racer 64')]
}

def norm(s):return helper.norm(s)

def atomic(path,data):
 t=path.with_suffix(path.suffix+'.tmp');t.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8');t.replace(path)

def identify():
 catalog=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))['entries']
 existing={(norm(e['title']),e['year']) for e in catalog if e['kind']=='game'}
 if '--retry-missing' in __import__('sys').argv and (HERE/'franchise-mainline-additions.json').exists():
  existing.update((norm(e['title']),e['year']) for e in json.loads((HERE/'franchise-mainline-additions.json').read_text(encoding='utf8'))['entries'])
 todo=[{'series':series,'year':year,'requested_title':title} for series,rows in SERIES.items() for year,title in rows if (norm(title),year) not in existing]
 records=[];entities={};missing=[]
 for start in range(0,len(todo),12):
  batch=todo[start:start+12]
  result=helper.api('https://en.wikipedia.org/w/api.php',{'action':'query','titles':'|'.join(x['requested_title'] for x in batch),'redirects':1,'prop':'extracts|revisions|pageprops','exintro':1,'explaintext':1,'exlimit':'max','rvprop':'ids|timestamp|content','rvslots':'main','ppprop':'wikibase_item'},'franchise-articles')
  pages={p['title']:p for p in result.get('query',{}).get('pages',[])}
  redirects={r['from']:r['to'] for r in result.get('query',{}).get('normalized',[])+result.get('query',{}).get('redirects',[])}
  for item in batch:
   title=item['requested_title']
   while title in redirects:title=redirects[title]
   page=pages.get(title)
   if not page or 'pageid' not in page:missing.append({**item,'reason':'Original article not resolved'});continue
   if not re.search(r'\b'+str(item['year'])+r'\b',page.get('extract','')[:1600]):missing.append({**item,'reason':'Expected original year not confirmed in article introduction','resolved_title':title});continue
   records.append((item,page))
  print('Original article identities',min(start+12,len(todo)),'/',len(todo),flush=True)
 qids=[p.get('pageprops',{}).get('wikibase_item') for _,p in records];qids=[q for q in qids if q]
 for start in range(0,len(qids),45):entities.update(helper.api('https://www.wikidata.org/w/api.php',{'action':'wbgetentities','ids':'|'.join(qids[start:start+45]),'props':'claims'},'franchise-identities').get('entities',{}))
 atomic(CACHE/'article-identities.json',{'records':[{'request':x,'page':p} for x,p in records],'missing':missing})
 return records,entities,missing

def archive_candidates(records):
 aliases={norm(p['title']):item for item,p in records}
 for item,p in records:
  aliases[norm(item['requested_title'])]=item
 # Canonical arcade names and portable subtitles must not drift to a later port.
 manual={'streetfighteriiinewgeneration':'Street Fighter III','ridge racer':'Ridge Racer (1993 video game)'}
 wanted={(norm(p['title']),item['year']):item for item,p in records}
 for item,p in records:wanted[(norm(item['requested_title']),item['year'])]=item
 for alias,title in manual.items():
  for item,p in records:
   if item['requested_title']==title:wanted[(norm(alias),item['year'])]=item
 matches={};images={}
 with zipfile.ZipFile(ROOT/'build/research/launchbox/Metadata-range.zip') as z,z.open('Metadata.xml') as stream:
  for _,node in ET.iterparse(stream,events=('end',)):
   if node.tag=='Game':
    g={x.tag:x.text or '' for x in node};node.clear();date=g.get('ReleaseDate') or g.get('ReleaseYear') or ''
    if not re.match(r'\d{4}',date) or g.get('ReleaseType') in ['Unreleased','ROM Hack','Homebrew']:continue
    item=wanted.get((norm(g.get('Name','')),int(date[:4])))
    if item:matches[g['DatabaseID']]=(item,g)
   elif node.tag=='GameImage':
    i={x.tag:x.text or '' for x in node};node.clear()
    if i.get('DatabaseID') in matches and i.get('Type') in ['Box - Front','Box - Back','Advertisement Flyer - Front','Advertisement Flyer - Back']:images.setdefault(i['DatabaseID'],[]).append(i)
 result={}
 for dbid,(item,g) in matches.items():
  for i in images.get(dbid,[]):result.setdefault(item['requested_title'],[]).append({'game':g,'image':i})
 atomic(CACHE/'archive-candidates.json',result);return result

def archive_images(item,candidates,body_count):
 result=[];front=None
 def score(c):
  g,i=c['game'],c['image'];arcade=any(x in item['requested_title'] for x in ['Tekken','Street Fighter','Ridge Racer (1993','Ridge Racer 2 (1994'])
  return (0 if not arcade or g.get('Platform')=='Arcade' else 1,0 if i['Type']=='Box - Front' and not arcade or i['Type']=='Advertisement Flyer - Front' and arcade else 1,0 if i.get('Region') in ['North America','Japan'] else 1)
 for c in sorted(candidates,key=score):
  g,i=c['game'],c['image'];isfront=i['Type'].endswith('Front')
  if isfront and front:continue
  if not isfront and len(result)>=max(2,body_count):continue
  url='https://images.launchbox-app.com/'+i['FileName'];f=ROOT/'build/research/launchbox/scans'/i['FileName']
  try:
   if not f.is_file():f.write_bytes(helper.fetch(url))
   with Image.open(f) as im:im.load();w,h=im.size
   if max(w,h)<600 or min(w,h)<300:continue
   row={'url':url,'title':re.sub(r'\s*\([^)]*video game\)$','',item['requested_title'])+' - '+i['Type'].lower()+' ('+g.get('Platform','')+')','width':w,'height':h,'creator':g.get('Publisher','Original publisher'),'credit':g.get('Publisher','Original publisher')+' / LaunchBox scan archive','source_page':'https://gamesdb.launchbox-app.com/games/details/'+g['DatabaseID'],'license':'Original publisher and illustration rights retained; authentic archival packaging or promotional material','license_url':'','recovery_local_source':f.relative_to(ROOT).as_posix(),'cover_art':isfront,'story_paragraph':0 if isfront else len(result),'verification':{'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'native_dimensions':[w,h]},'identity_evidence':{'database_id':g['DatabaseID'],'name':g['Name'],'year':g.get('ReleaseDate') or g.get('ReleaseYear'),'platform':g.get('Platform'),'wikipedia_url':g.get('WikipediaURL'),'image_type':i['Type'],'release_type':g.get('ReleaseType')}}
   if isfront:front=row
   else:result.append(row)
  except Exception:continue
  if front and len(result)>=max(1,body_count-1):break
 return ([front] if front else [])+result

def main():
 records,entities,held=identify();candidates=archive_candidates(records);outputs=[]
 if '--retry-missing' in __import__('sys').argv and (HERE/'franchise-mainline-additions.json').exists():outputs=json.loads((HERE/'franchise-mainline-additions.json').read_text(encoding='utf8'))['entries']
 def process(pair):
  item,page=pair
  try:
   originals=archive_images(item,candidates.get(item['requested_title'],[]),5)
   recoveries=json.loads((HERE/'franchise-cover-recoveries.json').read_text(encoding='utf8')).get('entries',{}) if (HERE/'franchise-cover-recoveries.json').exists() else {}
   image=recoveries.get(norm(item['requested_title'])+'|'+str(item['year'])) or (originals[0] if originals and originals[0].get('cover_art') else helper.cover(page,entities,item['year']))
   if not image:return None,{**item,'reason':'No authentic useful-size original cover acquired'}
   record=helper.entry(page,item['year'],image);record['provenance']['coverage_module']='franchise-mainline-additions';record['provenance']['series_audit']=item['series']
   record['title']=re.sub(r'\s*\((?:\d{4} )?video game\)$','',item['requested_title'])
   if item['requested_title']=='The Stanley Parable':record['id']='stanley-parable-standalone-2013'
   if item['requested_title']=='Forza Horizon 6':record['date']={'month':5,'day':19,'precision':'day','region':'General commercial release, excluding premium early access'}
   if 'Oracle of ' in item['requested_title']:
    which='Seasons' if item['requested_title'].endswith('Seasons') else 'Ages'
    record['id']='zelda-oracle-of-'+which.lower()
    record['summary']='Link travels through changing '+('seasons to uncover new routes and solve environmental puzzles.' if which=='Seasons' else 'eras, carrying discoveries between the past and present.')+' Oracle of '+which+' is a distinct 2001 Game Boy Color adventure that can exchange progress with its companion game.'
    record['body'][0]='This exhibit follows Oracle of '+which+', one of two separate Game Boy Color adventures. '+record['body'][0]
   record['images']+= [i for i in originals if i['url']!=image['url']]
   helper.context_images(record)
   if len(record['summary'])>240:record['summary']=record['summary'].split(',')[0].rstrip('.')+'.'
   return record,None
  except Exception as ex:return None,{**item,'reason':str(ex)}
 with ThreadPoolExecutor(max_workers=5) as pool:
  futures=[pool.submit(process,pair) for pair in records]
  for n,future in enumerate(as_completed(futures),1):
   record,error=future.result()
   if record:outputs.append(record)
   if error:held.append(error)
   if n%10==0:
    print('Mainline originals',n,'/',len(records),'admitted',len(outputs),'held',len(held),flush=True)
    atomic(CACHE/'progress.json',{'completed':n,'total':len(records),'admitted':len(outputs),'held':held})
 for entry in outputs:
  if entry['title']=='Forza Horizon 6':entry['date']={'month':5,'day':19,'precision':'day','region':'General commercial release, excluding premium early access'}
 outputs.sort(key=lambda e:(e['year'],e['date']['month'],e['date']['day'],e['title']))
 atomic(HERE/'franchise-mainline-additions.json',{'schema_version':1,'scope_notice':'Finite audited mainline series gaps; no claim to enumerate all AAA games. No DLC or remaster wrappers.','entries':outputs})
 atomic(CACHE/'coverage-audit.json',{'series':SERIES,'admitted':len(outputs),'held':held,'paragraphs':sum(len(e['body']) for e in outputs),'words':sum(len(' '.join(e['body']).split()) for e in outputs),'images':sum(len(e['images']) for e in outputs)})
 print('ADMITTED',len(outputs),'HELD',len(held),flush=True)

if __name__=='__main__':main()
