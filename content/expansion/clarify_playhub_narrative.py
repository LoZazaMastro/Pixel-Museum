"""Admit a frozen, independently read replacement while retaining its archive."""
from pathlib import Path
import copy,hashlib,json

def apply(entries,root,candidate_relative='content/expansion/museum-playhub-clarity-candidate.json',receipt_relative='build/research/playhub-semantic-coverage/wiki-clarity/root-independent-review.json'):
    root=Path(root)
    candidate=root/candidate_relative
    receipt=root/receipt_relative
    if not candidate.is_file()or not receipt.is_file():return {'status':'not_available'}
    review=json.loads(receipt.read_text(encoding='utf8'))
    digest=hashlib.sha256(candidate.read_bytes()).hexdigest()
    if review.get('status')!='PASS':return {'status':'not_admitted'}
    if review.get('candidate_sha256')!=digest:raise ValueError('Playhub clarity candidate changed after independent review')
    doc=json.loads(candidate.read_text(encoding='utf8'))
    owners={}
    for entry in entries:
        owners[entry['id']]=entry
        for feature in entry.get('editorial_features',[]):owners[feature['id']]=feature
    admitted=[]
    for change in doc['replacements']:
        owner=owners.get(change['entry_id'])
        if owner is None:raise ValueError('Reviewed clarity owner absent: '+change['entry_id'])
        body=owner.get('body',[])
        if change['old_body'] not in body:
            if change['body']in body:continue
            raise ValueError('Reviewed source paragraph absent: '+change['entry_id'])
        if body.count(change['old_body'])!=1:raise ValueError('Ambiguous paragraph match: '+change['entry_id'])
        index=body.index(change['old_body'])
        if hashlib.sha256(body[index].encode()).hexdigest()!=change['old_body_sha256']:raise ValueError('Old passage hash differs')
        if change['body']in body:raise ValueError('Wikipedia replacement would repeat existing prose: '+change['entry_id'])
        source_file=root/change['provenance']['source_file']
        if hashlib.sha256(source_file.read_bytes()).hexdigest()!=change['provenance']['source_file_sha256']:raise ValueError('Frozen Wikipedia source changed')
        provenance=owner.setdefault('provenance',{})
        if not isinstance(provenance,dict):provenance={'original_record':provenance};owner['provenance']=provenance
        archive=provenance.setdefault('clarity_replaced_playhub_passages',[])
        headings=owner.setdefault('story_headings',[])
        while len(headings)<len(body):headings.append('')
        archive.append(dict(old_body=body[index],old_heading=owner['story_headings'][index],
            old_body_sha256=change['old_body_sha256'],paragraph_index=index,reason=change.get('reason','Replace an independently reviewed generic passage with a source-bound concrete account of the same subject.'),
            replacement_source=copy.deepcopy(change['source']),reviewed_candidate_sha256=digest,
            independent_review=receipt.relative_to(root).as_posix(),source_revision=copy.deepcopy(change['provenance'])))
        body[index]=change['body'];owner['story_headings'][index]=change['heading']
        sources=owner.setdefault('sources',[])
        for source in [change['source'], *change.get('additional_sources', [])]:
            if not any(s.get('url')==source['url']for s in sources):sources.append(copy.deepcopy(source))
        if 'en.wikipedia.org/'in change['source'].get('url','')and not change['provenance'].get('copyedit_only'):
            credit='Includes English Wikipedia passages, credited by article revision under Creative Commons Attribution-ShareAlike4.0; card headings supplied editorially and any typographic corrections recorded in provenance.'
            if credit not in owner.get('editorial_credit',''):owner['editorial_credit']=(owner.get('editorial_credit','').rstrip()+' '+credit).strip()
        admitted.append(dict(entry_id=owner['id'],paragraph_index=index,source_chapter_index=change['source_chapter_index'],source_revision=change['provenance'].get('revision_id')))
    date_changes=[]
    for correction in doc.get('date_corrections',[]):
        owner=owners.get(correction['entry_id'])
        if owner is None:raise ValueError('Reviewed date correction owner absent: '+correction['entry_id'])
        if owner.get('date')==correction['date']and owner.get('year')==correction.get('year',owner.get('year')):continue
        if owner.get('date')!=correction['old_date']:raise ValueError('Reviewed old calendar date changed: '+correction['entry_id'])
        provenance=owner.setdefault('provenance',{})
        if not isinstance(provenance,dict):owner['provenance']={'original_record':provenance};provenance=owner['provenance']
        provenance.setdefault('removed_artificial_calendar_dates',[]).append(dict(original_year=owner['year'],original_date=copy.deepcopy(owner['date']),
            reviewed_correction=copy.deepcopy(correction),reviewed_candidate_sha256=digest))
        owner['date']=copy.deepcopy(correction['date'])
        if 'year'in correction:owner['year']=correction['year']
        if 'date_provenance'in correction:owner['date_provenance']=copy.deepcopy(correction['date_provenance'])
        if 'event_semantics'in correction:owner['event_semantics']=correction['event_semantics']
        date_changes.append(correction['entry_id'])
    field_changes=[]
    for correction in doc.get('field_corrections',[]):
        owner=owners.get(correction['entry_id'])
        if owner is None:raise ValueError('Reviewed field correction owner absent: '+correction['entry_id'])
        field=correction['field']
        if field not in ['summary','subtitle']:raise ValueError('Unsupported reviewed field correction: '+field)
        if owner.get(field)==correction['value']:continue
        if owner.get(field)!=correction['old_value']:raise ValueError('Reviewed old field changed: '+correction['entry_id'])
        provenance=owner.setdefault('provenance',{})
        if not isinstance(provenance,dict):owner['provenance']={'original_record':provenance};provenance=owner['provenance']
        provenance.setdefault('reviewed_field_copyedits',[]).append(dict(field=field,original_value=owner.get(field),
            reason=correction['reason'],reviewed_candidate_sha256=digest))
        owner[field]=correction['value'];field_changes.append(dict(entry_id=owner['id'],field=field))
    removed_sources=[]
    for removal in doc.get('source_removals',[]):
        owner=owners.get(removal['entry_id'])
        if owner is None:raise ValueError('Unrelated calendar citation owner absent: '+removal['entry_id'])
        urls=set(removal['source_urls']);sources=owner.get('sources',[])
        rejected=[source for source in sources if source.get('url')in urls]
        if not rejected:continue
        provenance=owner.setdefault('provenance',{})
        if not isinstance(provenance,dict):owner['provenance']={'original_record':provenance};provenance=owner['provenance']
        provenance.setdefault('removed_unrelated_calendar_sources',[]).append(dict(sources=copy.deepcopy(rejected),
            reason=removal['reason'],reviewed_candidate_sha256=digest))
        owner['sources']=[source for source in sources if source.get('url')not in urls]
        removed_sources.append(dict(entry_id=owner['id'],removed=len(rejected)))
    return {'status':'PASS','candidate_sha256':digest,'replacements':admitted,'date_corrections':date_changes,'field_corrections':field_changes,'source_removals':removed_sources,'retained_chapters':28 if candidate_relative.endswith('/museum-playhub-clarity-candidate.json')else None}
