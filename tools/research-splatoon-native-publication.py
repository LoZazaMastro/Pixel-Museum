"""Check exact public playlist recordings using the app's native metadata path.

Descriptions are optional publication fields, never manufactured. This is
separate from the broad soundtrack admission gate and does not change it.
"""
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'build/research/soundtrack-broad/splatoon-original-2015'
spec = importlib.util.spec_from_file_location('museum_video_probe', ROOT / 'tools/discover-museum-videos.py')
video = importlib.util.module_from_spec(spec)
spec.loader.exec_module(video)
playlist = json.loads((FOLDER / 'playlist-original-flat.json').read_text(encoding='utf8'))
records = []
excluded = []
failures = 0
for row in playlist['entries']:
    title = row.get('title', '')
    if re.search(r'\bLIVE\b|\bExtended\b|\bSFX\b|\bJingle\b', title, re.I) or (row.get('duration') or 0) < 30:
        excluded.append({'youtube_id': row['id'], 'title': title,
                         'reason': 'Live/extended performance, sound effect or short incidental cue; not admitted as a full music selection.'})
        continue
    result = {'youtube_id': row['id'], 'playlist_title': title}
    try:
        meta = video.metadata(row['id'], row)
        assert meta['channel_id'] == playlist['channel_id'], 'Actual uploader differs from playlist archive'
        assert meta['title'] == title, 'Actual publication title differs from playlist'
        assert meta['native_compatible_avc_aac'] is True
        assert float(meta['duration']) >= 30
        assert not re.search(r'\b(?:remix|remaster|cover)\b|Splatoon\s*[23]', meta['title'], re.I)
        result.update(status='native_metadata_verified_pending_semantic_peer', metadata=meta,
                      metadata_file='build/research/video-discovery/video-' + row['id'] + '.json')
        failures = 0
    except Exception as error:
        result.update(status='held', reason=str(error))
        failures += 1
    records.append(result)
    document = {'status': 'research_only_not_admitted',
                'scope': 'Original Wii U game archival playlist. Title/channel/duration and actual native AVC/AAC metadata checked. Empty descriptions explicitly retained as empty; no audio fingerprint or exact retail-master completeness claim.',
                'playlist_id': playlist['id'], 'records': records, 'excluded': excluded}
    (FOLDER / 'native-publication-research.json').write_text(json.dumps(document, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(result['status'], title, flush=True)
    if failures >= 3:
        print('Circuit breaker: three consecutive metadata failures.', flush=True)
        break
# The final playlist rows can all be exclusions. Persist them even when there
# was no later accepted recording to trigger the in-loop checkpoint.
document['excluded'] = excluded
(FOLDER / 'native-publication-research.json').write_text(json.dumps(document, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
