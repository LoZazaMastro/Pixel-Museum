"""Verify publicly indexed longer original-game loops; never fake album edits."""
import concurrent.futures
import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/nintendo-full'
spec = importlib.util.spec_from_file_location('reader', ROOT / 'content/expansion/research-botw-cd-individuals.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
reader.cache_dir = OUT / 'mkworld-final-core-loop-individuals'
reader.cache_dir.mkdir(exist_ok=True)

by_id = {row['id']: row for row in json.loads((OUT / 'mkworld-preston-public-flat-playlist.json').read_text(encoding='utf-8'))['entries']}
for index in range(11):
    for row in json.loads((OUT / ('mkworld-final-core-gap-search-' + str(index) + '.json')).read_text(encoding='utf-8'))['entries']:
        by_id[row['id']] = row
inventory = {row['number']: row for row in json.loads((OUT / 'mkworld-nintendo-music-secondary-inventory.json').read_text(encoding='utf-8'))['tracks']}
selected = []
for number, video_id in [
    (105, 'jnTl2qepOgw'), (106, '-_pucK3eVkE'), (107, 'lwqN6imZT9I'),
    (108, 'nM_YCfZy_E0'), (109, 'BsUwYxXqTyY'), (110, 'lk6XQor6iks'),
    (113, 'Ojo8cylipIc'), (114, '7dXqBSb1gUY'), (115, 'Uxvmdb2XkPk'),
    (116, 're_c9yiwf4Y'), (117, 'Pr8LrKoJfIs'),
]:
    source = by_id[video_id]
    assert source['channel'] == 'Mario Kart Music Channel'
    selected.append({'album_track_number': number, 'title': inventory[number]['title'],
                     'expected_seconds': source['duration'], 'source': source,
                     'inventory_expected_duration_seconds': inventory[number]['length_seconds'],
                     'alias_context': 'Public original-game archival LOOP version, longer than edited Nintendo Music version. Actual duration retained without invented cut points; publisher master equivalence explicitly NOT asserted.'})

if __name__ == '__main__':
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for row in pool.map(reader.read, selected):
            rows.append(row)
            reader.pipeline.write(OUT / 'mkworld-final-core-loops-publication-research.json', {
                'publication_status': 'research_only', 'tracks': rows,
                'scope': 'Eleven original-game loop versions, NOT the shorter edited Nintendo Music masters. Requires independent identity/source review; no automatic full-album claim.'})
            print(row['album_track_number'], row['source']['id'], row['status'], row.get('error', ''), flush=True)
