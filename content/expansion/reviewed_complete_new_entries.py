"""Admit only independently reviewed, fully illustrated new entry batches."""
import copy
import hashlib
import json
import re
import runpy
import unicodedata
from pathlib import Path
from PIL import Image


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def identity(title):
    title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]', '', title)


def validate_illustration_groups(original, batch):
    count = len(original['body'])
    groups = batch.get('paragraph_groups', [[index] for index in range(count)])
    if not isinstance(groups, list) or len(groups) < 2:
        raise ValueError('Reviewed narrative needs at least two paragraph groups')
    for group in groups:
        if not isinstance(group, list) or not group or any(type(index) is not int for index in group):
            raise ValueError('Reviewed paragraph groups require nonempty integer lists')
        if group != list(range(group[0], group[0] + len(group))):
            raise ValueError('Reviewed paragraph groups must be contiguous')
    if [index for group in groups for index in group] != list(range(count)):
        raise ValueError('Reviewed paragraph groups must preserve every paragraph in order')
    opening = batch.get('opening_film_owned', False)
    if not isinstance(opening, bool):
        raise ValueError('Invalid reviewed opening-film policy')
    if opening and (not original.get('videos') or original['videos'][0].get('story_paragraph', -1) >= 0):
        raise ValueError('Reviewed opening film must use original default ownership')
    illustrations = original['images']
    if len({image['url'] for image in illustrations}) != len(illustrations):
        raise ValueError('Duplicate illustration in reviewed entry')
    for group in groups:
        start = group[0]
        matches = sum(image.get('story_paragraph') == start for image in illustrations)
        if start == 0 and opening:
            if matches:
                raise ValueError('Opening film cannot compete with a paragraph-zero illustration')
        elif matches != 1:
            raise ValueError('Each reviewed paragraph group needs one distinct illustration')
        if any(image.get('story_paragraph') in group[1:] for image in illustrations):
            raise ValueError('Reviewed continuation paragraphs cannot have competing image anchors')


def apply(entries, root):
    root = Path(root)
    path = root / 'content/expansion/museum-complete-new-entries-reviewed.json'
    if not path.is_file():
        return {'status': 'not_admitted', 'added': []}
    plan = json.loads(path.read_text(encoding='utf8'))
    if plan.get('publication_status') != 'independently_reviewed':
        return {'status': 'not_admitted', 'added': []}
    by_id = {entry['id']: entry for entry in entries}
    model_index = runpy.run_path(str(root / 'content/expansion/user_console_png_policy.py'))['authoring_models'](root)
    added = []
    for batch in plan['batches']:
        candidate_path = root / batch['candidate_path']
        peer_path = root / batch['peer_path']
        if file_digest(candidate_path) != batch['candidate_sha256'] or file_digest(peer_path) != batch['peer_sha256']:
            raise ValueError('Reviewed new-entry batch or peer changed')
        peer = json.loads(peer_path.read_text(encoding='utf8'))
        if not peer.get('status', '').startswith('PASS') or peer.get('candidate_sha256') != batch['candidate_sha256']:
            raise ValueError('New-entry candidate has no source-bound independent PASS')
        candidate = json.loads(candidate_path.read_text(encoding='utf8'))
        if 'paragraph_groups' in batch:
            native_path = root / batch['native_group_peer_path']
            if file_digest(native_path) != batch['native_group_peer_sha256']:
                raise ValueError('Reviewed paragraph-group native proof changed')
            native = json.loads(native_path.read_text(encoding='utf8'))
            if (not native.get('status', '').startswith('PASS') or
                    native.get('candidate_sha256') != batch['candidate_sha256'] or
                    native.get('actual_groups') != batch['paragraph_groups']):
                raise ValueError('Reviewed paragraph-group native proof does not match')
        source_files = candidate['source_files']
        if isinstance(source_files, list):
            normalized = {}
            for record in source_files:
                if (type(record) is not dict or set(record) != {'path', 'sha256'} or
                        not isinstance(record['path'], str) or not record['path'] or
                        record['path'] in normalized or
                        not isinstance(record['sha256'], str) or
                        re.fullmatch(r'[0-9a-f]{64}', record['sha256']) is None):
                    raise ValueError('Invalid or duplicate reviewed source-file record')
                normalized[record['path']] = record['sha256']
            source_files = normalized
        for source, expected in source_files.items():
            if file_digest(root / source) != expected:
                raise ValueError('Reviewed new-entry source changed: ' + source)
        if sorted(entry['id'] for entry in candidate['entries']) != sorted(batch['approved_entry_ids']):
            raise ValueError('Reviewed new-entry owner set changed')
        for original in candidate['entries']:
            identifier = original['id']
            if len(original['body']) < 3 or len(original['body']) != len(original['story_headings']):
                raise ValueError('Incomplete reviewed narrative: ' + identifier)
            if original.get('subtitle') == 'From the reference collection':
                raise ValueError('Generic display subtitle cannot be published')
            illustrations = original['images']
            if not illustrations or not 0 <= original.get('preferred_image', 0) < len(illustrations):
                raise ValueError('Reviewed entry has no valid cover')
            cover = illustrations[original.get('preferred_image', 0)]
            if cover.get('story_paragraph', -1) >= 0:
                raise ValueError('Reviewed cover must remain exclusive to its hero')
            validate_illustration_groups(original, batch)
            for image in illustrations:
                local = root / (image.get('recovery_local_source') or image['local_path'])
                verification = image.get('verification', {})
                expected = verification.get('sha256') or image.get('source_sha256') or image.get('source_asset_sha256')
                if not expected or file_digest(local) != expected:
                    raise ValueError('Reviewed original illustration changed')
                with Image.open(local) as picture:
                    picture.load()
                    if picture.size != (image['width'], image['height']):
                        raise ValueError('Reviewed illustration dimensions changed')
            for video in original.get('videos', []):
                verification = video.get('verification', {})
                receipt = verification.get('metadata_receipt') or verification.get('receipt')
                if not receipt or receipt not in candidate['source_files']:
                    raise ValueError('New film metadata proof is not source-bound')
                metadata = json.loads((root / receipt).read_text(encoding='utf8'))
                formats = metadata.get('formats', [])
                avc = metadata.get('avc_format_count', 0) or sum('avc' in item.get('vcodec', '') for item in formats)
                aac = metadata.get('aac_format_count', 0) or sum('mp4a' in item.get('acodec', '') for item in formats)
                if metadata.get('id') != video['youtube_id'] or not avc or not aac:
                    raise ValueError('Reviewed film identity or native codecs changed')
                if not any(image['url'] == video.get('poster_url') and image.get('kind') == 'video-poster'
                           for image in illustrations):
                    raise ValueError('Reviewed film needs its reserved original preview')
            for model in original.get('models', []):
                if not model.get('asset_file', '').startswith('models/') or '..' in model['asset_file']:
                    raise ValueError('Reviewed model path is not a workspace model')
                matches = [row for row in model_index if row.get('exhibit_id') == identifier]
                if len(matches) != 1 or {key: value for key, value in matches[0].items() if key != 'exhibit_id'} != model:
                    raise ValueError('Reviewed new model does not match the approved model index')
                if file_digest(root / model['asset_file']) != model['sha256']:
                    raise ValueError('Approved new model bytes changed')
            if identifier in by_id:
                current = by_id[identifier]
                for field in ('title', 'year', 'date', 'kind', 'body', 'story_headings', 'images', 'videos', 'models'):
                    if current.get(field) != original.get(field):
                        raise ValueError('Reviewed new-entry identity collision: ' + identifier)
                continue
            if any(identity(entry['title']) == identity(original['title']) and entry['year'] == original['year'] for entry in entries):
                raise ValueError('Duplicate reviewed title and year: ' + identifier)
            entry = copy.deepcopy(original)
            entry.setdefault('provenance', {})['independent_admission'] = {
                'candidate_path': batch['candidate_path'], 'candidate_sha256': batch['candidate_sha256'],
                'peer_path': batch['peer_path'], 'peer_sha256': batch['peer_sha256']}
            entries.append(entry)
            by_id[identifier] = entry
            added.append(identifier)
    return {'status': 'PASS', 'added': added, 'added_count': len(added)}
