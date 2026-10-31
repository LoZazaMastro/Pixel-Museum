"""Exact four-owner source-bound replacement after382andcombinedmusic joins."""
from pathlib import Path
import copy, hashlib, json

def packed(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def digest(x):return hashlib.sha256(packed(x)).hexdigest()
def file_sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def apply(entries, root, config_path=None):
    if config_path is None:config_path=Path(root)/"content/expansion/museum-reviewed-2011-postmusic-owner-replacements.json"
    root=Path(root).resolve();config=json.loads(Path(config_path).read_bytes());actions=[]
    if config['status']!='independently_reviewed':raise ValueError('Unreviewed hook config')
    for row in config['rows']:
        approvalpath=(root/row.get('approval_path',config['approval_path'])).resolve()
        if not approvalpath.is_relative_to(root) or file_sha(approvalpath)!=row.get('approval_sha256',config['approval_sha256']):raise ValueError('Root approval changed')
        approval=json.loads(approvalpath.read_bytes())
        if approval.get('status')!=row.get('approval_status',config['approval_status']) or approval.get('plan_sha256')!=row.get('plan_sha256',config['plan_sha256']):raise ValueError('Wrong Root approval')
        source=(root/row['source_path']).resolve();peerpath=(root/row['peer_path']).resolve()
        if not source.is_relative_to(root) or not peerpath.is_relative_to(root):raise ValueError('Unsafe pin path')
        if file_sha(source)!=row['source_sha256'] or file_sha(peerpath)!=row['peer_sha256']:raise ValueError('Reviewed source or peer changed')
        peer=json.loads(peerpath.read_bytes())
        allowed={'ROOT_FULL_SOURCE_MEDIA_AND_FOUR_LANGUAGE_PEER_PASS_PRIVATE_ONLY','ROOT_FULL_ENGLISH_SOURCE_MEDIA_AND_FOUR_LANGUAGE_PEER_PASS_PRIVATE_ONLY'}
        if peer['status'] not in ({row['peer_status']} if 'peer_status' in row else allowed) or peer['source_sha256']!=row['source_sha256']:raise ValueError('Peer does not bind source')
        reviewed=copy.deepcopy(json.loads(source.read_bytes())['entry'])
        for pin in row.get('nested_feature_pins',[]):
            nestedsource=(root/pin['source_path']).resolve();nestedpeer=(root/pin['peer_path']).resolve()
            if not nestedsource.is_relative_to(root) or not nestedpeer.is_relative_to(root):raise ValueError('Unsafe nested pin path')
            if file_sha(nestedsource)!=pin['source_sha256'] or file_sha(nestedpeer)!=pin['peer_sha256']:raise ValueError('Nested source or peer changed')
            ns=json.loads(nestedsource.read_bytes());np=json.loads(nestedpeer.read_bytes())
            if np['status'] not in allowed or np['source_sha256']!=pin['source_sha256']:raise ValueError('Nested peer does not bind source')
            if ns['entry_id']!=row['owner_id'] or ns['owner_id']!=pin['nested_owner_id'] or ns['entry']['id']!=pin['nested_owner_id']:raise ValueError('Nested owner identity differs')
            indices=[n for n,f in enumerate(reviewed.get('editorial_features',[])) if f['id']==pin['nested_owner_id']]
            if len(indices)!=1:raise ValueError('Nested source owner missing or duplicated')
            reviewed['editorial_features'][indices[0]]=copy.deepcopy(ns['entry'])
        if reviewed!=row['new_entry']:raise ValueError('Config differs from reviewed source family')
        if digest(row['old_entry'])!=row['before_sha256'] or digest(row['new_entry'])!=row['after_sha256']:raise ValueError('Config owner digest changed')
        owner=next((e for e in entries if e['id']==row['owner_id']),None)
        if owner is None:raise ValueError('Missing owner')
        current=digest(owner)
        comparable=lambda x:{k:v for k,v in x.items() if k!='publication_readiness'}
        if comparable(owner)==comparable(row['new_entry']):continue
        if current==row['after_sha256']:continue
        if current!=row['before_sha256']:
            comparable=lambda x:{k:v for k,v in x.items() if k!='publication_readiness'}
            if comparable(owner)!=comparable(row['old_entry']):raise ValueError('Owner preimage drift')
        if digest(row['old_entry'])!=row['before_sha256'] or digest(row['new_entry'])!=row['after_sha256']:raise ValueError('Config owner content changed')
        for image in [im for o in [row['new_entry']]+row['new_entry'].get('editorial_features',[]) for im in o.get('images',[])]:
            local=image.get('recovery_local_source');expected=image.get('verification',{}).get('sha256')
            if local and expected:
                p=(root/local).resolve()
                if not p.is_relative_to(root) or file_sha(p)!=expected:raise ValueError('Reviewed image changed')
        actions.append((owner,row['new_entry']))
    for owner,new in actions:owner.clear();owner.update(copy.deepcopy(new))
    return {'changed':len(actions),'idempotent':not actions}
