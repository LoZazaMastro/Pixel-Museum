"""Admit independently reviewed, fully illustrated retail Xbox Series entries."""
import copy
import hashlib
import json
from pathlib import Path
from PIL import Image


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply(entries, root):
    root = Path(root)
    manifest = root / 'content/expansion/museum-missing-xbox-series-reviewed.json'
    if not manifest.is_file():
        return {'status': 'not_available', 'added': []}
    module = json.loads(manifest.read_text(encoding='utf-8'))
    if module.get('publication_status') != 'independently_reviewed':
        return {'status': 'not_admitted', 'added': []}
    by_id = {entry['id']: entry for entry in entries}
    report = {'status': 'PASS', 'added': []}
    for batch in module['batches']:
        path = root / batch['candidate_path']
        checksum = digest(path)
        if checksum != batch['candidate_sha256']:
            raise ValueError('Xbox candidate changed: ' + str(path))
        peer_path = root / batch['independent_review_receipt']
        if digest(peer_path) != batch['independent_review_sha256']:
            raise ValueError('Xbox peer receipt changed')
        peer = json.loads(peer_path.read_text(encoding='utf-8'))
        if peer.get('status') != 'PASS' or peer.get('candidate_sha256') != checksum:
            raise ValueError('Xbox candidate is not independently approved in full')
        candidate = json.loads(path.read_text(encoding='utf-8'))
        for source, expected in candidate['source_files'].items():
            if digest(root / source) != expected:
                raise ValueError('Xbox source changed: ' + source)
        if {entry['id'] for entry in candidate['entries']} != {'xbox-series-x', 'xbox-series-s'}:
            raise ValueError('Unexpected Xbox candidate owner set')
        for original in candidate['entries']:
            identifier = original['id']
            if original['year'] != 2020 or original['date']['month'] != 11 or original['date']['day'] != 10:
                raise ValueError('Unexpected retail launch date')
            if len(original['body']) < 4 or len(original['body']) != len(original['story_headings']):
                raise ValueError('Incomplete Xbox narrative')
            illustrations = original['images']
            if sorted(image.get('story_paragraph') for image in illustrations if image.get('story_paragraph', -1) >= 0) != list(range(len(original['body']))):
                raise ValueError('Every Xbox paragraph needs its own image')
            seen = set()
            for image in illustrations:
                local = root / image['recovery_local_source']
                verification = image['verification']
                if digest(local) != verification.get('sha256', verification.get('source_sha256')):
                    raise ValueError('Xbox image changed')
                with Image.open(local) as picture:
                    picture.load()
                    if picture.size != (image['width'], image['height']):
                        raise ValueError('Xbox image dimensions changed')
                    pixels = hashlib.sha256(picture.convert('RGBA').tobytes()).hexdigest()
                if pixels in seen:
                    raise ValueError('Repeated Xbox illustration')
                seen.add(pixels)
            for video in original.get('videos', []):
                metadata = json.loads((root / video['verification']['metadata_receipt']).read_text(encoding='utf-8-sig'))
                formats = metadata.get('formats', [])
                if metadata.get('id') != video['youtube_id'] or not any('avc1' in f.get('vcodec', '') for f in formats) or not any('mp4a' in f.get('acodec', '') for f in formats):
                    raise ValueError('Xbox public video codec evidence mismatch')
            if identifier in by_id:
                for field in ('title', 'year', 'date', 'body', 'story_headings', 'images', 'videos'):
                    if by_id[identifier].get(field) != original.get(field):
                        raise ValueError('Xbox identity collision: ' + identifier)
                continue
            if any(entry.get('title') == original['title'] and entry.get('year') == original['year'] for entry in entries):
                raise ValueError('Duplicate Xbox retail launch')
            entry = copy.deepcopy(original)
            entry.setdefault('provenance', {})['independent_admission'] = {
                'candidate_path': batch['candidate_path'], 'candidate_sha256': checksum,
                'independent_review_receipt': batch['independent_review_receipt']}
            entries.append(entry)
            by_id[identifier] = entry
            report['added'].append(identifier)
    return report
