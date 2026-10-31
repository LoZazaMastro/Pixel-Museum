"""Verify available public original-score videos; no exhaustive title-alias hunt."""
import concurrent.futures
import importlib.util
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/nintendo-full'
spec = importlib.util.spec_from_file_location('reader', ROOT / 'content/expansion/research-botw-cd-individuals.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
reader.cache_dir = OUT / 'totk-public9cd-individuals'
reader.cache_dir.mkdir(exist_ok=True)
playlist = json.loads((OUT / 'next-totk9cd-public-playlist-flat.json').read_text(encoding='utf-8'))['entries']
inventory = json.loads((ROOT / 'build/research/soundtrack-broad/nintendo-complete-priority/totk344-localized-inventory-candidate.json').read_text(encoding='utf-8'))['tracks']
by_key = {(row['disc'], row['track']): row for row in inventory}
selected = []
for source in playlist:
    match = re.match(r'^(\d+)\.(\d+)\s+(.+?)\s+[—–]\s*.*Tears of the Kingdom', source['title'])
    correction = ''
    if match:
        disc, number, title = int(match[1]), int(match[2]), match[3]
        if (disc, number) == (6, 52):
            assert title == "Link's Humming 6"
            disc, number = 9, 52
            correction = 'Uploader label6.52 is a typo; actual named Link humming6 corresponds to9.52, not a nonexistent disc6track52.'
    else:
        assert source['title'].startswith(('2nd Trailer BGM (5.1 Audio)', '3rd Trailer BGM (5.1 Audio)'))
        disc, number = 9, 66 if source['title'].startswith('2nd') else 67
        title = source['title'].split(' — ', 1)[0]
        correction = 'Bonus trailer publication omits the CD index and explicitly declares5.1 audio version; original public version retained, no master-equivalence claim.'
    reference = by_key[(disc, number)]
    seconds = sum(int(value) * (60 ** index) for index, value in enumerate(reversed(reference['length'].split(':'))))
    assert source['channel'] == 'The Nintendo Music Channel'
    selected.append({'album_track_number': len(selected) + 1, 'disc': disc, 'disc_track': number,
                     'title': title, 'source': source, 'expected_seconds': source['duration'],
                     'primary_album_index_reference': {'disc': disc, 'track': number,
                                                      'localized_reference_title': reference['title'],
                                                      'reference_seconds': seconds},
                     'reference_duration_delta_seconds': source['duration'] - seconds,
                     'source_index_context': correction,
                     'credit_scope': 'Nintendo sound team game-level collective; community per-cue author transcription is not silently promoted as independent primary proof.'})
assert len(selected) == len({(row['disc'], row['disc_track']) for row in selected}) == 344

if __name__ == '__main__':
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for row in pool.map(reader.read, selected):
            rows.append(row)
            reader.pipeline.write(OUT / 'totk-public344-individual-publication-research.json', {
                'publication_status': 'research_only', 'tracks': rows,
                'scope': 'Actual public344item nine-disc collection; individual availability verified without private-auth workarounds. Minor localized-title spelling/order perfection not a publication prerequisite. No master fingerprint or all-in-game-variant completeness claim.',
            })
            print(row['album_track_number'], row['source']['id'], row['status'], row.get('error', ''), flush=True)
