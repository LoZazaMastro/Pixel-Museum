"""Freeze two separately selectable complete artist albums, pending peer review."""
import concurrent.futures,hashlib,importlib.util,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=ROOT/'build/research/death-stranding2-complete-score'
sp=importlib.util.spec_from_file_location('v',ROOT/'tools/discover-museum-videos.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
data=json.loads((OUT/'both-rooms-complete72-discovery.json').read_text())['records'];assert len(data)==72
def probe(row):
 id=row['candidate_id']
 try:
  d=v.metadata(id,{'title':row['publication']['title'],'channel':row['publication']['author']})
  return id,{'ok':d['native_compatible_avc_aac'],'receipt':f'build/research/video-discovery/video-{id}.json'}
 except Exception as e:return id,{'ok':False,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:
 native={}
 for id,state in pool.map(probe,data):native[id]=state;print(id,state['ok'],flush=True)
(OUT/'complete72-native-probes.json').write_text(json.dumps(native,indent=2)+'\n',encoding='utf-8')
if not all(v['ok']for v in native.values()):raise SystemExit('Native holds preserved; no promotion.')
rooms=[]
for id,artist,count in [('woodkid','Woodkid',16),('forssell','Ludvig Forssell',56)]:
 room={'id':id,'title':f'Listen to {artist}','composer':artist,'curator_note':f'Listen to the music of {artist}\nDeath Stranding 2: On the Beach','tracks':[],'full_album_collection':True,'expected_album_tracks':count}
 for row in [r for r in data if r['room_id']==id]:
  video=row['candidate_id'];w=row['publication'];roles={};composers=[]
  for block in row['credits'][0].split(' - '):
   fields=[f.strip()for f in block.split(',')];name=fields[0]
   for role in fields[1:]:
    if role in {'Composer','Lyricist','Arranger','Guitar','Piano','Choir','Producer','Recording Engineer','Mastering Engineer','Mixing Engineer','Programmer','Chorus Master','FeaturedArtist','Bassoon','Saxophone','Clarinet'}:roles.setdefault(role,[]).append(name)
   if 'Composer'in fields:composers.append(name)
  assert composers,row['item_name']
  t={'youtube_id':video,'url':'https://www.youtube.com/watch?v='+video,'source_page':'https://www.youtube.com/watch?v='+video,'title':row['item_name'],'creator':', '.join(dict.fromkeys(composers)),'composer_source':row['source'],'album_inventory_source':row['source'],'album_track_number':row['album_number'],'recording_album':row['item_category'],'recording_year':2025,'recording_version':'Official 2025 '+('Woodkid artist album, including its labelled bonus tracks.'if id=='woodkid'else'original game-score album.'),'uploader':w['author'],'channel_url':'https://www.youtube.com/channel/'+w['channelId'],'official_uploader_verified':True,'publishing_kind':'official_label_delivered_recording','label_published_track_credits':row['credits'],'additional_recording_roles':{k:names for k,names in roles.items()if k not in ['Composer','MainArtist','AssociatedPerformer']},'duration_seconds':float(w['lengthSeconds']),'primary_published_title':w['title'],'native_codec_metadata_verified':True,'native_codec_metadata_receipt':native[video]['receipt'],'publication_metadata_receipt':f'build/research/soundtrack-broad/watch/{video}.json','rights':'Original composition, performance and recording rights retained by credited authors and recording owners; streams remain on the actual public artist/label publication.','playback_verified_on_ps5':False}
  if row['item_name']=='Minus Sixty One':
   t['recording_year']=2020;t['recording_version']='Original artist-issued S16 recording (2020), licensed on the 2025 Woodkid for Death Stranding2 album; the album itself retains a2020phonogram credit. Mastering equivalence is not asserted.'
  if row['item_name']=="BB's Theme (2022)":t['recording_version']='2022 vocal version featuring Troy Baker, included on the official2025DeathStranding2 score album; not claimed as a newly recorded2025cue.'
  room['tracks'].append(t)
 assert len(room['tracks'])==count
 assert len(set(t['youtube_id']for t in room['tracks']))==count
 rooms.append(room)
out={'schema_version':1,'publication_status':'awaiting_independent_review','entries':[{'match_title':'Death Stranding 2: On the Beach','match_year':2025,'soundtrack_rooms':rooms}],'scope':'Two complete separately selectable artist albums: Woodkid16 and LudvigForssell56, each actual cue and composition role preserved. The score inventory was read through the ordinary public Qobuz pagination endpoint. No media download, listening, audio-fingerprint or physicalPS5playback assertion.'}
dest=OUT/'two-rooms-complete72-candidate.json';dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('FREEZE',hashlib.sha256(dest.read_bytes()).hexdigest())
