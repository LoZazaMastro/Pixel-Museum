"""Collect original Cinematronics documentation and viewable museum photographs."""
from pathlib import Path
import urllib.request,json,hashlib,re
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'build/research/starhawk-existing-prose-original-machines';base.mkdir(parents=True,exist_ok=True)
items=[('original-arcade-manual.pdf','https://www.arcade-museum.com/manuals-videogames/S/StarHawk.pdf'),
 ('original-museum-controls.jpg','https://www.arcade-museum.com/images-game/15/starhawk-15737.jpg')]
rows=[]
for name,url in items:
 p=base/name
 if not p.exists():
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=30)as r:p.write_bytes(r.read())
 rows.append(dict(file=p.relative_to(ROOT).as_posix(),url=url,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(base/'source-downloads.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8')
print(json.dumps(rows))
