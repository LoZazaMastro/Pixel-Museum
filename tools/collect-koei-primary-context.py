"""Collect publisher material for the existing Koei history paragraphs."""
from pathlib import Path
import hashlib
import json
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'build/research/koei-existing-prose-publisher-context'
BASE.mkdir(parents=True,exist_ok=True)
sources = [
    ('founders-2019.pdf','https://www.koeitecmo.co.jp/e/ir/docs/33833de079919bad7675b6707903b8765d275855.pdf'),
    ('three-kingdoms40.html','https://www.gamecity.ne.jp/sangokushi40th/jp/'),
    ('nobunaga-history.html','https://www.gamecity.ne.jp/nobunaga330/history.html'),
    ('nobunaga-original-screen.jpg','https://www.gamecity.ne.jp/nobunaga330/images/history/img_101.jpg'),
    ('three-kingdoms-original.jpg','https://www.gamecity.ne.jp/sangokushi40th/assets/img/history/img_01.jpg'),
    ('nobunaga-steam.json','https://store.steampowered.com/api/appdetails?appids=544990&l=english'),
    ('three-kingdoms-steam.json','https://store.steampowered.com/api/appdetails?appids=521670&l=english'),
]
rows=[]
for name,url in sources:
    path=BASE/name
    try:
        if not path.exists():
            request=urllib.request.Request(url,headers={'User-Agent':'PixelMuseumResearch/1.0 (historical source review)'})
            with urllib.request.urlopen(request,timeout=45) as response:
                path.write_bytes(response.read())
        rows.append(dict(file=path.relative_to(ROOT).as_posix(),url=url,bytes=path.stat().st_size,
                         sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    except Exception as exc:
        rows.append(dict(url=url,error=str(exc)))
for stem in ('nobunaga','three-kingdoms'):
    doc=json.loads((BASE/(stem+'-steam.json')).read_text(encoding='utf8'))
    data=next(iter(doc.values()))['data']
    for item in data['screenshots'][:4]:
        path=BASE/(stem+'-publisher-shot'+str(item['id'])+'.jpg')
        url=item['path_full']
        if not path.exists():
            with urllib.request.urlopen(url,timeout=45) as response:
                path.write_bytes(response.read())
        rows.append(dict(file=path.relative_to(ROOT).as_posix(),url=url,bytes=path.stat().st_size,
                         sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
(BASE/'primary-pages.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8')
print(json.dumps(rows))
