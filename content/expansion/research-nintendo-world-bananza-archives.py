"""Resume safe identity/codec discovery for two archival Nintendo collections.

This file does not publish, declare completeness, or label uploaders official.
The published Nintendo Music inventories are separate reconciliation targets.
"""
import concurrent.futures
import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/nintendo-full'
spec = importlib.util.spec_from_file_location('reader', ROOT / 'content/expansion/research-botw-cd-individuals.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
name = sys.argv[1]
filename = {'mkworld': 'mkworld-wiiplayz-public-flat-playlist.json',
            'bananza': 'bananza-ambigamer-public-flat-playlist.json',
            'mkworld-clean-grandprix': 'mkworld-nintendo-channel-grandprix-public-flat-playlist.json',
            'mkworld-clean-freeroam': 'mkworld-nintendo-channel-freeroam-public-flat-playlist.json',
            'mkworld-koopasaurus-core': 'mkworld-koopasaurus-core-selected-public-videos.json'}[name]
source = json.loads((OUT / filename).read_text(encoding='utf-8'))
reader.cache_dir = OUT / (name + '-archive-individuals')
reader.cache_dir.mkdir(exist_ok=True)
selections = []
held_source_entries = []
for index, entry in enumerate(source['entries'], 1):
    if not entry.get('title') or not entry.get('duration') or not entry.get('channel'):
        held_source_entries.append({'number': index, 'youtube_id': entry['id'], 'reason': 'No actual public title/duration/channel in playlist metadata.'})
        continue
    selections.append({'album_track_number': index, 'title': entry['title'],
                       'expected_seconds': entry['duration'], 'source': entry,
                       'alias_context': 'Playlist ordinal only, NOT a published-album track number. Actual playlist identity and duration checked; Nintendo Music composition/version reconciliation remains separate.'})
rows = []
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    for row in pool.map(reader.read, selections):
        rows.append(row)
        reader.pipeline.write(OUT / (name + '-archive-publication-research.json'), {
            'publication_status': 'research_only',
            'source_playlist': filename,
            'playlist_count': len(source['entries']),
            'held_playlist_entries': held_source_entries,
            'scope': 'Individual archival publication identity and native codec only. No publisher-upload, primary cue-authorship, published album equivalence or game-score exhaustiveness claim.',
            'tracks': rows,
        })
        print(name, row['album_track_number'], row['source']['id'], row['status'], flush=True)
