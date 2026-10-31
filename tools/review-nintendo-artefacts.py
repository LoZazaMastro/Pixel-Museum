"""Make an internal contact sheet from real source photographs, never stand-ins."""
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
import hashlib,io,json
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/research/nintendo-complete-story'
PLAYHUB=Path('F:/Playhub/Plugin/Playhub/assets/on-this-day/v1')
manifest=json.loads((ROOT/'assets/images/manifest.json').read_text(encoding='utf-8'))['images']
catalog=json.loads((OUT/'existing-exhibit-artifacts.json').read_text(encoding='utf-8'))
rows=[]
for file in sorted(PLAYHUB.glob('jul-dec-review-wiki-nintendo-*.png')):
    rows.append(dict(label=file.name,path=str(file)))
for file in [PLAYHUB/'nintendo-ultra-hand.jpg']:
    if file.is_file():rows.append(dict(label=file.name,path=str(file)))
selection={'nes':1,'game-boy':1,'daily-11-21':0,'nintendo-64':0,'workbook-03-21-game-boy-advance':0,
    'workbook-09-14-nintendo-gamecube':0,'daily-12-02':1,'wii':0,'nintendo-3ds':2,
    'daily-11-18':0,'switch':0,'switch-2':0,'daily-12-06':0}
for e in catalog:
    if e['id'] in selection:
        image=e['images'][selection[e['id']]];local=manifest.get(image['url'])
        if local:rows.append(dict(label=e['id'],path=str(ROOT/local),image=image))
for url,name in [('https://museum.nintendo.com/assets/images/exhibition/know/image01.webp','museum-display.webp')]:
    path=OUT/name
    if not path.exists():
        with urlopen(Request(url,headers={'User-Agent':'PixelMuseum source research'}),timeout=20) as response:path.write_bytes(response.read(20<<20))
    rows.append(dict(label=name,path=str(path),image=dict(url=url,source_page='https://museum.nintendo.com/en/exhibition/index.html',
        title='Nintendo Museum historical product display',creator='Nintendo',credit='Nintendo / official museum photography',
        license='Original Nintendo photographic rights retained',license_url='',recovery_local_source=path.relative_to(ROOT).as_posix())))
width=1600;cellw=400;cellh=280
sheet=Image.new('RGB',(width,((len(rows)+3)//4)*cellh),'#202020');draw=ImageDraw.Draw(sheet)
for n,row in enumerate(rows):
    with Image.open(row['path']) as im:
        im.load();row['dimensions']=list(im.size);thumb=ImageOps.contain(im.convert('RGB'),(cellw-16,cellh-50))
        x=(n%4)*cellw;y=(n//4)*cellh
        sheet.paste(thumb,(x+(cellw-thumb.width)//2,y))
        draw.text((x+8,y+cellh-43),str(n)+' '+row['label'][:46],fill='white')
        draw.text((x+8,y+cellh-24),str(im.size),fill='#bbbbbb')
        if 'image' in row:row['image'].update(width=im.width,height=im.height)
sheet.save(OUT/'nintendo-artefact-contact.jpg',quality=90)
(OUT/'nintendo-artefact-contact.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Recorded',len(rows),'real artefacts for visual review.')
