"""Append exactly11 root-reviewed longer game-score loop publications."""
import copy
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/nintendo-full'
DEST = ROOT / 'content/expansion/soundtrack-multitrack-priority-overrides.json'
load = lambda p: json.loads(p.read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
candidate_path = OUT / 'mkworld-distinct11-long-loop-versions-candidate.json'
review_path = OUT / 'root-independent-mkworld11-loop-review.json'
review = load(review_path)
assert sha(candidate_path) == review['candidate_sha256'] == 'a6960da4df2dce57e4d48d2945056c43fb1f30cf763683cd53cc86a52b603a5e'
assert review['status'] == 'PASS_AS_PUBLIC_GAME_LOOP_VERSIONS'
candidate = load(candidate_path)
assert sha(DEST) == candidate['requires_base_module_sha256'] == '7f9568e6cdb5303bac258a82523af2d719cd76c36df7458829a7509a11150359'
module = load(DEST)
before = copy.deepcopy(module)
entry = next(entry for entry in module['entries'] if entry['entry_id'] == 'wikipedia-79613463')
assert len(entry['tracks']) == 331
addition = candidate['entries'][0]['tracks']
assert len(addition) == 11
entry['tracks'].extend(copy.deepcopy(addition))
assert len(entry['tracks']) == len({track['youtube_id'] for track in entry['tracks']}) == len({track['title'] for track in entry['tracks']}) == 342
entry['completeness'].update(verified_archival_recordings=342, separately_reviewed_supplemental_cues=89)
entry['recording_collection_scope'] = '342 individually identified game-score archival recordings. Includes separately reviewed original-game loop versions of11 results/replay/trophy/mission cues; these longer loop publications are not the shorter edited Nintendo Music masters. This remains partial versus the348-name research inventory, with unresolved composition/version mapping explicitly retained.'
entry['independent_review_receipt'].append(str(review_path.relative_to(ROOT)).replace('\\', '/'))
for old, new in zip(before['entries'], module['entries']):
    if old['entry_id'] != entry['entry_id']:
        assert old == new
    else:
        assert old['tracks'] == new['tracks'][:331]
DEST.write_text(json.dumps(module, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
report = {'status': 'PASS', 'base331_tracks_preserved_exactly': True,
          'other_entries_preserved_exactly': len(module['entries']) - 1,
          'supplemental_cues': 11, 'union_tracks': 342, 'coverage_status': 'partial',
          'production_sha256': sha(DEST), 'independent_review_receipt': str(review_path.relative_to(ROOT)).replace('\\', '/'),
          'source_global_assembly_performed': False}
(OUT / 'mkworld342-production-reconciliation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report))
