"""Available original game and explicitly labelled Torna DLC archive recordings."""
import concurrent.futures
import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/nintendo-full'
spec = importlib.util.spec_from_file_location('reader', ROOT / 'content/expansion/research-botw-cd-individuals.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
reader.cache_dir = OUT / 'xenoblade2-public-individuals'
reader.cache_dir.mkdir(exist_ok=True)
raw = json.loads((OUT / 'xenoblade2-joevgm-public-flat-raw.json').read_text(encoding='utf-16'))
selected, held = [], []
for index, item in enumerate(raw['entries'], 1):
    assert item['channel'] == 'J.O.E. VGM'
    if '(beta)' in item['title'].lower():
        held.append({'id': item['id'], 'reason': 'Explicit beta recording, excluded from original release collection.'})
        continue
    source = {key: item.get(key) for key in ['id', 'title', 'channel', 'channel_id', 'duration', 'url']}
    selected.append({'collection': 'xenoblade2', 'source_playlist_position': index, 'source': source,
                     'expected_seconds': source['duration']})
if __name__ == '__main__':
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for row in pool.map(reader.read, selected):
            rows.append(row)
            reader.pipeline.write(OUT / 'xenoblade2-available-publication-research.json', {
                'publication_status': 'research_only', 'tracks': rows, 'excluded_beta_publication': held,
                'scope': 'Original2017 game and explicitly labelled2018Torna official expansion recordings; no all-album completeness or physical-console assertion.'})
            print(row['source_playlist_position'], row['source']['id'], row['status'], row.get('error', ''), flush=True)
