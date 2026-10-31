"""Restore complete source themes after the legacy short narrative projection.

Exact source text and native local photographs are bound to an immutable source
snapshot. The previous article remains archived rather than appended twice.
"""
from __future__ import annotations
import copy, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DOCUMENT='content/expansion/playhub-theme-complete-kojima.json'

def digest(value):
 return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf8')).hexdigest()

def checked_document(root=ROOT):
 root=Path(root);doc=json.loads((root/DOCUMENT).read_text(encoding='utf8'))
 if doc.get('publication_status')!='complete_source_reuse_verified':raise ValueError('Complete theme is not verified')
 for name,expected in doc['source_files'].items():
  if hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected:raise ValueError('Playhub source snapshot changed: '+name)
 archive=root/doc['previous_record_archive']
 if hashlib.sha256(archive.read_bytes()).hexdigest()!=doc['previous_record_archive_sha256']:raise ValueError('Previous theme archive changed')
 source=json.loads((root/'content/expansion/playhub-theme-sources/history_editorial.json').read_text(encoding='utf8'))
 theme=next(t for t in source['themes'] if t['id']==doc['theme_id'])
 expected=[theme['intro']['en']]+[c['body']['en'] for c in theme['chapters']]
 headings=[theme['title']['en']]+[c['title']['en'] for c in theme['chapters']]
 if doc['body']!=expected or doc['story_headings']!=headings:raise ValueError('Complete source theme text/order changed')
 mapped={image['story_paragraph'] for image in doc['images'] if image.get('story_paragraph',-1)>=0}
 if mapped!=set(range(len(expected))):raise ValueError('Complete theme has an unillustrated paragraph')
 pixels=[image['source_pixel_sha256'] for image in doc['images']]
 if len(pixels)!=len(set(pixels)):raise ValueError('Repeated source image pixels in complete theme')
 if any(max(image.get('width',0),image.get('height',0))<1000 for image in doc['images']):raise ValueError('Small image in complete HD theme')
 if len(doc['videos'])!=2 or doc['videos'][0]['youtube_id']!='6thnV_sV96M':raise ValueError('Kojima official conversation order changed')
 for movie in doc['videos']:
  if not movie['verification']['native_codec_metadata_verified']:raise ValueError('Unverified video in complete theme')
 return doc

def integrate(entries,root=ROOT):
 root=Path(root);doc=checked_document(root);entry=next((e for e in entries if e['id']==doc['target_entry_id']),None)
 if entry is None:raise ValueError('Missing destination for complete theme: '+doc['target_entry_id'])
 before={'body':copy.deepcopy(entry.get('body',[])),'story_headings':copy.deepcopy(entry.get('story_headings',[])),'images':copy.deepcopy(entry.get('images',[])),'videos':copy.deepcopy(entry.get('videos',[])),'sources':copy.deepcopy(entry.get('sources',[])),'provenance':copy.deepcopy(entry.get('provenance',{}))}
 for field in ['subtitle','summary','body','story_headings','images','videos','preferred_image']:
  entry[field]=copy.deepcopy(doc[field])
 # Visible source credits identify original institutions/creators. The original
 # project/import credit remains verbatim in the preserved prior record.
 sources=[s for s in before['sources'] if 'playhub' not in (s.get('publisher','')+' '+s.get('url','')).lower()]
 known={s.get('url') for s in sources}
 for source in doc['sources']:
  if source['url'] not in known:sources.append(copy.deepcopy(source));known.add(source['url'])
 entry['sources']=sources
 entry['editorial_mode']='complete_source_theme'
 entry['editorial_credit']='Exhibition narrative from the preserved source edition; historical references and original media creators listed in Credits.'
 entry['source_feature_title']=doc['subtitle']
 entry['explicit_story_media_only']=True
 provenance=entry.setdefault('provenance',{})
 if not isinstance(provenance,dict):provenance={'previous_provenance':copy.deepcopy(provenance)};entry['provenance']=provenance
 provenance['complete_playhub_theme']={'theme_id':doc['theme_id'],'declaration':DOCUMENT,'source_files':copy.deepcopy(doc['source_files']),'original_record_archive':doc['previous_record_archive'],'original_record_archive_sha256':doc['previous_record_archive_sha256'],'verbatim_english_intro_and_chapters':True,'chapter_count':len(doc['body'])-1,'source_body_sha256':digest(doc['body']),'original_languages_preserved_in_source_snapshot':True,'replacement_notes':copy.deepcopy(doc['media_replacement_notes'])}
 return {'status':'PASS','entry_id':entry['id'],'theme_id':doc['theme_id'],'paragraphs':len(entry['body']),'chapters':len(entry['body'])-1,'native_unique_images':len(entry['images']),'paragraph_bindings':len([i for i in entry['images'] if i['story_paragraph']>=0]),'verified_videos':len(entry['videos']),'previous_record_archive':doc['previous_record_archive'],'previous_projection_body_sha256':digest(before['body']),'complete_source_body_sha256':digest(entry['body']),'previous_projection':before,'new_records_created':0,'source_text_rewritten':False,'images_upscaled':False}
