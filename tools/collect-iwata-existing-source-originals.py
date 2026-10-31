"""Collect original photographs already identified by the Playhub archive."""
from pathlib import Path
import hashlib
import json
import urllib.request
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/research/iwata-existing-prose-illustrated-chapters'
BASE.mkdir(parents=True, exist_ok=True)
sources = [
    ('pet-original.jpg', 'https://upload.wikimedia.org/wikipedia/commons/c/c5/Commodore_2001_Series-IMG_0448b.jpg'),
    ('gdc-2011-original.jpg', 'https://upload.wikimedia.org/wikipedia/commons/7/7d/Satoru_Iwata_-_Game_Developers_Conference_2011_-_Day_3_%283%29.jpg'),
    ('pet-source.html', 'https://commons.wikimedia.org/wiki/File:Commodore_2001_Series-IMG_0448b.jpg'),
    ('gdc-source.html', 'https://commons.wikimedia.org/wiki/File:Satoru_Iwata_-_Game_Developers_Conference_2011_-_Day_3_(3).jpg'),
]
rows=[]
for name, url in sources:
    path=BASE/name
    if not path.exists():
        request=urllib.request.Request(url,headers={'User-Agent':'PixelMuseumResearch/1.0 (historical source review)'})
        with urllib.request.urlopen(request, timeout=45) as response:
            path.write_bytes(response.read())
    row=dict(file=path.relative_to(ROOT).as_posix(),url=url,
             sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size)
    if name.endswith('.jpg'):
        with Image.open(path) as image:
            image.load()
            row['native_dimensions']=list(image.size)
    rows.append(row)
out=BASE/'original-photograph-source-files.json'
out.write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8')
print(json.dumps(rows))
