"""Reconcile published211-composition inventory with actual archival cue timestamps.

This is a review candidate, not an approval of bit-identical CD performance or
all uploader annotations. Ambiguous durations remain explicitly reported.
"""
import hashlib,html,json,pathlib,re,unicodedata
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=ROOT/'build/research/soundtrack-broad/nintendo-full'
raw=(OUT/'botw-columbia-actual.html').read_text(encoding='utf-8')
primary=[html.unescape(re.sub('<[^>]+>','',x))for x in re.findall(r'<p class="stream-ttl">(.*?)</p>',raw,re.S)][:211]
mb=json.loads((OUT/'botw-cd-english-translated-inventory.json').read_text());english=[t for medium in mb['media']for t in medium['tracks']];assert len(primary)==len(english)==211
watch=json.loads((ROOT/'build/research/soundtrack-broad/watch/zncStfmvIA4.json').read_text())
chapters=[]
for m in re.finditer(r'(?m)^(\d{1,2}:\d{2}(?::\d{2})?)\s*-\s*(.+)',watch['shortDescription']):
 parts=[int(x)for x in m[1].split(':')];chapters.append({'title':m[2],'start_seconds':sum(n*60**i for i,n in enumerate(reversed(parts)))})
assert len(chapters)==210
def norm(s):
 s=re.sub(r'[\W\d_]','',unicodedata.normalize('NFKC',s)).lower()
 return s.replace('originalsoundtrackver','').replace('bonustrack','')
for n,ch in enumerate(chapters):
 index=n if n<136 else n+1
 if index!=121:assert norm(primary[index])==norm(ch['title']),(index,primary[index],ch['title'])
tracks=[];duration_flags=[]
for i in range(211):
 if i==136:
  id='eV3lW-l9SFE';start=2110;end=2126;uploader='Seec Aesyr';title_source='[4.25] All Twelve Memories'
 else:
  n=i if i<136 else i-1;ch=chapters[n];id='zncStfmvIA4';start=ch['start_seconds'];end=chapters[n+1]['start_seconds'] if n+1<len(chapters) else 22222;uploader='fwug';title_source=ch['title']
 assert end>start and start>=0
 expected=english[i].get('length',0)/1000
 if abs(expected-(end-start))>7:duration_flags.append({'track':i+1,'title':english[i]['title'],'published_cd_seconds':expected,'archival_chapter_seconds':end-start,'status':'REVIEW_CAPTURE_VERSION_OR_BOUNDARY','not_claimed':'Not a bit-identical CD recording assertion.'})
 t={'youtube_id':id,'url':'https://www.youtube.com/watch?v='+id,'source_page':'https://www.youtube.com/watch?v='+id,'title':english[i]['title'],'creator':'Nintendo sound team','composer_source':'https://www.nintendo.com/jp/topics/article/a0d07f85-1b5c-11e8-a129-063b7ac45a6d','album_inventory_source':'https://columbia.jp/prod-info/COCX-40313-7/','translated_track_title_source':'https://musicbrainz.org/release/6c100fef-6abf-41c4-bd21-6f9becaaab6c','published_original_title':primary[i],'album_track_number':i+1,'start_seconds':start,'end_seconds':end,'duration_seconds':end-start,'archival_published_cue_label':title_source,'uploader':uploader,'official_uploader_verified':False,'publishing_kind':'archival_game_score_recording','recording_version':'Archival same-game soundtrack compilation; the published2018album inventory includes DLC/bonus compositions. Capture hardware and CD-master identity are not independently established.','artist_credit_scope':'Nintendo sound team is a collective game/album-level credit. Individual cue authorship is not separately documented here; no whole roster is attributed to every cue.','base_game_score_composers':['Manaka Kataoka','Yasuaki Iwata','Hajime Wakai'],'rights':'Original music rights retained by Nintendo and credited authors. This is an independently credited archival YouTube upload, not an official Nintendo channel.','native_codec_metadata_verified':True,'native_codec_metadata_receipt':f'build/research/video-discovery/video-{id}.json','publication_metadata_receipt':f'build/research/soundtrack-broad/watch/{id}.json','playback_verified_on_ps5':False}
 tracks.append(t)
candidate={'schema_version':1,'publication_status':'awaiting_independent_archival_and_boundary_review','scope':'211 distinct published album compositions covered by actual source timestamps, with explicit review flags for archival version/boundary differences. No promotion until these flags are resolved.','entries':[{'entry_id':'wikipedia-32307637','match_title':'The Legend of Zelda: Breath of the Wild','match_year':2017,'title':'Listen to The Legend of Zelda: Breath of the Wild','composer':'Nintendo sound team','curator_note':'Listen to the music of Nintendo sound team\nThe Legend of Zelda: Breath of the Wild','tracks':tracks,'replace_existing_tracks':True,'expected_album_tracks':211}],'duration_review_flags':duration_flags,'missing_cue_supplement_review':'Disc4.25 chapter2110–2126 agrees with published14.933s cue within1.1s; other end-of-disc annotations in that supplemental upload are erroneous and are not used.'}
dest=OUT/'botw-211-boundary-review-candidate.json';dest.write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('Candidate211 SHA',hashlib.sha256(dest.read_bytes()).hexdigest(),'duration reviews',len(duration_flags))
