"""Source-bound admission of independently reviewed new game articles."""
import copy
import hashlib
import json
from pathlib import Path
from PIL import Image


def apply(entries, root, manifest_name='museum-new-game-articles-reviewed.json'):
    root = Path(root).resolve()

    def pinned(path, sha):
        target = (root / path).resolve()
        if not target.is_relative_to(root) or not target.is_file():
            raise ValueError('Invalid reviewed article source: ' + str(path))
        raw = target.read_bytes()
        if hashlib.sha256(raw).hexdigest() != sha:
            raise ValueError('Reviewed article source changed: ' + str(path))
        return raw

    manifest = json.loads((root / 'content/expansion' / manifest_name).read_bytes())
    if manifest.get('publication_status') != 'independently_reviewed':
        raise ValueError('New articles are not independently reviewed')
    by_id = {e['id']: e for e in entries}
    if len(by_id) != len(entries):
        raise ValueError('Duplicate current article ID')
    additions = []
    for batch in manifest['batches']:
        candidate = json.loads(pinned(batch['candidate_path'], batch['candidate_sha256']))
        peer = json.loads(pinned(batch['peer_path'], batch['peer_sha256']))
        if peer.get('status') != 'PASS' or peer.get('candidate_sha256') != batch['candidate_sha256']:
            raise ValueError('New article peer does not bind this candidate')
        for path, sha in candidate['source_files'].items():
            pinned(path, sha)
        layout = json.loads(pinned(batch['native_layout_path'], batch['native_layout_sha256']))
        composition = json.loads(pinned(batch['native_composition_path'], batch['native_composition_sha256']))
        if set(batch['groups']) != {e['id'] for e in candidate['entries']}:
            raise ValueError('New article owner set mismatch')
        for entry in candidate['entries']:
            identifier = entry['id']
            body = entry['body']
            groups = batch['groups'][identifier]
            flat = [i for group in groups for i in group]
            if (not body or len(body) != len(entry['story_headings']) or not groups
                    or any(not group for group in groups)
                    or any(type(i) is not int for i in flat)
                    or flat != list(range(len(body)))):
                raise ValueError('Invalid complete paragraph groups')
            actual = [r for r in layout['scoped_composed_narrative_checks'] if r['entry_id'] == identifier]
            if [r['paragraphs'] for r in actual] != groups or not all(r['complete_source_layout'] for r in actual):
                raise ValueError('Native text layout does not match article groups')
            composed = next(e for e in composition['entries'] if e['entry_id'] == identifier)
            cards = [c for c in composed['cards'] if c['paragraph'] >= 0]
            if [[c['paragraph'], *c['continuation']] for c in cards] != groups:
                raise ValueError('Native composition does not match article groups')
            cover = entry['preferred_image']
            pixels = set()
            for image in entry['images']:
                source = image['recovery_local_source']
                raw = pinned(source, image['verification']['sha256'])
                if source not in candidate['source_files']:
                    raise ValueError('Image is not a pinned candidate source')
                with Image.open(root / source) as picture:
                    picture.load()
                    if picture.size != (image['width'], image['height']):
                        raise ValueError('Original image dimensions changed')
                    identity = hashlib.sha256(picture.convert('RGBA').tobytes()).hexdigest()
                if identity in pixels:
                    raise ValueError('Repeated original image')
                pixels.add(identity)
            identities = []
            for card in cards:
                if card['image_index'] == cover:
                    raise ValueError('Cover repeated in narrative')
                if card['image_index'] < 0 and card['video'] < 0:
                    raise ValueError('Unillustrated new article chapter')
                if card['image_url']:
                    identities.append(card['image_url'])
            if len(set(identities)) != len(identities):
                raise ValueError('Repeated narrative image')
            if identifier in by_id:
                if any(by_id[identifier].get(key) != value for key, value in entry.items()):
                    raise ValueError('New article ID collision: ' + identifier)
                continue
            if any(e['title'] == entry['title'] and e['year'] == entry['year'] for e in by_id.values()):
                raise ValueError('New article title/year collision: ' + identifier)
            proposed = copy.deepcopy(entry)
            additions.append(proposed)
            by_id[identifier] = proposed
    entries.extend(additions)
    return {'status': 'PASS', 'added': [e['id'] for e in additions]}
