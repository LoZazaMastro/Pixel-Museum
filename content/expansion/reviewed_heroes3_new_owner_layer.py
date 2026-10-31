"""Append the exact independently reviewed Heroes III owner once."""
from pathlib import Path
import copy, hashlib, json

def apply(entries, root):
    root = Path(root).resolve()
    policy = json.loads((root/'content/expansion/museum-reviewed-heroes3-new-owner-policy.json').read_bytes())
    def pinned(path, digest):
        p = (root/path).resolve()
        if not p.is_relative_to(root): raise ValueError('Input escapes project')
        raw = p.read_bytes()
        if hashlib.sha256(raw).hexdigest() != digest: raise ValueError('Immutable input changed: '+path)
        return raw
    for item in policy['immutable_inputs']: pinned(item['path'], item['sha256'])
    review = json.loads(pinned(policy['root_review_path'], policy['root_review_sha256']))
    if review['status'] != 'ROOT_REVIEWED_HEROES3_COMPLETE_EDITORIAL_NEW_OWNER_MUSIC_PENDING_PRIVATE_ONLY':
        raise ValueError('Root full review changed')
    source = json.loads(pinned(policy['source_path'], policy['source_sha256']))
    if len(source['entries']) != 1: raise ValueError('Exactly one new owner required')
    entry = source['entries'][0]
    if entry['id'] != 'heroes-of-might-and-magic-iii' or len(entry['body']) != 3 or len(entry['images']) != 4 or 'soundtrack'in entry:
        raise ValueError('Reviewed owner scope changed')
    source_pin = next((x for x in review['immutable_inputs'] if x['sha256'] == policy['source_sha256']), None)
    if source_pin is None or json.loads(pinned(source_pin['path'], source_pin['sha256'])) != source:
        raise ValueError('Source differs from Root-reviewed candidate')
    current = [e for e in entries if e['id'] == entry['id']]
    if current:
        if len(current) != 1 or current[0] != entry: raise ValueError('Existing owner differs from reviewed source')
        return {'status':'PASS', 'changed':[], 'available_tracks':0}
    entries.append(copy.deepcopy(entry))
    return {'status':'PASS', 'changed':[entry['id']], 'available_tracks':0}
