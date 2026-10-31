"""Join independently reviewed, paragraph-bound original illustrations only."""
import copy
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def body_hash(body):
    return hashlib.sha256(json.dumps(body, ensure_ascii=False, separators=(',', ':')).encode('utf8')).hexdigest()


FINAL_BODY_BATCHES = frozenset((
    '30f64860b903b359b04f826b7349022d5143e2d74b457bf484ab6d5493a6a131',
    '4d71502ed27a91a2e34effe323a58b3c41009bf595283c65d6b1b38ec0ddfe2f',
    '4cba8c4dc2969c5733998607b09f6b1f31bb39465f29a4c74921c5a8fee4aee6',
))


def apply(entries, root, stage='before_clarity'):
    if stage not in ('before_clarity', 'after_clarity'):
        raise ValueError('Unknown reviewed illustration join stage')
    root = Path(root)
    module = root / 'content/expansion/museum-story-gap-illustrations-reviewed.json'
    if not module.is_file():
        return {'status': 'not_available'}
    doc = json.loads(module.read_text(encoding='utf8'))
    if doc.get('publication_status') != 'independently_reviewed':
        return {'status': 'not_admitted'}
    owners = {e['id']: e for e in entries}
    report = {'status': 'PASS', 'batches': [], 'images_added': 0}
    for batch in doc.get('batches', []):
        final_body = batch['candidate_sha256'] in FINAL_BODY_BATCHES
        if final_body != (stage == 'after_clarity'):
            continue
        path = root / batch['candidate_path']
        if digest(path) != batch['candidate_sha256']:
            raise ValueError('Reviewed illustration candidate changed: ' + str(path))
        candidate = json.loads(path.read_text(encoding='utf8'))
        review = json.loads((root / batch['independent_review_receipt']).read_text(encoding='utf8'))
        if review.get('status', review.get('publication_status')) != 'PASS' or review.get('candidate_sha256') != batch['candidate_sha256']:
            raise ValueError('Illustration peer receipt mismatch: ' + str(path))
        for source in candidate.get('source_receipts', []):
            if digest(root / source['path']) != source['sha256']:
                raise ValueError('Illustration source receipt changed: ' + source['path'])
        admitted = []
        for identifier, images in candidate.get('entries', {}).items():
            entry = owners.get(identifier)
            if entry is None:
                raise ValueError('Illustration article absent: ' + identifier)
            guard = candidate['article_guards'][identifier]
            if body_hash(entry['body']) != guard['body_sha256']:
                raise ValueError('Illustration paragraph source changed: ' + identifier)
            known = {i.get('url', '') for i in entry.get('images', [])}
            batch_hashes = set()
            for image in images:
                paragraph = image['story_paragraph']
                if not isinstance(paragraph, int) or paragraph < 0 or paragraph >= len(entry['body']):
                    raise ValueError('Invalid reviewed paragraph association: ' + identifier)
                source = root / image['recovery_local_source']
                image_sha = digest(source)
                expected = image['verification']['source_sha256']
                if image_sha != expected or image_sha in batch_hashes:
                    raise ValueError('Illustration original changed or repeated: ' + str(source))
                batch_hashes.add(image_sha)
                if image['url'] in known:
                    continue
                entry.setdefault('images', []).append(copy.deepcopy(image))
                known.add(image['url'])
                report['images_added'] += 1
                admitted.append({'entry_id': identifier, 'paragraph': paragraph, 'url': image['url']})
            provenance = entry.setdefault('provenance', {}).setdefault('reviewed_story_gap_images', [])
            if not any(i.get('candidate_sha256') == batch['candidate_sha256'] for i in provenance):
                provenance.append({'candidate_path': batch['candidate_path'], 'candidate_sha256': batch['candidate_sha256'],
                                   'independent_review_receipt': batch['independent_review_receipt']})
        for change in candidate.get('feature_entries', []):
            entry = owners.get(change['entry_id'])
            if entry is None:
                raise ValueError('Feature illustration article absent: ' + change['entry_id'])
            feature = next((f for f in entry.get('editorial_features', []) if f.get('id') == change['feature_id']), None)
            if feature is None or body_hash(feature['body']) != change['feature_body_sha256']:
                raise ValueError('Illustrated feature source changed: ' + change['feature_id'])
            known = {i.get('url', '') for i in feature.get('images', [])}
            batch_hashes = set()
            for image in change['images']:
                paragraph = image['story_paragraph']
                if not isinstance(paragraph, int) or paragraph < 0 or paragraph >= len(feature['body']):
                    raise ValueError('Invalid reviewed feature paragraph: ' + change['feature_id'])
                source = root / image['recovery_local_source']
                image_sha = digest(source)
                if image_sha != image['verification']['source_sha256'] or image_sha in batch_hashes:
                    raise ValueError('Feature illustration original changed or repeated: ' + str(source))
                batch_hashes.add(image_sha)
                if image['url'] in known:
                    continue
                feature.setdefault('images', []).append(copy.deepcopy(image))
                known.add(image['url'])
                report['images_added'] += 1
                admitted.append({'entry_id': entry['id'], 'feature_id': feature['id'], 'paragraph': paragraph, 'url': image['url']})
        report['batches'].append({'candidate_path': batch['candidate_path'], 'admitted': admitted})
    return report
