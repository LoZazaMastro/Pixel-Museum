"""Admit a reviewed additional-album batch without assembling shared outputs."""
import copy
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
DEST = ROOT / 'content/expansion/soundtrack-multiple-room-overrides.json'
load = lambda path: json.loads(path.read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
canonical_sha = lambda value: hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
candidate_relative, peer_relative, candidate_sha, previous_module_sha, report_relative = sys.argv[1:]
candidate_path, peer_path = ROOT / candidate_relative, ROOT / peer_relative
review = load(peer_path)
assert review['status'] == 'PASS'
assert sha(candidate_path) == review['candidate_sha256'] == candidate_sha
assert sha(DEST) == previous_module_sha, 'Source changed; reconcile before admission'
candidate = load(candidate_path)
for relative, expected in candidate['source_files'].items():
    assert sha(ROOT / relative) == expected, relative
catalog = {entry['id']: entry for entry in load(ROOT / 'content/catalog.json')['entries']}
module = load(DEST)
previous = copy.deepcopy(module['entries'])
entries = copy.deepcopy(candidate['entries'])
assert entries
for entry in entries:
    current = catalog[entry['entry_id']]
    assert current['title'] == entry['match_title'] and current['year'] == entry['match_year']
    assert canonical_sha(current['soundtrack']) == entry['expected_legacy_soundtrack_sha256']
    assert not current.get('soundtrack_rooms'), 'Existing rooms require explicit reconciliation'
    assert not any(old['match_title'] == entry['match_title'] and old['match_year'] == entry['match_year'] for old in previous)
    rooms = entry['soundtrack_rooms']
    original = copy.deepcopy(rooms[0])
    original.pop('id')
    assert original == current['soundtrack'], 'Original score must remain intact'
    assert len(rooms) >= 2 and len({room['id'] for room in rooms}) == len(rooms)
    assert all(room['tracks'] for room in rooms)
    entry['independent_review_receipt'] = peer_relative
    module['entries'].append(entry)
assert module['entries'][:len(previous)] == previous
temporary = DEST.with_suffix('.json.tmp')
temporary.write_text(json.dumps(module, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
temporary.replace(DEST)
report = {'status': 'PASS', 'candidate_sha256': candidate_sha, 'production_sha256': sha(DEST),
          'old_entries_preserved_exactly': len(previous), 'new_games': len(entries),
          'additional_selectable_recordings': sum(len(room['tracks']) for entry in entries for room in entry['soundtrack_rooms'][1:]),
          'source_global_assembly_performed': False, 'independent_review_receipt': peer_relative}
(ROOT / report_relative).write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report))
