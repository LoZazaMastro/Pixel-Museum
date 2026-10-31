"""Reviewed source-bound 2012 append/replacement layer; validate all before mutation."""
from pathlib import Path
import copy, hashlib, json

def packed(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def digest(x):return hashlib.sha256(packed(x)).hexdigest()
def file_sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def apply(entries, root, config_path=None):
    root=Path(root).resolve()
    if config_path is None:config_path=root/'content/expansion/museum-reviewed-2012-mixed-owner-layer.json'
    config=json.loads(Path(config_path).read_bytes())
    if config['status']!='independently_reviewed':raise ValueError('Unreviewed config')
    def pinned(path, expected):
        p=(root/path).resolve()
        if not p.is_relative_to(root) or file_sha(p)!=expected:raise ValueError('Source, peer or approval pin changed')
        return json.loads(p.read_bytes())
    ids=[e['id'] for e in entries]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate existing owner')
    planned=set();actions=[]
    for row in config['rows']:
        oid=row['owner_id']
        if oid in planned:raise ValueError('Duplicate planned owner')
        planned.add(oid)
        for extra in row.get('additional_immutable_inputs',[]):pinned(extra['path'],extra['sha256'])
        approval=pinned(row['approval_path'],row['approval_sha256'])
        if approval.get('status')!=row['approval_status'] or approval.get('plan_sha256')!=row['plan_sha256']:raise ValueError('Wrong Root approval')
        source=pinned(row['source_path'],row['source_sha256'])
        peer=pinned(row['peer_path'],row['peer_sha256'])
        if peer.get('status')!=row['peer_status'] or not peer['status'].startswith('ROOT_') or 'PEER_PASS_PRIVATE_ONLY' not in peer['status']:raise ValueError('Wrong source peer')
        if peer.get('source_sha256',peer.get('candidate_sha256'))!=row['source_sha256']:raise ValueError('Peer does not bind source')
        matches=[e for e in source['entries'] if e['id']==oid]
        if len(matches)!=1:raise ValueError('Reviewed source owner missing or duplicated')
        reviewed=copy.deepcopy(matches[0])
        nested_ids=set()
        for nested in row.get('nested_features',[]):
            nid=nested['owner_id']
            if nid in nested_ids:raise ValueError('Duplicate nested feature')
            nested_ids.add(nid)
            ns=pinned(nested['source_path'],nested['source_sha256']);np=pinned(nested['peer_path'],nested['peer_sha256']);nt=pinned(nested['translations_path'],nested['translations_sha256'])
            if np['status']!='ROOT_FULL_SOURCE_MEDIA_AND_FOUR_LANGUAGE_PEER_PASS_PRIVATE_ONLY' or np['source_sha256']!=nested['source_sha256'] or np['translations_sha256']!=nested['translations_sha256']:raise ValueError('Wrong nested Root peer')
            if ns['entry_id']!=oid or ns['owner_id']!=nid or ns['entry']['id']!=nid or nt['entry_id']!=oid or nt['owner_id']!=nid or nt['source_sha256']!=nested['source_sha256']:raise ValueError('Nested source identity differs')
            if nt['english']!={k:ns['entry'][k] for k in ('title','subtitle','summary','body','story_headings')}:raise ValueError('Nested English target differs')
            positions=[n for n,f in enumerate(reviewed.get('editorial_features',[])) if f['id']==nid]
            if len(positions)!=1:raise ValueError('Nested owner missing or duplicated')
            reviewed['editorial_features'][positions[0]]=copy.deepcopy(ns['entry'])
        if reviewed!=row['new_entry']:raise ValueError('Reviewed source family differs')
        if 'translation_peer_path' in row:
            targetpeer=pinned(row['translation_peer_path'],row['translation_peer_sha256'])
            aggregate=pinned(row['aggregate_path'],row['aggregate_sha256'])
            if targetpeer['status']!=row['translation_peer_status'] or 'SEMANTIC_PEER_PASS_PRIVATE_ONLY' not in targetpeer['status'] or targetpeer['source_sha256']!=row['source_sha256'] or targetpeer['aggregate_sha256']!=row['aggregate_sha256']:raise ValueError('Wrong target aggregate peer')
            targets=[e for e in aggregate['owners'] if e['entry_id']==oid]
            if len(targets)!=1 or targets[0]['sha256']!=row['translations_sha256']:raise ValueError('Aggregate target pin differs')
        else:
            if peer.get('translations_sha256')!=row['translations_sha256']:raise ValueError('Peer does not bind translation')
        translation=pinned(row['translations_path'],row['translations_sha256'])
        if translation['entry_id']!=oid or translation['source_sha256']!=row['source_sha256']:raise ValueError('Translation source differs')
        fields=('title','subtitle','summary','body','story_headings')
        if translation['english']!={k:row['new_entry'][k] for k in fields}:raise ValueError('Translation English differs')
        if digest(row['new_entry'])!=row['after_sha256']:raise ValueError('New owner digest differs')
        aliases={a['source_path']:a for a in row.get('asset_aliases',[])};used_aliases=set()
        if len(aliases)!=len(row.get('asset_aliases',[])):raise ValueError('Duplicate asset alias')
        for owner in [row['new_entry']]+row['new_entry'].get('editorial_features',[]):
            for image in owner.get('images',[]):
                local=image.get('recovery_local_source');expected=image.get('verification',{}).get('sha256')
                if local and expected:
                    if local in aliases:
                        alias=aliases[local];used_aliases.add(local)
                        if alias['sha256']!=expected:raise ValueError('Alias differs from reviewed image hash')
                        p=(root/alias['local_path']).resolve()
                    else:p=(root/local).resolve()
                    if not p.is_relative_to(root) or file_sha(p)!=expected:raise ValueError('Reviewed image changed')
        if used_aliases!=set(aliases):raise ValueError('Unused or unbound asset alias')
        current=next((e for e in entries if e['id']==oid),None)
        comparable=lambda e:{k:v for k,v in e.items() if k!='publication_readiness'}
        if current is not None and comparable(current)==comparable(row['new_entry']):continue
        if row['mode']=='append':
            if current is not None:raise ValueError('Append owner drift')
        elif row['mode']=='replace':
            if digest(row['old_entry'])!=row['before_sha256'] or current is None or comparable(current)!=comparable(row['old_entry']):raise ValueError('Replacement owner drift')
        else:raise ValueError('Unknown action')
        actions.append((current,row['new_entry']))
    for current,new in actions:
        if current is None:entries.append(copy.deepcopy(new))
        else:current.clear();current.update(copy.deepcopy(new))
    return {'changed':len(actions),'idempotent':not actions}
