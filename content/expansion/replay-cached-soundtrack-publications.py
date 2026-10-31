"""Re-check already cached actual publications after source/role fixes, offline.
Never downloads or mutates broad per-game records; candidates remain unapproved.
"""
import json,importlib.util,copy,collections
from pathlib import Path
R=Path(__file__).resolve().parents[2];s=importlib.util.spec_from_file_location('p',R/'content/expansion/soundtrack-broad-pipeline.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
def offline(url):raise ValueError('Offline replay has no source fetch; cached independent evidence required')
p.fetch=offline
cat=json.loads((R/'content/catalog.json').read_text());cat=cat if isinstance(cat,list) else cat['entries'];games={e['id']:e for e in cat if e.get('kind')=='game'}
for e in games.values():p.TITLE_YEARS.setdefault(p.norm(e['title']),set()).add(e['year'])
known=set()
for file in [R/'content/expansion/soundtrack-broad-research-selections.json',p.RESEARCH/'supradarky-original-cue-candidates.json',p.RESEARCH/'public-curated-original-cue-candidates.json',p.RESEARCH/'supradarky-additional-cue-candidates.json']:
 known.update(e['entry_id'] for e in json.loads(file.read_text())['entries'] if e.get('tracks'))
results=[];holds=[]
for path in sorted((p.RESEARCH/'games').glob('*.json')):
 record=json.loads(path.read_text());entry=games.get(record['entry_id'])
 if not entry:continue
 names,url,ev=p.composer(entry);names=p.clean_composer_names(names,entry['title'])
 if not names or not p.composer_source_identity_verified(entry,url):continue
 vids=list(dict.fromkeys([v['youtube_id'] for v in record.get('candidates',[]) if v.get('youtube_id')]+[t['youtube_id'] for t in record.get('selection',{}).get('tracks',[])]));tracks=[]
 for vid in vids:
  if not (p.RESEARCH/'watch'/(vid+'.json')).exists():continue
  v=p.watch(vid);row={'id':vid,'title':v['title'],'channel':v['author'],'channel_id':v['channelId'],'description':v['shortDescription']};track,reason=p.consider(entry,row,names,url)
  if track:tracks.append(track)
  else:holds.append({'entry_id':entry['id'],'youtube_id':vid,'reason':reason})
 if not tracks:continue
 tracks.sort(key=lambda t:(not t['official_uploader_verified'],t['duration_seconds']>1200));individual=[t for t in tracks if t['duration_seconds']<=1200];tracks=(individual or tracks)[:3];selection={'entry_id':entry['id'],'match_title':entry['title'],'match_year':entry['year'],'title':'Listen to '+entry['title'],'composer':p.selected_music_credit(tracks,names),'tracks':tracks,'independent_composer_credit':{'composers':names,'source_page':url,'evidence':ev}}
 selection,errors=p.final_identity_gate({'entry_id':entry['id'],'composers':names,'selection':selection},list(games.values()))
 if not selection['tracks']:continue
 selection['new_coverage_route']=entry['id'] not in known;results.append(selection)
 if selection['new_coverage_route']:print('NEW',entry['title'],len(selection['tracks']),flush=True)
 if len(results)%25==0:p.write(p.RESEARCH/'cached-publication-identity-replay.json',{'publication_status':'auditing','entries':results})
p.write(p.RESEARCH/'cached-publication-identity-replay.json',{'publication_status':'auditing','scope':'Offline replay of cached actual publications after exact-source/composition-role corrections. Source/page/album gate retained; candidates not approved; codec and independent review still required.','entries':results,'holds':holds})
print('FINAL',len(results),'rooms',sum(e['new_coverage_route'] for e in results),'new coverage',flush=True)
