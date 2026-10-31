"""Admit only the immutable six-game batch with completed independent review."""
from pathlib import Path
import copy, hashlib, json
ROOT=Path(__file__).resolve().parents[2]
def integrate(entries,root=ROOT):
    root=Path(root);path=root/'content/expansion/recent-six-reviewed-additions.json'
    if not path.is_file():return {'status':'not_available','added':[]}
    doc=json.loads(path.read_text(encoding='utf8'))
    if doc.get('publication_status')!='validated':return {'status':'not_admitted','added':[]}
    receipt=root/doc['review_receipt']
    if hashlib.sha256(receipt.read_bytes()).hexdigest()!=doc['review_receipt_sha256']:
        raise ValueError('Recent six-game independent review changed')
    by_id={e['id']:e for e in entries};added=[]
    for original in doc['entries']:
        if original['id'] in by_id:
            current=by_id[original['id']]
            if current.get('body')!=original['body']:
                raise ValueError('Recent six-game identity collides with another article: '+original['id'])
            continue
        entry=copy.deepcopy(original)
        assert len(entry['body'])>=5 and entry['images'] and entry['videos']
        entries.append(entry);by_id[entry['id']]=entry;added.append(entry['id'])
    return {'status':'PASS','added':added,'review_receipt':doc['review_receipt']}
