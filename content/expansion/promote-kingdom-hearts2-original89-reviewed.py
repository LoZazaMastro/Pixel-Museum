"""Admit exact reviewed original KHII album while preserving all prior modules."""
import copy
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/kingdom-hearts-complete'
DEST = ROOT / 'content/expansion/soundtrack-multitrack-priority-overrides.json'
load = lambda path: json.loads(path.read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
candidate_path = OUT / 'kh2-original89-plus5-original2006-primary-candidate.json'
review_path = OUT / 'root-independent-kh2-original89-review.json'
review = load(review_path)
assert review['status'] == 'PASS'
assert sha(candidate_path) == review['candidate_sha256'] == '88a202f3d0087f5479c1523a835234835118ebc77ddfd935465ef1f10d145845'
assert sha(DEST) == '941576447bcb169175805ef3ba9d1da4adbe04b0c26c53c83be6a0880b63a9f1'
module = load(DEST)
before = copy.deepcopy(module)
entry = copy.deepcopy(load(candidate_path)['entries'][0])
assert entry['entry_id'] == 'wikipedia-1745270' and len(entry['tracks']) == 94
assert entry['album_completeness']['verified_album_tracks'] == 89
assert not any(row['entry_id'] == entry['entry_id'] for row in module['entries'])
entry['independent_review_receipt'] = str(review_path.relative_to(ROOT)).replace('\\', '/')
module['entries'].append(entry)
assert module['entries'][:-1] == before['entries']
temporary = DEST.with_suffix('.json.tmp')
temporary.write_text(json.dumps(module, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
temporary.replace(DEST)
report = {'status': 'PASS', 'production_sha256': sha(DEST), 'album_tracks': 89,
          'prior_supplements_preserved': 5, 'other_entries_preserved_exactly': 9,
          'independent_review_receipt': str(review_path.relative_to(ROOT)).replace('\\', '/'),
          'source_global_assembly_performed': False,
          'scope': 'Original2006 Japanese89item published album; not every2007expanded, FinalMix or HD rerecording variant.'}
(OUT / 'kh2-original89-production-reconciliation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report))
