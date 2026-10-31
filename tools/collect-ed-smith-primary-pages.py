"""Collect the two already cited first-person Ed Smith publications."""
from pathlib import Path
import hashlib
import json
import urllib.request
from html.parser import HTMLParser

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/ed-smith-existing-prose-primary-images'
BASE.mkdir(parents=True,exist_ok=True)
sources=[('about.html','https://www.imaginethat2.com/about'),
    ('interview.html','https://www.vintagecomputing.com/index.php/archives/1230/ed-smith-interview')]
class Images(HTMLParser):
    def handle_starttag(self,tag,attrs):
        if tag=='a' and dict(attrs).get('href'):
            links.append(dict(attrs)['href'])
        if tag=='img':
            attributes=dict(attrs)
            if attributes.get('src'):
                images.append(attributes)
rows=[]
for name,url in sources:
    path=BASE/name
    if not path.exists():
        request=urllib.request.Request(url,headers={'User-Agent':'PixelMuseumResearch/1.0 (historical source review)'})
        with urllib.request.urlopen(request,timeout=45) as response:
            path.write_bytes(response.read())
    images=[]
    links=[]
    Images().feed(path.read_text(encoding='utf8'))
    rows.append(dict(file=path.relative_to(ROOT).as_posix(),url=url,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),images=images,
        relevant_links=[x for x in links if any(k in x for k in ['ed_smith','imagination_machine'])]))
(BASE/'observed-primary-image-elements.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8')
print(json.dumps([dict(file=r['file'],images=len(r['images']),links=r['relevant_links']) for r in rows]))
