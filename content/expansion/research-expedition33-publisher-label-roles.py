"""Read publisher-delivered album credit blocks, retaining no preview transports."""
import hashlib
import html
import json
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/modern-public-albums'
url = 'https://www.qobuz.com/us-en/album/clair-obscur-expedition-33-original-soundtrack-lorien-testard/ipjxnayoe1y1a'
target = OUT / 'expedition33-label.html'
if not target.exists():
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=25) as response:
        raw = response.read().decode('utf-8')
    assert 'Lorien Testard' in raw and 'data-track-v2' in raw
    raw = re.sub(r'\sdata-source="[^"]*"', ' data-source="[preview transport omitted]"', raw)
    target.write_text(raw, encoding='utf-8')
raw = target.read_text(encoding='utf-8')
tracks = []
for block in raw.split('<div class="player__item">')[1:]:
    match = re.search(r'data-track-v2="(.*?)"', block, re.S)
    if not match:
        continue
    row = json.loads(html.unescape(match[1]))
    row['credits'] = [html.unescape(text) for text in re.findall(r'<p class="track__info">(.*?)</p>', block, re.S)]
    tracks.append(row)
(OUT / 'expedition33-label-roles-first-page.json').write_text(json.dumps({'url': url, 'actual_body_retrieved': True,
    'local_path': target.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
    'tracks': tracks}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('rows', len(tracks))
for track in tracks[:4]:
    print(track['item_name'], track['credits'])
for line in raw.splitlines():
    if any(key in line.lower() for key in ['pagination', 'offset', 'tracklist/load', 'tracks/load', 'album/get', 'load-more']):
        print(line.strip()[:1300])
