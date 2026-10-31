"""Download and contact-review bounded, identified C64 artifact candidates."""
from pathlib import Path
from urllib.request import Request, urlopen
import concurrent.futures
import hashlib
import json
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/research/c64-loading-media'
metadata=json.loads((OUT/'exact-c64-packaging-candidates.json').read_text(encoding='utf8'))
items=[]
for row in metadata['images']:
    game,image=row['game'],row['image']
    if game['Name'] not in ('Leviathan','Enlightenment','RoboCop'):continue
    if image['Type'] not in ('Box - Front','Advertisement Flyer - Front'):continue
    if image.get('Region') not in ('Europe','North America'):continue
    items.append({'name':game['Name']+' '+image['Type']+' '+image.get('Region',''),
                  'url':'https://images.launchbox-app.com/'+image['FileName'],
                  'source_page':'https://gamesdb.launchbox-app.com/games/images/'+game['DatabaseID'],
                  'identity_record':row})
for slug in ('batman-the-caped-crusader','bubble-bobble','gryzor-full'):
    url='https://retro-video-gaming.com/wp-content/uploads/2015/06/commodore-c64-'+slug+'.jpg'
    assert url in (OUT/'collector-c64-scans.html').read_text(encoding='utf8')
    items.append({'name':'Collector Hit Squad '+slug,'url':url,'source_page':'https://retro-video-gaming.com/commodore-64-collection/'})
for slug in ('leviathan','druid_2_enlightenment'):
    items.append({'name':'DOKK original native '+slug,'url':'https://www.c64.com/pictures/dokk_gallery/images/'+slug+'.gif',
                  'source_page':'https://www.c64.com/pictures/dokk_gallery/'+('20' if slug=='leviathan' else '10')+'.php'})

def acquire(row):
    row=dict(row);suffix=Path(row['url']).suffix
    path=OUT/(hashlib.sha256(row['url'].encode()).hexdigest()[:16]+suffix)
    try:
        if not path.exists():
            with urlopen(Request(row['url'],headers={'User-Agent':'Mozilla/5.0'}),timeout=30) as response:body=response.read(16<<20)
            temporary=path.with_suffix(path.suffix+'.part');temporary.write_bytes(body);temporary.replace(path)
        with Image.open(path) as image:
            image.load();row['source_width'],row['source_height']=image.size
        row.update({'recovery_local_source':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size})
    except Exception as error:row.update({'status':'held_fetch_failed','reason':str(error)})
    print(row['name'],row.get('source_width'),row.get('source_height'),row.get('status','decoded'),flush=True)
    return row

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(acquire,items))
(OUT/'decoded-artifact-candidates.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
valid=[row for row in rows if row.get('recovery_local_source')]
contact=Image.new('RGB',(1280,((len(valid)+3)//4)*430),'#ece9df');draw=ImageDraw.Draw(contact)
for n,row in enumerate(valid):
    with Image.open(ROOT/row['recovery_local_source']) as image:
        thumb=image.convert('RGB');thumb.thumbnail((300,370))
        x=(n%4)*320+(320-thumb.width)//2;y=(n//4)*430
        contact.paste(thumb,(x,y+35))
    label=f"{n}: {row['name']}\n{row['source_width']}x{row['source_height']}"
    draw.text(((n%4)*320+5,(n//4)*430+5),label,fill='#101510')
contact.save(OUT/'artifact-contact.jpg',quality=92)
