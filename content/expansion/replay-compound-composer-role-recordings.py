import importlib.util,json,copy
from pathlib import Path
R=Path(__file__).resolve().parents[2];s=importlib.util.spec_from_file_location('p',R/'content/expansion/soundtrack-broad-pipeline.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p);B=p.RESEARCH;D=json.loads((R/'content/catalog.json').read_text());games={e['id']:e for e in (D if isinstance(D,list) else D['entries']) if e.get('kind')=='game'};done={e['entry_id'] for e in json.loads((R/'content/expansion/soundtrack-independent-approved.json').read_text())['entries']};out=[];folder=B/'compound-role-replay';folder.mkdir(exist_ok=True)
for eid,e in games.items():
 if eid in done:continue
 recordpath=B/'games'/(eid+'.json');target=folder/(eid+'.json')
 if not recordpath.exists():continue
 if target.exists():out.append(json.loads(target.read_text()));continue
 old=json.loads(recordpath.read_text());vs=[];seen=set()
 for c in old.get('candidates',[]):
  vid=c.get('youtube_id');wp=B/'watch'/(str(vid)+'.json')
  if not vid or vid in seen or not wp.exists():continue
  seen.add(vid);vs.append((vid,json.loads(wp.read_text())))
 if not vs:continue
 names,source,ev=p.composer(e)
 if not names:continue
 names=p.clean_composer_names(names,e['title']);tracks=[];checks=[]
 for vid,w in vs:
  row={'id':vid,'title':w['title'],'channel':w['author'],'channel_id':w['channelId']}
  t,reason=p.consider(e,row,names,source);checks.append({'youtube_id':vid,'accepted':bool(t),'reason':reason})
  if t and t['duration_seconds']<1200:tracks.append(t)
 selection={'entry_id':eid,'match_title':e['title'],'match_year':e['year'],'title':'Listen to '+e['title'],'tracks':tracks,'composer':p.selected_music_credit(tracks,names),'curator_note':'Listen to music from '+e['title']+'.','independent_composer_credit':{'composers':names,'source_page':source,'evidence':ev}}
 if tracks:selection,holds=p.final_identity_gate({'entry_id':eid,'composers':names,'selection':selection},list(games.values()))
 else:holds=[]
 result={'entry_id':eid,'title':e['title'],'state':'candidate_pending_independent_review' if selection['tracks'] else 'recording_pending','selection':selection,'checks':checks,'final_holds':holds};p.write(target,result);out.append(result);print(e['title'],len(selection['tracks']),'candidates',flush=True)
 p.write(B/'compound-role-replay-candidates.json',{'publication_status':'research_only_not_admitted','scope':'Actual cached publications replayed after recognizing explicit compound ComposerLyricist roles. Exact source, album, edition and contributor gates retained; no new search queries. Individual review and native codec remain required.','checked':len(out),'entries':[x['selection'] for x in out if x['selection']['tracks']]})
print('FINAL',len(out),sum(bool(x['selection']['tracks']) for x in out),flush=True)
