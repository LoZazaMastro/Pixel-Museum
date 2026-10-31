"""Offline recertification of cached soundtrack research. No network requests.
Keeps original receipts; broad output remains quarantined until editorial review.
"""
import importlib.util,json,collections,copy
from pathlib import Path
root=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('broad',root/'content/expansion/soundtrack-broad-pipeline.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
doc=json.loads((root/'content/catalog.json').read_text());catalog=doc if isinstance(doc,list) else doc['entries'];games={e['id']:e for e in catalog if e.get('kind')=='game'}
for e in games.values():p.TITLE_YEARS.setdefault(p.norm(e['title']),set()).add(e['year'])
overrides={}
for filename in ['soundtrack-composer-source-overrides.json','soundtrack-composer-source-overrides-extra.json','soundtrack-composer-source-overrides-primary.json','soundtrack-composer-source-overrides-third.json','soundtrack-composer-credit-completeness-extra.json']:
 path=root/'content/expansion'/filename
 if path.exists():overrides.update({k:v for k,v in json.loads(path.read_text()).get('entries',{}).items() if not v.get('name_correction_only') and not any('Credited artist' in role for role in v.get('roles',{}).values())})
raw={}
for f in (p.RESEARCH/'search').glob('*.json'):
 try:
  for row in json.loads(f.read_text()):raw[row['id']]=row
 except Exception:pass
review=[]
for file in (p.RESEARCH/'games').glob('*.json'):
 old=json.loads(file.read_text());eid=old['entry_id']
 if eid not in games:continue
 e=games[eid]
 if p.norm(e['title']) in p.SILENT:
  p.write(file,{**old,'pipeline_version':p.PIPELINE_VERSION,'state':'excluded_no_original_score','reason':p.SILENT[p.norm(e['title'])]});continue
 c=overrides.get(eid,{})
 names=p.clean_composer_names(c.get('composers') or old.get('composers',[]),e['title']);source=c.get('source_page') or old.get('composer_source','');evidence=c.get('evidence') or old.get('composer_evidence','')
 source_ok=p.composer_source_identity_verified(e,source) or (c.get('source_identity_verified_for_entry')==eid)
 if not source_ok and names:
  names,source,evidence=p.composer(e);names=p.clean_composer_names(names,e['title'])
 out={**old,'pipeline_version':p.PIPELINE_VERSION,'composers':names,'composer_source':source,'composer_evidence':evidence,'offline_recertification':p.STAMP,'state':'recording_research_required'}
 out.pop('selection',None)
 candidates=[];tracks=[];seen=set()
 for candidate in old.get('candidates',[])+old.get('selection',{}).get('tracks',[]):
  vid=candidate.get('youtube_id','')
  if not vid or vid in seen:continue
  seen.add(vid);receipt=p.RESEARCH/'watch'/(vid+'.json')
  if not receipt.exists():continue
  v=json.loads(receipt.read_text());row=raw.get(vid) or {'id':vid,'title':v.get('title'),'channel':v.get('author'),'channel_id':v.get('channelId'),'description':v.get('shortDescription')}
  t,reason=p.consider(e,row,names,source)
  candidates.append({'youtube_id':vid,'title':v.get('title'),'uploader':v.get('author'),'accepted':bool(t),'reason':reason})
  if t:tracks.append(t)
 if not names:out['state']='composer_research_required'
 if tracks:
  tracks.sort(key=lambda t:(not t['official_uploader_verified'],t['duration_seconds']>1200))
  individual=[t for t in tracks if t['duration_seconds']<=1200]
  if individual:tracks=individual
  n=', '.join(names)
  out['selection']={'entry_id':eid,'match_title':e['title'],'match_year':e['year'],'title':'Listen to '+e['title'],'composer':n,'curator_note':f'Listen to music by {n} from {e["title"]}.','tracks':tracks[:3]}
  selected,holds=p.final_identity_gate(out,list(games.values()))
  if selected['tracks']:out.update(state='admitted',selection=selected)
  else:out.pop('selection',None)
  if holds:out['identity_holds']=holds
 out['candidates']=candidates
 p.write(file,out)
 if old['state']=='admitted' or out['state']=='admitted':review.append({'entry_id':eid,'title':e['title'],'year':e['year'],'before':old['state'],'after':out['state'],'composer':names,'tracks':out.get('selection',{}).get('tracks',[]),'holds':out.get('identity_holds',[]),'rejections':[x for x in candidates if not x['accepted']]})
p.write(p.RESEARCH/'offline-identity-recertification.json',{'publication_status':'auditing','checked':p.STAMP,'entries':review})
print(p.assemble())
print(collections.Counter(r['after'] for r in review))
