"""Quarantine a same-name game image only in the Lua language article."""
import copy
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def body_hash(body):
    return hashlib.sha256(json.dumps(body, ensure_ascii=False, separators=(',', ':')).encode('utf8')).hexdigest()


def has_url(value, urls):
    if isinstance(value, str):
        return any(url in value for url in urls)
    if isinstance(value, dict):
        return any(has_url(v, urls) for v in value.values())
    if isinstance(value, list):
        return any(has_url(v, urls) for v in value)
    return False


def apply(entries, root):
    root = Path(root)
    module = root / 'content/expansion/museum-lua-language-cover-reviewed.json'
    if not module.is_file():
        return {'status': 'not_available'}
    plan = json.loads(module.read_text(encoding='utf8'))
    if plan.get('publication_status') != 'independently_reviewed':
        return {'status': 'not_admitted'}
    candidate = root / plan['candidate_path']
    actual = digest(candidate)
    if actual != plan['candidate_sha256']:
        raise ValueError('Reviewed Lua logo candidate changed')
    review_file = root / plan['independent_review_receipt']
    if digest(review_file) != plan['independent_review_sha256']:
        raise ValueError('Reviewed Lua logo peer receipt changed')
    peer = json.loads(review_file.read_text(encoding='utf8'))
    if peer.get('status') != 'PASS' or peer.get('candidate_sha256') != actual:
        raise ValueError('Reviewed Lua logo peer receipt mismatch')
    change = json.loads(candidate.read_text(encoding='utf8'))
    for source in change['source_receipts']:
        if digest(root / source['path']) != source['sha256']:
            raise ValueError('Reviewed Lua logo source changed: ' + source['path'])
    owner = next((e for e in entries if e['id'] == change['entry_id']), None)
    if owner is None or body_hash(owner['body']) != change['old_body_sha256']:
        raise ValueError('Reviewed Lua language article guard changed')
    image = change['new_cover']
    if digest(root / image['recovery_local_source']) != image['verification']['source_sha256']:
        raise ValueError('Reviewed Lua vector raster changed')
    forbidden = set(change['superseded_urls'])
    # Build the complete owner change before mutating the shared catalogue.
    updated = copy.deepcopy(owner)
    removed = [i for i in updated.get('images', []) if has_url(i, forbidden)]
    if removed and any(i not in change['old_images'] for i in removed):
        raise ValueError('Reviewed Lua wrong-subject image record changed')
    kept = [i for i in updated.get('images', [])
            if not has_url(i, forbidden) and i.get('url') != image['url']]
    updated['images'] = [copy.deepcopy(image)] + kept
    updated['preferred_image'] = 0
    for feature in updated.get('editorial_features', []):
        feature['images'] = [i for i in feature.get('images', []) if not has_url(i, forbidden)]
    # Rejected URL and full metadata live in the external, hash-bound candidate,
    # never in this owner's gallery or a nested runtime provenance record.
    if has_url(updated, forbidden):
        raise ValueError('Unexpected Lua wrong-subject URL outside display images')
    provenance = updated.setdefault('provenance', {})
    provenance['reviewed_lua_language_cover'] = {
        'candidate_path': plan['candidate_path'],
        'candidate_sha256': actual,
        'independent_review_receipt': plan['independent_review_receipt'],
        'quarantined_record_count': len(change['quarantined_images']),
        'quarantine_location': 'External reviewed candidate; not runtime media.',
        'reason': 'Replace a different same-name game with the official language logo.'}
    changed = updated != owner
    owner.clear()
    owner.update(updated)
    return {'status': 'PASS', 'entry_id': change['entry_id'],
            'candidate_sha256': actual, 'changed': changed,
            'removed_display_images': len(removed), 'forbidden_url_occurrences_after': 0}
