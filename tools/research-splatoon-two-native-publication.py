"""Resolve original Switch-game archival music candidates; no admission."""
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'build/research/soundtrack-broad/splatoon-two-original-2017'
spec = importlib.util.spec_from_file_location('museum_video_probe', ROOT / 'tools/discover-museum-videos.py')
video = importlib.util.module_from_spec(spec)
spec.loader.exec_module(video)
playlist = json.loads((FOLDER / 'original-base-flat-playlist.json').read_text(encoding='utf8'))
records, excluded = [], []
failures = 0
def save():
    document = {'status': 'research_only_not_admitted',
        'scope': 'Splatoon 2 original Switch game and later base-game updates. Actual individual publication fields are authoritative. Playlist description erroneously names Splatoon 3 and is NOT identity evidence. No Octo Expansion track or retail-master completeness claim.',
        'playlist_id': playlist['id'], 'records': records, 'excluded': excluded,
        'playlist_description_identity_conflict': playlist.get('description')}
    (FOLDER / 'native-publication-research.json').write_text(json.dumps(document, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
for row in playlist['entries']:
    title = row.get('title', '')
    if re.search(r'\b(?:LIVE|Extended|SFX|Jingle|Demo)\b', title, re.I) or (row.get('duration') or 0) < 30:
        excluded.append({'youtube_id': row['id'], 'title': title, 'reason': 'Demo, live/extended performance, sound effect or short incidental cue excluded.'})
        continue
    result = {'youtube_id': row['id'], 'playlist_title': title}
    try:
        meta = video.metadata(row['id'], row)
        assert meta['channel_id'] == playlist['channel_id'], 'Actual uploader differs'
        assert meta['title'] == title and '[Splatoon 2 OST]' in meta['title'], 'Exact game title mismatch'
        assert meta['native_compatible_avc_aac'] is True and float(meta['duration']) >= 30
        result.update(status='native_metadata_verified_pending_semantic_peer', metadata=meta,
                      metadata_file='build/research/video-discovery/video-' + row['id'] + '.json')
        failures = 0
    except Exception as error:
        result.update(status='held', reason=str(error))
        failures += 1
    records.append(result)
    save()
    print(result['status'], title, flush=True)
    if failures >= 3:
        print('Circuit breaker: three consecutive metadata failures.', flush=True)
        break
save()
