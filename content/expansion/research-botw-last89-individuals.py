"""Replace every remaining compilation passage by a full individual cue."""
import concurrent.futures
import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/nintendo-full'
spec = importlib.util.spec_from_file_location('reader', ROOT / 'content/expansion/research-botw-cd-individuals.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
reader.cache_dir = OUT / 'botw-last89-individuals'
reader.cache_dir.mkdir(exist_ok=True)
selections = json.loads((OUT / 'botw-last89-individuals-selected-research.json').read_text(encoding='utf-8'))['tracks']
rows = []
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    for row in pool.map(reader.read, selections):
        rows.append(row)
        reader.pipeline.write(OUT / 'botw-last89-individual-publication-research.json', {
            'publication_status': 'research_only', 'tracks': rows,
            'scope': 'Actual individual original-game score recordings, matched to the remaining89publishedalbumcompositions; no synthetic boundaries or CDmasterfingerprint assertion.',
        })
        print(row['album_track_number'], row['source']['id'], row['status'], flush=True)
