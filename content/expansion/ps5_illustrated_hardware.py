"""Keep approved PS5 models and features while replacing duplicate parent cards."""
from pathlib import Path
import copy,hashlib,json

def apply(entries,root):
    root=Path(root);candidate=root/'build/research/ps5-illustrated-hardware/candidate.json'
    receipt=root/'build/research/ps5-illustrated-hardware/independent-review.json'
    if not candidate.is_file()or not receipt.is_file():return dict(status='not_available')
    review=json.loads(receipt.read_text(encoding='utf8'))
    if review.get('status')!='PASS':return dict(status='not_admitted')
    digest=hashlib.sha256(candidate.read_bytes()).hexdigest()
    if review.get('candidate_sha256')!=digest:raise ValueError('PS5 candidate changed after review')
    source=json.loads(candidate.read_text(encoding='utf8'));entry=next(e for e in entries if e['id']==source['entry_id'])
    assert len(source['body'])==len(source['story_headings'])==8
    assert sorted(i['story_paragraph']for i in source['images']if i['story_paragraph']>=0)==list(range(8))
    for image in source['images']:
        if image.get('recovery_local_source')and image.get('verification'):
            if hashlib.sha256((root/image['recovery_local_source']).read_bytes()).hexdigest()!=image['verification']['sha256']:
                raise ValueError('Reviewed PS5 source image changed')
    provenance=entry.setdefault('provenance',{})
    if not isinstance(provenance,dict):entry['provenance']={'original_record':provenance};provenance=entry['provenance']
    provenance.setdefault('ps5_previous_parent_draft',copy.deepcopy(source['provenance']['previous_draft']))
    provenance['ps5_illustrated_admission']=dict(candidate=candidate.relative_to(root).as_posix(),candidate_sha256=digest,
        independent_review=receipt.relative_to(root).as_posix(),source_provenance=copy.deepcopy(source['provenance']))
    for field in ['body','story_headings','summary','images','preferred_image','videos','sources','explicit_story_media_only','editorial_credit','factual_note']:
        entry[field]=copy.deepcopy(source[field])
    entry['editorial_mode']='illustrated_hardware_history'
    return dict(status='PASS',entry_id=entry['id'],narrative_paragraphs=8,illustrated_paragraphs=8,candidate_sha256=digest)
