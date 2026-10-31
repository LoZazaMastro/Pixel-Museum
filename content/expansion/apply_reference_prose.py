"""Repair a few verified import-flow defects, retaining source and media indices."""
from __future__ import annotations
import hashlib

def apply(entries, fixes):
    by_id={entry['id']:entry for entry in entries};report={'applied':[],'held':[]}
    for row in fixes.get('entries',[]):
        eid=row.get('entry_id');entry=by_id.get(eid)
        if not entry or entry.get('editorial_mode')!='reference':
            report['held'].append({'entry_id':eid,'reason':'not_an_imported_reference'});continue
        old=entry.get('body',[]);actual=[hashlib.sha256(p.encode('utf-8')).hexdigest() for p in old]
        body=row.get('body',[]);headings=row.get('story_headings',[]);mapping=row.get('paragraph_mapping',{})
        if actual!=row.get('expected_body_sha256') or old!=row.get('original_body'):
            report['held'].append({'entry_id':eid,'reason':'source_changed_requires_review'});continue
        if not body or len(body)!=len(headings) or any(not isinstance(p,str) or not p.strip() for p in body+headings) or set(mapping)!={str(n) for n in range(len(old))} or any(not isinstance(n,int) or n<0 or n>=len(body) for n in mapping.values()):
            report['held'].append({'entry_id':eid,'reason':'invalid_repair_or_index_mapping'});continue
        # Retain original source prose in the authoring repair record. Runtime
        # metadata records the exact source hashes, not a second copy of prose.
        entry['body']=list(body);entry['story_headings']=list(headings)
        for field in ('images','videos'):
            for media in entry.get(field,[]):
                n=media.get('story_paragraph',-1)
                if isinstance(n,int) and n>=0:
                    if str(n) in mapping:media['story_paragraph']=mapping[str(n)]
                    else:media['story_paragraph']=-1
        entry['reading_flow_provenance']={'original_body_sha256':actual,'reason':row['reason'],'fact_check':'pending','original_retained_in':'content/expansion/reference-prose-fixes.json'}
        report['applied'].append({'entry_id':eid,'old_sections':len(old),'new_sections':len(body),'reason':row['reason']})
    return report
