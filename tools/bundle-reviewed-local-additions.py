"""Register only missing offline images from their already reviewed local originals.

Uses the existing production raster policy. Never makes network requests or
rewrites existing manifest records, original sources, or the staged PS5 folder.
"""
from pathlib import Path
import hashlib
import io
import json
import runpy
from PIL import Image, ImageOps

root = Path(__file__).resolve().parents[1]
policy = runpy.run_path(str(root / 'tools/bundle-editorial-images.py'))
manifest_path = root / 'assets/images/manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf8'))
catalog = json.loads((root / 'content/catalog.json').read_text(encoding='utf8'))
images = {}
for entry in catalog['entries']:
    for owner in [entry, *entry.get('editorial_features', [])]:
        for image in owner.get('images', []):
            images.setdefault(image['url'], image)
added = []
for url, image in images.items():
    if url in manifest['images'] and url in manifest['previews']:
        continue
    local = image.get('recovery_local_source') or image.get('local_path')
    if not local:
        raise ValueError('Missing reviewed local original: ' + url)
    source = root / local
    body = source.read_bytes()
    expected = image.get('verification', {}).get('sha256') or image.get('source_sha256')
    if expected and hashlib.sha256(body).hexdigest() != expected:
        raise ValueError('Reviewed local original changed: ' + local)
    with Image.open(io.BytesIO(body)) as original:
        original.load()
        original = ImageOps.exif_transpose(original)
        source_size = original.size
        if min(source_size) < 32:
            raise ValueError('Image below native minimum: ' + local)
        full, preview, alpha = policy['prepare_rasters'](original)
        digest = hashlib.sha256(url.encode()).hexdigest()[:24]
        suffix = '.png' if alpha else '.jpg'
        relative = 'assets/images/' + digest + suffix
        small = 'assets/images/previews/' + digest + suffix
        policy['save_raster'](full, root / relative)
        policy['save_raster'](preview, root / small, preview=True)
    metadata = dict(source_width=source_size[0], source_height=source_size[1],
                    width=full.width, height=full.height,
                    preview_width=preview.width, preview_height=preview.height,
                    sha256=hashlib.sha256((root / relative).read_bytes()).hexdigest(),
                    acquisition='existing_local_original', alpha_composited=False,
                    alpha_preserved=alpha, alpha_policy_version=policy['ALPHA_POLICY_VERSION'])
    for key in ['title', 'source_page', 'creator', 'credit', 'license', 'license_url']:
        if key in image:
            metadata[key] = image[key]
    manifest['images'][url] = relative
    manifest['previews'][url] = small
    manifest['metadata'][url] = metadata
    manifest.get('failures', {}).pop(url, None)
    added.append(url)
temporary = manifest_path.with_suffix('.json.tmp')
temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
temporary.replace(manifest_path)
print(json.dumps(dict(status='PASS_LOCAL_ONLY', added=len(added), urls=added), indent=2))
