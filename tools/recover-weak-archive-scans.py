"""Replace weak archival scans only with larger originals of the same DB/game/platform/type."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from urllib.request import Request,urlopen
from urllib.parse import urlparse
import json,re,hashlib,copy,sys,xml.etree.ElementTree as ET,zipfile
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];CACHE=ROOT/'build/research/image-quality';OUT=ROOT/'content/expansion/museum-image-quality-replacements.json'
rootcovers={'wikipedia-153399','wikipedia-153418','wikipedia-490832','wikipedia-39211167','wikipedia-2146430','wikipedia-12231736','wikipedia-292736','wikipedia-884570','wikipedia-9785797','wikipedia-27721863','wikipedia-29924238'}
cat=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))['entries'];weak={r['url']:r for r in json.loads((ROOT/'build/research/local-image-resolution-audit.json').read_text(encoding='utf8'))['weak_images']};targets=[]
for e in cat:
 for n,i in enumerate(e['images']):
  if i['url'] not in weak or 'images.launchbox-app.com/' not in i['url']:continue
  if n==e.get('preferred_image',0) and e['id'] in rootcovers:continue
  db=i.get('identity_evidence',{}).get('database_id') or (re.search(r'/details/(\d+)',i.get('source_page','')) or [None,None])[1]
  kind=i.get('identity_evidence',{}).get('image_type')
  if not kind:
   t=i.get('title','').lower();kind='Box - Back' if 'back' in t else 'Box - Front' if i.get('cover_art') or 'front' in t or 'cover art' in t else None
  if db and kind:targets.append({'entry_id':e['id'],'entry_title':e['title'],'db':str(db),'type':kind,'image':i,'cover':n==e.get('preferred_image',0)})
wanted={t['db'] for t in targets};pictures={};games={}
with zipfile.ZipFile(ROOT/'build/research/launchbox/Metadata-range.zip') as z,z.open('Metadata.xml') as stream:
 for _,node in ET.iterparse(stream,events=('end',)):
  if node.tag=='Game':
   g={x.tag:x.text or '' for x in node};node.clear()
   if g.get('DatabaseID') in wanted:games[g['DatabaseID']]=g
  elif node.tag=='GameImage':
   i={x.tag:x.text or '' for x in node};node.clear()
   if i.get('DatabaseID') in wanted:pictures.setdefault((i['DatabaseID'],i.get('Type')),[]).append(i)
rows=json.loads(OUT.read_text(encoding='utf8')).get('replacements',[]) if OUT.exists() else [];rows_by_key={(r['entry_id'],r['match_url']):r for r in rows};held=[]
def acquire(t):
 key=(t['entry_id'],t['image']['url'])
 if key in rows_by_key:return key,rows_by_key[key],None
 cs=pictures.get((t['db'],t['type']),[]);oldname=t['image']['url'].rsplit('/',1)[-1];valid=[]
 cs=sorted(cs,key=lambda i:0 if (ROOT/'build/research/launchbox/scans'/i['FileName']).exists() else 1)
 trials=0
 for i in cs:
  if i['FileName']==oldname:continue
  p=ROOT/'build/research/launchbox/scans'/i['FileName'];url='https://images.launchbox-app.com/'+i['FileName']
  if not p.exists():
   if '--local-only' in sys.argv:continue
   if trials>=8:continue
   trials+=1
   try:
    with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=8) as response:p.write_bytes(response.read(24<<20))
   except Exception:continue
  try:
   with Image.open(p) as im:im.load();w,h=im.size
   if max(w,h)<800 or min(w,h)<300:continue
   old=t['image'];g=games[t['db']]
   image={**copy.deepcopy(old),'url':url,'width':w,'height':h,'recovery_local_source':p.relative_to(ROOT).as_posix(),'creator':g.get('Publisher') or old.get('creator'),'credit':(g.get('Publisher') or old.get('creator','Original publisher'))+' / original packaging scan','source_page':'https://gamesdb.launchbox-app.com/games/details/'+t['db'],'title':t['entry_title']+' - original '+t['type'].lower()+' ('+g.get('Platform','')+')','verification':{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'native_dimensions':[w,h]},'identity_evidence':{'database_id':t['db'],'name':g['Name'],'year':g.get('ReleaseDate') or g.get('ReleaseYear'),'platform':g.get('Platform'),'wikipedia_url':g.get('WikipediaURL'),'image_type':t['type']},'supersedes_original_scan':{'url':old['url'],'native_dimensions':[old.get('width'),old.get('height')],'reason':'Larger genuine scan of same game/platform and same illustration category; no enlargement.'}}
   valid.append(image)
   if max(w,h)>=1600:break
  except Exception:continue
 if valid:return key,{'entry_id':t['entry_id'],'match_url':t['image']['url'],'image':max(valid,key=lambda i:i['width']*i['height']),'scope':'same original game database/platform/image category'},None
 return key,None,{'entry_id':t['entry_id'],'title':t['entry_title'],'url':t['image']['url'],'type':t['type'],'database_id':t['db'],'reason':'No larger authentic scan acquired; original retained, quality gate remains open'}
def save():
 tmp=OUT.with_suffix('.tmp');tmp.write_text(json.dumps({'schema_version':1,'replacements':list(rows_by_key.values()),'held':held},ensure_ascii=False,indent=2)+'\n',encoding='utf8');tmp.replace(OUT)
with ThreadPoolExecutor(max_workers=4) as pool:
 for n,f in enumerate(as_completed([pool.submit(acquire,t) for t in targets]),1):
  key,row,hold=f.result()
  if row:rows_by_key[key]=row
  if hold:held.append(hold)
  save()
  if n%10==0:print('QUALITY',n,'/',len(targets),'RECOVERED',len(rows_by_key),'HELD',len(held),flush=True)
print('FINAL',len(rows_by_key),'HELD',len(held),flush=True)
