import json,importlib.util,re,copy
from pathlib import Path
R=Path(__file__).resolve().parents[2];s=importlib.util.spec_from_file_location('p',R/'content/expansion/soundtrack-broad-pipeline.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p);B=p.RESEARCH/'user-priority';doc=json.loads((B/'priority-original-score-composer-checkpoint.json').read_text());folder=B/'recordings-v2';folder.mkdir(exist_ok=True)
for row in doc['entries']:
 e=row['entry'];names=p.clean_composer_names(row.get('composers',[]),e['title']);source=row.get('composer_source','');f=folder/(e['id']+'.json')
 if f.exists():continue
 if not names:continue
 if e['title']=='Fantavision':names=[re.sub(r'^(?:JP|NA|PAL):\s*','',n) for n in names]
 queries=[e['title']+' original soundtrack Topic',e['title']+' '+names[0]+' original soundtrack',e['title']+' main theme original soundtrack',e['title']+' battle original soundtrack',e['title']+' '+names[0]+' Provided to YouTube'];tracks=[];checked=[];seen=set()
 for q in queries:
  try:
   for v in p.search(q):
    if v['id'] in seen:continue
    seen.add(v['id']);track,reason=p.consider(e,v,names,source);checked.append({'youtube_id':v['id'],'title':v.get('title'),'channel':v.get('channel'),'accepted':bool(track),'reason':reason})
    if track and track['duration_seconds']<=1200:tracks.append(track)
    if len(tracks)>=8:break
  except Exception as ex:checked.append({'query':q,'error':str(ex)})
  if len(tracks)>=8:break
 selection={'entry_id':e['id'],'match_title':e['title'],'match_year':e['year'],'title':'Listen to '+e['title'],'composer':p.selected_music_credit(tracks,names),'tracks':tracks,'curator_note':'Listen to music from '+e['title']+'.','independent_composer_credit':{'composers':names,'source_page':source,'evidence':row.get('composer_evidence','')}}
 result={'entry':e,'catalog_identity_pending':row.get('catalog_identity_pending',False),'composers':names,'composer_source':source,'state':'candidates_pending_manual_review' if tracks else 'recording_pending','selection':selection,'checked_candidates':checked};p.write(f,result);print(e['title'],len(tracks),'candidates',flush=True)
 records=[json.loads(x.read_text()) for x in folder.glob('*.json')];p.write(B/'priority-original-recording-candidates-v2.json',{'publication_status':'research_only_not_admitted','scope':'Userpriority exact-game original recording search, up to8individualcue for meaningful selections. All metadata/source gates unchanged; manual role/version review and codec still required. No media downloaded.','checked':len(records),'entries':[r['selection'] for r in records if r['selection']['tracks']],'holds':[{'title':r['entry']['title'],'state':r['state']} for r in records if not r['selection']['tracks']]})
