import hashlib, importlib.util, json, re
from pathlib import Path
R = Path(__file__).resolve().parents[2]
def mod(name, path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=mod('p', R/'content/expansion/soundtrack-broad-pipeline.py')
v=mod('v', R/'tools/discover-museum-videos.py')
D=p.RESEARCH/'simpsons-steamworld-inside-fe';D.mkdir(exist_ok=True)
primary=[
 ('steamworld-artist-album','https://steampoweredgiraffe.bandcamp.com/album/music-from-steamworld-heist',['SteamWorld Heist','Honeybee']),
 ('inside-composer','https://martinstigandersen.com/',['INSIDE']),
 ('fire-emblem-publisher-composer','https://www.nintendo.com/jp/topics/article/5c9bd56d-3e21-11e9-b104-0a6d14145cb1',['金﨑猛','フォドラ']),
 ('fire-emblem-english-single','https://music.apple.com/us/album/the-edge-of-dawn-seasons-of-warfare-single/1488436985',['Buttercup','Nintendo']),
 ('fire-emblem-booklet-credit-transcription','https://downloads.khinsider.com/game-soundtracks/album/fire-emblem-three-houses-original-soundtrack-2021/change_log',['Takeru Kanazaki','Buttercup','Toshiyuki Kusakihara']),
]
receipts=[]
for slug,url,markers in primary:
    try:
        raw=p.fetch(url);assert all(m in raw or m in p.text(raw) for m in markers)
        f=D/(slug+'.html');f.write_text(raw,encoding='utf8');receipts.append({'source_page':url,'local_source':str(f.relative_to(R)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'actual_body_retrieved':True})
    except Exception as ex:
        receipts.append({'source_page':url,'actual_body_retrieved':False,'error':str(ex),'note':'Actual page separately read through web where specified in editorial audit; error body is not evidence.'})
cat=json.loads((R/'content/catalog.json').read_text(encoding='utf8'));cat=cat if isinstance(cat,list) else cat['entries']
add=json.loads((R/'content/expansion/user-requested-game-additions.json').read_text(encoding='utf8'))['entries']
ids={(p.norm(e['title']),e['year']):e['id'] for e in cat+add}
groups=[
 ('The Simpsons: Hit & Run',2003,'Jeff Tymoschuk',[
  ('XVB9AH9uhyk',"Professor Frink's Theme",'Jeff Tymoschuk','https://soundcloud.com/jefftymoschuk/professor-frink',{},False,'Original 2003 game score, credited archival upload; capture hardware not identified. Composer portfolio corroborates authorship of this cue, without asserting its 2021 demo is the final game master.'),
  ('7gXQaDpUhNk',"Monkey See, Monkey D'oh — Dr. Nick",'Jeff Tymoschuk','https://soundcloud.com/jefftymoschuk/dr-nick',{},False,'Original 2003 game score, credited archival upload; capture hardware not identified. Composer portfolio independently identifies the Dr. Nick composition.'),
  ('6EwoEkZM1r4','Halloween Havoc — Kang and Kodos','Jeff Tymoschuk','https://soundcloud.com/jefftymoschuk/kang-kodos',{},False,'Original 2003 game score, credited archival upload; capture hardware not identified. Composer portfolio independently identifies the Kang and Kodos composition.')]),
 ('SteamWorld Heist',2015,'Steam Powered Giraffe',[
  ('xjtRH1Rlk0I','Honeybee (SteamWorld Heist version)','Isabella Bennett; David Michael Bennett','https://www.youtube.com/watch?v=xjtRH1Rlk0I',{'lyrics':'Isabella Bennett','composition_roles_as_published':'Music & Lyrics: Isabella Bennett; Composed by: David Bennett','recording_artist':'Steam Powered Giraffe'},True,'Official 2015 same-game soundtrack version, artist-issued publication. Distinct from the 2012 Two-Cent Show recording.'),
  ('y1RC9rCsj8M','The Stars','David Michael Bennett','https://www.youtube.com/watch?v=y1RC9rCsj8M',{'lyrics':'David Michael Bennett','recording_artist':'Steam Powered Giraffe','additional_vocals':'Isabella Bennett; Samuel Luke'},True,'Official Music from SteamWorld Heist (2015) artist-issued recording. Publication includes spoken passage; no assertion of identical game edit.')]),
 ('Inside',2016,'Martin Stig Andersen',[
  ('OiRhv79qpEI','Shockwave','Martin Stig Andersen','https://soundcloud.com/martin-stig-andersen/shockwave-martin-stig-andersen',{},False,'Original 2016 game soundtrack, archival cue; capture hardware not identified. Composer individually published this same-game composition, independently corroborating the named cue.')]),
 ('Fire Emblem: Three Houses',2019,'Takeru Kanazaki',[
  ('FSXuM2v0YLY','The Edge of Dawn (Seasons of Warfare) — English','Takeru Kanazaki','https://www.nintendo.com/jp/topics/article/5c9bd56d-3e21-11e9-b104-0a6d14145cb1',{'vocals':'Buttercup','lyrics':'Toshiyuki Kusakihara','arrangement':'Takeru Kanazaki','vocal_direction':'Greg Chun'},False,'Official 2019 English Seasons of Warfare full single, archived upload; Nintendo/Intelligent Systems publication, distinct from the ending arrangement or fan covers.')])
]
entries=[];audit=[]
for game,year,composer,rows in groups:
    eid=ids.get((p.norm(game),year))
    if not eid:print('ARTICLE_HOLD',game,flush=True);continue
    tracks=[]
    for vid,title,creator,source,roles,official,version in rows:
        actual=p.watch(vid)
        try:
            codec=v.metadata(vid,{'title':actual['title'],'channel':actual['author']});assert codec.get('native_compatible_avc_aac')
        except Exception as ex:
            audit.append({'youtube_id':vid,'status':'CODEC_HOLD','reason':str(ex)});continue
        t={'youtube_id':vid,'url':'https://www.youtube.com/watch?v='+vid,'title':title,'creator':creator,'composer_source':source,'recording_context_source':source,'recording_version':version,'additional_recording_roles':roles,'uploader':actual['author'],'channel_url':'https://www.youtube.com/channel/'+actual['channelId'],'source_page':'https://www.youtube.com/watch?v='+vid,'official_uploader_verified':official,'publishing_kind':'official_game_recording' if official else 'credited_archival_game_recording','duration_seconds':int(actual['lengthSeconds']),'verification_receipt':'build/research/soundtrack-broad/watch/'+vid+'.json','native_codec_metadata_receipt':'build/research/video-discovery/video-'+vid+'.json','native_codec_metadata_verified':True,'playback_verified_on_ps5':False,'rights':'Composition and recording rights remain with the game publishers, composers, performers and original labels. Archival upload credit does not imply official endorsement.'}
        if game.startswith('The Simpsons'):
            slug={'XVB9AH9uhyk':'professor-frink','7gXQaDpUhNk':'dr-nick','6EwoEkZM1r4':'kang-kodos'}[vid]
            t['primary_credit_receipt']='build/research/soundtrack-broad/final-user-score-priorities/primary/simpsons-'+slug+'-public-metadata.json'
            t['cue_identity_context_source']='https://forum.donutteam.com/topic/211-list-of-composers'
            t['credit_scope']='Individual cue composer established by his own portfolio; the archive uploader full-game roster is not assigned to this cue.'
        if game=='SteamWorld Heist':t['publisher_album_context_source']='https://steampoweredgiraffe.bandcamp.com/album/music-from-steamworld-heist'
        if game.startswith('Fire Emblem'):
            t['performer_source']='https://music.apple.com/us/album/the-edge-of-dawn-seasons-of-warfare-single/1488436985'
            t['additional_role_credit_source']='https://downloads.khinsider.com/game-soundtracks/album/fire-emblem-three-houses-original-soundtrack-2021/change_log'
        tracks.append(t);audit.append({'youtube_id':vid,'status':'CANDIDATE_PENDING_PEER','game':game,'actual_title':actual['title'],'actual_description_read':True});print(game,title,'AVC_AAC',flush=True)
    if tracks:entries.append({'entry_id':eid,'match_title':game,'match_year':year,'title':'Listen to '+game,'composer':composer,'curator_note':'Listen to music by '+composer+' from '+game+'.','tracks':tracks})
f=D/'four-games7-candidate.json';f.write_text(json.dumps({'publication_status':'awaiting_independent_review','entries':entries},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(D/'source-receipts.json').write_text(json.dumps(receipts,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(D/'editorial-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('FINAL',len(entries),sum(len(e['tracks']) for e in entries),hashlib.sha256(f.read_bytes()).hexdigest(),flush=True)
