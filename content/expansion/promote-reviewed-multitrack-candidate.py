"""Guarded source-only admission of an immutable independently reviewed batch."""
import copy
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
DEST = ROOT / 'content/expansion/soundtrack-multitrack-priority-overrides.json'
load = lambda path: json.loads(path.read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
candidate_relative, peer_relative, candidate_sha, previous_module_sha, report_relative = sys.argv[1:]
candidate, peer_path = ROOT / candidate_relative, ROOT / peer_relative
review = load(peer_path)
assert review['status'] == 'PASS'
assert sha(candidate) == review['candidate_sha256'] == candidate_sha
assert sha(DEST) == previous_module_sha, 'Source changed; reconcile checkpoint before admission'
module = load(DEST)
previous = copy.deepcopy(module['entries'])
entries = copy.deepcopy(load(candidate)['entries'])
assert entries
for entry in entries:
    assert not any(old['entry_id'] == entry['entry_id'] for old in module['entries']), 'Already present: explicit reconciliation required'
    entry['independent_review_receipt'] = peer_path.relative_to(ROOT).as_posix()
    module['entries'].append(entry)
assert module['entries'][:len(previous)] == previous
temporary = DEST.with_suffix('.json.tmp')
temporary.write_text(json.dumps(module, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
temporary.replace(DEST)
report = {'status': 'PASS', 'candidate_sha256': candidate_sha, 'production_sha256': sha(DEST),
          'old_entries_preserved_exactly': len(previous), 'new_games': len(entries),
          'new_selectable_recordings': sum(len(entry['tracks']) for entry in entries),
          'total_override_entries': len(module['entries']), 'source_global_assembly_performed': False,
          'independent_review_receipt': peer_relative}
(ROOT / report_relative).write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report))
