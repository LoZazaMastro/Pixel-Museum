#!/usr/bin/env python3
"""Prepare original-image gallery corrections separately from a released build."""
from pathlib import Path
import argparse
import copy
import hashlib
import io
import json
import re
import shutil
from urllib.parse import urlsplit, urlunsplit
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / 'build/research/repeated-card-images-20261101'


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')


def canonical(url):
    parts = urlsplit(url)
    path = re.sub('/+', '/', parts.path)
    if parts.hostname == 'images.launchbox-app.com':
        path = re.sub(r'/r\d+_', '/', path)
    scheme = 'https' if parts.scheme.lower() in ('http', 'https') else parts.scheme.lower()
    return urlunsplit((scheme, parts.netloc.lower(), path, parts.query, ''))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', action='append', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=RESEARCH / 'candidate')
    parser.add_argument('--rebind-2005', action='store_true')
    parser.add_argument('--repair-existing', action='store_true')
    parser.add_argument('--include-severe', action='store_true')
    args = parser.parse_args()
    out = args.output.resolve()
    if not out.is_relative_to(RESEARCH.resolve()):
        parser.error('Candidate must stay in this investigation directory')
    runtime = read(ROOT / 'dist/PPSA70421/content/catalog.json')
    original = read(ROOT / 'content/catalog.json')
    entries = {e['id']: e for e in runtime['entries']}
    authoring = {e['id']: e for e in original['entries']}
    metadata = read(ROOT / 'assets/images/manifest.json').get('metadata', {})
    groups = {}
    if args.rebind_2005:
        for deficit in read(RESEARCH / '2005-deficits.json'):
            groups[deficit['id']] = []
    if args.repair_existing:
        for item in read(RESEARCH / 'existing-gallery-rebinding-approved.json'):
            groups[item['entry_id']] = []
    if args.include_severe:
        for item in read(RESEARCH / 'all-same-severe.json'):
            if item.get('kind') == 'game' and 2000 <= item.get('year', 0) <= 2009:
                groups[item['entry_id']] = []
    discarded = []
    conversions = []
    avoided = set()
    restored_urls = {}
    overlay = {'schema_version': 1, 'images': {}, 'metadata': {}}
    for manifest in args.manifest:
        manifest_data = read(manifest)
        avoided.update(canonical(url) for url in manifest_data.get('avoid_source_urls', []))
        for raw in manifest_data['images']:
            item = copy.deepcopy(raw)
            for field in ('url', 'source_page'):
                if item.get(field, '').startswith('http://'):
                    item[field] = 'https://' + item[field][7:]
            # This GBA conversion is not the Rockport console/PC game described.
            if item['entry_id'] == 'wikipedia-37047259' and ('02c80a3b' in item['url'] or item.get('platform') in ('Nintendo Game Boy Advance', 'Nintendo Game Boy')):
                discarded.append({'url': item['url'], 'reason': 'Different handheld conversion'})
                continue
            path = Path(item['path'])
            if not path.is_absolute():
                path = ROOT / path
            data = path.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            if digest != item['sha256']:
                raise ValueError(f'Changed source file: {path}')
            with Image.open(io.BytesIO(data)) as image:
                if image.size != (item['width'], item['height']):
                    raise ValueError(f'Incorrect source dimensions: {path}')
                format_name = image.format
                if format_name not in ('JPEG', 'PNG', 'GIF', 'BMP', 'TGA'):
                    # stb_image does not support WebP/AVIF. Preserve every
                    # decoded pixel in PNG; never crop, resize or upscale.
                    buffer = io.BytesIO()
                    image.convert('RGBA').save(buffer, format='PNG')
                    data = buffer.getvalue()
                    conversions.append({'url': item['url'], 'from': format_name, 'to': 'PNG',
                                        'source_sha256': digest, 'width': image.width, 'height': image.height})
                    digest = hashlib.sha256(data).hexdigest()
                    item['sha256'] = digest
                    format_name = 'PNG'
            if not 0 < len(data) < 32 * 1024 * 1024:
                raise ValueError(f'Invalid image size: {path}')
            if item['entry_id'] not in entries:
                raise ValueError(f'Unknown entry: {item["entry_id"]}')
            ext = {'JPEG': '.jpg', 'PNG': '.png', 'GIF': '.gif', 'BMP': '.bmp', 'TGA': '.tga'}[format_name]
            relative = f'assets/image-supplements/{digest}{ext}'
            destination = out / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                destination.write_bytes(data)
            overlay['images'][item['url']] = relative
            overlay['metadata'][item['url']] = {'sha256': digest}
            if item.get('registration_only'):
                restored_urls[item['original_url']] = item['url']
                continue
            group = groups.setdefault(item['entry_id'], [])
            if not any(canonical(x['url']) == canonical(item['url']) or x['sha256'] == digest for x in group):
                group.append(item)
    reports = []
    for entry_id, pictures in groups.items():
        entry = entries[entry_id]
        body = entry.get('body', [])
        count = len(body)
        if len(authoring[entry_id].get('body', [])) != count:
            raise ValueError(f'Authoring/runtime paragraph mismatch: {entry_id}')
        old = entry.get('images', [])
        preferred = entry.get('preferred_image', 0)
        cover_url = old[preferred]['url'] if old and 0 <= preferred < len(old) else ''
        used = set()
        used_urls = set()
        assignments = {}
        # Curated paragraph bindings arrive first. Additional originals fill gaps.
        for picture in pictures:
            if picture.get('hero'):
                continue
            paragraph = picture.get('story_paragraph', -1)
            if paragraph in assignments or not 0 <= paragraph < count:
                options = picture.get('story_paragraph_options', range(count))
                paragraph = next((p for p in options if 0 <= p < count and p not in assignments), -1)
                if paragraph < 0:
                    paragraph = next((p for p in range(count) if p not in assignments), -1)
            if paragraph >= 0:
                assignments[paragraph] = picture['url']
                used.add(picture['sha256'])
                used_urls.add(canonical(picture['url']))
        # Retain genuine existing artwork/screenshots when a complete gallery
        # is not available. Covers, packaging, manuals and film thumbnails do
        # not stand in for missing gameplay.
        existing = []
        video_urls = {v.get('poster_url') for v in entry.get('videos', [])}
        for photo in old:
            title = photo.get('title', '').lower()
            if canonical(photo['url']) in avoided:
                continue
            if photo['url'] == cover_url or photo.get('cover_art') or photo['url'] in video_urls or photo.get('kind') == 'video-poster':
                continue
            if any(word in title for word in ('cover', 'packaging', 'box back', 'manual', 'booklet', 'logo', 'film preview')):
                continue
            if photo.get('story_feature', -1) >= 0:
                continue
            if any(canonical(p['url']) == canonical(photo['url']) for p in pictures):
                continue
            identity = metadata.get(photo['url'], {}).get('sha256', photo['url'])
            if identity in used or canonical(photo['url']) in used_urls:
                continue
            used.add(identity)
            used_urls.add(canonical(photo['url']))
            existing.append(photo)
        for photo in existing:
            paragraph = photo.get('story_paragraph', -1)
            if paragraph in assignments or not 0 <= paragraph < count:
                paragraph = next((p for p in range(count) if p not in assignments), -1)
            if paragraph >= 0:
                assignments[paragraph] = photo['url']
        reverse = {url: paragraph for paragraph, url in assignments.items()}
        for target in (entry, authoring[entry_id]):
            photos = target.setdefault('images', [])
            by_url = {p['url']: p for p in photos}
            for picture in pictures:
                photo = by_url.get(picture['url'])
                if photo is None:
                    photo = {'url': picture['url']}
                    photos.append(photo)
                    by_url[photo['url']] = photo
                photo.update({
                    'title': picture['title'], 'width': picture['width'], 'height': picture['height'],
                    'source_page': picture['source_page'],
                    'creator': picture.get('creator', 'Original game developer and publisher'),
                    'credit': picture.get('credit', 'Original game screenshot; source archive credited'),
                    'license': picture.get('license', 'Game imagery remains the property of its respective rights holders'),
                    'license_url': picture.get('license_url', ''),
                    'story_paragraph': reverse.get(picture['url'], -1),
                })
                if picture.get('hero'):
                    photo['cover_art'] = True
                    target['preferred_image'] = photos.index(photo)
                else:
                    photo.pop('cover_art', None)
            for photo in photos:
                if photo.get('story_feature', -1) < 0:
                    photo['story_paragraph'] = reverse.get(photo['url'], -1)
            target['explicit_story_media_only'] = True
        reports.append({'entry_id': entry_id, 'title': entry['title'], 'paragraphs': count,
                        'distinct_bound_images': len(assignments), 'complete': len(assignments) == count,
                        'new_originals': len(pictures), 'bindings': assignments})
    # Historical HTTP records are rejected by Catalog::load. Their already
    # packaged raster bytes can be registered under HTTPS without any fetch
    # or changes to the installed collection archives.
    for document in (runtime, original):
        for entry in document['entries']:
            for owner in [entry] + entry.get('editorial_features', []):
                for photo in owner.get('images', []):
                    if photo.get('url') in restored_urls:
                        photo['url'] = restored_urls[photo['url']]
    for report in reports:
        report['bindings'] = {p: restored_urls.get(url, url) for p, url in report['bindings'].items()}
    write(out / 'content/catalog.json', original)
    runtime['source_catalog_sha256'] = hashlib.sha256((out / 'content/catalog.json').read_bytes()).hexdigest()
    write(out / 'dist/PPSA70421/content/catalog.json', runtime)
    write(out / 'content/collection-image-supplements.json', overlay)
    report = {'entries': reports, 'discarded': discarded, 'lossless_format_conversions': conversions,
              'restored_https_images': len(restored_urls),
              'owners': len(reports), 'complete': sum(x['complete'] for x in reports),
              'original_images': len(overlay['images']),
              'missing': [x for x in reports if not x['complete']]}
    write(out / 'report.json', report)
    print(json.dumps({k: report[k] for k in ('owners', 'complete', 'original_images')}))
    print('Still short:', ', '.join(x['entry_id'] for x in report['missing']))


if __name__ == '__main__':
    main()
