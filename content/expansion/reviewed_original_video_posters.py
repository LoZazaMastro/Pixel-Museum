"""Bind reviewed original previews to their exact current films, preserving prose."""
import collections
import copy
import hashlib
import json
from pathlib import Path
from PIL import Image
import runpy


def digest_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def apply_candidate(entries, root, candidate, minimum_width=600):
    assert minimum_width in (480, 600), 'Only original HD previews or explicitly reviewed native HQ fallback'
    root = Path(root)
    excluded = runpy.run_path(str(root / 'content/expansion/user_sports_policy.py'))['excluded_ids'](root)
    owners = {}
    for entry in entries:
        owners[(entry['id'], entry['id'])] = entry
        for feature in entry.get('editorial_features', []):
            owners[(entry['id'], feature['id'])] = feature
    groups = collections.defaultdict(list)
    for row in candidate['rows']:
        groups[(row['entry_id'], row['owner_id'])].append(row)
    changed = []
    appended = 0
    for key, rows in groups.items():
        if key not in owners:
            if key[0] in excluded:
                continue
            raise ValueError('Reviewed film owner disappeared: ' + key[1])
        owner = owners[key]
        before_hashes = {row['owner_images_before_sha256'] for row in rows}
        if len(before_hashes) != 1:
            raise ValueError('Conflicting reviewed image-owner guards')
        original_images = owner.get('images', [])
        additions = [copy.deepcopy(row['new_poster']) for row in rows
                     if row['action'] == 'append_reserved_video_poster_and_bind_film']
        before_hash = next(iter(before_hashes))
        already = False
        if digest(original_images) != before_hash:
            if (additions and original_images[-len(additions):] == additions
                    and digest(original_images[:-len(additions)]) == before_hash):
                already = True
            else:
                raise ValueError('Reviewed film owner images changed: ' + key[1])
        videos = copy.deepcopy(owner.get('videos', []))
        any_video_change = False
        for row in rows:
            image = row['new_poster']
            local = root / image['recovery_local_source']
            if digest_file(local) != image['verification']['sha256']:
                raise ValueError('Original film preview bytes changed')
            with Image.open(local) as picture:
                picture.load()
                if picture.size != (image['width'], image['height']) or picture.width < minimum_width:
                    raise ValueError('Original film preview dimensions changed')
            if row['action'] == 'cache_existing_image_and_bind_film':
                index = row['existing_image_index']
                if original_images[index]['url'] != image['url']:
                    raise ValueError('Existing yearly film image identity changed')
            elif row['action'] != 'append_reserved_video_poster_and_bind_film':
                raise ValueError('Unknown reviewed preview action')
            matches = [n for n, video in enumerate(videos)
                       if video.get('youtube_id') == row['youtube_id']]
            if len(matches) != 1:
                raise ValueError('Reviewed current film identity is not unique')
            index = matches[0]
            expected = copy.deepcopy(row['video_before'])
            expected['poster_url'] = image['url']
            if videos[index] not in (row['video_before'], expected):
                raise ValueError('Reviewed current film metadata changed')
            any_video_change |= videos[index] != expected
            videos[index] = expected
        if not already and additions:
            if any(image['url'] in {old['url'] for old in original_images} for image in additions):
                raise ValueError('Refusing duplicate original film preview image')
            owner['images'] = original_images + additions
            appended += len(additions)
        if any_video_change:
            owner['videos'] = videos
        if any_video_change or (additions and not already):
            changed.append({'entry_id': key[0], 'owner_id': key[1]})
    return {'status': 'PASS', 'changed_owners': changed,
            'source_bound_films': len(candidate['rows']), 'appended_reserved_images': appended,
            'existing_matching_images_preserved': sum(row['action'] == 'cache_existing_image_and_bind_film'
                                                      for row in candidate['rows'])}


def apply(entries, root):
    root = Path(root)
    path = root / 'content/expansion/museum-original-film-posters-reviewed.json'
    if not path.is_file():
        return {'status': 'not_admitted'}
    plan = json.loads(path.read_text(encoding='utf8'))
    if plan.get('publication_status') != 'independently_reviewed':
        return {'status': 'not_admitted'}
    candidate_path = root / plan['candidate_path']
    peer_path = root / plan['peer_path']
    if digest_file(candidate_path) != plan['candidate_sha256'] or digest_file(peer_path) != plan['peer_sha256']:
        raise ValueError('Reviewed film preview candidate or peer changed')
    peer = json.loads(peer_path.read_text(encoding='utf8'))
    if peer.get('status') != 'PASS' or peer.get('candidate_sha256') != plan['candidate_sha256']:
        raise ValueError('Original film preview peer is not source-bound PASS')
    candidate = json.loads(candidate_path.read_text(encoding='utf8'))
    if digest_file(root / candidate['source_report_path']) != candidate['source_report_sha256']:
        raise ValueError('Original film preview discovery report changed')
    return apply_candidate(entries, root, candidate)
