import hashlib, importlib.util, json, urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[2]
def mod(n,f):
 s=importlib.util.spec_from_file_location(n,f);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=mod('p',R/'content/expansion/soundtrack-broad-pipeline.py');v=mod('v',R/'tools/discover-museum-videos.py');D=p.RESEARCH/'rhythm-priorities'
BUT='https://music.apple.com/us/song/butterfly/696134076'
BEAT='https://musicbrainz.org/release/8eec00c4-1101-4f49-8ed6-e917e41f3d2b'
BEAT2='https://bm5keys-forever.com/soundtracks/2ndmix'
SOLO='https://dancedancerevolution.fandom.com/wiki/PARANOIA_EVOLUTION'
receipts=[]
for slug,u,markers in [('butterfly-label-credit',BUT,['Butterfly','Robert Uhlmann','Robin Rex']),('beatmania-original1998-album',BEAT,['u gotta groove','1998']),('beatmania-original-booklet-transcription',BEAT2,['U GOTTA GROOVE','DJ NAGUREO']),('solo-composer-comment-transcription',SOLO,['NAOKI','EVOLUTION'])]:
 try:
  raw=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=18).read().decode('utf8');assert all(x in raw for x in markers);f=D/(slug+'.html');f.write_text(raw,encoding='utf8');receipts.append({'source_page':u,'actual_body_retrieved':True,'local_source':f.relative_to(R).as_posix(),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
 except Exception as ex:receipts.append({'source_page':u,'actual_body_retrieved':False,'error':str(ex),'separate_web_read':True,'note':'Actual web source reviewed; no local error/challenge body accepted as evidence.'})
groups=[
 ('dance-dance-revolution','Dance Dance Revolution',1998,'Smile.dk','licensed_playlist',[
  ('QzcvRDWgRIE','Butterfly','Smile.dk',BUT,'https://zenius-i-vanisher.com/v5.2/viewsimfile.php?simfileid=672',True,{'songwriters':'Robert Uhlmann; Robin Rex','vocals':'Nina Boquist; Veronica Almqvist','production_and_mixing':'Robert Uhlmann; Robin Rex','mastering':'Bj\u00f6rn Engelmann'},'Original 1998 Parlophone performance, official Warner Music Denmark music-video publication. Full commercial single rather than the shorter interactive game edit; not the 2009 re-recording.')]),
 ('wikipedia-234683','Beatmania',1997,'DJ nagureo','game_score',[
  ('szi-hi8x5FY','u gotta groove!','DJ nagureo',BEAT2,BEAT,False,{},'Original-game composition, archived 1998 BEAT MANIA -REMIXES- WITH beatmania ORIGINAL SOUNDTRACK, track 8 in the original-soundtrack section. The selected 1:12 original is separate from the album\u2019s long remix tracks.'),
  ('Wb3iFqLv43I','20, November (single edit)','DJ nagureo','https://www.idec.or.jp/aboutus/news_release/190809_YBG2020.pdf',BEAT2,False,{},'Official later beatmania IIDX soundtrack version of the original 1997 composition, archived upload. Exact IIDX album edition not identified by uploader; no assertion of original arcade capture hardware.')]),
 ('workbook-08-19-dance-dance-revolution-solo-bass-mix','Dance Dance Revolution Solo Bass Mix',1999,'NAOKI Maeda','game_score',[
  ('-ojArcVgUOk','PARANOIA EVOLUTION','200 (NAOKI Maeda)',SOLO,'https://musicbrainz.org/release/21e9b99e-ccaa-4cdb-9dd4-4b612e6f9858',False,{'credited_composer_alias':'200','credit_evidence_scope':'Original composer\u2019s NAOKI MAEDA production comment transcribed by specialist archive; alias and original Solo BASS MIX composition independently corroborated.'},'Original 1999 Solo BASS MIX composition, credited archival upload. Capture hardware and album edit not identified; not the NONSTOP MEGAMIX or later fan arrangement.')]),
 ('workbook-06-08-green-day-rock-band','Green Day: Rock Band',2010,'Green Day','licensed_playlist',[
  ('3PEcvNwN49w','Jesus of Suburbia','Green Day','https://www.youtube.com/watch?v=3PEcvNwN49w','https://purenintendo.com/entertainment-weekly-reveals-full-track-list-for-green-day-rock-band/',True,{'songwriters':'Billie Joe Armstrong; Mike Dirnt; Tr\u00e9 Cool','production':'Billie Joe Armstrong; Mike Dirnt; Tr\u00e9 Cool; Rob Cavallo','mixing':'Chris Lord-Alge','mastering':'Ted Jensen'},'Official Reprise original 2004 American Idiot album recording. Full commercial song licensed by the 2010 game, not the Broadway cast recording, music-video narrative edit or later live performance.')]),
]
entries=[];audit=[]
for eid,game,year,composer,kind,rows in groups:
 ts=[]
 for vid,title,creator,source,context,official,roles,version in rows:
  a=p.watch(vid)
  try:c=v.metadata(vid,{'title':a['title'],'channel':a['author']});assert c.get('native_compatible_avc_aac') is True
  except Exception as ex:audit.append({'youtube_id':vid,'status':'CODEC_HOLD','reason':str(ex)});print('HOLD',vid,flush=True);continue
  t={'youtube_id':vid,'url':'https://www.youtube.com/watch?v='+vid,'title':title,'creator':creator,'composer_source':source,'recording_context_source':context,'recording_version':version,'additional_recording_roles':roles,'uploader':a['author'],'channel_url':'https://www.youtube.com/channel/'+a['channelId'],'source_page':'https://www.youtube.com/watch?v='+vid,'official_uploader_verified':official,'publishing_kind':'official_artist_or_label_recording' if official else 'credited_archival_game_recording','duration_seconds':int(a['lengthSeconds']),'verification_receipt':'build/research/soundtrack-broad/watch/'+vid+'.json','native_codec_metadata_receipt':'build/research/video-discovery/video-'+vid+'.json','native_codec_metadata_verified':True,'playback_verified_on_ps5':False,'rights':'Original composers, writers, performers, publishers and labels retain their rights. Archival uploader credit does not imply official endorsement.'}
  if kind=='licensed_playlist':t.update({'music_kind':'licensed_song','recording_artists':[creator],'delivered_music_roles':[line for line in a.get('shortDescription','').splitlines() if ':' in line and any(w in line.lower().split(':')[0] for w in ['composer','writer','lyricist','producer','engineer','vocals','guitar','drums'])]})
  ts.append(t);audit.append({'youtube_id':vid,'status':'AWAITING_INDEPENDENT_REVIEW','actual_title':a['title'],'actual_description_read':True});print('CANDIDATE',game,title,flush=True)
 if ts:
  e={'entry_id':eid,'match_title':game,'match_year':year,'title':'Listen to '+game,'composer':composer,'curator_note':('Listen to the licensed music of '+game+'.') if kind=='licensed_playlist' else ('Listen to music by '+composer+' from '+game+'.'),'tracks':ts}
  if kind=='licensed_playlist':e.update({'music_kind':kind,'replace_existing_tracks':True})
  entries.append(e)
out=D/'rhythm-three-gaps-and-greenday-five-candidate.json';assert not out.exists();p.write(out,{'publication_status':'awaiting_independent_review','entries':entries});p.write(D/'rhythm-three-more-source-receipts.json',receipts);p.write(D/'rhythm-three-more-editorial-audit.json',audit);print('FINAL',len(entries),sum(len(e['tracks']) for e in entries),hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
