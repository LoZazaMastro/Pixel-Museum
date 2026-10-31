"""Actual public composer/publisher playlists, with cached native-failure holds."""
import concurrent.futures
import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/modern-public-albums'
spec = importlib.util.spec_from_file_location('reader', ROOT / 'content/expansion/research-botw-cd-individuals.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
name = sys.argv[1]
profiles = {'expedition33': ('expedition33-official-flat-raw.json', 'Sandfall Interactive'),
            'baldursgate3': ('baldursgate3-composer-flat-raw.json', 'Borislav Slavov (Bobby)'),
            'ghosttsushima': ('ghosttsushima-sony-flat-raw.json', {'Ilan Eshkeri', 'Shigeru Umebayashi - Topic', 'SonySoundtracksVEVO'}),
            'bayonetta3': ('bayonetta3-official-digital-flat-raw.json', {'BAYONETTA 3 - Topic', 'Release - Topic', 'Mikaila Delgado - Topic', 'helenaofficiel'}),
            'ff7rebirth': ('ff7rebirth-official-full-flat-raw.json', {'【公式】植松伸夫TV', 'Mitsuto Suzuki - Topic', 'Masashi Hamauzu - Topic', 'Release - Topic', 'Shotaro Shima - Topic', 'Yoshinori Nakamura - Topic', 'Tadayoshi Makino - Topic', 'Yoshitaka Suzuki', 'Shingo Kataoka - Topic', 'SQUARE ENIX MUSIC Channel'}),
            'acvalhalla': ('acvalhalla-ubisoft-flat-raw.json', {'Sarah Schachner', 'JesperKyd', 'Max Aruj - Topic', 'Einar Selvik - Topic', 'Lakeshore Records', 'Ubisoft Music'}),
            'outerwilds': ('outerwilds-artist-album-flat-raw.json', {'Andrew Prahlow - Topic'}),
            'ff16': ('ff16-square-official-flat-raw.json', {'SQUARE ENIX MUSIC Channel'}),
            'hfw': ('hfw-sony-official-flat-raw.json', {'SonySoundtracksVEVO'}),
            'kirbystarallies': ('kirbystarallies-original-flat-raw.json', {'Eternal', 'KIRBY CHANNEL'}),
            'splatoon3': ('splatoon3-splatune-flat-raw.json', None),
            'discoelysium': ('discoelysium-public-flat-raw.json', {'Sea Power'})}
filename, author = profiles[name]
reader.cache_dir = OUT / (name + '-public-individuals')
reader.cache_dir.mkdir(exist_ok=True)
raw = json.loads((OUT / filename).read_text(encoding='utf-16'))
selected, excluded = [], []
seen_ids = set()
for index, item in enumerate(raw['entries'], 1):
    if item['id'] in seen_ids:
        excluded.append({'id': item['id'], 'title': item['title'], 'reason': 'Duplicate video ID within the public source playlist; first occurrence retained.'})
        continue
    seen_ids.add(item['id'])
    if name == 'splatoon3' and not item.get('channel'):
        excluded.append({'id': item['id'], 'title': item['title'], 'reason': 'Private/unavailable source presentation, not claimed absent from game music.'})
        continue
    if name == 'discoelysium' and item.get('channel') != 'Sea Power':
        excluded.append({'id': item['id'], 'title': item['title'], 'reason': 'Private/unavailable or third-party source outside this original artist collection.'})
        continue
    if name == 'baldursgate3' and item['title'].startswith('*Remix*'):
        excluded.append({'id': item['id'], 'title': item['title'], 'reason': 'Composer-issued symphonic song remix omitted from this score-oriented collection; not labeled a fake fan upload.'})
        continue
    if author is not None:
        assert item['channel'] in (author if isinstance(author, set) else {author}), (name, item['channel'])
    source = {key: item.get(key) for key in ['id', 'title', 'channel', 'channel_id', 'duration', 'url']}
    selected.append({'collection': name, 'source_playlist_position': index, 'source': source,
                     'expected_seconds': source['duration']})
assert len(selected) == len({row['source']['id'] for row in selected})
rows, skipped = [], []
consecutive = 0
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    iterator = iter(selected)
    pending, exhausted = {}, False
    while pending or not exhausted:
        while len(pending) < 2 and not exhausted:
            try:
                selection = next(iterator)
            except StopIteration:
                exhausted = True
                break
            if consecutive >= 6:
                skipped.append({'id': selection['source']['id'], 'reason': 'Not requested after six consecutive native failures.'})
                continue
            pending[pool.submit(reader.read, selection)] = selection
        if not pending:
            continue
        done, _ = concurrent.futures.wait(pending, return_when=concurrent.futures.FIRST_COMPLETED)
        for future in done:
            pending.pop(future)
            row = future.result()
            rows.append(row)
            error = row.get('error', '')
            consecutive = consecutive + 1 if 'Unsigned app player:' in error or row['status'] == 'codec_hold' else 0
            reader.pipeline.write(OUT / (name + '-available-publication-research.json'), {
                'publication_status': 'research_only', 'tracks': rows, 'not_requested_after_breaker': skipped,
                'excluded_recordings': excluded,
                'scope': 'Available real composer/publisher recordings; actual individual title/author/description/duration and unsigned native AVC/AAC. No media download or physical console assertion.'})
            print(name, row['source_playlist_position'], row['source']['id'], row['status'], error, flush=True)
