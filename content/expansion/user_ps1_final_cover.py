"""Final PS1-only cover correction after full-owner editorial joins."""
import copy
import hashlib
import json
from pathlib import Path
from PIL import Image


def apply(entries, root):
    root = Path(root)
    plan = json.loads((root / 'content/expansion/user-ps1-final-cover.json').read_text(encoding='utf8'))
    owners = [entry for entry in entries if entry['id'] == plan['entry_id']]
    if len(owners) != 1:
        raise ValueError('Final PS1 cover requires exactly one owner')
    for source, digest in plan['source_files'].items():
        if hashlib.sha256((root / source).read_bytes()).hexdigest() != digest:
            raise ValueError('Final PS1 cover source changed: ' + source)
    image = plan['image']
    with Image.open(root / image['recovery_local_source']) as source:
        source.load()
        if source.format != 'PNG' or source.mode != 'RGBA' or source.size != (1600, 654) or source.getchannel('A').getextrema() != (0, 255):
            raise ValueError('Final PS1 cover must retain the original transparent Sony PNG')
    if image['story_paragraph'] != -1 or image.get('cover_art') is not True:
        raise ValueError('Final PS1 cover must be exclusive')
    owner = owners[0]
    old_index = plan['expected_preferred_image']
    new_index = plan['expected_image_count']
    cleared = copy.deepcopy(plan['original_image'])
    cleared['cover_art'] = False
    cleared['cover_role'] = False
    if len(owner['images']) == new_index + 1 and owner.get('preferred_image') == new_index and owner['images'][new_index] == image and owner['images'][old_index] == cleared:
        return {'status': 'PASS_PS1_FINAL_COVER_ALREADY_APPLIED', 'entry_id': owner['id'], 'preferred_image': new_index}
    if len(owner['images']) != new_index or owner.get('preferred_image') != old_index or owner['images'][old_index] != plan['original_image']:
        raise ValueError('Final PS1 cover original image/preferred slot changed')
    if any(item['url'] == image['url'] for item in owner['images']):
        raise ValueError('Final PS1 cover already exists outside its expected slot')
    owner['images'][old_index] = cleared
    owner['images'].append(copy.deepcopy(image))
    owner['preferred_image'] = new_index
    return {'status': 'PASS_PS1_FINAL_COVER_APPLIED', 'entry_id': owner['id'], 'previous_preferred_image': old_index, 'preferred_image': new_index}
