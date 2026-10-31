"""Apply exact-source copy edits without deleting factual narrative or media."""
from pathlib import Path
import hashlib,json

def apply(entries,root):
    root=Path(root);path=root/'content/expansion/museum-reviewed-template-tail-cleanups.json'
    if not path.is_file():return dict(status='not_available')
    doc=json.loads(path.read_text(encoding='utf8'))
    if doc.get('status')!='root_and_editorial_read_reviewed':return dict(status='not_admitted')
    owners={owner['id']:owner for entry in entries for owner in [entry]+entry.get('editorial_features',[])}
    applied=[]
    for change in doc['changes']:
        owner=owners.get(change['entry_id'])
        if owner is None:raise ValueError('Template cleanup owner absent: '+change['entry_id'])
        body=owner.get('body',[])
        if change['old_body']not in body:
            if change['body']in body:continue
            raise ValueError('Reviewed template source changed: '+change['entry_id'])
        assert body.count(change['old_body'])==1
        assert hashlib.sha256(change['old_body'].encode()).hexdigest()==change['old_body_sha256']
        assert change['old_body'].startswith(change['body'])
        assert change['old_body'][len(change['body']):].strip()==change['removed_template']
        index=body.index(change['old_body'])
        provenance=owner.setdefault('provenance',{})
        if not isinstance(provenance,dict):owner['provenance']={'original_record':provenance};provenance=owner['provenance']
        provenance.setdefault('reviewed_repeated_template_copyedits',[]).append(dict(paragraph_index=index,
            original_body=change['old_body'],original_body_sha256=change['old_body_sha256'],removed_template=change['removed_template'],
            review_source=path.relative_to(root).as_posix(),reason='Preserve the complete concrete account and remove only its repeated non-factual interpretive tail.'))
        body[index]=change['body'];applied.append(dict(entry_id=owner['id'],paragraph_index=index))
    return dict(status='PASS',paragraphs=applied)
