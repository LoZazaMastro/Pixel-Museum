"""Check the eighty-three public original-game recordings, never audio files."""
import importlib.util
import json
from pathlib import Path
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
F = ROOT / 'build/research/soundtrack-broad/modern-following'

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

video = module('mhw_video', 'tools/discover-museum-videos.py')
music = module('mhw_music', 'content/expansion/soundtrack-broad-pipeline.py')
playlist = json.loads((F / 'mhw-original-archive-playlist.json').read_text(encoding='utf8'))
label = json.loads((F / 'mhw-original-label-album.json').read_text(encoding='utf8'))
rows, published = playlist['entries'][1:], label['results'][1:]
assert len(rows) == len(published) == 83
assert playlist['entries'][0]['id'] == '-yEL0ZrpzE8'
records, failures = [], 0
for number, (row, song) in enumerate(zip(rows, published), 1):
    result = {'youtube_id': row['id'], 'playlist_title': row['title'], 'album_ordinal': number,
              'published_title': song['trackName'], 'label_artist_credit': song['artistName']}
    try:
        native, watch = video.metadata(row['id'], row), music.watch(row['id'])
        assert native['native_compatible_avc_aac']
        assert native['channel_id'] == watch['channelId'] == 'UCFQh_mbkLL1Chm0HrU0YWHA'
        assert native['title'] == watch['title'] == row['title']
        assert native['duration'] == float(watch['lengthSeconds'])
        assert 'Monster Hunter World OST:' in native['title']
        result.update(status='verified_pending_semantic_peer', metadata=native,
                      exact_label_title_substring=unicodedata.normalize('NFKC', song['trackName']) in unicodedata.normalize('NFKC', row['title']))
        failures = 0
    except Exception as error:
        result.update(status='held', reason=str(error))
        failures += 1
    records.append(result)
    (F / 'mhw-original-native-research.json').write_text(json.dumps({'records': records, 'audio_downloaded': False}, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(number, result['status'], row['title'], flush=True)
    if failures >= 3:
        break
