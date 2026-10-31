"""Append the exact nine independently reviewed public soundtrack collections."""
import copy
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = ROOT / 'build/research/soundtrack-broad'
DEST = ROOT / 'content/expansion/soundtrack-multitrack-priority-overrides.json'
load = lambda path: json.loads(path.read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()

assert sha(DEST) == '35e2f68a51dd2f7f3e733311064ac3ec8396c71d57d82f58abd0202d1b7bb607'
module = load(DEST)
previous = copy.deepcopy(module['entries'])
assert len(previous) == 11
for folder, filename, expected_sha, expected_games, expected_tracks in [
    ('classic-trilogy-complete', 'six-public-classic-score-collections-candidate.json',
     '5b74c9081818e615840bf89abdf57fb854d4506fbe954176a637b88667ce96e4', 6, 216),
    ('spider-complete', 'three-public-albums67-candidate.json',
     '24bab38329a8d422775f5c8286ab95df612480892e692dbc40f02156faadcac8', 3, 67),
]:
    candidate_path = BASE / folder / filename
    review_path = BASE / folder / 'root-independent-public-collections-review.json'
    review = load(review_path)
    assert review['status'] == 'PASS'
    assert sha(candidate_path) == review['candidate_sha256'] == expected_sha
    entries = copy.deepcopy(load(candidate_path)['entries'])
    assert len(entries) == expected_games
    assert sum(len(entry['tracks']) for entry in entries) == expected_tracks
    for entry in entries:
        assert not any(old['entry_id'] == entry['entry_id'] for old in module['entries'])
        entry['independent_review_receipt'] = review_path.relative_to(ROOT).as_posix()
        module['entries'].append(entry)

assert module['entries'][:11] == previous
temporary = DEST.with_suffix('.json.tmp')
temporary.write_text(json.dumps(module, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
temporary.replace(DEST)
report = {'status': 'PASS', 'production_sha256': sha(DEST), 'old_entries_preserved_exactly': 11,
          'new_games': 9, 'new_selectable_recordings': 283, 'total_override_entries': len(module['entries']),
          'source_global_assembly_performed': False,
          'scope': 'Exact root-reviewed public collections. Classic archival collections remain partial; no audio-fingerprint or physical-console playback claim.'}
(BASE / 'checkpoints/classics-spider-nine-production-reconciliation.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report))
