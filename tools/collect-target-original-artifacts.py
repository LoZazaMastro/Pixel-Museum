"""Collect the original Target manual and the already identified Sol photograph."""
from pathlib import Path
import hashlib
import json
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/target-1977-existing-prose-primary-artifacts'
BASE.mkdir(parents=True,exist_ok=True)
sources=[('gamepac1-original.pdf','https://www.sol20.org/manuals/gamepac1.pdf'),
    ('sol20-original.jpg','https://upload.wikimedia.org/wikipedia/commons/5/5e/Processor_Technology_SOL_20_Computer.jpg'),
    ('sol20-source.html','https://commons.wikimedia.org/wiki/File:Processor_Technology_SOL_20_Computer.jpg'),
    ('program-notes.html','https://sol20.org/program_notes.html')]
rows=[]
for name,url in sources:
    path=BASE/name
    if not path.exists():
        request=urllib.request.Request(url,headers={'User-Agent':'PixelMuseumResearch/1.0 (historical source review)'})
        with urllib.request.urlopen(request,timeout=45) as response:
            path.write_bytes(response.read())
    rows.append(dict(file=path.relative_to(ROOT).as_posix(),url=url,
        bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
(BASE/'original-source-downloads.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8')
print(json.dumps(rows))
