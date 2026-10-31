"""Admit source-bound, illustrated Switch articles after independent review."""
import copy
import hashlib
import json
from pathlib import Path

from PIL import Image


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply(entries, root, module_name='museum-switch-game-additions-reviewed.json'):
    root = Path(root)
    module = root / 'content/expansion' / module_name
    if not module.is_file():
        return {'status': 'not_available', 'added': []}
    document = json.loads(module.read_text(encoding='utf8'))
    if document.get('publication_status') != 'independently_reviewed':
        return {'status': 'not_admitted', 'added': []}
    by_id = {entry['id']: entry for entry in entries}
    report = {'status': 'PASS', 'added': [], 'batches': []}
    for batch in document.get('batches', []):
        candidate_path = root / batch['candidate_path']
        candidate_sha = digest(candidate_path)
        if candidate_sha != batch['candidate_sha256']:
            raise ValueError('Reviewed Switch article changed: ' + str(candidate_path))
        receipt = json.loads((root / batch['independent_review_receipt']).read_text(encoding='utf8'))
        if receipt.get('status') != 'PASS' or receipt.get('candidate_sha256') != candidate_sha:
            raise ValueError('Switch article peer receipt mismatch: ' + str(candidate_path))
        candidate = json.loads(candidate_path.read_text(encoding='utf8'))
        for source in candidate.get('source_receipts', []):
            if digest(root / source['path']) != source['sha256']:
                raise ValueError('Switch article source changed: ' + source['path'])
        admitted = []
        for original in candidate['entries']:
            identifier = original['id']
            body = original['body']
            if len(body) < 4 or len(body) != len(original['story_headings']) or any(not text.strip() for text in body):
                raise ValueError('Incomplete reviewed Switch article: ' + identifier)
            images = original['images']
            mapping = sorted(image['story_paragraph'] for image in images if image.get('story_paragraph', -1) >= 0)
            if mapping != list(range(len(body))):
                raise ValueError('Switch article lacks unique paragraph illustrations: ' + identifier)
            urls, pixels = set(), set()
            for image in images:
                source = root / image['recovery_local_source']
                verification = image['verification']
                if digest(source) != verification.get('source_sha256', verification.get('sha256')):
                    raise ValueError('Switch article image changed: ' + str(source))
                with Image.open(source) as picture:
                    picture.load()
                    if picture.size != (image['width'], image['height']):
                        raise ValueError('Switch image dimensions changed: ' + str(source))
                    pixel_hash = hashlib.sha256(picture.convert('RGB').tobytes()).hexdigest()
                if image['url'] in urls or pixel_hash in pixels:
                    raise ValueError('Repeated Switch article illustration: ' + identifier)
                urls.add(image['url'])
                pixels.add(pixel_hash)
            for video in original.get('videos', []):
                poster = video.get('poster_url')
                if poster and not any(image['url'] == poster and image.get('kind') == 'video-poster' for image in images):
                    raise ValueError('Video preview is not locally bundled: ' + identifier)
                metadata = json.loads((root / video['verification']['receipt']).read_text(encoding='utf8'))
                if metadata.get('id') != video['youtube_id'] or not metadata.get('native_compatible_avc_aac'):
                    raise ValueError('Switch article video metadata mismatch: ' + identifier)
            if identifier in by_id:
                current = by_id[identifier]
                for field in ('title', 'year', 'date', 'body', 'story_headings'):
                    if current.get(field) != original.get(field):
                        raise ValueError('Reviewed Switch article identity collision: ' + identifier)
                continue
            entry = copy.deepcopy(original)
            entry.setdefault('provenance', {})['independent_admission'] = {
                'candidate_path': batch['candidate_path'], 'candidate_sha256': candidate_sha,
                'independent_review_receipt': batch['independent_review_receipt']}
            entries.append(entry)
            by_id[identifier] = entry
            admitted.append(identifier)
            report['added'].append(identifier)
        report['batches'].append({'candidate_path': batch['candidate_path'], 'added': admitted})
    return report
