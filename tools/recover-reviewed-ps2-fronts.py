"""Acquire original PS2 fronts for explicit visual corrections; review before promotion."""
from pathlib import Path
from urllib.request import Request,urlopen
from PIL import Image,ImageOps,ImageDraw
import xml.etree.ElementTree as ET,zipfile,json,hashlib,sys
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/research/ps2-front-corrections';OUT.mkdir(parents=True,exist_ok=True)
targets={'Final Fantasy X':('wikipedia-52759',None),'Tekken 4':('wikipedia-739177',None),'Ico':('ico','Europe')}
games={};images={}
with zipfile.ZipFile(ROOT/'build/research/launchbox/Metadata-range.zip') as z,z.open('Metadata.xml') as stream:
 for _,node in ET.iterparse(stream,events=('end',)):
  if node.tag=='Game':
   g={x.tag:x.text or '' for x in node};node.clear()
   match=next((t for t in targets if t.casefold()==g.get('Name','').casefold()),None)
   if match and g.get('Platform')=='Sony Playstation 2' and g.get('ReleaseDate','')[:4] in ['2001','2002']:
    games[g['DatabaseID']]={**g,'target_title':match}
  elif node.tag=='GameImage':
   i={x.tag:x.text or '' for x in node};node.clear()
   if i.get('DatabaseID') in games and i.get('Type')=='Box - Front':images.setdefault(i['DatabaseID'],[]).append(i)
(OUT/'metadata.json').write_text(json.dumps({'games':games,'images':images},ensure_ascii=False,indent=2),encoding='utf-8')
if '--metadata-only' in sys.argv:sys.exit(0)
rows=[]
for db,g in games.items():
 title=g['target_title'];region=targets[title][1]
 choices=[i for i in images.get(db,[]) if not region or i.get('Region')==region]
 choices.sort(key=lambda i:(i.get('Region') not in ['Europe','North America','Japan'],i['FileName']))
 accepted=0
 for i in choices[:12]:
  path=ROOT/'build/research/launchbox/scans'/i['FileName'];url='https://images.launchbox-app.com/'+i['FileName']
  try:
   if not path.exists():
    with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=12) as r:path.write_bytes(r.read(24<<20))
   with Image.open(path) as im:im.load();w,h=im.size
   if min(w,h)<650 or max(w,h)<1000:continue
   rows.append({'title':title,'entry_id':targets[title][0],'game':g,'image_record':i,'path':path.relative_to(ROOT).as_posix(),'url':url,'width':w,'height':h,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()});accepted+=1
   print(title,i.get('Region'),w,h,i['FileName'],flush=True)
   if accepted>=3:break
  except Exception as e:print('HOLD',title,str(e)[:100],flush=True)
(OUT/'acquired.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
sheet=Image.new('RGB',(320*max(1,len(rows)),580),(238,235,225));draw=ImageDraw.Draw(sheet)
for n,row in enumerate(rows):
 with Image.open(ROOT/row['path']) as im:im=ImageOps.contain(im.convert('RGB'),(300,510));sheet.paste(im,(n*320+(320-im.width)//2,50))
 draw.text((n*320+8,8),str(n)+' '+row['title']+' '+row['image_record'].get('Region',''),fill='black')
sheet.save(OUT/'contact.jpg',quality=94)
