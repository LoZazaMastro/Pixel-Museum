"""Actual original artist uploads,21 OST cues; no fan B-sides substituted."""
import concurrent.futures
import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/modern-public-albums'
spec = importlib.util.spec_from_file_location('reader', ROOT / 'content/expansion/research-botw-cd-individuals.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
reader.cache_dir = OUT / 'celeste-artist-individuals'
reader.cache_dir.mkdir(exist_ok=True)
raw = json.loads((OUT / 'celeste-artist-flat-raw.json').read_text(encoding='utf-16'))
selected = []
for index, item in enumerate(raw['entries'], 1):
    assert item['channel'] == 'Lena Raine'
    source = {key: item.get(key) for key in ['id', 'title', 'channel', 'channel_id', 'duration', 'url']}
    selected.append({'collection': 'celeste', 'source_playlist_position': index, 'source': source,
                     'expected_seconds': source['duration']})
if __name__ == '__main__':
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for row in pool.map(reader.read, selected):
            rows.append(row)
            reader.pipeline.write(OUT / 'celeste-artist21-publication-research.json', {
                'publication_status': 'research_only', 'tracks': rows,
                'scope': 'Actual LenaRaine original2018 artist videos; game version identity and unsignednativecodec, no media downloads or console-playback claim.'})
            print(row['source_playlist_position'], row['source']['id'], row['status'], row.get('error', ''), flush=True)
