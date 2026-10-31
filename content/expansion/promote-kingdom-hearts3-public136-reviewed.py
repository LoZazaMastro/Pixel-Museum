"""Admit reviewed available KHIII score collection without claiming perfect completeness."""
import copy
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/kingdom-hearts-complete'
DEST = ROOT / 'content/expansion/soundtrack-multitrack-priority-overrides.json'
load = lambda path: json.loads(path.read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
candidate_path = OUT / 'kh3-public136-plus2-vocals-primary-roles-v2-candidate.json'
review_path = OUT / 'root-independent-kh3-available-score-review.json'
review = load(review_path)
assert review['status'] == 'PASS'
assert sha(candidate_path) == review['candidate_sha256'] == 'ecc3212bb7b9d31386bf2baea03561a8fb51e9e200198a69d018e156777b5874'
assert sha(DEST) == '1514e338a01268e63f24c89e036e27c3bac8e4a4fb74acea8810a3e4894322f1'
module = load(DEST)
before = copy.deepcopy(module)
entry = copy.deepcopy(load(candidate_path)['entries'][0])
assert entry['entry_id'] == 'wikipedia-10007933' and len(entry['tracks']) == 138
assert not entry['full_album_collection'] and entry['coverage_status'] == 'partial'
assert not any(row['entry_id'] == entry['entry_id'] for row in module['entries'])
entry['independent_review_receipt'] = str(review_path.relative_to(ROOT)).replace('\\', '/')
module['entries'].append(entry)
assert module['entries'][:-1] == before['entries']
temporary = DEST.with_suffix('.json.tmp')
temporary.write_text(json.dumps(module, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
temporary.replace(DEST)
report = {'status': 'PASS_AVAILABLE_PUBLIC_SCORE_COLLECTION', 'production_sha256': sha(DEST),
          'available_score_recordings': 136, 'prior_english_vocals_preserved': 2,
          'other_entries_preserved_exactly': 10, 'source_global_assembly_performed': False,
          'independent_review_receipt': str(review_path.relative_to(ROOT)).replace('\\', '/'),
          'coverage_status': 'partial'}
(OUT / 'kh3-public136-production-reconciliation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report))
