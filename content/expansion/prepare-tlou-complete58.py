"""Freeze all58 exact original album tracks, after bounded native metadata probes."""
import concurrent.futures,copy,hashlib,importlib.util,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=ROOT/'build/research/last-of-us-score-review'
s=importlib.util.spec_from_file_location('v',ROOT/'tools/discover-museum-videos.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
discovery=json.loads((OUT/'complete58-individual-discovery.json').read_text())
base=json.loads((ROOT/'content/expansion/soundtrack-multitrack-priority-overrides.json').read_text())
def probe(r):
 if r.get('candidate'):return r['candidate']['youtube_id'],True,r['candidate']['native_codec_metadata_receipt']
 assert r['state']in ['actual_sony_publication_read','actual_sony_label_topic_publication_read'],r
 try:
  d=v.metadata(r['candidate_id'],{'title':r['publication']['title'],'channel':r['publication']['author']})
  return r['candidate_id'],d['native_compatible_avc_aac'],f"build/research/video-discovery/video-{r['candidate_id']}.json"
 except Exception as exc:return r['candidate_id'],False,str(exc)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 native={}
 for id,ok,path in pool.map(probe,discovery['records']):
  native[id]={'ok':ok,'receipt':path};print(id,ok,flush=True)
(OUT/'complete58-native-probes.json').write_text(json.dumps(native,indent=2)+'\n',encoding='utf-8')
if not all(r['ok']for r in native.values()):raise SystemExit('Some native probes held; all results preserved, no production promotion.')
entries=copy.deepcopy(base['entries'])
for part,e in enumerate(entries):
 template=e['tracks'][0];e['tracks']=[];e['full_album_collection']=True
 e['album_completeness']={'expected_tracks':30 if part==0 else 28,'source':'Original Sony-delivered album table; exact order and titles, no DLC or television album.','inventory_receipt':'build/research/last-of-us-score-review/complete58-individual-discovery.json'}
 for r in [r for r in discovery['records'] if r['part']==part]:
  t=copy.deepcopy(r.get('candidate') or template)
  id=r.get('candidate_id') or t['youtube_id'];assert native[id]['ok']
  w=r.get('publication') or json.loads((ROOT/f'build/research/soundtrack-broad/watch/{id}.json').read_text())
  composers=[]
  for block in r['credits'][0].split(' - '):
   fields=[x.strip() for x in block.split(',')]
   if 'Composer'in fields:composers.append(fields[0])
  assert len(composers)==1,(r['item_name'],r['credits'])
  t.update(youtube_id=id,url='https://www.youtube.com/watch?v='+id,source_page='https://www.youtube.com/watch?v='+id,title=r['item_name'],creator=composers[0],duration_seconds=float(w['lengthSeconds']),label_published_track_credits=r['credits'],primary_published_title=w['title'],label_credited_recording_artists=[r['item_brand']],native_codec_metadata_receipt=native[id]['receipt'],publication_metadata_receipt=f'build/research/soundtrack-broad/watch/{id}.json',album_track_number=r['album_number'],recording_album=r['item_category'])
  if r['state']=='actual_sony_label_topic_publication_read':
   t['uploader']=w['author'];t['channel_url']='https://www.youtube.com/channel/'+w['channelId']
   t['publishing_kind']='official_label_delivered_recording'
   t['official_uploader_evidence']=r['publication_provenance']
  t.pop('independent_identity_review',None)
  e['tracks'].append(t)
 assert len(e['tracks'])==(30 if part==0 else 28)
 assert len(set(t['youtube_id']for t in e['tracks']))==len(e['tracks'])
out={'schema_version':1,'publication_status':'awaiting_independent_full_album_review','scope':'Complete original base-game albums:30 tracks2013 and28 tracks2020. Each is an individual official Sony publication.','entries':entries,'validation_scope':'Exact Sony channel/title/album provenance, independently read original label per-cue roles and native AVC/AAC metadata. No listening/fingerprint/console playback claim.'}
dest=OUT/'two-games-complete58-candidate.json';dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('FREEZE',hashlib.sha256(dest.read_bytes()).hexdigest(),flush=True)
