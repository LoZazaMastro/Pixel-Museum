"""Append the exact57 independently reviewed phased cues to the reviewed274."""
import copy
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/nintendo-full'
DEST = ROOT / 'content/expansion/soundtrack-multitrack-priority-overrides.json'
load = lambda p: json.loads(p.read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
candidate_path = OUT / 'mkworld-distinct57-core-candidate.json'
review_path = OUT / 'independent-mkworld57-risk15-review.json'
review = load(review_path)
assert sha(candidate_path) == review['candidate_sha256'] == 'f4a2298e12669677723fa493779ec377adddd85465ff14d02b5bc66d82a01e50'
assert review['status'] == 'BOUNDED_IDENTITY_CREDIT_SCOPE_PASS'
candidate = load(candidate_path)
assert sha(DEST) == candidate['requires_base_module_sha256'] == 'e17d21ab1d6dabe62cef44d7679c88b22ed91b807d026dba85b6239a64797997'
module = load(DEST)
before = copy.deepcopy(module)
entry = next(entry for entry in module['entries'] if entry['entry_id'] == 'wikipedia-79613463')
assert len(entry['tracks']) == 274
addition = candidate['entries'][0]['tracks']
assert len(addition) == 57
entry['tracks'].extend(copy.deepcopy(addition))
assert len(entry['tracks']) == len({track['youtube_id'] for track in entry['tracks']}) == len({track['title'] for track in entry['tracks']}) == 331
entry['completeness'].update(verified_archival_recordings=331, separately_reviewed_supplemental_cues=78)
entry['recording_collection_scope'] = '331 individually identified game-score archival recordings, including separately reviewed race intros, DK Spaceport laps, Rainbow Road phases, cup openings, title/menu, battle and fanfare cues. This remains partial versus the348-name Nintendo Music research inventory; versions, loops and fades are disclosed and publisher-master identity is not asserted.'
entry['independent_review_receipt'].append(str(review_path.relative_to(ROOT)).replace('\\', '/'))
for old, new in zip(before['entries'], module['entries']):
    if old['entry_id'] != entry['entry_id']:
        assert old == new
    else:
        assert old['tracks'] == new['tracks'][:274]
DEST.write_text(json.dumps(module, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
report = {'status': 'PASS', 'base274_tracks_preserved_exactly': True,
          'other_entries_preserved_exactly': len(module['entries']) - 1,
          'supplemental_cues': 57, 'union_tracks': 331, 'coverage_status': 'partial',
          'production_sha256': sha(DEST), 'independent_review_receipt': str(review_path.relative_to(ROOT)).replace('\\', '/'),
          'source_global_assembly_performed': False}
(OUT / 'mkworld331-production-reconciliation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report))
