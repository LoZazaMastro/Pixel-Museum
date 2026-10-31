"""Join independently reviewed creator biographies after generic enrichments."""
from pathlib import Path
import copy,json

def apply(entries,root):
    path=Path(root)/'content/expansion/yu-suzuki-complete-story-reviewed.json'
    if not path.is_file():return []
    source=json.loads(path.read_text(encoding='utf-8'))
    if source.get('status')!='text_and_images_reviewed':return []
    body=source['body'];images=source['images']
    assert len(body)==len(source['story_headings'])>=2
    assert sorted(i['story_paragraph'] for i in images if type(i.get('story_paragraph')) is int)==list(range(len(body)))
    assert len({i['url'] for i in images})==len(images)
    for entry in entries:
        if entry['id']!=source['entry_id']:continue
        provenance=entry.setdefault('provenance',{})
        if not isinstance(provenance,dict):
            entry['provenance']={'original_record':provenance};provenance=entry['provenance']
        provenance.setdefault('creator_previous_template_draft',{k:copy.deepcopy(entry.get(k)) for k in ('body','story_headings','images','videos','sources','editorial_credit','factual_note')})
        for field in ('body','story_headings','images','preferred_image','videos','sources','summary'):
            entry[field]=copy.deepcopy(source[field])
        entry['editorial_credit']=''
        entry['factual_note']=''
        entry['editorial_mode']='illustrated_creator_history'
        entry['explicit_story_media_only']=True
        entry['canonical_narrative_enrichment']={
            'source_module':path.relative_to(root).as_posix(),
            'review':'Specific sourced biography; person-first hero, distinct paragraph images and contextual films.',
            'text_licence':'Original editorial account with attributed reference sources; individual image and film rights retained.'}
        provenance['creator_story_review']=copy.deepcopy(source['review'])
        return [dict(entry_id=entry['id'],narrative_chapters=len(body),images=len(images),films=len(entry['videos']))]
    return []
