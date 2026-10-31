"""Append the curator-reviewed peripheral objects; never silently replace owners."""
from pathlib import Path
import copy,json,hashlib
def apply(entries,root):
    doc=json.loads((Path(root)/'content/expansion/required-peripheral-hardware.json').read_text(encoding='utf-8'));index={e['id']:e for e in entries};added=[]
    for e in doc['entries']:
        digest=hashlib.sha256(json.dumps(e,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        if digest!=doc['source_fingerprints'][e['id']]:raise ValueError('Peripheral source fingerprint changed: '+e['id'])
        if e['id']in index:
            if index[e['id']]!=e:raise ValueError('Peripheral owner collision: '+e['id'])
            continue
        entries.append(copy.deepcopy(e));index[e['id']]=e;added.append(e['id'])
    return {'status':'PASS_REVIEWED_PERIPHERALS_APPEND_ONLY','added':added}
