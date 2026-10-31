"""Join only the two exact independently reviewed Mario Kart World sets."""
import copy
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/nintendo-full'
DEST = ROOT / 'content/expansion/soundtrack-multitrack-priority-overrides.json'
load = lambda p: json.loads(p.read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
parts = []
for candidate, expected, review, status in [
    ('mkworld253-clean-original-archive-candidate.json',
     '5053224e5fa05acd0a4c701c97a90c2f6f425af2a1986972adf4882d80547271',
     'independent-mkworld253-risk17-review.json', 'BOUNDED_IDENTITY_CREDIT_SCOPE_PASS'),
    ('mkworld-distinct21-battle-fanfare-candidate.json',
     'fa388be8ba1761e6034be8afad3c273f315d96fd629441f980c679f51f7b1a16',
     'root-independent-mkworld21-review.json', 'PASS'),
]:
    receipt = load(OUT / review)
    assert sha(OUT / candidate) == expected == receipt['candidate_sha256']
    assert receipt['status'] == status
    parts.append((copy.deepcopy(load(OUT / candidate)['entries'][0]), review))
entry = parts[0][0]
old_tracks = copy.deepcopy(entry['tracks'])
entry['tracks'].extend(copy.deepcopy(parts[1][0]['tracks']))
assert len(entry['tracks']) == 274
assert entry['tracks'][:253] == old_tracks
assert len({track['youtube_id'] for track in entry['tracks']}) == 274
assert len({track['title'] for track in entry['tracks']}) == 274
assert all(track['native_codec_metadata_verified'] for track in entry['tracks'])
entry['completeness'].update(verified_archival_recordings=274, separately_reviewed_supplemental_cues=21)
entry['recording_collection_scope'] = '274 individually identified original-game archival recordings:253 Grand Prix/replay and Free Roam selections plus21 separately reviewed battle, start/finish and menu cues. Source loops/fades may differ from the later edited348-track Nintendo Music release. This remains partial; missing cue and version reconciliation is open.'
entry['independent_review_receipt'] = [str((OUT / review).relative_to(ROOT)).replace('\\', '/') for _, review in parts]
module = load(DEST)
before = copy.deepcopy(module['entries'])
assert not any(existing['entry_id'] == entry['entry_id'] for existing in before)
module['entries'].append(entry)
DEST.write_text(json.dumps(module, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
assert load(DEST)['entries'][:-1] == before
report = {'status': 'PASS', 'previous_entries_preserved_exactly': len(before),
          'base253_tracks_preserved_exactly': True, 'supplemental_tracks': 21,
          'union_tracks': 274, 'coverage_status': 'partial',
          'production_sha256': sha(DEST), 'source_global_assembly_performed': False,
          'independent_reviews': entry['independent_review_receipt']}
(OUT / 'mkworld274-production-reconciliation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report))
