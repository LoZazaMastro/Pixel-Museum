"""Restore reviewed source chapters without resurrecting calendar wrappers.

The existing museum adaptation remains intact. Only concepts independently read
as missing are appended, and existing unique gallery artifacts become narrative
illustrations. No photograph-only padding or invented historical dates.
"""
from pathlib import Path
import copy,hashlib,json
ROOT=Path(__file__).resolve().parents[2]
def integrate(entries,root=ROOT):
 root=Path(root);path=root/'content/expansion/playhub-theme-semantic-restorations.json'
 doc=json.loads(path.read_text(encoding='utf8'))
 if doc.get('publication_status')!='source_chapters_semantically_reviewed':return {'status':'not_admitted'}
 source=root/'content/expansion/playhub-theme-sources/history_editorial.json'
 if hashlib.sha256(source.read_bytes()).hexdigest()!=doc['source_sha256']:raise ValueError('Reviewed Playhub source changed')
 themes={t['id']:t for t in json.loads(source.read_text(encoding='utf8'))['themes']};by_id={e['id']:e for e in entries};report=[]
 by_id.update({feature['id']:feature for e in entries for feature in e.get('editorial_features',[])})
 for repair in doc.get('calendar_wrapper_repairs',[]):
  entry=by_id[repair['entry_id']]
  entry['year']=repair['year'];entry['date']=copy.deepcopy(repair['date']);entry['event_semantics']='release'
  for original,replacement in repair['text_replacements']:
   entry['body']=[p.replace(original,replacement)for p in entry['body']]
   entry['summary']=entry.get('summary','').replace(original,replacement)
  entry.setdefault('provenance',{})['calendar_wrapper_removed']={'previous_scheduling':repair['previous_scheduling'],'verified_release_source':repair['source'],'semantic_review':'Keep original narrative; remove the unrelated observance framing. One release stop only.'}
  if repair['source']['url']not in{s.get('url')for s in entry['sources']}:entry['sources'].append(copy.deepcopy(repair['source']))
 for row in doc['restorations']:
  entry=by_id[row['entry_id']];theme=themes[row['theme_id']];restored=[]
  for chapter in row['chapters']:
   original=theme['chapters'][chapter['source_chapter_index']]
   if chapter['body']!=original['body']['en'] or chapter['title']!=original['title']['en']:raise ValueError('Chapter is not the preserved English source')
   body=entry.setdefault('body',[]);heads=entry.setdefault('story_headings',[])
   if chapter['body']in body:index=body.index(chapter['body'])
   else:
    while len(heads)<len(body):heads.append('')
    replace=next((n for n,p in enumerate(body)if hashlib.sha256(p.encode()).hexdigest()==chapter.get('replace_generic_body_sha256')),None)
    if replace is None:index=len(body);body.append(chapter['body']);heads.append(chapter['title'])
    else:index=replace;body[index]=chapter['body'];heads[index]=chapter['title']
   # Fresh, independently checked source artifacts belong to their narrative,
   # rather than becoming another uncaptioned gallery at the end of the article.
   for addition in chapter.get('images',[]):
    image=next((i for i in entry.setdefault('images',[])if i['url']==addition['url']),None)
    if image is None:image=copy.deepcopy(addition);entry['images'].append(image)
    else:image.update(copy.deepcopy(addition))
    image['story_paragraph']=index
   for url in chapter.get('existing_image_urls',[]):
    image=next((i for i in entry.get('images',[])if i['url']==url),None)
    if image is None:raise ValueError('Missing reviewed illustration '+url)
    image['story_paragraph']=index
    if chapter.get('image_title'):image['title']=chapter['image_title']
    if chapter.get('image_credit'):image['creator']=chapter['image_credit'];image['credit']=chapter['image_credit']+' / original game imagery'
   restored.append({'source_chapter_index':chapter['source_chapter_index'],'story_paragraph':index,'body_sha256':hashlib.sha256(chapter['body'].encode()).hexdigest(),'illustration_pending':not bool(chapter.get('existing_image_urls')or chapter.get('images'))})
  for url in row.get('remove_redundant_image_urls',[]):entry['images']=[i for i in entry.get('images',[])if i['url']!=url]
  # Source credit is provenance, never a claim that Playhub owns game artwork.
  entry.setdefault('provenance',{}).setdefault('restored_playhub_chapters',[]).append({'theme_id':row['theme_id'],'source_file':source.relative_to(root).as_posix(),'source_sha256':doc['source_sha256'],'chapters':restored,'calendar_wrapper_excluded':True,'museum_adaptation_preserved':True})
  known={s.get('url')for s in entry.setdefault('sources',[])}
  for url in row['historical_sources']:
   if url not in known:entry['sources'].append({'title':'Historical reference retained from the source exhibition','url':url});known.add(url)
  report.append({'entry_id':entry['id'],'theme_id':row['theme_id'],'chapters':len(restored),'new_timeline_entries':0})
 return {'status':'PASS','restorations':report,'chapters':sum(r['chapters']for r in report)}
