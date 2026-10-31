"""Preserve the university's original reunion photograph identified in its page."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin
import hashlib
import json
import urllib.request
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/mud-existing-prose-primary-illustrations'
class Reunion(HTMLParser):
    def handle_starttag(self,tag,attrs):
        attributes=dict(attrs)
        if tag=='img' and attributes.get('alt')=='Nigel Roberts with Roy Trubshaw and Professor Richard Bartle':
            found.append(attributes)
found=[]
Reunion().feed((BASE/'essex-2022-reunion.html').read_text(encoding='utf8'))
item,=found
observed=urljoin('https://www.essex.ac.uk',item['src'])
original=observed.split('?',1)[0]
path=BASE/'essex-2022-reunion-original.jpg'
if not path.exists():
    request=urllib.request.Request(original,headers={'User-Agent':'PixelMuseumResearch/1.0 (historical source review)'})
    with urllib.request.urlopen(request,timeout=45) as response:
        path.write_bytes(response.read())
with Image.open(path) as image:
    image.load()
    dimensions=list(image.size)
record=dict(file=path.relative_to(ROOT).as_posix(),url=original,observed_url=observed,
    observed_alt=item['alt'],source_page='https://www.essex.ac.uk/news/2022/07/19/computer-pioneers-meet-up-to-celebrate-honorary-degree-for-nigel-roberts',
    native_dimensions=dimensions,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    processing='Original published asset without a Sitecore resize/crop query. Original JPEG retained byte-for-byte.')
(BASE/'essex-2022-original-download.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
print(json.dumps(record))
