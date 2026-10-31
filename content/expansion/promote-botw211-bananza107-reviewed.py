"""Admit only the exact two independently reviewed Nintendo checkpoints."""
import copy
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
RESEARCH = ROOT / 'build/research/soundtrack-broad/nintendo-full'
DEST = ROOT / 'content/expansion/soundtrack-multitrack-priority-overrides.json'


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


before = load(DEST)
updated = copy.deepcopy(before)
checks = []
for filename, expected, receipt, accepted, count in [
    ('botw211-final209-plus2-base-roster-candidate.json',
     '4be14690144a418f7a878f0ced81aab0c44efa621e58210578bd8520d383c858',
     'root-independent-botw211-review.json', 'PASS', 211),
    ('bananza107-archival-staff-scoped-candidate.json',
     'bd9f84c4bd7642965374edb1a83f1ed451a5cc73d3b89882169f090cca4e80e0',
     'independent-bananza107-risk13-review.json', 'BOUNDED_IDENTITY_CREDIT_SCOPE_PASS', 107),
]:
    source = RESEARCH / filename
    review_path = RESEARCH / receipt
    review = load(review_path)
    assert sha(source) == expected == review['candidate_sha256']
    assert review['status'] == accepted
    entry = copy.deepcopy(load(source)['entries'][0])
    assert len(entry['tracks']) == count
    assert all(track['native_codec_metadata_verified'] for track in entry['tracks'])
    entry['independent_review_receipt'] = str(review_path.relative_to(ROOT)).replace('\\', '/')
    entry['coverage_status'] = 'full_published_album_compositions' if count == 211 else 'partial'
    updated['entries'] = [existing for existing in updated['entries'] if existing['entry_id'] != entry['entry_id']]
    updated['entries'].append(entry)
    checks.append({'entry_id': entry['entry_id'], 'tracks': count, 'candidate_sha256': expected, 'review': entry['independent_review_receipt'], 'scope': entry['recording_collection_scope']})

previous_by_id = {entry['entry_id']: entry for entry in before['entries']}
for entry in updated['entries']:
    if entry['entry_id'] in previous_by_id:
        assert entry == previous_by_id[entry['entry_id']], 'Previous validated entry changed'
updated['scope'] = 'Independently reviewed score collections. Completeness is stated per game and per published inventory; partial archival collections remain explicitly partial.'
updated['validation_scope'] = 'Actual public source identity, role-scoped credits and native AVC/AAC receipts. BOTW211 published compositions use209 individual recordings and2 real chapter passages. Bananza107 is partial versus229. No CD-master audio fingerprint or physical PS5 playback assertion.'
DEST.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
report = {
    'status': 'PASS', 'previous_entries_preserved_exactly': len(before['entries']),
    'production_path': str(DEST.relative_to(ROOT)).replace('\\', '/'),
    'production_sha256': sha(DEST), 'new_entries': checks,
    'global_assembly_performed': False,
}
(RESEARCH / 'botw211-bananza107-production-reconciliation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
