"""Resume-safe metadata-only verification of original KHII two-disc album."""
import concurrent.futures
import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/kingdom-hearts-complete'
spec = importlib.util.spec_from_file_location('reader', ROOT / 'content/expansion/research-botw-cd-individuals.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
reader.cache_dir = OUT / 'kh2-original89-individuals'
reader.cache_dir.mkdir(exist_ok=True)
inventory = json.loads((OUT / 'kh2-original89-secondary-inventory.json').read_text(encoding='utf-8'))['tracks']
playlist = json.loads((OUT / 'kh2-kaiyo-original-playlist-flat.json').read_text(encoding='utf-8'))['entries']
search = json.loads((OUT / 'followup-original-search-1.json').read_text(encoding='utf-8'))['entries']
sources = {row['id']: row for row in search}
selected = []
for expected, source in zip(inventory, playlist):
    if expected['number'] == 3:
        source = sources['_bLznocUuI0']
    elif expected['number'] == 84:
        source = sources['3-pLiM970L8']
    assert source['title'] and source['channel']
    assert abs(source['duration'] - expected['duration_seconds']) <= 4
    selected.append({'album_track_number': expected['number'], 'expected': expected,
                     'source': source, 'expected_seconds': source['duration']})

if __name__ == '__main__':
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for row in pool.map(reader.read, selected):
            rows.append(row)
            reader.pipeline.write(OUT / 'kh2-original89-individual-publication-research.json', {
                'publication_status': 'research_only', 'tracks': rows,
                'scope': 'Actual individual archive candidates for original2006 two-disc89item album, not HD rerecordings or arbitrary reconstructed timestamps. Exact cue roles require original printed booklet verification before publication.',
            })
            print(row['album_track_number'], row['source']['id'], row['status'], row.get('error', ''), flush=True)
