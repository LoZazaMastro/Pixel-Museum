"""Contact sheets of actual native history assets, without changing originals."""
from pathlib import Path
import json, sys, math
from PIL import Image, ImageOps, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
source=ROOT/(sys.argv[1] if len(sys.argv)>1 else 'build/research/human-history/illustrated-candidate-checkpoint.json')
entries=sorted(json.loads(source.read_text(encoding='utf8'))['entries'],key=lambda e:(e['year'],e['title']))
out=ROOT/(sys.argv[2] if len(sys.argv)>2 else 'build/research/human-history/contact-sheets');out.mkdir(exist_ok=True)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
for start in range(0,len(entries),30):
 sheet=Image.new('RGB',(1800,1320),'#191919');draw=ImageDraw.Draw(sheet)
 for offset,entry in enumerate(entries[start:start+30]):
  image=entry['images'][0];path=ROOT/image['recovery_local_source'];x=(offset%6)*300;y=(offset//6)*264
  with Image.open(path) as original:
   thumb=ImageOps.contain(original.convert('RGB'),(290,205))
   sheet.paste(thumb,(x+(300-thumb.width)//2,y+(205-thumb.height)//2))
  label=str(start+offset)+' '+str(entry['year'])+' '+entry['title']
  while draw.textlength(label,font=font)>292:label=label[:-2]
  draw.text((x+4,y+210),label,fill='white',font=font)
  draw.text((x+4,y+236),str(image['width'])+'x'+str(image['height']),fill='#bbbbbb',font=small)
 sheet.save(out/('history-'+str(start//30+1).zfill(2)+'.jpg'),quality=92)
print(len(entries),'assets in',math.ceil(len(entries)/30),'contact sheets',flush=True)
