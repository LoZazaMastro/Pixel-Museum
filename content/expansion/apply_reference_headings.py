"""Apply reviewed headings only to the exact unchanged English source paragraphs."""
from __future__ import annotations
import hashlib

def apply(entries, additions):
    by_id={entry['id']:entry for entry in entries}
    result={'applied':[], 'held':[], 'body_or_date_changes':0}
    for row in additions.get('entries',[]):
        eid=row.get('entry_id');entry=by_id.get(eid)
        if not entry:
            result['held'].append({'entry_id':eid,'reason':'entry_missing'});continue
        body=entry.get('body',[]);headings=row.get('story_headings',[])
        hashes=[hashlib.sha256(text.encode('utf-8')).hexdigest() for text in body]
        if hashes!=row.get('body_sha256'):
            result['held'].append({'entry_id':eid,'reason':'source_paragraphs_changed_requires_review'});continue
        if any(entry.get('story_headings',[])):
            result['held'].append({'entry_id':eid,'reason':'existing_headings_preserved'});continue
        if len(headings)!=len(body) or not headings or any(not isinstance(x,str) or not x.strip() or len(x)>160 for x in headings):
            result['held'].append({'entry_id':eid,'reason':'invalid_heading_set'});continue
        entry['story_headings']=list(headings)
        entry['heading_provenance']={'origin':'Pixel Museum editorial headings','source_paragraph_hashes':hashes,'body_unchanged':True,'historical_fact_check':'pending'}
        result['applied'].append({'entry_id':eid,'headings':len(headings)})
    result['article_count']=len(result['applied']);result['heading_count']=sum(x['headings'] for x in result['applied'])
    return result
