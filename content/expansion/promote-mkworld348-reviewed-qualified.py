"""Append the exact six reviewed compositions without a false master claim."""
import copy
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/nintendo-full'
DEST = ROOT / 'content/expansion/soundtrack-multitrack-priority-overrides.json'
load = lambda p: json.loads(p.read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
candidate_path = OUT / 'mkworld-final-six-compositions-candidate.json'
review_path = OUT / 'root-independent-mkworld-final-six-review.json'
review = load(review_path)
assert sha(candidate_path) == review['candidate_sha256'] == 'f6b611872a036fafa9080e1dfe8a1c5d909f105cad4f2bf93df496a149ad8dfb'
assert review['status'] == 'PASS_AS_QUALIFIED_PUBLIC_RECORDINGS'
candidate = load(candidate_path)
assert sha(DEST) == candidate['requires_base_module_sha256'] == '7b1e54ae0db82fd4d6078305182cd0b0b76a0272c82a3dcc805ef93fe0c0ddb7'
module = load(DEST)
before = copy.deepcopy(module)
entry = next(entry for entry in module['entries'] if entry['entry_id'] == 'wikipedia-79613463')
assert len(entry['tracks']) == 342
addition = candidate['entries'][0]['tracks']
assert len(addition) == 6
entry['tracks'].extend(copy.deepcopy(addition))
assert len(entry['tracks']) == len({track['youtube_id'] for track in entry['tracks']}) == len({track['title'] for track in entry['tracks']}) == 348
entry['completeness'].update(verified_archival_recordings=348, separately_reviewed_supplemental_cues=95,
                           all_game_music_complete=False, edited_master_equivalence=False,
                           semantic_alias_mapping_independent_review='Historical level/theme-name aliases and differing published edits remain qualified.348recordings is not automatic complete-master certification.')
entry['recording_collection_scope'] = '348 individually identified game-score and bonus publications. Includes explicitly longer original-game loop versions and the full100-second official Nintendo In the Studio Title Theme performance rather than a fabricated96-second cut. Coverage remains qualified PARTIAL: historical theme-name aliases, edits, loops and mastering are not all certified as identical to the348-track Nintendo Music release.'
entry['independent_review_receipt'].append(str(review_path.relative_to(ROOT)).replace('\\', '/'))
assert entry['full_album_collection'] is False and entry['coverage_status'] == 'partial'
for old, new in zip(before['entries'], module['entries']):
    if old['entry_id'] != entry['entry_id']:
        assert old == new
    else:
        assert old['tracks'] == new['tracks'][:342]
temporary = DEST.with_suffix('.json.tmp')
temporary.write_text(json.dumps(module, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
temporary.replace(DEST)
report = {'status': 'PASS_QUALIFIED_PARTIAL', 'base342_tracks_preserved_exactly': True,
          'other_entries_preserved_exactly': len(module['entries']) - 1,
          'supplemental_cues': 6, 'union_tracks': 348, 'coverage_status': 'partial',
          'edited_master_equivalence': False, 'production_sha256': sha(DEST),
          'independent_review_receipt': str(review_path.relative_to(ROOT)).replace('\\', '/'),
          'source_global_assembly_performed': False}
(OUT / 'mkworld348-qualified-production-reconciliation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report))
