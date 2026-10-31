"""Replace one modern reconstruction with the original Japanese package back.

Prepared for the next publication boundary; not active until assemble hook is
explicitly installed. Never change source prose or translated field bindings.
"""
import copy
import hashlib
import json
from pathlib import Path
from PIL import Image


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def apply(entries, root):
    root = Path(root)
    plan = json.loads((root / 'content/expansion/super-butoden-original-back.json').read_text(encoding='utf-8'))
    matches = [e for e in entries if e['id'] == plan['owner_id']]
    if len(matches) != 1:
        raise ValueError('Original Super Butoden back requires exactly one owner')
    owner = matches[0]
    if digest(owner['body']) != plan['source_body_sha256']:
        raise ValueError('Super Butoden prose changed; review the image context again')
    image = plan['after_image']
    source = root / image['recovery_local_source']
    if hashlib.sha256(source.read_bytes()).hexdigest() != image['verification']['sha256']:
        raise ValueError('Original Japanese package scan changed')
    with Image.open(source) as raster:
        raster.load()
        if raster.format != 'PNG' or raster.size != (1239, 2226):
            raise ValueError('Original Japanese package scan format or native size changed')
    if image['story_paragraph'] != 1 or owner.get('preferred_image') == 1:
        raise ValueError('The correction must remain an internal paragraph-one image')
    if len(owner.get('images', [])) != plan['expected_image_count']:
        raise ValueError('Super Butoden image slots changed')
    if owner['images'][1] == image:
        return {'status': 'PASS', 'changed': False, 'owner_id': owner['id']}
    if owner['images'][1] != plan['before_image']:
        raise ValueError('Modern reconstruction differs from the reviewed original slot')
    owner['images'][1] = copy.deepcopy(image)
    return {'status': 'PASS', 'changed': True, 'owner_id': owner['id'],
            'scope': 'Only internal image1 replaced; English prose, headings, dates, preferred cover and other media unchanged.'}
