"""Admit exact replacements after quarantine; deduplicate equal image bytes."""
import copy
import hashlib
import json
from pathlib import Path

FILES = ('legacy-media-replacements-01.json', 'legacy-media-replacements-02.json', 'legacy-media-replacements-03.json')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def body_hash(body):
    return hashlib.sha256(json.dumps(body, ensure_ascii=False).encode()).hexdigest()


def integrate(entries, project, quarantine):
    project = Path(project)
    bindings = json.loads((project / 'content/editorial/legacy-media-replacement-admissions.json').read_text(encoding='utf-8'))
    working = copy.deepcopy(entries)
    lookup = {entry['id']:entry for entry in working}
    affected = {(row['entry_id'], row['index']) for row in quarantine['quarantined_associations']}
    actions, input_hashes = [], {}
    for filename in FILES:
        raw = (project / 'content/expansion' / filename).read_bytes()
        binding = bindings['batches'][filename]
        file_hash = hashlib.sha256(raw).hexdigest()
        require(file_hash == binding['sha256'], 'Replacement batch changed: ' + filename)
        input_hashes[filename] = file_hash
        rows = json.loads(raw)['entries']
        require({row['entry_id'] for row in rows} == set(binding['body_sha256']), 'Replacement owner set changed')
        for row in rows:
            identifier = row['entry_id']
            require(identifier in lookup, 'Replacement owner missing: ' + identifier)
            entry = lookup[identifier]
            require(body_hash(entry['body']) == binding['body_sha256'][identifier], 'Replacement owner prose changed: ' + identifier)
            require(all((identifier, index) in affected for index in row['replaces_quarantined_indices']), 'Replacement lacks matching quarantine: ' + identifier)
            images = entry.setdefault('images', [])
            added, superseded = [], []
            for incoming in row['images']:
                require(incoming['url'].startswith('https://') and incoming.get('source_page')
                        and incoming.get('credit') and incoming.get('license')
                        and incoming.get('quality_verified')
                        and max(incoming.get('width', 0), incoming.get('height', 0)) >= 1600,
                        'Replacement image lacks reviewed identity/rights/quality evidence')
                sha = incoming.get('verification', {}).get('sha256', '')
                require(len(sha) == 64, 'Replacement lacks decoded-byte hash')
                positions = [index for index, image in enumerate(images)
                             if image.get('url') == incoming['url']
                             or image.get('verification', {}).get('sha256') == sha]
                for index in reversed(positions):
                    superseded.append({'original_index':index, 'original_image':copy.deepcopy(images.pop(index)),
                        'reason':'Same exact image bytes or URL; replace generic/inaccurate edition caption without repeating a gallery frame.'})
                if identifier in binding.get('preferred_cover_owners', []):
                    images.insert(0, copy.deepcopy(incoming))
                else:
                    images.append(copy.deepcopy(incoming))
                added.append(copy.deepcopy(incoming))
            actions.append({'entry_id':identifier, 'replaces_quarantined_indices':row['replaces_quarantined_indices'],
                'images_admitted':added, 'same_content_records_superseded':superseded,
                'identity_review':row.get('identity_review', row['images'][0].get('edition_review', '')),
                'paragraph_mappings_created':0})
    entries[:] = working
    return {'schema_version':1, 'input_sha256':input_hashes, 'actions':actions,
        'original_prose_or_translations_changed':False, 'new_subjects_claimed':0,
        'image_bytes_modified':False, 'editorial_publication_signoffs':0,
        'review_note':'Root independently inspected replacement contact sheets and original Wright/PSP photographs. Later PC/PS3 editions remain explicit in captions. All source credit and licence fields preserved; no blanket game-art rights assertion.'}
