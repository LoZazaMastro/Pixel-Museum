"""Verify the publisher's22 actual original soundtrack videos."""
import concurrent.futures
import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/modern-public-albums'
spec = importlib.util.spec_from_file_location('reader', ROOT / 'content/expansion/research-botw-cd-individuals.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
reader.cache_dir = OUT / 'bastion-publisher-individuals'
reader.cache_dir.mkdir(exist_ok=True)
raw = json.loads((OUT / 'bastion-official-flat-raw.json').read_text(encoding='utf-16'))
selected = []
for index, item in enumerate(raw['entries'], 1):
    assert item['channel'] == 'Supergiant Games'
    source = {key: item.get(key) for key in ['id', 'title', 'channel', 'channel_id', 'duration', 'url']}
    selected.append({'collection': 'bastion', 'source_playlist_position': index, 'source': source,
                     'expected_seconds': source['duration']})
if __name__ == '__main__':
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for row in pool.map(reader.read, selected):
            rows.append(row)
            reader.pipeline.write(OUT / 'bastion-publisher22-publication-research.json', {
                'publication_status': 'research_only', 'tracks': rows,
                'scope': 'Real original publisher soundtrack videos, no archive/fan substitution or media downloads.'})
            print(row['source_playlist_position'], row['source']['id'], row['status'], row.get('error', ''), flush=True)
