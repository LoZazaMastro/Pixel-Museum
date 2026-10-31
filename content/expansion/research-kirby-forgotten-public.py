"""Verify available original2022 archive recordings; no DLC or cover substitutions."""
import concurrent.futures
import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/nintendo-full'
spec = importlib.util.spec_from_file_location('reader', ROOT / 'content/expansion/research-botw-cd-individuals.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
reader.cache_dir = OUT / 'kirby-forgotten-public-individuals'
reader.cache_dir.mkdir(exist_ok=True)
load = lambda path: json.loads(path.read_text(encoding='utf-8'))
raw_path = OUT / 'kirby-forgotten-land-raw-flat.json'
raw = json.loads(raw_path.read_text(encoding='utf-16'))
playlist = {'id': raw['id'], 'title': raw['title'], 'entries': [
    {key: value.get(key) for key in ['id', 'title', 'channel', 'channel_id', 'duration', 'url']}
    for value in raw['entries'] if value.get('title')]}
reader.pipeline.write(OUT / 'kirby-forgotten-land-public-flat.json', playlist)
selected = []
for index, source in enumerate(playlist['entries'], 1):
    assert source['channel'] == 'J.O.E. VGM'
    assert 'Kirby and the Forgotten Land OST' in source['title']
    selected.append({'collection': 'kirby-forgotten', 'source_playlist_position': index,
                     'game_title': 'Kirby and the Forgotten Land', 'game_year': 2022,
                     'entry_id': 'wikipedia-69752856', 'source': source,
                     'title': source['title'].split(' - Kirby and the Forgotten Land OST')[0],
                     'expected_seconds': source['duration']})

if __name__ == '__main__':
    rows, skipped = [], []
    consecutive = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        iterator = iter(selected)
        pending = {}
        exhausted = False
        while pending or not exhausted:
            while len(pending) < 2 and not exhausted:
                try:
                    selection = next(iterator)
                except StopIteration:
                    exhausted = True
                    break
                if consecutive >= 6:
                    skipped.append({'id': selection['source']['id'], 'reason': 'Not requested after consecutive native failures; not individually assessed.'})
                    continue
                pending[pool.submit(reader.read, selection)] = selection
            if not pending:
                continue
            completed, _ = concurrent.futures.wait(pending, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in completed:
                pending.pop(future)
                row = future.result()
                rows.append(row)
                error = row.get('error', '')
                consecutive = consecutive + 1 if 'Unsigned app player:' in error or row['status'] == 'codec_hold' else 0
                reader.pipeline.write(OUT / 'kirby-forgotten-public-research.json', {
                    'publication_status': 'research_only', 'tracks': rows, 'not_requested_after_breaker': skipped,
                    'scope': 'Original2022 public archival recordings; Star-CrossedWorld/Switch2 additions and fan covers excluded. No complete-master or physical-console claim.'})
                print(row['source_playlist_position'], row['source']['id'], row['status'], error, flush=True)
