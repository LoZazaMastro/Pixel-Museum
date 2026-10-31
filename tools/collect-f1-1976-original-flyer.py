"""Collect the original manufacturer leaflet, without a modern racing-game substitute."""
from pathlib import Path
import urllib.request,json,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'build/research/f1-1976-existing-prose-original-machine';base.mkdir(parents=True,exist_ok=True)
rows=[]
for name,url in [('original-flyer-source.html','https://flyers.arcade-museum.com/arcades/show/7648'),
 ('original-flyer-back.jpg','https://flyers.arcade-museum.com/arcade-flyers/7/f-1--atari-07639-02.jpg')]:
 p=base/name
 if not p.exists():
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=30)as r:data=r.read()
  p.write_bytes(data)
 rows.append(dict(file=p.relative_to(ROOT).as_posix(),url=url,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(base/'source-downloads.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(size=Image.open(base/'original-flyer-back.jpg').size,sources=rows)))
