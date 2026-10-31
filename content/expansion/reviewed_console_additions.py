"""Append the curator-reviewed console gaps without replacing existing articles."""
import copy, hashlib, json
from pathlib import Path

def apply(entries,root):
    root=Path(root).resolve()
    policy_path=root/'content/expansion/console-additions-reviewed.json'
    if not policy_path.exists():return {'status':'NO_ADDITIONS','added':[]}
    policy=json.loads(policy_path.read_bytes())
    if policy.get('status')!='ROOT_REVIEWED_ADDITIONS':raise ValueError('Unreviewed console additions')
    by={e['id']:e for e in entries};pending=[]
    for row in policy['owners']:
        p=(root/row['source']).resolve()
        if not p.is_relative_to(root) or hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:
            raise ValueError('Console addition source changed')
        entry=json.loads(p.read_bytes())
        if entry['id']!=row['entry_id'] or not entry.get('body') or not entry.get('images') or not entry.get('sources'):
            raise ValueError('Incomplete console addition')
        if entry['id'] in by:
            if by[entry['id']]!=entry:raise ValueError('Console addition ID collision')
            continue
        pending.append(copy.deepcopy(entry));by[entry['id']]=entry
    entries.extend(pending)
    return {'status':'REVIEWED_CONSOLE_ADDITIONS_APPLIED','added':[e['id'] for e in pending]}
