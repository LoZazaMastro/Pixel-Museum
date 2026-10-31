"""Promote exact independently reviewed publisher chapter collections."""
import copy
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/modern-public-albums'
DEST = ROOT / 'content/expansion/soundtrack-multitrack-priority-overrides.json'
load = lambda path: json.loads(path.read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
candidate = OUT / 'hades-two-publisher-albums82-candidate.json'
peer_path = OUT / 'root-independent-hades82-review.json'
peer = load(peer_path)
assert peer['status'] == 'PASS'
assert sha(candidate) == peer['candidate_sha256'] == 'f4c01f8a1c9af66584b9e4ad9607949fe8f5387c312c777bd9c4ff2c22289626'
assert sha(DEST) == '00ccbdc9425b90132e71cc7d3f61a7af988eec7581f5b12aab3d2acf1cc348b4'
module = load(DEST)
previous = copy.deepcopy(module['entries'])
entries = copy.deepcopy(load(candidate)['entries'])
assert len(entries) == 2 and sum(len(row['tracks']) for row in entries) == 82
for entry in entries:
    assert not any(old['entry_id'] == entry['entry_id'] for old in previous)
    entry['independent_review_receipt'] = peer_path.relative_to(ROOT).as_posix()
    # Readable spacing only, not a semantic version or credit change.
    for track in entry['tracks']:
        track['recording_version'] = track['recording_version'].replace('Games2020', 'Games 2020').replace('Games2025', 'Games 2025')
        track['rights'] = track['rights'].replace('copyright2020', 'copyright 2020').replace('copyright2025', 'copyright 2025')
    module['entries'].append(entry)
assert module['entries'][:len(previous)] == previous
temp = DEST.with_suffix('.json.tmp')
temp.write_text(json.dumps(module, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
temp.replace(DEST)
report = {'status': 'PASS', 'production_sha256': sha(DEST), 'old_entries_preserved_exactly': len(previous),
          'new_games': 2, 'new_selectable_chapters': 82, 'source_global_assembly_performed': False,
          'presentation_delta': 'Spaces inserted between publisher/copyright words and years only.'}
(OUT / 'hades-two-production-reconciliation.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report))
