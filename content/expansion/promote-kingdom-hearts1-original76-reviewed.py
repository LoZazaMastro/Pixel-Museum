"""Admit the exact peer-reviewed original album without changing prior entries."""
import copy
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/kingdom-hearts-complete'
DEST = ROOT / 'content/expansion/soundtrack-multitrack-priority-overrides.json'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
load = lambda path: json.loads(path.read_text(encoding='utf-8'))
candidate_path = OUT / 'kh1-original76-plus5-preserved-candidate.json'
review_path = OUT / 'independent-kh1-original76-review.json'
review = load(review_path)
assert review['status'] == 'PASS'
assert sha(candidate_path) == review['candidate_sha256'] == '25b3e8475dd88fff4c4854882b1085807b18156e424bba182b47c9e4bbdf692c'
assert sha(DEST) == '8ccfa25a8077fe10c5238a143b09e2701b0cc06bcbb4145ff23764f577bb288f'
module = load(DEST)
before = copy.deepcopy(module)
entry = copy.deepcopy(load(candidate_path)['entries'][0])
assert entry['entry_id'] == 'workbook-03-28-kingdom-hearts'
assert len(entry['tracks']) == 81 and entry['album_completeness']['verified_album_tracks'] == 76
assert not any(row['entry_id'] == entry['entry_id'] for row in module['entries'])
entry['independent_review_receipt'] = str(review_path.relative_to(ROOT)).replace('\\', '/')
module['entries'].append(entry)
assert module['entries'][:-1] == before['entries']
temporary = DEST.with_suffix('.json.tmp')
temporary.write_text(json.dumps(module, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
temporary.replace(DEST)
report = {'status': 'PASS', 'production_sha256': sha(DEST), 'original_album_tracks': 76,
          'prior_supplements_preserved': 5, 'other_entries_preserved_exactly': 8,
          'peer_receipt': str(review_path.relative_to(ROOT)).replace('\\', '/'),
          'source_global_assembly_performed': False,
          'scope': 'Original published Japanese2002 album composition inventory, not every regional/gamerip variant or fingerprint-certified CDmaster.'}
(OUT / 'kh1-original76-production-reconciliation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report))
