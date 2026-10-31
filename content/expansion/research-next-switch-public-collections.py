"""Bounded resume-safe public score metadata, with per-collection failure breaker."""
import concurrent.futures
import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/nintendo-full'
spec = importlib.util.spec_from_file_location('reader', ROOT / 'content/expansion/research-botw-cd-individuals.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
reader.cache_dir = OUT / 'next-switch-public-individuals'
reader.cache_dir.mkdir(exist_ok=True)
selected = []
for key, title, year, entry_id in [
    ('echoes', 'The Legend of Zelda: Echoes of Wisdom', 2024, 'wikipedia-77176762'),
    ('mk8booster', 'Mario Kart 8', 2014, 'wikipedia-38323830'),
    ('calamity', 'Hyrule Warriors: Age of Calamity', 2020, ''),
]:
    playlist = json.loads((OUT / f'next-{key}-public-playlist-flat.json').read_text(encoding='utf-8'))['entries']
    for index, source in enumerate(playlist, 1):
        if not source.get('title'):
            continue
        assert source['channel'] == 'The Nintendo Music Channel'
        selected.append({'collection': key, 'source_playlist_position': index,
                         'game_title': title, 'game_year': year, 'entry_id': entry_id,
                         'title': source['title'].split(' — ', 1)[0],
                         'source': source, 'expected_seconds': source['duration']})


if __name__ == '__main__':
    rows, skipped = [], []
    failures, consecutive_failures, blocked = {}, {}, set()
    iterator = iter(selected)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        pending = {}
        exhausted = False
        while pending or not exhausted:
            while len(pending) < 2 and not exhausted:
                try:
                    selection = next(iterator)
                except StopIteration:
                    exhausted = True
                    break
                if selection['collection'] in blocked:
                    skipped.append({'collection': selection['collection'], 'id': selection['source']['id'],
                                    'reason': 'Not requested after repeated native unavailability; this is not proof this individual video is unavailable.'})
                    continue
                pending[pool.submit(reader.read, selection)] = selection
            if not pending:
                continue
            completed, _ = concurrent.futures.wait(pending, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in completed:
                selection = pending.pop(future)
                row = future.result()
                rows.append(row)
                error = row.get('error', '')
                if 'Unsigned app player:' in error or row['status'] == 'codec_hold':
                    key = row['collection']
                    failures[key] = failures.get(key, 0) + 1
                    consecutive_failures[key] = consecutive_failures.get(key, 0) + 1
                    if consecutive_failures[key] >= 6:
                        blocked.add(key)
                else:
                    consecutive_failures[row['collection']] = 0
                reader.pipeline.write(OUT / 'next-switch-public-collections-research.json', {
                    'publication_status': 'research_only', 'tracks': rows, 'not_requested_after_breaker': skipped,
                    'native_failure_counts': failures, 'blocked_collections': sorted(blocked),
                    'scope': 'Available public archive recordings with honest collective game-score credits planned. No exhaustive album-order/master perfection or authenticated-download workaround.',
                })
                print(row['collection'], row['source_playlist_position'], row['source']['id'], row['status'], error, flush=True)
        reader.pipeline.write(OUT / 'next-switch-public-collections-research.json', {
            'publication_status': 'research_only', 'tracks': rows, 'not_requested_after_breaker': skipped,
            'native_failure_counts': failures, 'blocked_collections': sorted(blocked),
            'scope': 'Available public archive recordings; unrequested items after repeated native failures are not described as individually unavailable. No download/auth workaround.',
        })
