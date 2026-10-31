"""Promote only exact root-reviewed available Switch score collections."""
import copy
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/nintendo-full'
DEST = ROOT / 'content/expansion/soundtrack-multitrack-priority-overrides.json'
load = lambda path: json.loads(path.read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(DEST) == '8d1bdaa4ecde9d77ae1bb5cc66c24be7050b402dbe695bbe3ee327a63cb3896e'
module = load(DEST)
previous = copy.deepcopy(module['entries'])
for filename, peername, expected_sha, expected_count in [
    ('echoes-mk8booster-calamity-available-public-v4-supplement-candidate.json', 'root-independent-switch264-review.json',
     '9357d1a3b9292a5372ef1fa07449d92ee4b8003f1f0854f438f45a23a34fa981', 264),
    ('kirby-forgotten92-public-candidate.json', 'root-independent-kirby92-review.json',
     'db673cd8c29f131d3db81f8e6706d409c4dbcd71db8b23edb6c5f7abde9d38c6', 92),
]:
    candidate, peer_path = OUT / filename, OUT / peername
    review = load(peer_path)
    assert review['status'] == 'PASS'
    assert sha(candidate) == review['candidate_sha256'] == expected_sha
    entries = copy.deepcopy(load(candidate)['entries'])
    assert sum(len(entry['tracks']) for entry in entries) == expected_count
    for entry in entries:
        assert not any(old['entry_id'] == entry['entry_id'] for old in module['entries'])
        entry['independent_review_receipt'] = peer_path.relative_to(ROOT).as_posix()
        module['entries'].append(entry)
assert module['entries'][:22] == previous and len(module['entries']) == 26
temporary = DEST.with_suffix('.json.tmp')
temporary.write_text(json.dumps(module, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
temporary.replace(DEST)
report = {'status': 'PASS', 'production_sha256': sha(DEST), 'new_games': 4, 'new_available_recordings': 356,
          'old_entries_preserved_exactly': 22, 'source_global_assembly_performed': False,
          'scope': 'All four collections remain partial. MarioKart8Booster appends to any existing base-score selections, never replaces them.'}
(OUT / 'four-switch-public-production-reconciliation.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report))
