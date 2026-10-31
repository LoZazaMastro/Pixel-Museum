"""One reviewed full-array replacement. Call LAST, after other media/clarity joins."""
from pathlib import Path
import copy
import hashlib
import json


def digest(value):
    return hashlib.sha256(value).hexdigest()


def canonical(value):
    return digest(json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode('utf8'))


def apply(entries, root):
    root = Path(root)
    manifest = root / 'content/expansion/museum-i-am-alive-bindings-reviewed.json'
    if not manifest.is_file():
        return {'status': 'not_available'}
    plan = json.loads(manifest.read_text(encoding='utf8'))
    if plan.get('publication_status') != 'independently_reviewed':
        return {'status': 'not_admitted'}
    path = root / plan['candidate_path']
    if digest(path.read_bytes()) != plan['candidate_sha256']:
        raise ValueError('I Am Alive reviewed image candidate changed')
    peer_path = root / plan['independent_review_receipt']
    if digest(peer_path.read_bytes()) != plan['independent_review_sha256']:
        raise ValueError('I Am Alive independent image review changed')
    peer = json.loads(peer_path.read_text(encoding='utf8'))
    if peer.get('status') != 'PASS' or peer.get('candidate_sha256') != plan['candidate_sha256']:
        raise ValueError('I Am Alive image peer mismatch')
    doc = json.loads(path.read_text(encoding='utf8'))
    for source in doc['source_receipts']:
        if digest((root / source['path']).read_bytes()) != source['sha256']:
            raise ValueError('I Am Alive publisher receipt changed')
    owner = next((e for e in entries if e['id'] == doc['entry_id']), None)
    if owner is None or canonical(owner['body']) != doc['body_sha256']:
        raise ValueError('I Am Alive reviewed prose changed')
    for image in doc['new_images']:
        verification = image.get('verification', {})
        expected = verification.get('source_sha256')
        if expected and digest((root / image['recovery_local_source']).read_bytes()) != expected:
            raise ValueError('I Am Alive reviewed original image changed')
    if owner['images'] == doc['new_images']:
        return {'status': 'PASS', 'changed_arrays': 0, 'paragraph_bindings': 3}
    if owner['images'] != doc['old_images'] or canonical(owner['images']) != doc['old_images_sha256']:
        raise ValueError('I Am Alive final image array changed; join must run LAST')
    owner['images'] = copy.deepcopy(doc['new_images'])
    owner.setdefault('provenance', {}).setdefault('reviewed_image_array_replacements', []).append({
        'candidate_path': plan['candidate_path'], 'candidate_sha256': plan['candidate_sha256'],
        'independent_review_receipt': plan['independent_review_receipt'],
        'old_images_sha256': doc['old_images_sha256'],
        'new_images_sha256': canonical(doc['new_images']),
        'quarantine': 'Original spare image retained in the external reviewed candidate, not deleted from source.',
    })
    return {'status': 'PASS', 'changed_arrays': 1, 'paragraph_bindings': 3, 'new_original_images': 1}
