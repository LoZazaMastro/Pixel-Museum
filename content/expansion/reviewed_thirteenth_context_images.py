"""Exact-array admission of independently reviewed historical context images."""
import copy
import hashlib
import json
from pathlib import Path

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def apply(entries, root):
    root = Path(root)
    manifest = root / 'content/expansion/museum-thirteenth-context-images-reviewed.json'
    if not manifest.is_file():
        return {'status': 'not_available'}
    plans = json.loads(manifest.read_text(encoding='utf8'))
    if plans['publication_status'] != 'independently_reviewed':
        raise ValueError('Context images are not admitted')
    added = 0
    for plan in plans['plans']:
        path = root / plan['candidate_path']
        review_path = root / plan['independent_review_receipt']
        if sha(path) != plan['candidate_sha256'] or sha(review_path) != plan['independent_review_sha256']:
            raise ValueError('Context candidate or peer bytes changed')
        review = json.loads(review_path.read_text(encoding='utf8'))
        if not review.get('status', '').startswith('PASS') or review.get('candidate_sha256') != plan['candidate_sha256']:
            raise ValueError('Context peer does not approve exact candidate')
        candidate = json.loads(path.read_text(encoding='utf8'))
        for source in candidate['source_receipts']:
            if sha(root / source['path']) != source['sha256']:
                raise ValueError('Context source changed')
        owner = next(e for e in entries if e['id'] == plan['entry_id'])
        if owner['body'] != plan['old_body'] or owner.get('story_headings', []) != plan['old_headings']:
            raise ValueError('Context prose or headings changed')
        old, new = plan['old_images'], plan['new_images']
        if new[:len(old)] != old or len({i['url'] for i in new}) != len(new):
            raise ValueError('Context append changes existing images or duplicates URL')
        for image in new[len(old):]:
            local = root / image['recovery_local_source']
            verify = image['verification']
            expected = verify.get('source_sha256', verify.get('sha256'))
            if not expected or sha(local) != expected:
                raise ValueError('Context original bytes changed')
            if not 0 <= image['story_paragraph'] < len(owner['body']):
                raise ValueError('Context paragraph is invalid')
        if owner.get('images', []) == new:
            continue
        if owner.get('images', []) != old:
            raise ValueError('Context exact previous image array changed')
        owner['images'] = copy.deepcopy(new)
        owner.setdefault('provenance', {})['reviewed_thirteenth_context_images'] = {
            'candidate_path': plan['candidate_path'],
            'candidate_sha256': plan['candidate_sha256'],
            'independent_review_receipt': plan['independent_review_receipt'],
            'scope': 'Historical context photographs; no prose or complete-article claim.'
        }
        added += len(new) - len(old)
    return {'status': 'PASS', 'added_images': added}
