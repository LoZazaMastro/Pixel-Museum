from pathlib import Path
import copy,json,hashlib
NAME='museum-reviewed-required2014-six-music'
IDS=['wikipedia-38323830','wikipedia-32010904','wikipedia-42644362','workbook-08-14-hyrule-warriors','wikipedia-41301253','wikipedia-39646535']
def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def apply(entries,root):
 root=Path(root).resolve()
 def read(p,h=None):
  path=(root/p).resolve()
  if not path.is_relative_to(root):raise ValueError('Input escapes root')
  raw=path.read_bytes()
  if h and hashlib.sha256(raw).hexdigest()!=h:raise ValueError('Pinned input changed: '+p)
  return raw
 policy=json.loads(read('content/expansion/'+NAME+'-policy.json'));a=json.loads(read(policy['candidate_path'],policy['candidate_sha256']))
 for p in a['immutable_inputs']:read(p['path'],p['sha256'])
 if [r['entry_id']for r in a['entries']]!=IDS:raise ValueError('Exact six-owner scope changed')
 pending=[]
 for r in a['entries']:
  found=[e for e in entries if e['id']==r['entry_id']]
  if len(found)!=1:raise ValueError('Missing or duplicate owner')
  e=found[0];before=tuple(r['before_'+k]for k in('soundtrack','soundtrack_rooms'));after=tuple(r['after_'+k]for k in('soundtrack','soundtrack_rooms'));current=tuple(e.get(k)for k in('soundtrack','soundtrack_rooms'))
  if current not in(before,after):raise ValueError('Music drift or partial state')
  restored=copy.deepcopy(e)
  for k in('soundtrack','soundtrack_rooms'):
   if r['before_'+k]is None:restored.pop(k,None)
   else:restored[k]=copy.deepcopy(r['before_'+k])
  if digest(restored)!=r['source_entry_sha256']:raise ValueError('Non-music owner changed')
  if current!=after:pending.append((e,r))
 for e,r in pending:
  for k in('soundtrack','soundtrack_rooms'):
   if r['after_'+k]is None:e.pop(k,None)
   else:e[k]=copy.deepcopy(r['after_'+k])
 return {'status':'PASS','changed':[e['id']for e,r in pending],'new_selections':225,'final_selections':273}
