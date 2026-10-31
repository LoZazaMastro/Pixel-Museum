#!/usr/bin/env python3
"""Prefer publisher Steam library box art to narrow header/hero strips."""
from pathlib import Path
from urllib.request import Request,urlopen
from PIL import Image
import concurrent.futures,hashlib,io,json,re,runpy,copy
ROOT=Path(__file__).resolve().parents[1]
entries=copy.deepcopy(json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))['entries'])
runpy.run_path(str(ROOT/'content/expansion/apply_museum_revision.py'))['apply'](entries)
output=ROOT/'content/expansion/cover-proportion-overrides.json'
prior=json.loads(output.read_text(encoding='utf8')) if output.exists() else {'schema_version':1,'entries':{}}
queue={}
for e in entries:
 if e['kind']!='game' or e['id'] in prior['entries']:continue
 for image in e.get('images',[]):
  match=re.search(r'/steam/apps/(\d+)/',image['url'])
  if match:queue.setdefault(match.group(1),[]).append(e);break

def acquire(item):
 app,subjects=item
 url=f'https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{app}/library_600x900_2x.jpg'
 try:
  with urlopen(Request(url,headers={'User-Agent':'PixelMuseum/0.1 historical collection'}),timeout=12) as response:body=response.read(8<<20)
  with Image.open(io.BytesIO(body)) as picture:
   picture.load();w,h=picture.size
   if w<600 or h<900:return []
  cache=ROOT/'build/research/image-quality'/(hashlib.sha256(url.encode()).hexdigest()[:16]+'.jpg');cache.write_bytes(body)
  return [(e['id'],{'url':url,'title':e['title']+' — cover art','width':w,'height':h,'source_page':f'https://store.steampowered.com/app/{app}/','creator':'Original game publisher','credit':'Original game publisher / Steam library artwork','license':'Publisher promotional artwork; original rights reserved','license_url':'','cover_art':True}) for e in subjects]
 except Exception:return []
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
 for rows in executor.map(acquire,queue.items()):
  for identifier,image in rows:prior['entries'][identifier]=image
output.write_text(json.dumps(prior,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'steam_apps_checked':len(queue),'verified_high_resolution_covers':len(prior['entries'])}))
