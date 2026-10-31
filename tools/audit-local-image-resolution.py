"""Inspect the actual packaged full images, without enlarging or replacing them."""
from pathlib import Path
from collections import defaultdict
import json
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / 'assets/images/manifest.json').read_text(encoding='utf8'))
owners = defaultdict(list)
for name in ('catalog.json', 'human-history.json'):
    document = json.loads((ROOT / 'content' / name).read_text(encoding='utf8'))
    for entry in document['entries']:
        photos = entry.get('images', [])
        preferred = entry.get('preferred_image', 0)
        for index, photo in enumerate(photos):
            owners[photo['url']].append({'id': entry['id'], 'title': entry['title'],
                                        'cover': index == preferred})
        for feature in entry.get('editorial_features', []):
            for photo in feature.get('images', []):
                owners[photo['url']].append({'id': feature.get('id', entry['id']),
                                            'title': feature.get('title', entry['title']),
                                            'cover': False})

weak, missing, failed = [], [], []
for url, references in owners.items():
    relative = manifest.get('images', {}).get(url)
    if not relative or not (ROOT / relative).is_file():
        missing.append({'url': url, 'owners': references})
        continue
    try:
        with Image.open(ROOT / relative) as image:
            width, height = image.size
        if max(width, height) < 800:
            weak.append({'url': url, 'path': relative, 'width': width,
                         'height': height, 'owners': references})
    except Exception as error:
        failed.append({'url': url, 'path': relative, 'error': str(error)})

report = {'referenced_full_images_checked': len(owners),
          'native_edge_below_800': len(weak), 'missing_full_images': missing,
          'decode_header_failures': failed, 'weak_images': weak,
          'scope': 'Actual full-image file headers. No assertion of semantic identity, sharpness, source provenance or console loading speed.'}
output = ROOT / 'build/research/local-image-resolution-audit.json'
output.write_text(json.dumps(report, ensure_ascii=True, indent=2) + '\n', encoding='utf8')
print(json.dumps({'referenced': len(owners), 'weak_full_images': len(weak),
                  'weak_preferred_images': len({owner['id'] for item in weak for owner in item['owners'] if owner['cover']}),
                  'missing': len(missing), 'unreadable': len(failed)}, indent=2))
