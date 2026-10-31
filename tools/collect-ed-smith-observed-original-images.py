"""Download only image links actually published by the cited interview."""
from pathlib import Path
import hashlib
import json
import urllib.request
from urllib.parse import urljoin
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/ed-smith-existing-prose-primary-images'
observed=json.loads((BASE/'observed-primary-image-elements.json').read_text(encoding='utf8'))
interview=observed[1]
names=['ed_smith_headshot_small.jpg','ed_smith_black_enterprise_1982.jpg',
    'ed_smith_highschool.jpg','ed_smith_marbelite_large.jpg',
    'imagination_machine_large.jpg','ed_smith_ces_table.jpg','ed_smith_kronos.jpg']
rows=[]
for name in names:
    link,=[x for x in interview['relevant_links'] if x.endswith('/'+name)]
    url=urljoin(interview['url'],link)
    path=BASE/name
    if not path.exists():
        request=urllib.request.Request(url,headers={'User-Agent':'PixelMuseumResearch/1.0 (historical source review)'})
        with urllib.request.urlopen(request,timeout=45) as response:
            path.write_bytes(response.read())
    with Image.open(path) as image:
        image.load()
        dimensions=list(image.size)
    rows.append(dict(file=path.relative_to(ROOT).as_posix(),url=url,
        source_page=interview['url'],sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        native_dimensions=dimensions))
(BASE/'observed-original-image-downloads.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8')
print(json.dumps(rows))
