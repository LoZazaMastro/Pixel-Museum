"""Bounded three-owner music layer, validated completely before mutation."""
from pathlib import Path
import copy,hashlib,json
NAME='museum-reviewed-requested-three159-music'
def digest(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def apply(entries,root):
    root=Path(root).resolve()
    def read(p,h=None):
        path=(root/p).resolve()
        if not path.is_relative_to(root):raise ValueError('Input escapes root')
        raw=path.read_bytes()
        if h and hashlib.sha256(raw).hexdigest()!=h:raise ValueError('Pinned input changed: '+p)
        return raw
    policy=json.loads(read('content/expansion/'+NAME+'-policy.json'))
    candidate=json.loads(read(policy['candidate_path'],policy['candidate_sha256']))
    for p in candidate['immutable_inputs']:read(p['path'],p['sha256'])
    rows=candidate['entries']
    if [r['entry_id'] for r in rows]!=['wikipedia-4843160', 'wikipedia-13655028', 'wikipedia-1847427']:raise ValueError('Three requested-owner scope changed')
    pending=[]
    for row in rows:
        found=[e for e in entries if e['id']==row['entry_id']]
        if len(found)!=1:raise ValueError('Missing or duplicate owner')
        entry=found[0];before=tuple(row['before_'+k] for k in ('soundtrack','soundtrack_rooms'));after=tuple(row['after_'+k] for k in ('soundtrack','soundtrack_rooms'))
        current=tuple(entry.get(k) for k in ('soundtrack','soundtrack_rooms'))
        if current not in (before,after):raise ValueError('Music drift or partial state')
        restored=copy.deepcopy(entry)
        for k in ('soundtrack','soundtrack_rooms'):
            if row['before_'+k] is None:restored.pop(k,None)
            else:restored[k]=copy.deepcopy(row['before_'+k])
        if digest(restored)!=row['source_entry_sha256']:raise ValueError('Non-music owner changed')
        if current!=after:pending.append((entry,row))
    for entry,row in pending:
        for k in ('soundtrack','soundtrack_rooms'):
            if row['after_'+k] is not None:entry[k]=copy.deepcopy(row['after_'+k])
    return {'status':'PASS','changed':[e['id']for e,r in pending],'available_original_selections':159}
