"""Actual public official album videos; curated playlist membership alone is insufficient."""
import concurrent.futures
import importlib.util
import json
import pathlib
import re
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/spider-complete'
load = lambda path: json.loads(path.read_text(encoding='utf-8'))
spec = importlib.util.spec_from_file_location('reader', ROOT / 'content/expansion/research-botw-cd-individuals.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
reader.cache_dir = OUT / 'official-album-individuals'
reader.cache_dir.mkdir(exist_ok=True)


def norm(value):
    value = re.sub(r'^John Paesano - ', '', value or '')
    value = re.sub(r'\(From.*$', '', value)
    value = re.sub(r'\(Album Version\)', '', value)
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', value).casefold())


selected = []
for album in load(OUT / 'original-three-albums-inventory.json')['albums']:
    year = album['year']
    playlist = load(OUT / (f'{year}-label-publications-playlist-flat.json' if year == 2020 else f'{year}-official-publications-playlist-flat.json'))['entries']
    for index, expected in enumerate(album['tracks'], 1):
        source = None
        if year == 2020 and index in [18, 19]:
            search = load(OUT / f'licensed-final-{index - 18}-search.json')['entries']
            source = next(row for row in search if row['id'] == {18: 'OUSjNiAkx9o', 19: 'DTakCndtK4s'}[index])
        elif year == 2023 and index == 20:
            # The first playlist item is a74sec teaser. Select the actual full audio publication instead.
            source = next(row for row in playlist if row['id'] == 'LB-yamBsDHU')
        elif year == 2023 and index == 21:
            source = next(row for row in playlist if row['id'] == '-lAV1KkqTD0')
        else:
            matches = [row for row in playlist if norm(row['title']) == norm(expected['item_name'])]
            assert len(matches) == 1, (year, expected['item_name'], matches)
            source = matches[0]
        assert source['channel'] in ['John Paesano', 'MarvelMusicVEVO', 'Lecrae', 'Jaden'], source
        selected.append({'album_track_number': index, 'game_year': year, 'entry_id': album['entry_id'],
                         'game_title': album['title'], 'album_primary_source': album['url'],
                         'expected': expected, 'source': source, 'expected_seconds': source['duration']})
assert len(selected) == 67

if __name__ == '__main__':
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for row in pool.map(reader.read, selected):
            rows.append(row)
            reader.pipeline.write(OUT / 'three-public-albums67-publication-research.json', {
                'publication_status': 'research_only', 'tracks': rows,
                'scope': 'Real official/artist public recordings corresponding to27/19/21 published album cues, plus explicit official music-video/Surkin versions where named. Unreleased collector additions, wrong films and74sec Swing teaser excluded. No audio fingerprint or physical-console claim.',
            })
            print(row['game_year'], row['album_track_number'], row['source']['id'], row['status'], row.get('error', ''), flush=True)
