"""Collect both publication evidence and the original back of the 1973 Atari flyer."""
from pathlib import Path
import urllib.request,json,hashlib,sys
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
directory='space-race-existing-prose-period-flyer'
page='https://flyers.arcade-museum.com/videogames/show/5119'
image='https://flyers.arcade-museum.com/videogame-flyers/5/space-race-05112-02.jpg'
if sys.argv[1:]==['gran-trak10']:
    directory='gran-trak10-existing-prose-period-flyer'
    page='https://flyers.arcade-museum.com/videogames/show/434'
    image='https://flyers.arcade-museum.com/videogame-flyers/0/gran-trak-10-00435-02.jpg'
base=ROOT/'build/research'/directory;base.mkdir(parents=True,exist_ok=True)
rows=[]
for name,url in [('flyer-original-source.html',page),('original-flyer-back.jpg',image)]:
    p=base/name
    if not p.exists():
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=30)as r:data=r.read()
        p.write_bytes(data)
    rows.append(dict(file=p.relative_to(ROOT).as_posix(),url=url,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(base/'source-downloads.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(size=Image.open(base/'original-flyer-back.jpg').size,sources=rows)))
