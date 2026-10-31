"""Quarantine explicitly reviewed wrong/uncertain inherited image associations.

No source bytes are edited. Every removed record is archived in the returned
receipt. A subject match never becomes a copyright or publication signoff.
"""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path

REVIEWS = (
    'content/editorial/legacy-image-visual-review-00-07.json',
    'content/editorial/legacy-image-visual-review-08-14.json',
)
HOLD = {'quarantine_unrelated', 'needs_exact_identity_review'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked_reviews(project):
    project = Path(project)
    binding = json.loads((project / 'content/editorial/legacy-image-review-admission.json').read_text(encoding='utf-8'))
    rows, hashes = [], {}
    require(set(binding['reviews']) == set(REVIEWS), 'Unreviewed legacy image batch')
    for relative in REVIEWS:
        raw = (project / relative).read_bytes()
        hashes[relative] = hashlib.sha256(raw).hexdigest()
        require(hashes[relative] == binding['reviews'][relative], 'Legacy visual review changed: ' + relative)
        rows.extend(json.loads(raw)['entries'])
    require(len(rows) == 440 and {row['index'] for row in rows} == set(range(440)), 'Incomplete legacy image visual review')
    require(len({row['url'] for row in rows}) == 440, 'Duplicate legacy visual review URL')
    correction_path = project / 'content/expansion/switch-2017-image-identity-quarantine.json'
    correction_bytes = correction_path.read_bytes()
    correction_hash = hashlib.sha256(correction_bytes).hexdigest()
    require(correction_hash == '740b4f00eaa0247ee52095bd875e2402ca227823d099cf8f2f1684371f57a755', 'Switch identity correction changed since review')
    correction = json.loads(correction_bytes)
    row = next(row for row in rows if row['index'] == correction['source_index'])
    require(row == correction['previous_review'], 'Superseded Switch review no longer matches')
    require({owner['owner_id'] for owner in row['owner_decisions']} == {item['entry_id'] for item in correction['entries']}, 'Switch correction ownership changed')
    for owner in row['owner_decisions']:
        owner['decision'] = 'quarantine_unrelated'
        owner['reason'] = correction['reason']
    row['decision'] = 'quarantine_unrelated'
    row['observed_visual_content'] = correction['visual_finding']
    hashes[str(correction_path.relative_to(project)).replace('\\', '/')] = correction_hash
    return rows, hashes


def integrate(entries, project):
    rows, hashes = checked_reviews(project)
    working = copy.deepcopy(entries)
    lookup = {entry['id']:entry for entry in working}
    require(len(lookup) == len(working), 'Duplicate entry before visual review')
    removed, matches = [], 0
    for row in rows:
        decisions = row.get('owner_decisions', row['owners'])
        for owner in decisions:
            identifier = owner.get('owner_id', owner.get('id'))
            state = owner.get('decision', row['decision'])
            require(identifier in lookup, 'Missing reviewed image owner: ' + identifier)
            require(state in HOLD | {'approve_subject_match'}, 'Unknown visual review decision')
            entry = lookup[identifier]
            images = entry.get('images', [])
            positions = [i for i,image in enumerate(images) if image.get('url') == row['url']]
            require(len(positions) == 1, 'Reviewed association missing or repeated: ' + identifier + '/' + str(row['index']))
            position = positions[0]
            image = images[position]
            require(image.get('verification', {}).get('sha256') == row['sha256'], 'Reviewed image bytes changed: ' + identifier)
            if state in HOLD:
                removed.append({'entry_id':identifier, 'index':row['index'],
                    'decision':state, 'reason':owner.get('reason', row['reason']),
                    'original_image_index':position, 'original_image':copy.deepcopy(image)})
                images.pop(position)
            else:
                matches += 1
    receipt = {'schema_version':1, 'review_sha256':hashes,
        'visually_inspected_distinct_images':440, 'retained_subject_matched_associations':matches,
        'quarantined_associations':removed,
        'source_bodies_or_translations_changed':False, 'image_bytes_modified':False,
        'rights_signoffs':0, 'editorial_signoffs':0,
        'policy':'Only explicit wrong/uncertain URL-owner associations are omitted. Original records remain here; subject relevance does not establish rights, release edition, date or native-image quality.'}
    entries[:] = working
    return receipt
