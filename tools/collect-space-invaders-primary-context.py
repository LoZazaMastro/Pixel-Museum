"""Save public maker and museum sources for contextual image review."""
from pathlib import Path
import hashlib
import json
import re
import urllib.request
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/research/space-invaders-existing-prose-context'
BASE.mkdir(parents=True, exist_ok=True)
sources = [
    ('taito-exhibition.html', 'https://artsandculture.google.com/story/SwVBsVEMarKRfA'),
    ('taito-1978-flyer.html', 'https://flyers.arcade-museum.com/videogames/show/980'),
    ('commons-cocktail.html', 'https://commons.wikimedia.org/wiki/File:Space_Invaders.JPG'),
    ('taito-1978-flyer-original.jpg', 'https://flyers.arcade-museum.com/videogame-flyers/0/space-invaders-00980-01.jpg'),
    ('taito-gameplay-item.html', 'https://artsandculture.google.com/asset/space-invaders-ingame-screen-taito/wwEfnzrvs-tYow'),
    ('taito-invader-house-item.html', 'https://artsandculture.google.com/asset/inside-of-the-so-called-invader-house-5-taito/FAGr_KSCgnsgIA'),
]
rows = []
for name, url in sources:
    path = BASE / name
    if not path.exists():
        request = urllib.request.Request(url, headers={'User-Agent': 'PixelMuseumResearch/1.0 (historical source review)'})
        with urllib.request.urlopen(request, timeout=45) as response:
            path.write_bytes(response.read())
    rows.append(dict(file=path.relative_to(ROOT).as_posix(), url=url,
                     bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
class Preview(HTMLParser):
    image_url = None
    def handle_starttag(self, tag, attrs):
        item = dict(attrs)
        if tag == 'meta' and item.get('property') == 'og:image':
            self.image_url = item.get('content')
for stem in ('taito-gameplay', 'taito-invader-house'):
    parser = Preview()
    parser.feed((BASE / (stem+'-item.html')).read_text(encoding='utf8'))
    if not parser.image_url:
        raise RuntimeError('No ordinary published preview for '+stem)
    path = BASE / (stem+'-published-preview.jpg')
    if not path.exists():
        with urllib.request.urlopen(parser.image_url, timeout=45) as response:
            path.write_bytes(response.read())
    rows.append(dict(file=path.relative_to(ROOT).as_posix(), url=parser.image_url,
                     bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    html = (BASE / (stem+'-item.html')).read_text(encoding='utf8')
    # Use the larger ordinary preview URL actually published in the item HTML.
    match = re.search(re.escape(parser.image_url)+r'\\u003d(s[0-9]+)', html)
    if match:
        url = parser.image_url+'='+match.group(1)
        path = BASE / (stem+'-published-large-preview.jpg')
        if not path.exists():
            with urllib.request.urlopen(url, timeout=45) as response:
                path.write_bytes(response.read())
        rows.append(dict(file=path.relative_to(ROOT).as_posix(), url=url,
                         bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
(BASE / 'primary-pages.json').write_text(json.dumps(rows, indent=2)+'\n', encoding='utf8')
print(json.dumps(rows))
