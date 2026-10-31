"""Admit frozen, independently reviewed illustrated hardware revisions."""
from pathlib import Path
import copy,hashlib,json
def integrate(entries,root):
    root=Path(root);candidate=root/'content/expansion/ds-lite-specific-story-candidate.json'
    receipt=root/'build/research/ds-lite-complete-story/root-independent-review.json'
    if not candidate.is_file()or not receipt.is_file():return {'status':'not_available','entries':[]}
    review=json.loads(receipt.read_text(encoding='utf8'))
    if review.get('status')!='PASS':return {'status':'not_admitted','entries':[]}
    digest=hashlib.sha256(candidate.read_bytes()).hexdigest()
    if digest!=review['candidate_sha256']:raise ValueError('Reviewed DS Lite source changed')
    source=json.loads(candidate.read_text(encoding='utf8'))
    entry=next(e for e in entries if e['id']==source['entry_id'])
    before=copy.deepcopy(entry)
    assert len(source['body'])==len(source['story_headings'])==3
    assert sorted(i['story_paragraph']for i in source['images']if i['story_paragraph']>=0)==[0,1,2]
    assert len({i['url']for i in source['images']})==4
    provenance=entry.setdefault('provenance',{})
    if not isinstance(provenance,dict):provenance={'original_record':provenance};entry['provenance']=provenance
    provenance.setdefault('hardware_previous_template_draft',copy.deepcopy(source['provenance']['previous_draft']))
    provenance['hardware_reviewed_source']={
      'candidate':candidate.relative_to(root).as_posix(),'candidate_sha256':digest,
      'independent_review':receipt.relative_to(root).as_posix(),
      'independent_review_sha256':hashlib.sha256(receipt.read_bytes()).hexdigest(),
      'text_source':source['provenance']['source_html'],'text_source_sha256':source['provenance']['source_sha256'],
      'source_sections':copy.deepcopy(source['provenance']['source_sections'])}
    if entry.get('factual_note'):provenance.setdefault('previous_operational_factual_note',entry['factual_note'])
    for field in ['body','story_headings','images','preferred_image','videos','sources','summary','editorial_credit','attribution']:
        entry[field]=copy.deepcopy(source[field])
    entry['factual_note']='';entry['explicit_story_media_only']=True
    entry['editorial_mode']='illustrated_hardware_history'
    return {'status':'PASS','entries':[{'entry_id':entry['id'],'narrative_paragraphs':3,'illustrated_paragraphs':3,'unique_images':4,'candidate_sha256':digest}]}
