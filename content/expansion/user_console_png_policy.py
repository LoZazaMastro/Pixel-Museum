"""User-requested withdrawal of catalog console meshes; source assets stay archived."""
import copy
import hashlib
import json
from pathlib import Path
from PIL import Image

ARCHIVE = 'build/research/user-all-console-png-withdrawal/original-models-index.json'
ARCHIVE_SHA256 = 'b770ecac8b70828af55087f083b3c04c92b85dc9c8ae99c9cf5720235fa6e7a5'


def authoring_models(root):
    """Keep exact historical producer/peer comparisons before final withdrawal.

    These rows never authorize published meshes: apply() runs after every join.
    The immutable snapshot prevents model-gated canonical hardware disappearing
    and preserves strict editorial old-owner comparisons without changing prose.
    """
    root = Path(root)
    index = json.loads((root / 'models/index.json').read_text(encoding='utf8'))
    if index.get('catalog_console_models_withdrawn') is not True:
        return index['models']
    if index['models'] or index.get('authoring_archive') != ARCHIVE or index.get('authoring_archive_sha256') != ARCHIVE_SHA256:
        raise ValueError('Console model withdrawal policy changed')
    data = (root / ARCHIVE).read_bytes()
    if hashlib.sha256(data).hexdigest() != ARCHIVE_SHA256:
        raise ValueError('Historical model authoring snapshot changed')
    return json.loads(data)['models']


def apply(entries, root):
    root = Path(root)
    authoring_models(root)  # Validate historical source pins before writing.
    plan = json.loads((root / 'content/expansion/user-console-png-heroes.json').read_text(encoding='utf8'))
    by_id = {entry['id']: entry for entry in entries}
    for row in plan['rows']:
        owner = by_id[row['entry_id']]
        for source, expected in row.get('source_files', {}).items():
            if hashlib.sha256((root / source).read_bytes()).hexdigest() != expected:
                raise ValueError('Console photograph source record changed: ' + source)
        body_digest = hashlib.sha256(json.dumps(owner['body'], ensure_ascii=False,
                                               separators=(',', ':')).encode()).hexdigest()
        if body_digest != row['body_sha256']:
            raise ValueError('Console photograph owner prose changed: ' + row['entry_id'])
        image = row['image']
        if image['story_paragraph'] != -1 or image.get('cover_art') is not True:
            raise ValueError('Console photograph must be an exclusive hero')
        if hashlib.sha256((root / image['recovery_local_source']).read_bytes()).hexdigest() != image['verification']['sha256']:
            raise ValueError('Console photograph source changed: ' + row['entry_id'])
        with Image.open(root / image['recovery_local_source']) as source:
            if source.size != (image['width'], image['height']):
                raise ValueError('Console photograph dimensions changed: ' + row['entry_id'])
            if 'A' not in source.getbands() or source.getchannel('A').getextrema()[0] == 255:
                raise ValueError('Console photograph is not actually transparent: ' + row['entry_id'])
    heroes = []
    for row in plan['rows']:
        owner, image = by_id[row['entry_id']], row['image']
        original_url = row.get('original_image', image)['url']
        matches = [i for i, old in enumerate(owner['images']) if old['url'] in (original_url, image['url'])]
        if matches:
            before = row.get('original_image', image)
            if len(matches) != 1 or owner['images'][matches[0]] not in (before, image):
                raise ValueError('Conflicting console hero already used in narrative: ' + row['entry_id'])
            selected = matches[0]
            owner['images'][selected] = copy.deepcopy(image)
        else:
            selected = len(owner['images'])
            owner['images'].append(copy.deepcopy(image))
        owner['preferred_image'] = selected
        heroes.append(row['entry_id'])
    changed = []
    for entry in entries:
        if entry.get('models'):
            changed.append({'entry_id': entry['id'], 'models': copy.deepcopy(entry['models'])})
        entry['models'] = []
    if any(entry['models'] for entry in entries):
        raise ValueError('A console mesh survived final PNG-only policy')
    return {'status': 'PASS_USER_ALL_CONSOLES_IMAGE_ONLY',
            'withdrawn_count': len(changed), 'withdrawn': changed,
            'transparent_heroes': heroes,
            'source_assets_deleted': False, 'experience_geometry_changed': False}
