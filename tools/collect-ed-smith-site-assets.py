"""Preserve the original asset identifiers published by Ed Smith's own site."""
from pathlib import Path
import hashlib
import json
import urllib.request
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/ed-smith-existing-prose-primary-images'
pages=json.loads((BASE/'observed-primary-image-elements.json').read_text(encoding='utf8'))
images=pages[0]['images']
rows=[]
for alt,name in [('Ed APF Black Enterprise.PNG','ed-apf-site-original.png'),
                 ('Imagine That Book Cover.jpg','imagine-that-site-original.jpg')]:
    item,=[x for x in images if x.get('alt')==alt]
    # Wix publishes the original media identifier before its display transform.
    original=item['src'].split('/v1/',1)[0]
    assert original.startswith('https://static.wixstatic.com/media/')
    path=BASE/name
    if not path.exists():
        request=urllib.request.Request(original,headers={'User-Agent':'PixelMuseumResearch/1.0 (historical source review)'})
        with urllib.request.urlopen(request,timeout=45) as response:
            path.write_bytes(response.read())
    with Image.open(path) as image:
        image.load()
        dimensions=list(image.size)
    rows.append(dict(file=path.relative_to(ROOT).as_posix(),url=original,
        observed_display_url=item['src'],observed_alt=alt,
        source_page=pages[0]['url'],native_dimensions=dimensions,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        processing='Original published media asset, without a resize or crop transform; bytes preserved.'))
(BASE/'own-site-original-asset-downloads.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8')
print(json.dumps(rows))
