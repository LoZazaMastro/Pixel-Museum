import json,importlib.util,argparse,concurrent.futures
from pathlib import Path
R=Path(__file__).resolve().parents[2];s=importlib.util.spec_from_file_location('p',R/'content/expansion/soundtrack-broad-pipeline.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p);ap=argparse.ArgumentParser();ap.add_argument('--limit',type=int,default=120);args=ap.parse_args();rs=p.RESEARCH;folder=rs/'supplemental-mainstream';folder.mkdir(exist_ok=True)
doc=json.loads((R/'content/catalog.json').read_text());games=[e for e in (doc if isinstance(doc,list) else doc['entries']) if e.get('kind')=='game' and e.get('year',0)>=1980]
for e in games:p.TITLE_YEARS.setdefault(p.norm(e['title']),set()).add(e['year'])
covered={e['entry_id'] for e in json.loads((rs/'checkpoints/incremental-336-578-official-curated-rolefixed-2026-10-21.json').read_text())['entries']};seeds=json.loads((R/'content/expansion/major-release-seeds.json').read_text());priority={p.norm(t) for titles in seeds['years'].values() for t in titles};wanted=[]
for e in games:
 old=rs/'games'/(e['id']+'.json')
 if e['id'] in covered:continue
 if old.exists() and json.loads(old.read_text()).get('state') in ['admitted','excluded_no_original_score','composer_research_required']:continue
 wanted.append(e)
wanted.sort(key=lambda e:(p.norm(e['title']) not in priority,e['year']<1995,e['title']));base=p.source_searches
def queries(e):
 names,source,ev=p.composer(e)
 if not names:return []
 return [e['title']+' '+names[0]+' main theme soundtrack',e['title']+' original soundtrack Provided to YouTube']+base(e)
p.source_searches=queries
processed=0
for entry in wanted:
 path=folder/(entry['id']+'.json')
 if path.exists():continue
 if processed>=args.limit:break
 try:
  d=p.process(entry,retry=True);selection=d.get('selection')
  if selection:
   selection,holds=p.final_identity_gate({'entry_id':entry['id'],'composers':d['composers'],'selection':selection},games);d['selection']=selection;d['final_identity_holds']=holds
   if not selection['tracks']:d['state']='recording_research_required'
  p.write(path,d);print(processed,entry['title'],d['state'],len(d.get('selection',{}).get('tracks',[])),flush=True)
 except Exception as ex:p.write(path,{'entry_id':entry['id'],'title':entry['title'],'state':'research_error','error':str(ex)});print('ERROR',entry['title'],str(ex),flush=True)
 processed+=1
 records=[json.loads(x.read_text()) for x in folder.glob('*.json')];entries=[x['selection'] for x in records if x.get('state')=='admitted' and x.get('selection',{}).get('tracks')];p.write(rs/'supplemental-mainstream-candidates.json',{'publication_status':'research_only_not_admitted','scope':'New exactgame/currentcomposer searchphrases, cache-resumable. Same identity/credit/versiongates replayed; independentreview andnativecodec stillrequired. No media downloaded.','checked':len(records),'entries':entries,'holds':[{'entry_id':x['entry_id'],'title':x['title'],'state':x['state']} for x in records if x.get('state')!='admitted']})
print('FINAL',processed,'newchecked',len(entries),'candidates',flush=True)
