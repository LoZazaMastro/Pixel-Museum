import json,copy,re,hashlib,importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2];B=R/'build/research/soundtrack-broad';D=B/'user-priority/jedi-getaway-review';D.mkdir(exist_ok=True)
def mod(n,f):
 s=importlib.util.spec_from_file_location(n,R/f);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=mod('p','content/expansion/soundtrack-broad-pipeline.py');v=mod('v','tools/discover-museum-videos.py')
d=json.loads((B/'user-priority/priority-original-recording-candidates-v2.json').read_text());add=json.loads((R/'content/expansion/user-requested-game-additions.json').read_text())['entries'];cat=json.loads((R/'content/catalog.json').read_text());cat=cat if isinstance(cat,list) else cat['entries'];ids={(p.norm(e['title']),e['year']):e['id'] for e in cat+add}
sources={'Star Wars Jedi: Fallen Order':'https://www.ea.com/ea-play/news/star-wars-jedi-fallen-order-official-soundtrack-release','Star Wars Jedi: Survivor':'https://www.universal-music.de/star-wars-soundtrack/musik/star-wars-jedi-survivor-original-video-game-soundtrack-871498'}
receipts={};entries=[];audit=[]
for e in d['entries']:
 e=copy.deepcopy(e);e['entry_id']=ids[(p.norm(e['match_title']),e['match_year'])];url=sources.get(e['match_title'],e['tracks'][0]['composer_source']);f=D/(p.norm(e['match_title'])+'.html')
 try:
  raw=f.read_text(encoding='utf-8') if f.exists() else p.fetch(url);title=re.search('<title[^>]*>(.*?)</title>',raw,re.S|re.I);title=p.text(title.group(1)) if title else ''
  assert title and not re.search('client challenge|access denied|just a moment',title,re.I);f.write_text(raw,encoding='utf-8');receipts[e['entry_id']]={'source_page':url,'actual_title':title,'local_source':str(f.relative_to(R)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'actual_body_validated':True}
 except Exception as ex:receipts[e['entry_id']]={'source_page':url,'error':str(ex)};print('SOURCE_HOLD',e['match_title'],flush=True);continue
 tracks=[]
 for t in e['tracks']:
  vid=t['youtube_id']
  if vid=='ZmJJoDRcl2s':continue
  w=json.loads((B/'watch'/(vid+'.json')).read_text());q={'entry_id':e['entry_id'],'youtube_id':vid,'actual_title':w['title'],'actual_uploader':w['author'],'actual_publication_credit_fields':[l.strip() for l in w['shortDescription'].splitlines() if ':' in l and re.search(r'composer|producer|lyricist',l.split(':',1)[0],re.I)]}
  try:
   c=v.metadata(vid,{'title':w['title'],'channel':w['author']});assert c.get('native_compatible_avc_aac')
   t.update(native_codec_metadata_receipt='build/research/video-discovery/video-'+vid+'.json',native_codec_metadata_verified=True,playback_verified_on_ps5=False,composer_source=url,editorial_source_review_receipt='build/research/soundtrack-broad/user-priority/jedi-getaway-review/primary-source-receipts.json')
   release=re.search(r'Released on:\s*((?:19|20)\d{2})',w['shortDescription']);t['recording_version']='Archival original-game score; capture hardware not identified.'
   if release:t['recording_release_year']=int(release.group(1));t['recording_version']='Official '+release.group(1)+' original-game soundtrack album release.'
   t['delivered_music_roles']=q['actual_publication_credit_fields'];tracks.append(t);q['status']='PASS_CANDIDATE_PENDING_PEER';print(e['match_title'],vid,'PASS_CODEC',flush=True)
  except Exception as ex:q['status']='CODEC_HOLD';q['reason']=str(ex)
  audit.append(q)
 e['tracks']=tracks
 if tracks:entries.append(e)
 (D/'primary-source-receipts.json').write_text(json.dumps(receipts,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(D/'recording-editorial-review.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
out=D/'jedi-getaway-max12-candidate.json';out.write_text(json.dumps({'publication_status':'awaiting_independent_review','scope':'Exact original requested game score recordings; cue-specific actual publisher composer/compound composerlyricist roles, independent primary game association and native AVC/AAC metadata. No media/listening/fingerprint/PS5 claim.','entries':entries},ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('FINAL',len(entries),sum(len(e['tracks']) for e in entries),hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
