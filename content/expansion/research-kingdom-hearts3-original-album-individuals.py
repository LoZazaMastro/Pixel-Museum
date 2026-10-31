"""Verify public original-label album recordings; never include other-game disc8."""
import concurrent.futures
import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/kingdom-hearts-complete'
spec = importlib.util.spec_from_file_location('r', ROOT / 'content/expansion/reconcile-kingdom-hearts-original-albums.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
spec = importlib.util.spec_from_file_location('reader', ROOT / 'content/expansion/research-botw-cd-individuals.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
reader.cache_dir = OUT / 'kh3-original-album-individuals'
reader.cache_dir.mkdir(exist_ok=True)
playlist = json.loads((OUT / 'kh3-official-digital-combined-album-flat.json').read_text(encoding='utf-8'))['entries']
by_id = {row['id']: row for row in playlist}
aliases = {
    (1, 1): ('kiQxfZg7Z68', 'Japanese CHIKAI / English Don\'t Think Twice title aliases for the same instrumental composition; public label uses CHIKAI.'),
    (1, 3): ('YpcnL2lFK_g', 'Official audio-only publisher title gives the whole album name instead of explicit III-version subtitle; exact album slot and source retained.'),
    (4, 5): ('84jjnI6M2UI', 'Official Disney original Japanese licensed film-song recording by Takako Matsu; reused in KHIII. Full publisher music-video version retained, no fabricated CD edit or game-capture claim.'),
    (6, 13): ('tJH-7u4kAyw', 'Japanese HIKARI / English SIMPLE AND CLEAN title aliases for the same instrumental composition; public label uses HIKARI.'),
}
selected, holds = [], []
number = 0
for expected in r.kh3_inventory():
    if expected['disc'] > 7:
        continue
    number += 1
    key = (expected['disc'], expected['disc_track'])
    if key == (1, 4):
        holds.append({'album_track_number': number, 'expected': expected,
                      'reason': 'Japanese Face My Fears vocal not present in this region\'s public official digital album playlist; do not silently substitute English/live/fan remix.'})
        continue
    if key in aliases:
        video_id, context = aliases[key]
        source = by_id[video_id]
    else:
        matches = [row for row in playlist if r.norm(row['title']) == r.norm(expected['title'])]
        assert len(matches) == 1, (expected, matches)
        source, context = matches[0], 'Exact normalized title in the actual original publisher product tracklist and public label album playlist.'
    selected.append({'album_track_number': number, 'expected': expected, 'source': source,
                     'expected_seconds': source['duration'], 'identity_context': context})
assert len(selected) == 136 and len({row['source']['id'] for row in selected}) == 136

if __name__ == '__main__':
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for row in pool.map(reader.read, selected):
            rows.append(row)
            reader.pipeline.write(OUT / 'kh3-original136-individual-publication-research.json', {
                'publication_status': 'research_only', 'tracks': rows, 'holds': holds,
                'primary_album_inventory_expected_kh3_remind_tracks': 137,
                'other_game_disc8_tracks_excluded': 22,
                'scope': 'Exact2020 publisher album title mapping and actual official recording metadata;1Japanese vocal still unresolved. CHIKAI/HIKARI instrumental aliases and Japanese licensed Frozen source versions explicit; no complete-master/fingerprint claim.',
            })
            print(row['album_track_number'], row['source']['id'], row['status'], row.get('error', ''), flush=True)
