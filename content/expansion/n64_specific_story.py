"""Apply only the exact independently reviewed Nintendo64 narrative revision."""
from pathlib import Path
import copy,hashlib,json

def apply(entries,root):
    root=Path(root)
    candidate=root/'build/research/n64-specific-story/candidate.json'
    receipt=root/'build/research/n64-specific-story/independent-review.json'
    if not candidate.is_file() or not receipt.is_file():return []
    review=json.loads(receipt.read_text(encoding='utf8'))
    if review.get('status')!='PASS':return []
    digest=hashlib.sha256(candidate.read_bytes()).hexdigest()
    if digest!=review.get('candidate_sha256'):raise ValueError('Reviewed Nintendo64 source changed')
    source=json.loads(candidate.read_text(encoding='utf8'))
    assert len(source['body'])==len(source['story_headings'])==5
    assert sorted(i['story_paragraph']for i in source['images']if i.get('story_paragraph',-1)>=0)==list(range(5))
    assert len({i['url']for i in source['images']})==7
    for entry in entries:
        if entry['id']!=source['entry_id']:continue
        provenance=entry.setdefault('provenance',{})
        if not isinstance(provenance,dict):
            provenance={'original_record':provenance};entry['provenance']=provenance
        provenance.setdefault('n64_previous_template_draft',copy.deepcopy(source['provenance']['previous_draft']))
        for field in ('body','story_headings','images','preferred_image','videos','sources','summary','editorial_credit','factual_note','attribution','explicit_story_media_only'):
            entry[field]=copy.deepcopy(source[field])
        entry['editorial_mode']='illustrated_hardware_history'
        provenance['n64_story_review']={'candidate_sha256':digest,'independent_review':receipt.relative_to(root).as_posix(),
            'scope':'Five distinct illustrated chapters, existing documentary contextualized after chapter0; original model and release date retained.'}
        return [dict(entry_id=entry['id'],narrative_chapters=5,images=7,films=len(entry['videos']))]
    raise ValueError('Reviewed Nintendo64 exhibit absent')
