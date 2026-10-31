"""One Minecraft release stop; retain its public-development history internally."""
import copy

SOURCE_ID = 'daily-05-17'
TARGET_ID = 'minecraft'


def apply(entries):
    by_id = {entry['id']: entry for entry in entries}
    source, target = by_id.get(SOURCE_ID), by_id.get(TARGET_ID)
    if source is None:
        return {'status': 'already_consolidated', 'canonical_id': TARGET_ID}
    if target is None:
        raise ValueError('Minecraft full-release exhibit is absent')
    if target['year'] != 2011 or target.get('date', {}).get('month') != 11 or target['date'].get('day') != 18:
        raise ValueError('Minecraft consolidation requires its 18 November 2011 release stop')
    previous = copy.deepcopy(target)
    archived = copy.deepcopy(source)
    body, headings, maps = [], [], {}
    # The prototype history precedes the completed game's two existing passages.
    # Keep complete source paragraphs, avoiding only verbatim duplicates.
    for record in (source, previous):
        mapping = {}
        for index, paragraph in enumerate(record.get('body', [])):
            if paragraph not in body:
                body.append(paragraph)
                titles = record.get('story_headings', [])
                headings.append(titles[index] if index < len(titles) else record['title'])
            mapping[index] = body.index(paragraph)
        maps[record['id']] = mapping
    target['body'], target['story_headings'] = body, headings
    preferred = previous.get('images', [])
    preferred_url = preferred[min(previous.get('preferred_image', 0), len(preferred)-1)]['url'] if preferred else None
    photos, known = [], set()
    for record in (previous, source):
        for original in record.get('images', []):
            if original['url'] in known:
                continue
            image = copy.deepcopy(original)
            paragraph = image.get('story_paragraph')
            if isinstance(paragraph, int) and paragraph >= 0:
                image['story_paragraph'] = maps[record['id']].get(paragraph, -1)
            # The main-block artwork is never duplicated as an internal card.
            if image['url'] == preferred_url:
                image['story_paragraph'] = -1
            photos.append(image)
            known.add(image['url'])
    target['images'] = photos
    target['preferred_image'] = next((i for i, image in enumerate(photos) if image['url'] == preferred_url), 0)
    for field, identity in [('videos', 'youtube_id'), ('sources', 'url'), ('editorial_features', 'id')]:
        combined, seen = [], set()
        for record in (previous, source):
            for original in record.get(field, []):
                token = (original.get(identity), original.get('start_seconds'), original.get('end_seconds')) if field == 'videos' else original.get(identity)
                if token in seen:
                    continue
                item = copy.deepcopy(original)
                paragraph = item.get('story_paragraph')
                if field == 'videos' and isinstance(paragraph, int) and paragraph >= 0:
                    item['story_paragraph'] = maps[record['id']].get(paragraph, -1)
                combined.append(item)
                seen.add(token)
        if combined:
            target[field] = combined
    provenance = target.setdefault('provenance', {})
    if not isinstance(provenance, dict):
        provenance = {'original_record': provenance}
        target['provenance'] = provenance
    provenance['consolidated_public_development_record'] = archived
    provenance['release_consolidation'] = {
        'canonical_release': '2011-11-18',
        'historical_public_build': '2009-05-17',
        'old_id': SOURCE_ID,
        'paragraph_index_maps': maps,
        'policy': 'One commercial-release timeline stop; complete public-development prose retained in the article.'}
    target['explicit_story_media_only'] = True
    target['calendar_only'] = False
    for record in entries:
        related = [TARGET_ID if value == SOURCE_ID else value for value in record.get('related_ids', [])]
        record['related_ids'] = list(dict.fromkeys(value for value in related if value != record['id']))
    target['related_ids'] = list(dict.fromkeys(target.get('related_ids', []) + [value for value in source.get('related_ids', []) if value not in (SOURCE_ID, TARGET_ID)]))
    entries[:] = [record for record in entries if record['id'] != SOURCE_ID]
    return {'status': 'PASS', 'canonical_id': TARGET_ID, 'removed_id': SOURCE_ID,
            'paragraphs_preserved': len(body), 'unique_images': len(photos),
            'original_target_soundtrack_preserved': target.get('soundtrack') == previous.get('soundtrack'),
            'original_target_features_preserved': all(feature in target.get('editorial_features', []) for feature in previous.get('editorial_features', []))}
