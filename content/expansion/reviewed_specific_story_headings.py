"""Replace only independently reviewed generic headings, retaining exact prose."""
import collections,hashlib,json,runpy
from pathlib import Path

def apply(entries, root):
    root=Path(root);path=root/'content/expansion/museum-specific-story-headings-reviewed.json'
    if not path.exists():return {'status':'not_admitted'}
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    digest=lambda value:hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf8')).hexdigest()
    owners={}
    for entry in entries:
        owners[(entry['id'],entry['id'])]=entry
        for feature in entry.get('editorial_features',[]):owners[(entry['id'],feature['id'])]=feature
    changed=[]
    excluded=runpy.run_path(str(root/'content/expansion/user_sports_policy.py'))['excluded_ids'](root)
    for batch in json.loads(path.read_text(encoding='utf8'))['batches']:
        cp=root/batch['candidate_path'];pp=root/batch['peer_path']
        assert sha(cp)==batch['candidate_sha256'] and sha(pp)==batch['peer_sha256']
        candidate=json.loads(cp.read_text(encoding='utf8'));peer=json.loads(pp.read_text(encoding='utf8'))
        assert peer['status'].startswith('PASS') and peer['candidate_sha256']==batch['candidate_sha256']
        groups=collections.defaultdict(list)
        for row in candidate['rows']:groups[(row['entry_id'],row['owner_id'])].append(row)
        for key,rows in groups.items():
            if key not in owners and key[0] in excluded:continue
            owner=owners[key];assert all(digest(owner['body'])==row['body_sha256'] for row in rows)
            current=owner['story_headings'];before=list(current);after=list(current)
            assert len({row['paragraph_index'] for row in rows})==len(rows)
            for row in rows:
                index=row['paragraph_index'];assert owner['body'][index]==row['existing_paragraph']
                assert current[index] in (row['old_heading'],row['new_heading'])
                before[index]=row['old_heading'];after[index]=row['new_heading']
            assert all(digest(before)==row['story_headings_before_sha256'] for row in rows)
            if current==after:continue
            assert current==before
            owner['story_headings']=after;changed.append(key[1])
    return {'status':'PASS_HEADINGS_ONLY_ALL_PROSE_EXACT','changed_owners':changed}
