"""Available unextended original-game/mode recordings, excluding fan edits."""
import concurrent.futures
import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/nintendo-full'
spec = importlib.util.spec_from_file_location('reader', ROOT / 'content/expansion/research-botw-cd-individuals.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
reader.cache_dir = OUT / 'luigi3-public-individuals'
reader.cache_dir.mkdir(exist_ok=True)
raw = json.loads((OUT / 'luigi3-metaru-public-flat-raw.json').read_text(encoding='utf-16'))
selected, excluded = [], []
for index, item in enumerate(raw['entries'], 1):
    title = item.get('title') or ''
    if "Luigi's Mansion 3 Music" not in title or any(word in title.casefold() for word in ['extended', 'remix', 'cover', 'mashup']):
        excluded.append({'id': item['id'], 'title': title, 'reason': 'Extended duplicate or fan edit, outside this unextended game-score collection.'})
        continue
    assert item['channel'] == "Metaru's Mansion"
    source = {key: item.get(key) for key in ['id', 'title', 'channel', 'channel_id', 'duration', 'url']}
    selected.append({'collection': 'luigi3', 'source_playlist_position': index, 'source': source,
                     'expected_seconds': source['duration']})
assert len(selected) == len({row['source']['id'] for row in selected}) == 321

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
            done, _ = concurrent.futures.wait(pending, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                pending.pop(future)
                row = future.result()
                rows.append(row)
                error = row.get('error', '')
                consecutive = consecutive + 1 if 'Unsigned app player:' in error or row['status'] == 'codec_hold' else 0
                reader.pipeline.write(OUT / 'luigi3-available-publication-research.json', {
                    'publication_status': 'research_only', 'tracks': rows,
                    'not_requested_after_breaker': skipped, 'excluded_extended_edits': excluded,
                    'scope': 'Available unextended original game/mode-score publications, not a certified edited commercial album or exhaustive-game inventory.'})
                print(row['source_playlist_position'], row['source']['id'], row['status'], error, flush=True)
