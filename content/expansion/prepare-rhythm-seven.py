import hashlib, importlib.util, json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
def mod(n,f):
 s=importlib.util.spec_from_file_location(n,f);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=mod('p',R/'content/expansion/soundtrack-broad-pipeline.py');v=mod('v',R/'tools/discover-museum-videos.py')
D=p.RESEARCH/'rhythm-priorities';D.mkdir(exist_ok=True)
P1='https://soundcloud.com/masaya-matsuura/sets/parappa-the-rapper'
P2='https://downloads.khinsider.com/game-soundtracks/album/parappa-the-rapper-2-original-soundtrack'
REZ='https://www.rezinfinite.com/rez-infinite-original-soundtrack-releasing-on-october-11-2017/'
RB='https://www.nintendoworldreport.com/pr/23919/rock-band-3-full-song-list-officially-confirmed'
LUM='https://www.mobygames.com/game/110622/lumines-remastered/credits/windows/'
GH='https://www.engadget.com/2009-07-18-interview-shaimus.html'
SLIP='https://jambands.com/features/2006/04/16/the-future-in-the-present-tense-brad-barr-and-the-slip/'
GD='https://purenintendo.com/entertainment-weekly-reveals-full-track-list-for-green-day-rock-band/'
QUEEN='https://blogs.loc.gov/now-see-hear/2024/12/all-hail-queen-an-interview-with-sir-brian-may/'
sources=[('rez-publisher',REZ,['Protocol Rain','Keiichi']),('rockband3-harmonix-press-release',RB,['Bohemian Rhapsody','Break on Through']),('green-day-setlist',GD,['Basket Case']),('parappa2-album-credit-transcription',P2,['Masaya Matsuura','Naoto Sugai']),('shaimus-first-person-interview',GH,['not-quite-finished','All Of This']),('slip-first-person-interview',SLIP,['Even Rats','Guitar Hero']),('queen-brian-may-interview',QUEEN,['Freddie','Bohemian Rhapsody'])]
receipts=[]
for slug,url,markers in sources:
 f=D/(slug+'.html')
 try:
  raw=f.read_text(encoding='utf8') if f.exists() else p.fetch(url)
  text=p.text(raw);assert all(x in text for x in markers)
  f.write_text(raw,encoding='utf8');receipts.append({'source_page':url,'actual_body_retrieved':True,'local_source':f.relative_to(R).as_posix(),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
 except Exception as ex:receipts.append({'source_page':url,'actual_body_retrieved':False,'error':str(ex),'separate_web_read':True,'note':'Web actual read is recorded in review; local error/challenge body is not evidence.'})
# Explicit IDs keep Japanese original-release chronology independent of later local editions.
groups=[
 ('wikipedia-21468511','PaRappa the Rapper',1996,'Masaya Matsuura; Tattle & Dynamo','game_score',[
  ('5OwwiLKiVJQ',"Chop Chop Master Onion's Rap",'Masaya Matsuura; Tattle & Dynamo',False,P1,P1,{'additional_composition':'Tattle & Dynamo','rap_and_words':'Ryuichi Watabe'},'Original 1996 game song, credited archival upload. Composer-owned portfolio corroborates the composition and explicit additional-composition role; precise capture hardware not identified.'),
  ('ihowg8t9QwA',"Instructor Mooselini's Rap",'Masaya Matsuura; Tattle & Dynamo',False,P1,P1,{'additional_composition':'Tattle & Dynamo','words':'Ryuichi Watabe','rap':'Dred Foxx','Instructor_Mooselini_voice_as_credited':'Sandra'},'Original 1996 game song, credited archival upload. Composer portfolio identifies the original composition and collaborators; capture hardware not identified.')]),
 ('workbook-01-23-parappa-the-rapper-2','PaRappa the Rapper 2',2001,'Masaya Matsuura','game_score',[
  ('ErhyFXQjKwU','Toasty Buns','Masaya Matsuura',False,P2,P2,{'lyrics':'RYU','vocals':'Dred Foxx; Ethan Enbanks','arrangement':'Masaya Matsuura','drums':'Naoto Sugai'},'Original 2001 Toy\u2019s Factory album TFCG-88189, track 11, archival upload. Individual track authorship and drums retained from original-album credit transcription; no 2002 first-release claim.'),
  ('uw0nCHvU19o',"Noodles Can't Be Beat",'Masaya Matsuura',False,P2,P2,{'lyrics':'RYU','vocals':'Dred Foxx; Andrew Alonzo','arrangement':'Masaya Matsuura'},'Original 2001 game song, archival upload. Individual track 29 and performer roles corroborated by original Toy\u2019s Factory album credit transcription; capture hardware not identified.')]),
 ('wikipedia-101230','Rez',2001,'Keiichi Sugiyama; Mist','game_score',[
  ('8wo6sNbzlYk','Buggie Running Beeps 01 (Area 01)','Keiichi Sugiyama',True,'https://www.youtube.com/watch?v=8wo6sNbzlYk',REZ,{},'Official 2017 U/M/A/A Rez Infinite soundtrack edition, disc 1 original-game Area 01. Not the new Area X score.'),
  ('PnWM4JHYDRY','Protocol Rain (Area 02)','Mist',True,'https://www.youtube.com/watch?v=PnWM4JHYDRY',REZ,{},'Official 2017 U/M/A/A Rez Infinite soundtrack edition, disc 1 original-game Area 02. Not the new Area X score.')]),
 ('lumines','Lumines',2004,'Mondo Grosso','licensed_playlist',[
  ('n_xNTvN03TU',"SHININ'",'Mondo Grosso feat. Kj',True,LUM,LUM,{'music':'Shinichi Osawa','lyrics':'Kj','production':'Shinichi Osawa'},'Official Sony original 2003 single performance licensed by Lumines; full commercial single rather than the shorter interactive PSP game edit.')]),
 ('wikipedia-2757511','Guitar Hero',2005,'Various artists','licensed_playlist',[
  ('oDj-JAuo8xE','All of This','Shaimus',True,GH,GH,{'songwriting':'Phil Beaudreau'},'Artist-issued Paper Sun finished album version, 2006 CDBaby. The band confirms Guitar Hero used an earlier not-quite-finished 2005 demo; this is explicitly the later artist album edition of that licensed song, not the identical game master.'),
  ('wGpAb94Vvjs','Even Rats','The Slip',True,'https://www.youtube.com/watch?v=wGpAb94Vvjs',SLIP,{'composer_and_author_as_delivered':'Barr; Friedman; Moore'},'Official Aquarius 2007 Eisenhower album release of the song associated with Guitar Hero. Later studio album edition, not asserted identical to the 2005 game cut; surnames preserved exactly as the label supplies them.')]),
 ('workbook-06-08-green-day-rock-band','Green Day: Rock Band',2010,'Green Day','licensed_playlist',[
  ('AJDiYxKSAqQ','Basket Case','Green Day',True,'https://www.youtube.com/watch?v=AJDiYxKSAqQ',GD,{'songwriters':'Billie Joe Armstrong; Mike Dirnt; Tr\u00e9 Cool','production':'Billie Joe Armstrong; Mike Dirnt; Tr\u00e9 Cool; Rob Cavallo','mixing':'Jerry Finn'},"Original 1994 Reprise performance, officially delivered through the 2017 Greatest Hits: God's Favorite Band album. Full commercial song, not a claim of identical game stems or edit.")]),
 ('wikipedia-26488378','Rock Band 3',2010,'Various artists','licensed_playlist',[
  ('fJ9rUzIMcZQ','Bohemian Rhapsody','Queen',True,QUEEN,RB,{'songwriting':'Freddie Mercury'},'Original 1975 A Night at the Opera performance, official remastered HD music-video publication from Greatest Video Hits 1. Full commercial recording; video remaster disclosed and no identical game-stem claim.'),
  ('NFeUko-lQHg','Break on Through (To the Other Side)','The Doors',True,'https://www.youtube.com/watch?v=NFeUko-lQHg',RB,{'songwriters':'Jim Morrison; John Densmore; Ray Manzarek; Robby Krieger','production':'Paul A. Rothchild','recording_engineer':'Bruce Botnick','mastering_engineer':'Doug Sax'},'Official Rhino/Elektra delivery of the original 1967 album performance. Full commercial recording, not asserted identical to the game stems.')]),
]
entries=[];audits=[]
for eid,game,year,composer,kind,tracks in groups:
 ts=[]
 for vid,title,creator,official,credit,context,roles,version in tracks:
  a=p.watch(vid)
  try:
   c=v.metadata(vid,{'title':a['title'],'channel':a['author']});assert c.get('native_compatible_avc_aac') is True
  except Exception as ex:audits.append({'youtube_id':vid,'status':'CODEC_HOLD','reason':str(ex)});print('HOLD',vid,str(ex),flush=True);continue
  t={'youtube_id':vid,'url':'https://www.youtube.com/watch?v='+vid,'title':title,'creator':creator,'composer_source':credit,'recording_context_source':context,'recording_version':version,'additional_recording_roles':roles,'uploader':a['author'],'channel_url':'https://www.youtube.com/channel/'+a['channelId'],'source_page':'https://www.youtube.com/watch?v='+vid,'official_uploader_verified':official,'publishing_kind':'official_artist_or_label_recording' if official else 'credited_archival_game_recording','duration_seconds':int(a['lengthSeconds']),'verification_receipt':'build/research/soundtrack-broad/watch/'+vid+'.json','native_codec_metadata_receipt':'build/research/video-discovery/video-'+vid+'.json','native_codec_metadata_verified':True,'playback_verified_on_ps5':False,'rights':'Composition and recording rights remain with original composers, writers, performers, publishers and labels; archival uploader credit does not imply official endorsement.'}
  if kind=='licensed_playlist':
   t.update({'music_kind':'licensed_song','recording_artists':[creator],'credit_scope':'Named recording artist; separate authored roles retained without treating performer as universal composer.'})
   t['delivered_music_roles']=[line for line in a.get('shortDescription','').splitlines() if ':' in line and any(term in line.lower().split(':')[0] for term in ['composer','lyricist','writer','author','producer','engineer','vocals','guitar','drums','keyboards'])]
  if eid=='wikipedia-21468511':t['primary_credit_receipt']='build/research/soundtrack-broad/rhythm-priorities/parappa1-composer-public-metadata.json'
  if eid=='workbook-01-23-parappa-the-rapper-2':t['credit_source_scope']='Transcription of original 2001 Toy\u2019s Factory album booklet, with individual track numbers and collaborators; not falsely described as publisher-hosted primary HTML.'
  ts.append(t);audits.append({'entry_id':eid,'youtube_id':vid,'actual_title':a['title'],'actual_uploader':a['author'],'actual_description_read':True,'status':'AWAITING_INDEPENDENT_PEER'});print('CANDIDATE',game,title,vid,flush=True)
 if ts:
  e={'entry_id':eid,'match_title':game,'match_year':year,'title':'Listen to '+game,'composer':composer,'curator_note':('Listen to the licensed music of '+game+'.') if kind=='licensed_playlist' else ('Listen to music by '+composer+' from '+game+'.'),'tracks':ts}
  if kind=='licensed_playlist':e.update({'music_kind':kind,'replace_existing_tracks':True})
  entries.append(e)
out=D/'seven-rhythm-games12-candidate.json';assert not out.exists();p.write(out,{'publication_status':'awaiting_independent_review','entries':entries})
p.write(D/'rhythm-seven-source-receipts.json',receipts);p.write(D/'rhythm-seven-editorial-audit.json',audits)
print('FINAL',len(entries),sum(len(e['tracks']) for e in entries),hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
