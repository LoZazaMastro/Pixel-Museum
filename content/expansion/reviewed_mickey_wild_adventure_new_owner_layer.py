"""Append the exact independently reviewed Mickey Wild Adventure owner once."""
from pathlib import Path
import copy, hashlib, json

def apply(entries, root):
    root = Path(root).resolve()
    policy = json.loads((root/'content/expansion/museum-reviewed-mickey-wild-adventure-new-owner-policy.json').read_bytes())
    def pinned(path, digest):
        p = (root/path).resolve()
        if not p.is_relative_to(root): raise ValueError('Input escapes project')
        raw = p.read_bytes()
        if hashlib.sha256(raw).hexdigest() != digest: raise ValueError('Immutable input changed: '+path)
        return raw
    for item in policy['immutable_inputs']: pinned(item['path'], item['sha256'])
    review = json.loads(pinned(policy['root_review_path'], policy['root_review_sha256']))
    if review['status'] != 'ROOT_REVIEWED_MICKEY_WILD_ADVENTURE_COMPLETE_NEW_OWNER_PRIVATE_ONLY':
        raise ValueError('Root full review changed')
    source = json.loads(pinned(policy['source_path'], policy['source_sha256']))
    if len(source['entries']) != 1: raise ValueError('Exactly one new owner required')
    entry = source['entries'][0]
    if entry['id'] != 'mickeys-wild-adventure' or len(entry['body']) != 3 or len(entry['images']) != 4 or len(entry['soundtrack']['tracks']) != 27:
        raise ValueError('Reviewed owner scope changed')
    original = json.loads(pinned(source['original_source_path'], source['original_source_sha256']))
    music = json.loads(pinned(source['music_source_path'], source['music_source_sha256']))
    if not all(any(x['path']==path and x['sha256']==digest for x in review['immutable_inputs']) for path,digest in [(source['original_source_path'],source['original_source_sha256']),(source['music_source_path'],source['music_source_sha256'])]): raise ValueError('Original source and music not Root-bound')
    o=original['entry']
    if any(entry[k]!=o[k]for k in ('id','title','year','subtitle','summary','body')) or entry['story_headings']!=o['headings'] or entry['soundtrack']!=music['soundtrack']:raise ValueError('Root source text/music changed in schema mapping')
    current = [e for e in entries if e['id'] == entry['id']]
    if current:
        if len(current) != 1 or current[0] != entry: raise ValueError('Existing owner differs from reviewed source')
        return {'status':'PASS', 'changed':[], 'available_tracks':27}
    entries.append(copy.deepcopy(entry))
    return {'status':'PASS', 'changed':[entry['id']], 'available_tracks':27}
