"""Append only the two corrected, independently Root-reviewed Ape owners."""
from pathlib import Path
import copy, hashlib, json

def apply(entries, root):
    root=Path(root).resolve()
    def pinned(path, digest):
        p=(root/path).resolve()
        if not p.is_relative_to(root):raise ValueError('Input escapes root')
        raw=p.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('Immutable input changed')
        return raw
    policy=json.loads((root/'content/expansion/museum-reviewed-ape-two-new-owner-policy.json').read_bytes())
    if policy['publication_status']!='independently_reviewed':raise ValueError('Unreviewed policy')
    for pin in policy['immutable_inputs']:pinned(pin['path'],pin['sha256'])
    review=json.loads(pinned(policy['root_review_path'],policy['root_review_sha256']))
    if review['status']!='ROOT_REVIEWED_TWO_CORRECTED_APE_NEW_OWNERS_COMPLETE_PRIVATE_ONLY':raise ValueError('Root review changed')
    source=json.loads(pinned(policy['source_path'],policy['source_sha256']))
    selected=source['entries']
    if [e['id']for e in selected]!=['wikipedia-1350206','wikipedia-3575822'] or [len(e['soundtrack']['tracks'])for e in selected]!=[50,79]:raise ValueError('Exact two-owner scope changed')
    if len(source['components'])!=2:raise ValueError('Component count changed')
    for e,component in zip(selected,source['components']):
        for key in ('source','target','music'):
            path=component[key+'_path'];digest=component[key+'_sha256']
            if not any(x['path']==path and x['sha256']==digest for x in review['immutable_inputs']):raise ValueError('Component not Root-bound')
        original=json.loads(pinned(component['source_path'],component['source_sha256']));o=original['entry']
        music=json.loads(pinned(component['music_path'],component['music_sha256']))
        if any(e[k]!=o[k]for k in ('id','title','year','subtitle','summary','body')) or e['story_headings']!=o['headings'] or e['platforms']!=o['platforms']:raise ValueError('Source wording changed during mapping')
        if e['date']['month']!=o['month'] or e['date']['day']!=o['day'] or e['soundtrack']!=music['after_soundtrack']:raise ValueError('Release/music changed during mapping')
        images=[original['cover']]+original['story_images']
        if len(images)!=len(e['images']):raise ValueError('Image count changed')
        for image,old in zip(e['images'],images):
            if image['url']!=old['source_url'] or image['recovery_local_source']!=old['path'] or image['verification']['sha256']!=old['sha256'] or image['caption']!=old.get('caption',''):raise ValueError('Image binding/caption changed')
    # Validate both rows before appending either: a conflicting existing row is fatal.
    missing=[]
    for e in selected:
        current=[x for x in entries if x['id']==e['id']]
        if current and (len(current)!=1 or current[0]!=e):raise ValueError('Existing Ape owner differs')
        if not current:missing.append(copy.deepcopy(e))
    entries.extend(missing)
    return {'status':'PASS','changed':[e['id']for e in missing],'available_tracks':129}
