"""Retain artist-channel provenance already present in cached music metadata."""
from pathlib import Path
import json, hashlib, re

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'content/catalog.json'
raw = path.read_bytes()
doc = json.loads(raw)
cache, games = {}, []
for entry in doc['entries']:
    count = 0
    for track in (entry.get('soundtrack') or {}).get('tracks', []):
        receipt = track.get('album_metadata_receipt')
        if not receipt or track.get('channel_url'):
            continue
        if receipt not in cache:
            album = json.loads((ROOT / receipt).read_text(encoding='utf-8'))
            cache[receipt] = album, {t.get('videoId'): t for t in album['tracks']}
        album, by_id = cache[receipt]
        row = by_id.get(track['youtube_id'])
        if not row:
            continue
        identifiers = [a.get('id', '') for a in row.get('artists', []) + album.get('artists', [])]
        channel = next((x for x in identifiers if isinstance(x, str) and re.fullmatch(r'UC[A-Za-z0-9_-]{22}', x)), None)
        if channel:
            track['channel_url'] = 'https://www.youtube.com/channel/' + channel
            count += 1
    if count:
        games.append({'entry_id': entry['id'], 'channel_records_added': count})
base = ROOT / 'build/research/app-audio-channel-provenance-20261030'
base.mkdir(exist_ok=True)
if games:
    (base / 'catalog-before.json').write_bytes(raw)
    assert path.read_bytes() == raw
    payload = (json.dumps(doc, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    temporary = path.with_suffix('.channel.tmp')
    temporary.write_bytes(payload)
    temporary.replace(path)
    (base / 'receipt.json').write_text(json.dumps({
        'before_sha256': hashlib.sha256(raw).hexdigest(),
        'after_sha256': hashlib.sha256(payload).hexdigest(),
        'updated_tracks': sum(r['channel_records_added'] for r in games),
        'games': games,
        'scope': 'Only missing channel_url values from the same published album metadata; codec and playback verification flags unchanged.'
    }, indent=2) + '\n', encoding='utf-8')
print(len(games), 'games;', sum(r['channel_records_added'] for r in games), 'observed artist channel links added')
