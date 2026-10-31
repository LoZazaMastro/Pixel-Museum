"""Metadata-only, bounded Switch compilation/Tour music candidate. No admission."""
from pathlib import Path
import json,re,hashlib,datetime,copy
R=Path(__file__).resolve().parents[1];P=R/'build/research/soundtrack-broad/switch-compilations-tour-next'
def load(n):return json.loads((P/n).read_text(encoding='utf8'))
def sec(t):return sum(int(x)*60**i for i,x in enumerate(reversed(t.split(':'))))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def clean(t):
 t=re.sub(r'\s*\([^)]*[\U0001f000-\U0001ffff0-9]\ufe0f?[^)]*\)\s*',' ',t)
 t=re.sub(r'[\U0001f000-\U0001ffff\ufe0f\u20e3]','',t)
 return re.sub(r'\s+',' ',t).strip()
master=R/'content/catalog.json';catalog=json.loads(master.read_text(encoding='utf8'));byid={e['id']:e for e in catalog['entries']};credit=load('component-composer-source-reuse.json');credit={e['entry_id']:e for e in credit}
room=[];reconciliations=[];held=[]
configs=[("workbook-02-12-super-mario-3d-world-bowser-s-fury","Super Mario 3D World + Bowser's Fury",2021),('wikipedia-63528316','Super Mario 3D All-Stars',2020),('wikipedia-56464502','Mario Kart Tour',2019)]
for eid,title,year in configs:
 assert eid in byid and byid[eid]['title']==title and byid[eid]['year']==year
 tracks=[]
 def track(vid,label,begin,end,version,creator,source,context,rawline,scope,extra=None):
  w=load(vid+'-actual-watch.json');n=load('native-'+vid+'.json');assert n.get('native_compatible_avc_aac') is True
  length=int(w['lengthSeconds']);assert 0<=begin<end<=length,(label,begin,end,length)
  watch='https://www.youtube.com/watch?v='+vid
  d={'youtube_id':vid,'url':watch,'title':clean(label),'creator':creator,'uploader':w['author'],'channel_url':'https://www.youtube.com/channel/'+w['channelId'],'source_page':watch,'publishing_kind':'archival_game_recording','official_uploader_verified':False,'duration_seconds':end-begin,'start_seconds':begin,'end_seconds':end,'source_publication_duration_seconds':length,'source_actual_chapter_title':label,'source_actual_chapter_line':rawline,'recording_version':version,'composer_source':source,'recording_context_source':context,'credit_scope':scope,'rights':'Nintendo and the credited composition, performance and recording contributors retain their respective rights. Public archival uploader is credited separately; no official delivery or redistribution licence is asserted.','publication_metadata_receipt':str((P/(vid+'-actual-watch.json')).relative_to(R)).replace('\\','/'),'native_codec_metadata_receipt':str((P/('native-'+vid+'.json')).relative_to(R)).replace('\\','/'),'native_codec_metadata_verified':True,'playback_verified_on_ps5':False}
  if extra:d.update(extra)
  tracks.append(d);reconciliations.append({'entry_id':eid,'youtube_id':vid,'source_line':rawline,'start_seconds':begin,'end_seconds':end,'publication_duration':length,'positive_native_codec_receipt':d['native_codec_metadata_receipt']})
 if eid==configs[0][0]:
  vid='KHon1vND1pE';w=load(vid+'-actual-watch.json');matches=re.findall(r'^(\d\d:\d\d:\d\d)\s*:\s*#(\d+)\s*:\s*(.+)$',w['shortDescription'],re.M);assert len(matches)==77
  outro=re.search(r'^(\d\d:\d\d:\d\d)\s*:\s*Outro',w['shortDescription'],re.M);assert outro;finish=sec(outro[1])
  roster=credit['wikipedia-39645077']['composer_cache'];assert roster[0]==['Mahito Yokota','Toru Minegishi','Koji Kondo','Yasuaki Iwata']
  for i,(stamp,number,label) in enumerate(matches):
   assert int(number)==i+1
   end=sec(matches[i+1][0]) if i+1<len(matches) else finish
   track(vid,label,sec(stamp),end,'Original Super Mario 3D World score (2013), reused in the 2021 compilation; public archival recording, capture hardware not identified.','Nintendo sound team',roster[1],'https://www.nintendo.com/en-gb/Games/Nintendo-Switch-games/Super-Mario-3D-World-Bowser-s-Fury-1832228.html',stamp+' : #'+number+' : '+label,'Game-level collective attribution; the source game composer roster is retained separately, without assigning every listed person to each cue.',{'component_game':'Super Mario 3D World','original_component_release_year':2013,'game_score_composers':roster[0]})
  vid='GSdvVWFXDBM';w=load(vid+'-actual-watch.json');matches=re.findall(r'^(\d\d:\d\d)\s+(.+)$',w['shortDescription'],re.M);assert len(matches)==30
  for i,(stamp,label) in enumerate(matches):
   end=sec(matches[i+1][0]) if i+1<len(matches) else int(w['lengthSeconds'])
   track(vid,label,sec(stamp),end,"Original Bowser's Fury (2021) score; public archival recording. Capture hardware not identified.",'Nintendo sound team','https://www.nintendo.com/en-gb/Games/Nintendo-Switch-games/Super-Mario-3D-World-Bowser-s-Fury-1832228.html','https://www.nintendo.com/us/whatsnew/super-mario-3d-world-bowsers-fury-pounces-onto-nintendo-switch/',stamp+' '+label,'Organizational/game-level Nintendo credit only. Individual cue composers are not independently documented here; names appearing only as general staff are not assigned composition roles.',{'component_game':"Bowser's Fury",'original_component_release_year':2021,'individual_cue_authorship_documented':False,'organizational_credit_qualification':'Nintendo is the verified original game publisher/owner; Nintendo sound team is an explicit collective display attribution rather than a quoted album-artist credit.'})
  held.append({'youtube_id':vid,'status':'SOURCE_ALTERNATIVE_NOT_DUPLICATED','reason':'Earlier31chapter archive X-0LhAzyid0 is stored/native-compatible but overlapping phases are not counted as additional distinct cues. Selected30chapter source also includes menu/title material. No exhaustive game-file claim.'})
  composer='Nintendo sound team';context='Original Super Mario 3D World score and the new Bowser\u0027s Fury adventure score, with component/version context on every track.'
 elif eid==configs[1][0]:
  vid='NR3PS8aAxjE';w=load(vid+'-actual-watch.json');matches=re.findall(r'^(Super Mario (?:64|Sunshine|Galaxy)):\s*([\d:]+)$',w['shortDescription'],re.M);assert len(matches)==3
  componentids=['super-mario-64','workbook-08-26-super-mario-sunshine','wikipedia-5076476'];years=[1996,2002,2007]
  for i,(game,stamp) in enumerate(matches):
   end=sec(matches[i+1][1]) if i+1<len(matches) else int(w['lengthSeconds']);data=credit[componentids[i]]['composer_cache']
   track(vid,game+' - original score collection',sec(stamp),end,game+' original '+str(years[i])+' score in Super Mario 3D All-Stars compilation context (2020); public archival collection, not a newly composed 2020 score.',', '.join(data[0]),data[1],'https://play.nintendo.com/news-tips/tips-tricks/super-mario-3d-all-stars-game-tips-and-tricks/',game+': '+stamp,'Whole component-score collection credit: documented composers of this component game, not an invented individual cue assignment.',{'component_game':game,'original_component_release_year':years[i],'compilation_release_year':2020,'game_score_composers':data[0],'source_availability_qualification':'Uploader description reports a Denmark block; native metadata currently resolves compatible formats, but worldwide or physical PS5 playback is not asserted.'})
  composer='Koji Kondo, Shinobu Tanaka and Mahito Yokota';context='Three public component-score suites with actual source boundaries. Nintendo documents175music-player tunes; this candidate does not fabricate175individual cue boundaries or claim exact retail-master equivalence.'
 else:
  vid='Pbn5NX1awx0';w=load(vid+'-actual-watch.json');matches=re.findall(r'^([\d:]+)\s*-\s*(.+)$',w['shortDescription'],re.M);assert len(matches)>90
  for i,(stamp,label) in enumerate(matches):
   end=sec(matches[i+1][0]) if i+1<len(matches) else int(w['lengthSeconds'])
   track(vid,label,sec(stamp),end,'Original Mario Kart Tour mobile-game score, including subsequent in-game courses and arrangements; public archival collection.','Nintendo sound team','https://www.nintendo.com/en-gb/Games/Smart-device-games/Mario-Kart-Tour-1626402.html','https://www.nintendo.com/en-gb/Games/Smart-device-games/Mario-Kart-Tour-1626402.html',stamp+' - '+label,'Organizational/game-level Nintendo attribution; individual Tour cue composers and original-theme/arrangement roles are not independently resolved. Retrospective course names do not imply original SNES/DS/Wii capture.',{'individual_cue_authorship_documented':False,'organizational_credit_qualification':'Nintendo is the verified game publisher/owner; collective display attribution is not represented as an official named album artist.','original_component_release_year':2019})
  composer='Nintendo sound team';context='Available original mobile-game source passages, including course updates. This is not Mario Kart World or a substituted Mario Kart8Deluxe Booster Course Pass collection.'
 room.append({'entry_id':eid,'match_title':title,'match_year':year,'title':'Listen to '+title,'composer':composer,'curator_note':'Listen to the music of '+composer+' from '+title+'.','replace_existing_tracks':True,'full_album_collection':False,'coverage_status':'PUBLIC_AVAILABLE_COLLECTION_NOT_ALL_GAME_FILES_CLAIM','recording_collection_scope':context,'tracks':tracks})
result={'schema_version':1,'publication_status':'NEXT_AWAITING_INDEPENDENT_PEER_NOT_ADMITTED','source_catalog_sha256':sha(master),'scope':'Three requested Nintendo collections. No media download, inferred per-cue composer roster, fabricated chapter boundary or PS5-playback claim.','entries':room,'held_or_alternate_sources':held}
target=P/'three-switch-compilation-tour-public-music-candidate.json';assert not target.exists(),'Frozen candidate must not be overwritten; create a new version for changes.'
target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(P/'chapter-reconciliation.json').write_text(json.dumps({'rows':reconciliations},ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'candidate_sha256':sha(target),'counts':[(r['match_title'],len(r['tracks'])) for r in room],'tracks':sum(len(r['tracks']) for r in room)}))
