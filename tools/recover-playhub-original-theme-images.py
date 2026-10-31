"""Fetch real source masters for reviewed chapters, holding small native captures."""
from pathlib import Path
import concurrent.futures,hashlib,json,re,urllib.request
from PIL import Image,ImageDraw,ImageOps
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/research/playhub-semantic-coverage/native-images';OUT.mkdir(parents=True,exist_ok=True)
doc=json.loads((ROOT/'content/expansion/playhub-theme-semantic-restorations.json').read_text(encoding='utf8'))
sources=json.loads((ROOT/'content/expansion/playhub-theme-sources/history_images.json').read_text(encoding='utf8'))
jobs=[];seen=set()
for target in doc['restorations'][4:]:
 for image in sources.get(target['theme_id'],[]):
  url=image.get('url','')
  if not url or image.get('kind')=='cover':continue
  if 'images.igdb.com/'in url:url=re.sub(r'/t_[^/]+/','/t_original/',url)
  if url in seen:continue
  seen.add(url);jobs.append(dict(image,theme_id=target['theme_id'],entry_id=target['entry_id'],url=url))
def acquire(row):
 path=OUT/(hashlib.sha256(row['url'].encode()).hexdigest()[:24]+'.bin')
 try:
  if not path.exists():
   with urllib.request.urlopen(urllib.request.Request(row['url'],headers={'User-Agent':'Mozilla/5.0'}),timeout=20)as resp:data=resp.read()
   with Image.open(__import__('io').BytesIO(data))as im:im.load()
   path.write_bytes(data)
  with Image.open(path)as im:im.load();width,height=im.size
  row.update(width=width,height=height,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),recovery_local_source=path.relative_to(ROOT).as_posix(),status='pending_visual_review'if max(width,height)>=800 else'held_small_native_master')
 except Exception as ex:row.update(status='acquisition_failed',error=str(ex))
 return row
with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:results=list(pool.map(acquire,jobs))
(OUT/'inventory.json').write_text(json.dumps({'images':results},indent=2,ensure_ascii=True)+'\n',encoding='utf8')
ready=[r for r in results if r['status']=='pending_visual_review']
for page in range((len(ready)+19)//20):
 sheet=Image.new('RGB',(1500,((min(20,len(ready)-page*20)+3)//4)*240),'#ece9e1');draw=ImageDraw.Draw(sheet)
 for n,row in enumerate(ready[page*20:page*20+20]):
  with Image.open(ROOT/row['recovery_local_source'])as im:thumb=ImageOps.contain(im.convert('RGB'),(365,200));x=n%4*375;y=n//4*240;sheet.paste(thumb,(x+(365-thumb.width)//2,y))
  draw.text((x+3,y+203),f"{page*20+n}: {row['theme_id']} / {row['file']}"[:55],fill='black')
  draw.text((x+3,y+220),f"Native {row['width']} x {row['height']}",fill='black')
 sheet.save(OUT/f'review-{page+1:02}.jpg',quality=92)
print(json.dumps({'requested':len(results),'native_quality_ready':len(ready),'small_native_held':sum(r['status']=='held_small_native_master'for r in results),'failed':sum(r['status']=='acquisition_failed'for r in results)}))
