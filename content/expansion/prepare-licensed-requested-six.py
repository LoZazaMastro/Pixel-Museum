"""Curated research checkpoint, exact licensed works with visible publication versions."""
import json,re,hashlib,importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2];B=R/'build/research/soundtrack-broad';D=B/'licensed-requested-six'
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=module('p',R/'content/expansion/soundtrack-broad-pipeline.py');v=module('v',R/'tools/discover-museum-videos.py')
catalog=json.loads((R/'content/catalog.json').read_text(encoding='utf-8'));catalog=catalog if isinstance(catalog,list) else catalog['entries']
add=json.loads((R/'content/expansion/user-requested-game-additions.json').read_text(encoding='utf-8'))['entries'];ids={(p.norm(e['title']),e['year']):e['id'] for e in catalog+add}
requests=json.loads((D/'requested-tracklists.json').read_text(encoding='utf-8'))['entries'];associations={e['game']:e for e in requests}
associations['The Warriors']['source_page']='https://media-rockstargames-com.akamaized.net/rockstargames-newsite/img/manuals/en_us/TheWarriors-PS2-Manual.pdf'
associations['The Warriors']['source_kind']='Actual original Rockstar PS2 manual, printed49–51, explicitly credits these film recordings as licensed game music.'
associations['Need for Speed: Hot Pursuit 2']['source_page']='https://oldgamesdownload.com/wp-content/uploads/manuals/need-for-speed-hot-pursuit-2_gamecube_manual_en_nm2.pdf'
associations['Need for Speed: Hot Pursuit 2']['source_kind']='Actual original EA GameCube manual, PDF page8 / printed13, visually read licensed song and songwriter credits.'
associations['Burnout Paradise']['source_page']='https://www.psu.com/news/ea-announces-burnout-paradise-soundtrack/'
associations['Burnout Paradise']['source_kind']='Contemporary report of the EA announcement, December18,2007; exact original-game licensed song list.'
source_receipts=[]
for game in ['Burnout Paradise']:
 url=associations[game]['source_page'];f=D/p.norm(game)/'contemporary-ea-announcement.html'
 try:
  raw=f.read_text(encoding='utf-8') if f.exists() else p.fetch(url)
  assert 'Paradise City' in raw and 'Stand And Deliver' in raw and 'Seether' in raw
  f.write_text(raw,encoding='utf-8');source_receipts.append({'game':game,'source_page':url,'source_kind':associations[game]['source_kind'],'local_source':str(f.relative_to(R)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'actual_body_reviewed':True})
 except Exception as ex:source_receipts.append({'game':game,'error':str(ex),'actual_body_reviewed':False})
groups=[('Need for Speed: Underground',2003,[
 ('ZN43UoyAbwg','Get Low','Lil Jon & The East Side Boyz featuring Ying Yang Twins','Official original Kings of Crunk commercial album recording; longer than the edited game version.'),
 ('-EPRhDvaUnA','Out of Control','Rancid','Official Epitaph original Indestructible album track (2003).'),
 ('UYyc6UNFzfk','Two-Lane Blacktop','Rob Zombie','Official Geffen 2009 digital publication of the 2003 Past, Present & Future recording.'),
 ('vMCbJB4yNXo','The Only','Static-X','Official Warner music-video version of the 2003 Shadow Zone song.'),
 ('aC_wkSvTLpM','And the Hero Will Drown','Story of the Year','Official Maverick original 2003 Page Avenue album recording.'),
 ('E1u9u7mq9Ck',"24's",'T.I.','Original artist-issued official music video; commercial video edit of the 2003 song.')]),
 ('Need for Speed: Most Wanted',2005,[
 ('kRrOq4NipQQ','Shapeshifter','Celldweller featuring Styles of Beyond','Official artist-issued 2013 tenth-anniversary album publication of the licensed song; not claimed identical to the edited game master.'),
 ('-daTpfB-7K4','Decadence','Disturbed','Official artist-issued original Ten Thousand Fists album audio (2005).'),
 ('TYgxM_suaUw','Blinded in Chains','Avenged Sevenfold','Official Warner original 2005 City of Evil album recording; full-length commercial version.'),
 ('o6QDNLsrr5Y','Hand of Blood','Bullet for My Valentine','Official artist-issued Hand of Blood audio; current EP reissue publication with anniversary context, not an unverified original game master claim.'),
 ('labytsb3gfI','Blood and Thunder','Mastodon','Official Relapse music-video version of the original Leviathan song (2004).'),
 ('wFAA0_Acvqw',"You'll Be Under My Wheels",'The Prodigy','Official XL original 2004 Always Outnumbered, Never Outgunned album recording; not Under My Wheels (Remix).'),
 ('nhZ2_gl1GnQ','Feels Just Like It Should — Timo Maas Remix','Jamiroquai','Official artist-issued full Timo Maas remix; longer commercial remix, not the shortened game edit.')]),
 ('Burnout Paradise',2008,[
 ('Rbm6GXllBiw','Paradise City',"Guns N' Roses",'Official artist-issued music video of the original Appetite for Destruction song; remastered-album marketing retained in source, no unchanged game-master claim.'),
 ('qcHg7wCi6yI','Girlfriend — Radio Edit','Avril Lavigne','Official Sony/RCA 2007 single radio edit.'),
 ('EiZR4xyFK6Q','Would?','Alice in Chains','Official Sony/Columbia 1992 original recording, published on the Singles soundtrack; same licensed song independently identified in original game credits.'),
 ('AkMZ6fV3T_0','Too Much, Too Young, Too Fast','Airbourne','Official artist-issued music-video version of the 2007 Runnin\' Wild song.'),
 ('Kho7UvF9eJA','Fake It','Seether','Official artist-issued original Finding Beauty in Negative Spaces album audio (2007).'),
 ('WkqPVMKsN20','Epic','Faith No More','Official Rhino/Slash compilation publication of the original 1989 recording.'),
 ('tyHpTG1MjVU','I Wanna Rock — 2016 Remaster','Twisted Sister','Official 2016 Rhino remaster of the original 1984 Atlantic recording; not the 2008 re-recording.'),
 ('KxCxbtGWmAo','Stand and Deliver','Adam and the Ants','Official Sony 2006 compilation publication of the original 1981 recording.')]),
 ('FIFA Street',2005,[
 ('yQodCcbG6Qg','Stand Up Tall','Dizzee Rascal','Official XL original 2004 Showtime album recording; no later remix.'),
 ('am5Zot3aew8','Jin Go Lo Ba','Fatboy Slim','Official Tommy Boy soundtrack compilation publication of the 2004 Skint recording; not the Jon Carter remix.'),
 ('M6vgWFsKpdw','On a Ragga Tip — Original Remastered','SL2','Official Universal/Label Worx 2015 Original Remastered EP publication of the 1992 song; later mastering explicitly identified.'),
 ('ICOW-ts0778','Happy — Fatboy Slim Remix','Max Sedgley','Official Irma 2010 compilation publication of the exact licensed Fatboy Slim remix; full commercial version rather than shortened game edit.'),
 ('kN2uCPq0SYc','Rudebwoy','DJ Marky & XRS','Official Innerground original 2004 single mix; full commercial version.'),
 ('vJLZ8wQTkpA','Slam','Artificial Intelligence','Credited archival original FIFA Street (2005) game soundtrack recording; capture hardware not identified.')]),
 ('Need for Speed: Hot Pursuit 2',2002,[
 ('XDD-yGgKARw','Ordinary','The Buzzhorn','Official Atlantic original 2002 single recording.'),
 ('LqM5p4v1UqY','Wall of Shame','Course of Nature','Official Lava/Atlantic original 2002 Superkala recording.'),
 ('Ixqm8zeMD6w','The People That We Love','Bush','Official artist-issued video version of the Golden State song licensed in the 2002 game.'),
 ('gbBKXdMqo7w','One Little Victory','Rush','Credited archival original Hot Pursuit 2 licensed-song recording; not the later Vapor Trails Remixed album.'),
 ('GZ_iTzj5Z3k',"Keep It Comin'",'Uncle Kracker','Official Lava original 2002 No Stranger to Shame album recording.')]),
 ('The Warriors',2005,[
 ('rGFXiaaxIYc','Theme from The Warriors','Barry De Vorzon','Official Universal 2005 digital album publication of the original 1979 film recording, explicitly licensed in Rockstar\'s 2005 PS2 game.'),
 ('e5n7DeqNHFY','Baseball Furies Chase','Barry De Vorzon','Official Universal 2005 digital album publication of the original 1979 film recording, explicitly licensed in the 2005 PS2 game.'),
 ('jB9B1uNxwuY','In the City','Joe Walsh','Official Universal 2005 digital publication of Joe Walsh\'s original film recording, licensed by the PS2 game; not the Eagles re-recording.'),
 ('Auq-LJDAx-0','Nowhere to Run','Arnold McCuller','Official Universal 2005 digital publication of the original 1979 film recording licensed by the PS2 game; not Martha and the Vandellas.'),
 ('FC0iciE1Cb4','Love Is a Fire','Genya Ravan','Official Universal 2005 digital publication of the original 1979 film recording, explicitly licensed in the PS2 game.'),
 ('RpgIa4HkgeY','Last of an Ancient Breed','Desmond Child','Official Universal 2005 digital publication of the original 1979 film recording, explicitly licensed in the PS2 game.'),
 ('oLS57N4kUN0','Knock on Wood — 7-inch Edit','Amii Stewart','Official Sanctuary 2016 Anthology publication of the original Amii Stewart recording; commercial 7-inch edit, not Eddie Floyd\'s original performance.')])]
entries=[];audit=[]
for game,year,rows in groups:
 eid=ids.get((p.norm(game),year));a=associations[game]
 if not eid:print('ARTICLE_HOLD',game,flush=True);continue
 tracks=[]
 for vid,title,artist,version in rows:
  actual=p.watch(vid);q={'game':game,'youtube_id':vid,'title':title,'creator':artist,'recording_version':version,'actual_title':actual['title'],'actual_uploader':actual['author']}
  try:codec=v.metadata(vid,{'title':actual['title'],'channel':actual['author']});assert codec.get('native_compatible_avc_aac')
  except Exception as ex:q.update(status='CODEC_HOLD',reason=str(ex));audit.append(q);continue
  archive=vid in {'vJLZ8wQTkpA','gbBKXdMqo7w'}
  rolelines=[line.strip() for line in actual.get('shortDescription','').splitlines() if re.match(r'[^:]{1,230}:\s*\S',line) and re.search(r'composer|writer|lyricist|arrang|vocals|producer|performer|remix',line.partition(':')[0],re.I)]
  t={'youtube_id':vid,'url':'https://www.youtube.com/watch?v='+vid,'title':title,'creator':artist,
     'composer_source':a['source_page'],'recording_context_source':a['source_page'],'game_association_source_kind':a['source_kind'],
     'recording_version':version,'uploader':actual['author'],'channel_url':'https://www.youtube.com/channel/'+actual['channelId'],
     'source_page':'https://www.youtube.com/watch?v='+vid,'official_uploader_verified':not archive,
     'publishing_kind':'credited_archival_licensed_recording' if archive else 'official_licensed_song_recording',
     'music_kind':'licensed_playlist','credit_scope':'Recording artist displayed; composers, songwriters and technical roles remain individually attributed in publication credits.',
     'delivered_music_roles':rolelines,'duration_seconds':int(actual['lengthSeconds']),
     'rights':'Composition and recording rights remain with the named songwriters, recording artists, original labels and relevant rights owners.',
     'verification_receipt':'build/research/soundtrack-broad/watch/'+vid+'.json',
     'native_codec_metadata_receipt':'build/research/video-discovery/video-'+vid+'.json','native_codec_metadata_verified':True,'playback_verified_on_ps5':False}
  if vid=='tyHpTG1MjVU':t['recording_release_year']=2016
  if vid=='M6vgWFsKpdw':t['recording_release_year']=2015
  if vid in {'rGFXiaaxIYc','e5n7DeqNHFY','jB9B1uNxwuY','Auq-LJDAx-0','FC0iciE1Cb4','RpgIa4HkgeY'}:t['recording_release_year']=2005
  tracks.append(t);q['status']='CANDIDATE_PENDING_INDEPENDENT_REVIEW';audit.append(q);print(game,title,'AVC_AAC',flush=True)
 if tracks:entries.append({'entry_id':eid,'match_title':game,'match_year':year,'title':'Listen to '+game,'composer':'Various artists','curator_note':'Listen to the music of '+game+'.','music_kind':'licensed_playlist','replace_existing_tracks':True,'tracks':tracks})
 (D/'curated-six-editorial-review.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
f=D/'licensed-six-games39-candidate.json';f.write_text(json.dumps({'publication_status':'awaiting_independent_exact_recording_review','entries':entries},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(D/'additional-source-receipts.json').write_text(json.dumps(source_receipts,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('FINAL',len(entries),sum(len(e['tracks']) for e in entries),hashlib.sha256(f.read_bytes()).hexdigest(),flush=True)
