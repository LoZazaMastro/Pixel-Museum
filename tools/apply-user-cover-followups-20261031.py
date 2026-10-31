"""Admit the user's three selected cover files without cropping or enlargement."""
from pathlib import Path
import copy
import hashlib
import json
import runpy

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/research/final-user-followups-20261031'
path = ROOT / 'content/catalog.json'
original = path.read_bytes()
catalog = json.loads(original)
owners = {entry['id']: entry for entry in catalog['entries']}
manifest_path = ROOT / 'assets/images/manifest.json'
manifest = json.loads(manifest_path.read_bytes())
helper = runpy.run_path(str(ROOT / 'tools/bundle-editorial-images.py'))
rows = json.loads((BASE / 'user-cover-selections.json').read_bytes())
assert len(rows) == 3 and len({row['entry_id'] for row in rows}) == 3
admitted = []
for row in rows:
    source = BASE / row['file']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == row['source_sha256']
    with helper['Image'].open(source) as image:
        dimensions = image.size
        full, small, alpha = helper['prepare_rasters'](image)
    key = hashlib.sha256(row['url'].encode()).hexdigest()[:24]
    suffix = '.png' if alpha else '.jpg'
    relative = f'assets/images/{key}{suffix}'
    preview = f'assets/images/previews/{key}{suffix}'
    helper['save_raster'](full, ROOT / relative)
    helper['save_raster'](small, ROOT / preview, preview=True)
    manifest['images'][row['url']] = relative
    manifest['previews'][row['url']] = preview
    manifest['metadata'][row['url']] = {
        'source_width': dimensions[0], 'source_height': dimensions[1],
        'width': full.width, 'height': full.height,
        'preview_width': small.width, 'preview_height': small.height,
        'sha256': hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(),
        'alpha_preserved': alpha, 'alpha_composited': False,
        'alpha_policy_version': 1, 'acquisition': 'user_selected_imdb_cover',
        'source_page': row['url'], 'title': row['title'] + ': cover',
        'credit': 'Cover selected by Andrea Sgarro from IMDb',
        'license': 'Original image rights retained by their respective owners.',
    }
    manifest['failures'].pop(row['url'], None)
    entry = owners[row['entry_id']]
    index = entry.get('preferred_image', 0)
    old_url = entry['images'][index]['url']
    replacement = {
        'url': row['url'], 'title': row['title'] + ': cover',
        'kind': 'cover', 'cover_art': True, 'cover_role': True,
        'source_page': row['url'],
        'credit': 'Cover selected by Andrea Sgarro from IMDb',
        'license': 'Original image rights retained by their respective owners.',
        'width': dimensions[0], 'height': dimensions[1], 'story_paragraph': -1,
        'recovery_local_source': source.relative_to(ROOT).as_posix(),
        'verification': {'sha256': row['source_sha256'],
                         'native_dimensions': list(dimensions),
                         'no_crop': True, 'no_upscale': True},
    }
    for item_index, image in enumerate(entry['images']):
        if image['url'] == old_url:
            entry['images'][item_index] = copy.deepcopy(replacement)
    admitted.append({'entry_id': entry['id'], 'image_index': index,
                     'old_url': old_url, 'url': row['url'],
                     'native_dimensions': list(dimensions)})

def protected(document):
    result = copy.deepcopy(document)
    for entry in result['entries']:
        if entry['id'] in {row['entry_id'] for row in rows}:
            entry.pop('images', None)
    return result

assert protected(catalog) == protected(json.loads(original))
assert path.read_bytes() == original, 'Concurrent catalogue mutation'
backup = BASE / 'catalog-before-selected-covers.json'
assert not backup.exists(), 'Cover selections already admitted'
backup.write_bytes(original)
for target, document in ((manifest_path, manifest), (path, catalog)):
    temporary = target.with_suffix('.selected-covers.tmp')
    temporary.write_text(json.dumps(document, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    temporary.replace(target)
(BASE / 'selected-cover-receipt.json').write_text(json.dumps(admitted, indent=2) + '\n', encoding='utf8')
print('APPLIED user-selected Zelda, Yoshi and Saros covers; no crop or upscale')
