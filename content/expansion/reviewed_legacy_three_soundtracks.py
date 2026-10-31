"""Apply three independently reviewed soundtrack fields, after series owners exist."""
from pathlib import Path
import copy,hashlib,json
def apply(entries,root):
 root=Path(root).resolve();p=root/'content/expansion/reviewed-legacy-three-soundtracks.json'
 cfg=json.loads(p.read_bytes())
 def pinned(path,expected):
  f=(root/path).resolve()
  if not f.is_relative_to(root)or hashlib.sha256(f.read_bytes()).hexdigest()!=expected:raise ValueError('Legacy soundtrack pin changed')
  return json.loads(f.read_bytes())
 peer=pinned(cfg['independent_peer'],cfg['independent_peer_sha256'])
 if peer['status']!='APPROVED':raise ValueError('Legacy soundtrack peer not approved')
 idx=pinned(cfg['index'],cfg['index_sha256'])
 if peer['reviewed_index_sha256']!=cfg['index_sha256']:raise ValueError('Legacy soundtrack index not approved')
 owners={e['id']:e for e in entries};actions=[];seen=set()
 for row in idx['owners']:
  oid=row['entry_id']
  if oid in seen or oid not in owners:raise ValueError('Legacy soundtrack owner missing or duplicated')
  seen.add(oid);src=pinned(row['source'],row['source_sha256'])['entries'][0]
  if src['id']!=oid or src['soundtrack']!=row['after'] or row['field']!='soundtrack' or row['before']is not None:raise ValueError('Legacy soundtrack approved field differs')
  current=owners[oid].get('soundtrack')
  if current==row['after']:continue
  if current is not None:raise ValueError('Legacy soundtrack field drift: '+oid)
  actions.append((owners[oid],row['after']))
 for e,soundtrack in actions:e['soundtrack']=copy.deepcopy(soundtrack)
 return {'status':'PASS_REVIEWED_THREE_LEGACY_SOUNDTRACK_FIELDS','changed':len(actions),'idempotent':not actions,'owner_ids':sorted(seen)}
