"""Resolve the official Sony playlist's music only; no media downloads."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
F = ROOT / 'build/research/soundtrack-broad/modern-following'

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

music = module('hd_music', 'content/expansion/soundtrack-broad-pipeline.py')
video = module('hd_video', 'tools/discover-museum-videos.py')
flat = json.loads((F / 'helldivers2-sony-official-playlist.json').read_text(encoding='utf8'))
records, excluded, failures = [], [], 0
for row in flat['entries']:
    if not row.get('title') or 'Trailer' in row['title']:
        excluded.append({'youtube_id': row['id'], 'title': row.get('title'), 'reason': 'Trailer or unavailable unnamed playlist item, not an album recording.'})
        continue
    result = {'youtube_id': row['id'], 'playlist_title': row['title']}
    try:
        meta, watch = video.metadata(row['id'], row), music.watch(row['id'])
        assert meta['native_compatible_avc_aac']
        if row['id'] == 'g5srz-8PE58':
            assert meta['channel_id'] == 'UCEdikMFtocqFOnPYOuEKqUw'
            assert 'Provided to YouTube by Milan Records' in watch['shortDescription']
            assert 'Sony Interactive Entertainment LLC' in watch['shortDescription']
        else:
            assert meta['channel_id'] == 'UCGkX_HCD_T5XOwxi_KR6YoQ'
        assert watch['channelId'] == meta['channel_id']
        assert watch['title'] == meta['title'] == row['title']
        assert float(watch['lengthSeconds']) == float(meta['duration'])
        assert 'Helldivers' in watch['shortDescription']
        result.update(status='verified_pending_peer', metadata=meta)
        failures = 0
    except Exception as error:
        result.update(status='held', reason=str(error))
        failures += 1
    records.append(result)
    (F / 'helldivers2-native-research.json').write_text(json.dumps({'records': records, 'excluded': excluded, 'audio_downloaded': False}, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(result['status'], result['playlist_title'], flush=True)
    if failures >= 3:
        break
(F / 'helldivers2-native-research.json').write_text(json.dumps({'records': records, 'excluded': excluded, 'audio_downloaded': False}, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
