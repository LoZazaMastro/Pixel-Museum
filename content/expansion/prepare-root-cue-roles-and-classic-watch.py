import json,copy,hashlib,importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2];B=R/'build/research/soundtrack-broad'
def mod(n,path):
 s=importlib.util.spec_from_file_location(n,R/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=mod('p','content/expansion/soundtrack-broad-pipeline.py');v=mod('v','tools/discover-museum-videos.py')
d=json.loads((B/'compound-role-replay-candidates.json').read_text());roots=json.loads((B/'root-primary-cue-roles.json').read_text());decisions={x['youtube_id']:x for x in roots['decisions']};entries=[];audit=[]
for e in d['entries']:
 tracks=[]
 for t in e['tracks']:
  q=decisions.get(t['youtube_id'])
  if not q:continue
  t=copy.deepcopy(t);vid=t['youtube_id'];w=p.watch(vid)
  try:c=v.metadata(vid,{'title':w['title'],'channel':w['author']});assert c.get('native_compatible_avc_aac')
  except Exception as ex:audit.append({'youtube_id':vid,'status':'CODEC_HOLD','reason':str(ex)});continue
  t['creator']=q['composer'];t['independently_matched_composers']=[q['composer']];t.update(native_codec_metadata_receipt='build/research/video-discovery/video-'+vid+'.json',native_codec_metadata_verified=True,playback_verified_on_ps5=False,recording_version='Official 2015 original-game soundtrack album release.' if e['match_title']=='Bloodborne' else 'Official original 2017 Horizon Zero Dawn soundtrack recording.')
  t['composer_source']=q['primary_sources'][0];t['additional_recording_roles']={'vocals':q['performer']} if q.get('performer') else {'arrangement':'Penka Kouneva'}
  t['additional_role_credit_sources']=q['primary_sources']
  if e['match_title']=='Bloodborne':t['composer_source']='https://www.qobuz.com/jp-ja/album/bloodborne-bloodborne/ualpkukrtm76b';t['additional_role_credit_sources']=[t['composer_source'],'https://blog.playstation.com/?p=151755'];t['primary_source_review_receipt']='build/research/soundtrack-broad/compound-role-source-reviews/bloodborne-qobuz-label-review.json'
  else:t['primary_source_review_receipt']='build/research/soundtrack-broad/root-primary-cue-roles.json'
  tracks.append(t);audit.append({'youtube_id':vid,'status':'PASS_CANDIDATE_PENDING_PEER','creator':t['creator'],'additional_recording_roles':t['additional_recording_roles']});print(vid,'PASS_CODEC',flush=True)
 if tracks:
  e=copy.deepcopy(e);e['tracks']=tracks;e['composer']=', '.join(dict.fromkeys(t['creator'] for t in tracks));e['curator_note']='Listen to music by '+e['composer']+' from '+e['match_title']+'.';entries.append(e)
f=B/'checkpoints/root-cue-roles-two-games3-candidate.json';f.write_text(json.dumps({'publication_status':'awaiting_independent_review','entries':entries,'editorial_audit':audit},ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('ROOT3FINAL',len(entries),sum(len(e['tracks']) for e in entries),hashlib.sha256(f.read_bytes()).hexdigest(),flush=True)
watchids=['K7_JMWnC64g','kP48ndIylv4','tz9J1yyU8XQ','I8jQYD00cvw','UMn_wVF8wOQ','iFisJiUAd8c','OuNPduAfsHg'];records=[]
for vid in watchids:
 try:w=p.watch(vid);records.append({'youtube_id':vid,'actual_publication':w});print('CLASSIC_WATCH',vid,w['title'],flush=True)
 except Exception as ex:records.append({'youtube_id':vid,'error':str(ex)})
 (B/'user-priority/classic-seven-actual-watch.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
