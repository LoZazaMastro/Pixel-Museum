"""Collect the cited MUD creators' accounts and university publication."""
from pathlib import Path
import hashlib
import json
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/mud-existing-prose-primary-illustrations'
BASE.mkdir(parents=True,exist_ok=True)
sources=[('essex-effect-2017.pdf','https://alumni.essex.ac.uk/file/essex-effect-2017.pdf'),
    ('mud-history.html','https://mud.co.uk/richard/mudhist.htm'),
    ('your-computer-march-1985.html','https://mud.co.uk/richard/ycmar85.htm'),
    ('bartle-biography.html','https://mud.co.uk/richard/biog.htm'),
    ('essex-2022-reunion.html','https://www.essex.ac.uk/news/2022/07/19/computer-pioneers-meet-up-to-celebrate-honorary-degree-for-nigel-roberts')]
rows=[]
for name,url in sources:
    path=BASE/name
    if not path.exists():
        request=urllib.request.Request(url,headers={'User-Agent':'PixelMuseumResearch/1.0 (historical source review)'})
        with urllib.request.urlopen(request,timeout=45) as response:
            path.write_bytes(response.read())
    rows.append(dict(file=path.relative_to(ROOT).as_posix(),url=url,bytes=path.stat().st_size,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
(BASE/'primary-source-downloads.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8')
print(json.dumps(rows))
