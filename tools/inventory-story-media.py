"""Build one actionable media queue from authored cards and the local image cache."""
from pathlib import Path
import json, re
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/research/editorial-resume-20261030'

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def main():
    manifest = read(ROOT / 'assets/images/manifest.json')
    missing_files = []
    gaps = []
    manuals = []
    counts = Counter()
    seen_urls = set()
    manual_pattern = re.compile(r'\bbooklet\b|\binstruction\b|\bmanual\b|\blibretto\b|\buser guide\b', re.I)
    for collection in ('catalog', 'human-history'):
        for entry in read(ROOT / f'content/{collection}.json')['entries']:
            for owner in [entry, *entry.get('editorial_features', [])]:
                photos = owner.get('images', [])
                body = owner.get('body', [])
                video_targets = set()
                if owner is entry:
                    for v in entry.get('videos', []):
                        p = v.get('story_paragraph', -1)
                        if isinstance(p, int) and 0 <= p < len(body):
                            video_targets.add(p)
                        elif body and 0 not in video_targets:
                            video_targets.add(0)
                    choice = entry.get('preferred_image', 0)
                    if isinstance(choice, str):
                        choice = next((i for i, x in enumerate(photos) if x.get('url') == choice), 0)
                    cover = photos[choice].get('url') if photos and isinstance(choice, int) and choice < len(photos) else None
                else:
                    cover = None
                covered = set(video_targets)
                candidates = []
                manual_indices = []
                for i, image in enumerate(photos):
                    url = image.get('url', '')
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        missing = [group for group in ('images', 'previews') if not manifest.get(group, {}).get(url) or not (ROOT / manifest[group][url]).is_file()]
                        if missing:
                            missing_files.append({'entry_id': entry['id'], 'owner_id': owner['id'], 'url': url, 'missing': missing})
                    text = ' '.join(str(image.get(k, '')) for k in ('title', 'caption', 'source_page', 'url'))
                    if manual_pattern.search(text.replace('manual transmission', '')):
                        manual_indices.append(i)
                    p = image.get('story_paragraph', -1)
                    if url and url != cover and isinstance(p, int) and 0 <= p < len(body):
                        covered.add(p)
                    elif url and url != cover and (p is None or p == -1):
                        candidates.append(i)
                # This queue distinguishes unmapped legacy gallery candidates from a missing asset.
                missing = [p for p in range(len(body)) if p not in covered]
                if missing:
                    gaps.append({'collection': collection, 'entry_id': entry['id'], 'owner_id': owner['id'],
                        'title': owner.get('title', entry['title']), 'year': entry['year'], 'kind': entry.get('kind'),
                        'body_count': len(body), 'missing_explicit_indices': missing,
                        'unused_gallery_candidates': candidates, 'explicit_only': owner.get('explicit_story_media_only', entry.get('explicit_story_media_only', False))})
                if len(manual_indices) > 2 and len(manual_indices) / max(1, len(photos)) > .4:
                    manuals.append({'collection': collection, 'entry_id': entry['id'], 'owner_id': owner['id'],
                                    'title': owner.get('title', entry['title']), 'manual_image_indices': manual_indices,
                                    'total_images': len(photos)})
                counts['text_cards'] += len(body)
                counts['explicitly_illustrated_or_video'] += len(covered)
    report = {'counts': dict(counts), 'unique_image_urls': len(seen_urls),
              'missing_offline_files': missing_files, 'mapping_queue': gaps, 'manual_dominance': manuals,
              'note': 'Mapping gaps are not all blank runtime cards: legacy galleries can be distributed by the existing story director. Explicit curated mapping is preferred for revised content.'}
    path = BASE / 'story-media-inventory.json'
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'text_cards': counts['text_cards'], 'missing_offline_images': len(missing_files),
                      'owners_needing_mapping': len(gaps), 'manual_dominance': len(manuals)}))

if __name__ == '__main__':
    main()
