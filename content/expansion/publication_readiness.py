"""Report editorial readiness separately from import completeness; hide no history."""
import collections, hashlib, json, re
from pathlib import Path
def evaluate(entries):
    records=[]
    ids={e['id']:e for e in entries}
    for entry in entries:
        if entry.get('calendar_only') and (base:=ids.get(entry.get('linked_exhibit_id'))) and base['year']==entry['year']:continue
        body=entry.get('body',[]);images=entry.get('images',[])
        qualified=[x for x in images if max(x.get('width',0),x.get('height',0))>=1600 and x.get('quality_verified') and x.get('source_page') and x.get('credit')]
        mapped={x['story_paragraph'] for x in qualified if isinstance(x.get('story_paragraph'),int) and 0<=x['story_paragraph']<len(body)}
        # A verified image is a cover, not proof that every paragraph is illustrated.
        # Unmapped images remain gallery media until their context is reviewed.
        patterns=('as a concrete design problem','For the player the consequence is concrete',
                  'This is where the project gains historical value','The technical issue does not stay behind the scenes',
                  'enters this calendar through concrete design choices rather than through anniversary alone',
                  'is best understood through', 'changes scale when this chapter turns to',
                  'The key question here is how', 'following the chain from a specific rule or production choice',
                  'The chapter therefore treats the detail as evidence rather than trivia')
        generic=[n for n,text in enumerate(body) if any(p.casefold() in text.casefold() for p in patterns)]
        blockers=[]
        if not body or sum(len(p.split()) for p in body)<70:blockers.append('narrative_incomplete')
        if not qualified:blockers.append('verified_hd_cover_missing')
        if len(mapped)<=len(body)//2:blockers.append('majority_contextual_card_images_unreviewed')
        if not entry.get('sources'):blockers.append('historical_sources_missing')
        if generic:blockers.append('inherited_generic_prose_requires_editorial_review')
        if entry.get('source_edition_restoration'):blockers.append('source_edition_has_separate_researched_factual_review')
        if any(x.get('rights_review')=='Source attribution requires review' for x in images):blockers.append('recovered_image_attribution_requires_review')
        records.append(dict(entry_id=entry['id'],title=entry['title'],year=entry['year'],kind=entry.get('kind'),body_sections=len(body),words=sum(len(p.split()) for p in body),hd_images=len(qualified),contextual_sections=sorted(mapped),generic_paragraphs=generic,has_3d=bool(entry.get('models')),status='automated_checks_clear' if not blockers else 'requires_review',editorial_signoff=False,blockers=blockers))
    counts=collections.Counter(b for row in records for b in row['blockers'])
    return {'schema_version':1,'policy':'Readiness is automated metadata only: missing images or models do not remove imported historical articles. Automated checks do not establish editorial signoff. One cover does not imply that every card is illustrated.','target_distinct_illustrated_articles':1095,'distinct_runtime_articles':len(records),'articles_with_verified_hd_cover':sum(x['hd_images']>0 for x in records),'automated_checks_clear_articles':sum(x['status']=='automated_checks_clear' for x in records),'editorially_ready_articles':0,'blockers':dict(counts),'entries':records}
if __name__=='__main__':
    root=Path(__file__).resolve().parents[1];catalog=json.loads((root/'catalog.json').read_text(encoding='utf-8'));result=evaluate(catalog['entries']);result['catalog_sha256']=hashlib.sha256((root/'catalog.json').read_bytes()).hexdigest();(root/'publication-readiness.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='entries'},indent=2))
