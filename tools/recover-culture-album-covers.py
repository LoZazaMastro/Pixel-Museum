"""Recover identified record sleeves from the publisher deliveries on Apple Music.

This creates review candidates, never automatically approves an image. Album
identity, the visible sleeve and rights information must be checked separately.
"""
import hashlib
import io
import json
from pathlib import Path
import time
import urllib.parse
import urllib.request

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/research/human-history/album-cover-review'
TARGETS = [
    ('The Joshua Tree', 'U2'),
    ('Nevermind', 'Nirvana'),
    ('Thriller', 'Michael Jackson'),
    ('Revolver', 'The Beatles'),
    ('OK Computer', 'Radiohead'),
    ('In Rainbows', 'Radiohead'),
    ('Please Please Me', 'The Beatles'),
    ('Highway 61 Revisited', 'Bob Dylan'),
    ('Black Sabbath', 'Black Sabbath'),
]


def get(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'PixelMuseum-AssetReview/1.0'})
    with urllib.request.urlopen(request, timeout=40) as response:
        return response.read()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    for title, artist in TARGETS:
        key = hashlib.sha256((artist + ':' + title).encode()).hexdigest()[:16]
        source = 'https://itunes.apple.com/search?' + urllib.parse.urlencode({
            'term': artist + ' ' + title, 'entity': 'album', 'country': 'US', 'limit': 30,
        })
        cached = OUT / (key + '.json')
        try:
            if not cached.exists():
                cached.write_bytes(get(source))
                time.sleep(.4)
            matches = json.loads(cached.read_text(encoding='utf8'))['results']
            exact = [item for item in matches
                     if item.get('artistName', '').casefold() == artist.casefold()
                     and item.get('collectionName', '').casefold() == title.casefold()]
            if not exact:
                results.append({'subject': title, 'artist': artist, 'status': 'no_exact_match'})
                continue
            item = exact[0]
            url = item['artworkUrl100'].replace('/100x100bb.', '/3000x3000bb.')
            image_path = OUT / (key + '.jpg')
            if not image_path.exists():
                image_path.write_bytes(get(url))
            data = image_path.read_bytes()
            with Image.open(io.BytesIO(data)) as image:
                image.load()
                size = image.size
            results.append({
                'subject': title, 'artist': artist, 'status': 'pending_visual_review',
                'url': url, 'source_page': item['collectionViewUrl'],
                'metadata_source': source, 'release_date_in_delivery': item['releaseDate'],
                'rights_statement': item.get('copyright', ''),
                'license': 'All rights reserved; no Creative Commons licence asserted.',
                'recovery_local_source': image_path.relative_to(ROOT).as_posix(),
                'width': size[0], 'height': size[1],
                'sha256': hashlib.sha256(data).hexdigest(),
                'note': 'Current publisher delivery of the identified album. Original-edition sleeve identity still requires visual review.',
            })
        except Exception as error:
            results.append({'subject': title, 'artist': artist, 'status': 'held', 'reason': str(error)})
        print(title, results[-1]['status'], flush=True)
    (OUT / 'candidates.json').write_text(json.dumps({'entries': results}, ensure_ascii=True, indent=2) + '\n', encoding='utf8')


if __name__ == '__main__':
    main()
