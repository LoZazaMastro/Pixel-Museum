"""Replay independently reviewed soundtrack-only updates after earlier music layers."""
from pathlib import Path
import copy,hashlib,json,runpy

def apply(entries,root,policy_path=None):
 root=Path(root).resolve();policy_path=Path(policy_path)if policy_path else root/'content/expansion/museum-reviewed-audio-only-owner-policy.json'
 def read_pin(item):
  p=(root/item['path']).resolve()
  if not p.is_relative_to(root)or hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Reviewed audio-only input changed')
  return json.loads(p.read_bytes())
 policy=json.loads(policy_path.read_bytes());owners={e['id']:e for e in entries};pending=[];plans={}
 if policy.get('publication_status')!='independently_reviewed':raise ValueError('Unreviewed audio-only policy')
 for batch in policy['batches']:
  index=read_pin(batch['index']);peer=read_pin(batch['peer'])
  if peer.get('status')!='APPROVED'or peer.get('index_sha256')!=batch['index']['sha256']:raise ValueError('Independent audio-only peer mismatch')
  peer_ids={o if isinstance(o,str)else o['entry_id']for o in peer['owners']}
  if peer_ids!={o['entry_id']for o in index['owners']}:raise ValueError('Audio-only peer scope mismatch')
  for row in index['owners']:
   oid=row['entry_id']
   source=read_pin(dict(path=row['source'],sha256=row['source_sha256']))
   preimage_path=row.get('preimage')or index.get('before')
   preimage_sha=row.get('preimage_sha256')or index.get('before_sha256')
   before=read_pin(dict(path=preimage_path,sha256=preimage_sha))
   if isinstance(before,dict)and 'entries'in before:before=next(e for e in before['entries']if e['id']==oid)
   after=next(e for e in source['entries']if e['id']==oid);current=owners.get(oid)
   outside=lambda e:{k:v for k,v in e.items()if k!='soundtrack'}
   allowed=set(row.get('allowed_changed_fields')or[row.get('field')])
   if allowed!={'soundtrack'}or outside(before)!=outside(after):raise ValueError('Audio-only candidate changed another field')
   if current is None:raise ValueError('Audio-only owner missing')
   if outside(current)!=outside(before):
    # Later curator-approved image corrections must survive music replay.
    # Still reject every text change or unreviewed media change: normalize
    # only through the same exact-preimage media policy used by assembly.
    expected=copy.deepcopy(before)
    media=runpy.run_path(str(root/'content/expansion/reviewed_user_media.py'))
    media['apply']([expected],root,only_owner_ids={oid})
    if outside(current)!=outside(expected):raise ValueError('Audio-only source prose/media drift')
   chain=plans.setdefault(oid,[])
   if chain and chain[-1][1].get('soundtrack')!=before.get('soundtrack'):raise ValueError('Discontinuous reviewed soundtrack history')
   chain.append((before,after))
 for oid,chain in plans.items():
  current=owners[oid]
  states=[chain[0][0].get('soundtrack')]+[after.get('soundtrack')for _,after in chain]
  if current.get('soundtrack')not in states:raise ValueError('Unreviewed soundtrack overwrite')
  final=chain[-1][1]['soundtrack']
  if current.get('soundtrack')!=final:pending.append((current,copy.deepcopy(final)))
 # Validate every input before mutating any owner.
 for owner,room in pending:owner['soundtrack']=room
 return dict(status='PASS',changed=[e['id']for e,_ in pending],owners=len(plans))
