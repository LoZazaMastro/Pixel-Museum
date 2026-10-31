"""Compare actual source chapters and image identity with assembled articles.

Entry presence alone is never treated as a complete import. This is read-only
against the catalogue; optional projected imports are applied in memory only.
"""
import argparse, collections, hashlib, json, re, runpy, unicodedata
from pathlib import Path
from urllib.parse import unquote, urlsplit
from PIL import Image
R=Path(__file__).resolve().parents[2]
S=R/'content/expansion/playhub-theme-sources'
P=Path('F:/Playhub/Plugin/Playhub/assets/on-this-day/v1')
def norm(s):return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',s).casefold()).strip()
def title(s):return ''.join(c for c in norm(re.sub(r'\s*\([^)]*\)','',s)) if c.isalnum())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
cache={}
def identity(path):
 path=Path(path)
 if path not in cache:
  try:
   with Image.open(path) as im:
    im.load();cache[path]={'bytes_sha256':sha(path),'pixels_sha256':hashlib.sha256(im.convert('RGB').tobytes()).hexdigest(),'width':im.width,'height':im.height,'path':str(path)}
  except Exception as ex:cache[path]={'error':str(ex),'path':str(path)}
 return cache[path]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--project-kojima',action='store_true');ap.add_argument('--output');args=ap.parse_args()
 source=json.loads((S/'history_editorial.json').read_text(encoding='utf8'));media=json.loads((S/'history_images.json').read_text(encoding='utf8'))
 raw=(R/'content/catalog.json').read_bytes();catalog=json.loads(raw)['entries']
 if args.project_kojima:runpy.run_path(str(R/'content/expansion/integrate_playhub_theme_complete.py'))['integrate'](catalog,R)
 manifest=json.loads((R/'assets/images/manifest.json').read_text(encoding='utf8')) if (R/'assets/images/manifest.json').exists() else {}
 global_prose=norm('\n'.join(p for e in catalog for p in list(e.get('body',[]))+[p for f in e.get('editorial_features',[]) for p in f.get('body',[])]))
 reviewed_destinations={'lawson':'channel-f','kondo':'feature-kondo-functional-music'}
 rows=[]
 for theme in source['themes']:
  candidates=[e for e in catalog if title(e.get('title',''))==title(theme['topic']) or title(e.get('source_topic',''))==title(theme['topic']) or title(e.get('source_subject',''))==title(theme['topic'])]
  if theme['id'] in reviewed_destinations:candidates=[e for e in catalog if e['id']==reviewed_destinations[theme['id']]]
  if not candidates and theme['kind']=='creator':
   candidates=[e for e in catalog if e.get('kind') in ['person','feature'] and any(title(unquote(urlsplit(s.get('url','')).path.rsplit('/',1)[-1]).replace('_',' '))==title(theme['topic']) for s in e.get('sources',[]) if 'wikipedia.org/wiki/' in s.get('url',''))]
  source_texts=[theme.get('intro',{}).get('en','')]+[c.get('body',{}).get('en','') for c in theme.get('chapters',[])]
  source_texts=[s for s in source_texts if s]
  def texts(e):return list(e.get('body',[]))+[p for f in e.get('editorial_features',[]) for p in f.get('body',[])]
  if candidates:
   candidates.sort(key=lambda e:(sum(norm(s) in norm('\n'.join(texts(e))) for s in source_texts),e.get('kind')=='person',not e.get('calendar_only',False)),reverse=True)
  e=candidates[0] if candidates else None
  bodies=texts(e) if e else [];joined=norm('\n'.join(bodies));heads=(e.get('story_headings',[]) if e else [])+[h for f in (e or {}).get('editorial_features',[]) for h in f.get('story_headings',[])]
  matches=[{'source_index':n,'intro':n==0,'title':theme['title'].get('en','') if n==0 else theme['chapters'][n-1]['title'].get('en',''),'exact_complete_text_present':norm(s) in joined,'exact_heading_present':norm(theme['title'].get('en','') if n==0 else theme['chapters'][n-1]['title'].get('en','')) in [norm(h) for h in heads]} for n,s in enumerate(source_texts)]
  runtime_images=list((e or {}).get('images',[]))+[i for f in (e or {}).get('editorial_features',[]) for i in f.get('images',[])]
  runtime=[];groups=collections.defaultdict(list)
  for n,image in enumerate(runtime_images):
   u=image.get('url','');base=unquote(urlsplit(u).path.rsplit('/',1)[-1]);local=None
   if image.get('recovery_local_source') and (R/image['recovery_local_source']).is_file():local=R/image['recovery_local_source']
   elif (P/base).is_file():local=P/base
   elif manifest.get('images',{}).get(u) and (R/manifest['images'][u]).is_file():local=R/manifest['images'][u]
   ident=identity(local) if local else {};key=image.get('source_pixel_sha256') or ident.get('pixels_sha256') or u
   groups[key].append(n);runtime.append({'index':n,'url':u,'basename':base,'story_paragraph':image.get('story_paragraph'),'identity':ident,'pixel_identity':key,'title':image.get('title','')})
  expected=[]
  for image in media.get(theme['id'],[]):
   f=P/image['file'];ident=identity(f) if f.exists() else {'error':'source local file missing'}
   matched=[i['index'] for i in runtime if i['basename']==image['file'] or i['pixel_identity']==ident.get('pixels_sha256')]
   expected.append({'file':image['file'],'subject':image.get('subject',''),'source_identity':ident,'runtime_image_indices':matched,'source_long_edge':max(ident.get('width',0),ident.get('height',0))})
  mapped={i['story_paragraph'] for i in runtime if isinstance(i.get('story_paragraph'),int) and i['story_paragraph']>=0}
  duplicates=[{'image_indices':indices,'canonical_identity':key,'urls':[runtime[n]['url'] for n in indices]} for key,indices in groups.items() if len(indices)>1]
  rows.append({'theme_id':theme['id'],'topic':theme['topic'],'source_kind':theme.get('kind',''),'entry_id':e['id'] if e else None,'candidate_entry_ids':[c['id'] for c in candidates],'source_intro_and_chapters':len(source_texts),'complete_source_paragraphs_found':sum(m['exact_complete_text_present'] for m in matches),'complete_source_paragraphs_anywhere_in_runtime':sum(norm(s) in global_prose for s in source_texts),'missing_complete_source_paragraphs':[m for m in matches if not m['exact_complete_text_present']],'source_chapter_matches':matches,'runtime_body_paragraphs':len((e or {}).get('body',[])),'source_images':len(expected),'source_images_found':sum(bool(i['runtime_image_indices']) for i in expected),'source_images_missing':[i for i in expected if not i['runtime_image_indices']],'source_image_inventory':expected,'runtime_images':runtime,'repeated_image_identities':duplicates,'runtime_explicitly_illustrated_paragraphs':sorted(mapped),'runtime_paragraphs_without_explicit_image':[n for n in range(len((e or {}).get('body',[]))) if n not in mapped],'status':'COMPLETE_SOURCE_TEXT' if e and all(m['exact_complete_text_present'] for m in matches) else 'INCOMPLETE_SOURCE_TEXT' if e else 'NO_MATCHED_ARTICLE'})
 imported_path=Path('F:/Playhub/Plugin/Playhub/Source/GamingModeDeckyPlugin/quick_settings/history_imported.json')
 imported=json.loads(imported_path.read_text(encoding='utf8'))
 imported_rows=[]
 for record in imported['entries']:
  if not record.get('published'):continue
  t=record['theme'];eid=t['id'];targets=[e for e in catalog if e['id']==eid or e.get('source_record_id')==eid or e.get('calendar_editorial',{}).get('provenance',{}).get('source_record_id')==eid]
  body=[t.get('intro',{}).get('en','')]+[ch.get('body',{}).get('en','') for ch in t.get('chapters',[])];body=[s for s in body if s]
  whole=norm('\n'.join(p for e in targets for p in texts(e)))
  expected=media.get(t.get('media_id',eid),[]);actual=[i for e in targets for i in e.get('images',[])];actual_names={unquote(urlsplit(i.get('url','')).path.rsplit('/',1)[-1]) for i in actual}
  missing=[]
  for im in expected:
   local=P/im['file'];ident=identity(local) if local.exists() else {'error':'source local file missing'}
   # Current replacements can legitimately supersede the small original portrait.
   present=im['file'] in actual_names or any(i.get('url')==im.get('url') for i in actual)
   if not present:missing.append({'file':im['file'],'subject':im.get('subject',''),'source_dimensions':[ident.get('width',0),ident.get('height',0)],'source_url':im.get('url'),'source_page':im.get('sourceUrl'),'source_pixel_sha256':ident.get('pixels_sha256')})
  imported_rows.append({'source_id':eid,'subject':t.get('subject',t.get('topic','')),'source_kind':t.get('kind'),'runtime_ids':[e['id'] for e in targets],'runtime_kinds':[e.get('kind') for e in targets],'source_intro_and_chapters':len(body),'complete_source_paragraphs_present':sum(norm(s) in whole for s in body),'complete_source_paragraphs_anywhere_in_runtime':sum(norm(s) in global_prose for s in body),'runtime_images':len(actual),'source_images':len(expected),'source_images_missing':missing,'runtime_narrative_bindings':[{'entry_id':e['id'],'paragraphs':len(e.get('body',[])),'explicit_image_paragraphs':sorted({i['story_paragraph'] for i in e.get('images',[]) if isinstance(i.get('story_paragraph'),int) and i['story_paragraph']>=0})} for e in targets]})
 summary={'themes':len(rows),'matched_articles':sum(bool(r['entry_id']) for r in rows),'source_paragraphs':sum(r['source_intro_and_chapters'] for r in rows),'complete_source_paragraphs_found':sum(r['complete_source_paragraphs_found'] for r in rows),'themes_with_all_source_text':sum(r['status']=='COMPLETE_SOURCE_TEXT' for r in rows),'source_images':sum(r['source_images'] for r in rows),'source_images_found':sum(r['source_images_found'] for r in rows),'articles_with_repeated_image_identity':sum(bool(r['repeated_image_identities']) for r in rows),'published_workbook_entries':len(imported_rows),'workbook_source_paragraphs':sum(r['source_intro_and_chapters'] for r in imported_rows),'workbook_complete_paragraphs_present':sum(r['complete_source_paragraphs_present'] for r in imported_rows)}
 summary['theme_complete_paragraphs_anywhere_in_runtime']=sum(r['complete_source_paragraphs_anywhere_in_runtime'] for r in rows)
 summary['workbook_complete_paragraphs_anywhere_in_runtime']=sum(r['complete_source_paragraphs_anywhere_in_runtime'] for r in imported_rows)
 out={'schema_version':1,'scope':'Exact source-to-article audit, including complete body text, image identity and explicit card bindings. Missing exact prose may reflect a prior rewrite, not proof the subject was absent. Image matches are source basename or actual decoded source pixels; reused source wrappers alone do not count as complete chapters. Superseded low-quality originals are listed, not automatically restored.','catalog_sha256':hashlib.sha256(raw).hexdigest(),'projected_kojima_import':args.project_kojima,'source_file_hashes':{**{f.name:sha(f) for f in S.glob('*.json')},'history_imported.json':sha(imported_path)},'summary':summary,'people_priority':[r['theme_id'] for r in rows if r['source_kind'] in ['creator','person'] and (r['status']!='COMPLETE_SOURCE_TEXT' or r['source_images_found']<r['source_images'])],'themes':rows,'published_workbook':imported_rows,'published_people_image_gaps':[r for r in imported_rows if 'person' in r['runtime_kinds'] and r['source_images_missing']]}
 path=R/args.output if args.output else R/'build/research/kojima-playhub-complete'/('global-theme-audit-projected.json' if args.project_kojima else 'global-theme-audit-current.json');path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps(summary));print('PEOPLE PRIORITY',out['people_priority'])
 for row in rows:
  if 'sakurai' in row['theme_id'].lower() or 'sakurai' in row['topic'].lower():print('SAKURAI',json.dumps({k:v for k,v in row.items() if k not in ['runtime_images','source_image_inventory','source_images_missing','source_chapter_matches']},ensure_ascii=False))
 for row in imported_rows:
  if 'sakurai' in row['source_id']:print('SAKURAI',json.dumps(row,ensure_ascii=False))
if __name__=='__main__':main()
