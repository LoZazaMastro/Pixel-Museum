"""Apply the reviewed Nintendo chronology after generic archive enrichment."""
from pathlib import Path
import copy,json

def apply(entries,root):
    path=Path(root)/'content/expansion/nintendo-complete-story-reviewed.json'
    if not path.is_file():return None
    source=json.loads(path.read_text(encoding='utf-8'))
    if source.get('status')!='text_and_images_reviewed':return None
    assert len(source['body'])==len(source['story_headings'])==19
    mapped=[i['story_paragraph'] for i in source['images'] if i.get('story_paragraph',-1)>=0]
    assert sorted(mapped)==list(range(19))
    assert len({i['url'] for i in source['images']})==len(source['images'])
    for entry in entries:
        if entry['id']!=source['entry_id']:continue
        provenance=entry.setdefault('provenance',{})
        if not isinstance(provenance,dict):entry['provenance']={'original_record':provenance};provenance=entry['provenance']
        if 'nintendo_original_published_story' not in provenance:
            provenance['nintendo_original_published_story']={k:copy.deepcopy(entry.get(k)) for k in ('body','story_headings','images','sources','editorial_credit','factual_note')}
        for field in ('body','story_headings','images','preferred_image','videos','sources'):
            entry[field]=copy.deepcopy(source[field])
        entry['editorial_credit']=''
        entry['factual_note']=''
        entry['editorial_mode']='illustrated_company_history'
        entry['canonical_narrative_enrichment']={
            'source_module':path.relative_to(root).as_posix(),
            'review':'19 distinct illustrated chapters, original seven chapters retained verbatim, contextual official museum film.',
            'text_licence':'Wikipedia-derived chapters: CC BY-SA 4.0; individual image rights retained in their records.'}
        provenance['nintendo_complete_story_review']=copy.deepcopy(source['review'])
        return dict(entry_id=entry['id'],narrative_chapters=19,images=len(entry['images']),films=len(entry['videos']))
    return None
