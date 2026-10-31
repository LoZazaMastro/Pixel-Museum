"""Read-only chronological cover contact sheets using actual runtime preference and offline manifest."""
import argparse,hashlib,json,math,pathlib
from PIL import Image,ImageOps,ImageDraw,ImageFont
R=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('minimum',type=int);p.add_argument('maximum',type=int);p.add_argument('--out',default='build/research/modern-game-cover-visual-qa');a=p.parse_args()
D=R/a.out;D.mkdir(exist_ok=True);cp=R/'content/catalog.json';mp=R/'assets/images/manifest.json';c=json.loads(cp.read_text(encoding='utf8'));m=json.loads(mp.read_text(encoding='utf8'));es=sorted([e for e in c['entries'] if e.get('kind')=='game' and a.minimum<=e['year']<=a.maximum],key=lambda e:(e['year'],e['title']));f=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16);sm=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',12);rows=[]
for k,e in enumerate(es):
 im=e['images'][e['preferred_image']];rows.append({'index':k,'entry_id':e['id'],'title':e['title'],'year':e['year'],'preferred_image':e['preferred_image'],'image':im,'local_file':m['images'].get(im['url'])})
for st in range(0,len(rows),28):
 sheet=Image.new('RGB',(2100,1560),'#181b1d');dr=ImageDraw.Draw(sheet)
 for n,r in enumerate(rows[st:st+28]):
  x=n%7*300;y=n//7*390
  try:
   with Image.open(R/r['local_file']) as im:t=ImageOps.contain(im.convert('RGB'),(286,310));sheet.paste(t,(x+(300-t.width)//2,y+(310-t.height)//2))
  except Exception as ex:dr.text((x+10,y+100),'MISSING '+str(ex)[:10],font=f,fill='red')
  s=f"{r['index']:03} {r['year']} {r['title']}";lines=[]
  while s:
   t=s
   while dr.textlength(t,font=f)>290:t=t[:-1]
   lines.append(t);s=s[len(t):]
  for j,t in enumerate(lines[:2]):dr.text((x+5,y+315+j*20),t,font=f,fill='white')
  dr.text((x+5,y+357),r['entry_id'][:40],font=sm,fill='#aabbcc')
 sheet.save(D/f'{a.minimum}-{a.maximum}-cover-{st//28+1:02}.jpg',quality=93)
(D/f'{a.minimum}-{a.maximum}-cover-index.json').write_text(json.dumps({'catalog_sha256':hashlib.sha256(cp.read_bytes()).hexdigest(),'manifest_sha256':hashlib.sha256(mp.read_bytes()).hexdigest(),'entries':rows},ensure_ascii=False,indent=2),encoding='utf8');print(len(rows),math.ceil(len(rows)/28))
