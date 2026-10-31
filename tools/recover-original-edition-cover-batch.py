"""Recover original game packaging by explicit title/platform/year; never name-only Steam lookup."""
from pathlib import Path
import xml.etree.ElementTree as ET,zipfile,json,sys,hashlib
from urllib.request import urlopen,Request
from PIL import Image,ImageOps,ImageDraw
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/research/cover-duplicates/original-editions';OUT.mkdir(exist_ok=True)
targets={'wikipedia-1835791':('Forza Motorsport','Microsoft Xbox',2005),'workbook-12-29-shenmue':('Shenmue','Sega Dreamcast',1999),'daily-09-06':('Shenmue II','Sega Dreamcast',2001)}
games={};images={}
with zipfile.ZipFile(ROOT/'build/research/launchbox/Metadata-range.zip') as z,z.open('Metadata.xml') as stream:
 for _,node in ET.iterparse(stream,events=('end',)):
  if node.tag=='Game':
   g={x.tag:x.text or '' for x in node};node.clear()
   for eid,(name,platform,year) in targets.items():
    if g.get('Name','').casefold()==name.casefold() and g.get('Platform')==platform and (g.get('ReleaseDate','').startswith(str(year)) or (eid=='workbook-12-29-shenmue' and g.get('ReleaseDate','').startswith('2000'))):
     games[g['DatabaseID']]={**g,'entry_id':eid}
  elif node.tag=='GameImage':
   i={x.tag:x.text or '' for x in node};node.clear()
   if i.get('DatabaseID')in games and i.get('Type')in['Box - Front','Advertisement Flyer - Front']:
    images.setdefault(i['DatabaseID'],[]).append(i)
(OUT/'metadata.json').write_text(json.dumps({'games':games,'images':images},indent=2),encoding='utf8')
rows=[]
for db,g in games.items():
 candidates=sorted(images.get(db,[]),key=lambda i:(i['Type']!='Box - Front',i.get('Region')not in['North America','United States','Europe','World'],i['FileName']))
 for record in candidates[:12]:
  url='https://images.launchbox-app.com/'+record['FileName'];p=ROOT/'build/research/launchbox/scans'/record['FileName']
  try:
   if not p.exists():
    with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=15)as response:p.write_bytes(response.read(24<<20))
   with Image.open(p)as im:im.load();w,h=im.size
   if max(w,h)<900 or min(w,h)<500:continue
   rows.append({'entry_id':g['entry_id'],'game':{k:g.get(k)for k in['Name','DatabaseID','ReleaseDate','Platform','WikipediaURL','Publisher','Developer']},'record':record,'url':url,'path':p.relative_to(ROOT).as_posix(),'width':w,'height':h,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
   print(g['Name'],record['FileName'],w,h,flush=True)
   if max(w,h)>=1100:break
  except Exception as exc:print('HOLD',record['FileName'],str(exc)[:90],flush=True)
(OUT/'acquired.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
contact=Image.new('RGB',(900,650*max(1,(len(rows)+2)//3)),(240,237,228));draw=ImageDraw.Draw(contact)
for n,row in enumerate(rows):
 x=n%3*300;y=n//3*650
 with Image.open(ROOT/row['path'])as im:im=ImageOps.contain(im.convert('RGB'),(280,580));contact.paste(im,(x+(300-im.width)//2,y+35))
 draw.text((x+10,y+10),row['game']['Name']+' '+str(row['width'])+'x'+str(row['height']),fill='black')
contact.save(OUT/'contact.jpg',quality=94)
