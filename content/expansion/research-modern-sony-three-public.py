"""Use available real publisher/artist uploads; reject hijacked playlist padding."""
import concurrent.futures
import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/modern-public-albums'
spec = importlib.util.spec_from_file_location('reader', ROOT / 'content/expansion/research-botw-cd-individuals.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
reader.cache_dir = OUT / 'sony-three-public-individuals'
reader.cache_dir.mkdir(exist_ok=True)
selected, excluded = [], []
for key, entry_id, game_title, year in [
    ('gow2018', 'wikipedia-50810460', 'God of War', 2018),
    ('ragnarok', 'wikipedia-65333536', 'God of War Ragnar\u00f6k', 2022),
    ('returnal', 'workbook-04-30-returnal', 'Returnal', 2021),
]:
    raw = json.loads((OUT / (key + '-public-flat-raw.json')).read_text(encoding='utf-16'))
    for index, source in enumerate(raw['entries'], 1):
        title = source.get('title') or ''
        channel = source.get('channel') or ''
        if key == 'returnal':
            accepted = channel == 'Bobby Krlic'
        elif key == 'gow2018':
            accepted = (channel == 'Bear McCreary, Composer' and '(From "God of War" Soundtrack)' in title or
                        channel == 'SonySoundtracksVEVO' and 'God of War (PlayStation Soundtrack)' in title)
        else:
            accepted = channel == 'SonySoundtracksVEVO' and 'God of War Ragnar\u00f6k' in title
        if not accepted:
            excluded.append({'collection': key, 'youtube_id': source['id'], 'title': title,
                             'reason': 'Not the exact game official album/artist recording; playlist padding, different sequel, fan performance or unrelated publication.'})
            continue
        source = {key: source.get(key) for key in ['id', 'title', 'channel', 'channel_id', 'duration', 'url']}
        selected.append({'collection': key, 'source_playlist_position': index, 'game_title': game_title,
                         'game_year': year, 'entry_id': entry_id, 'source': source,
                         'expected_seconds': source['duration']})

if __name__ == '__main__':
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for row in pool.map(reader.read, selected):
            rows.append(row)
            reader.pipeline.write(OUT / 'sony-three-publication-research.json', {
                'publication_status': 'research_only', 'tracks': rows, 'excluded_playlist_padding': excluded,
                'scope': 'Available official publisher/artist recordings only; not an exhaustive album-order investigation. Mixed/hijacked collector playlist padding removed before acquisition.'})
            print(row['collection'], row['source']['id'], row['status'], row.get('error', ''), flush=True)
