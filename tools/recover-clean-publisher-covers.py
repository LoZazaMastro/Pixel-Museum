"""Acquire original publisher-delivered art for human visual review; never auto-publish."""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor,as_completed
from html.parser import HTMLParser
from PIL import Image
import json,hashlib,re,io
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/research/cover-post2015';(OUT/'pages').mkdir(parents=True,exist_ok=True)
class Meta(HTMLParser):
 def __init__(self):super().__init__();self.image='';self.title=''
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='meta' and a.get('property')=='og:image':self.image=a.get('content','')
  if tag=='meta' and a.get('property')=='og:title':self.title=a.get('content','')
def get(url):
 with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=22)as r:return r.read(24<<20),r.url
inventory=json.loads((OUT/'inventory.json').read_text(encoding='utf8'))['entries']
targets=[]
nintendo={17:'super-mario-odyssey',18:'the-legend-of-zelda-breath-of-the-wild',22:'kirby-star-allies',24:'super-smash-bros-ultimate',25:'astral-chain',30:'fire-emblem-three-houses',33:'luigis-mansion-3',36:'super-mario-maker-2',38:'yoshis-crafted-world',40:'animal-crossing-new-horizons',49:'super-mario-3d-all-stars',58:'metroid-dread',63:'bayonetta-3',67:'pokemon-legends-arceus',68:'pokemon-scarlet',69:'splatoon-3',70:'xenoblade-chronicles-3',71:'advance-wars-1-plus-2-re-boot-camp',74:'super-mario-bros-wonder',75:'the-legend-of-zelda-tears-of-the-kingdom',76:'another-code-recollection',83:'the-legend-of-zelda-echoes-of-wisdom',85:'donkey-kong-bananza',87:'mario-kart-world',88:'metroid-prime-4-beyond'}
ps={0:'alienation',11:'the-last-guardian',16:'gran-turismo-sport',23:'marvels-spider-man',42:'demons-souls',43:'final-fantasy-vii-remake',46:'ghost-of-tsushima',47:'marvels-spider-man-miles-morales',51:'the-last-of-us-part-ii',66:'gran-turismo-7',77:'astro-bot',84:'death-stranding-2-on-the-beach',86:'ghost-of-yotei'}
for ix,slug in nintendo.items():targets.append((inventory[ix],f'https://www.nintendo.com/us/store/products/{slug}-switch/'))
for ix,slug in ps.items():targets.append((inventory[ix],f'https://www.playstation.com/en-us/games/{slug}/'))
steam={12:378648,31:1097840,35:1172380,57:1240440,73:1774580,81:2778580}
for ix,app in steam.items():targets.append((inventory[ix],f'https://store.steampowered.com/api/appdetails?appids={app}&l=english'))
def worker(pair):
 row,url=pair;eid=row['entry_id'];record={'entry_id':eid,'title':row['title'],'year':row['year'],'source_page':url,'status':'pending_visual_review'}
 try:
  cache=OUT/'pages'/(eid+'.txt')
  if cache.exists():b=cache.read_bytes();final=url
  else:b,final=get(url);cache.write_bytes(b)
  record['resolved_page']=final
  if '/api/appdetails?'in url:
   j=json.loads(b);d=next(iter(j.values()))['data'];record['publisher_page_title']=d['name'];record['publishers']=d.get('publishers',[])
   app=next(iter(j));image=f'https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{app}/library_600x900_2x.jpg'
  else:
   p=Meta();p.feed(b.decode('utf8','replace'));image=urljoin(final,p.image);record['publisher_page_title']=p.title
   if not p.image:raise ValueError('No publisher OG image')
  path=OUT/(eid+'-publisher-art.bin')
  if path.exists():raw=path.read_bytes()
  else:raw,_=get(image);path.write_bytes(raw)
  with Image.open(io.BytesIO(raw))as im:im.load();w,h=im.size
  if max(w,h)<800:raise ValueError(f'Native source only {w}x{h}')
  record.update(url=image,recovery_local_source=path.relative_to(ROOT).as_posix(),width=w,height=h,sha256=hashlib.sha256(raw).hexdigest())
 except Exception as e:record.update(status='hold_acquisition',error=str(e))
 return record
records=[]
with ThreadPoolExecutor(max_workers=5)as pool:
 for f in as_completed([pool.submit(worker,t)for t in targets]):
  r=f.result();records.append(r);print(r['entry_id'],r['status'],r.get('width'),r.get('error',''),flush=True)
(OUT/'publisher-acquisitions.json').write_text(json.dumps(records,indent=2,ensure_ascii=True),encoding='utf8')
