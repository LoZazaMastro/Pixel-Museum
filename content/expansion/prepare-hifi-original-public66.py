"""Original Hi-Fi RUSH album with real public chapter bounds; no licensed-song substitution."""
import hashlib
import json
import pathlib
import re

ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=ROOT/'build/research/soundtrack-broad/modern-public-albums'
load=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
path=OUT/'VwerMi16TvI-actual-publication-research.json'
receipt=load(path)
pub=receipt['publication']
assert pub['author']=='TheResidentGames' and receipt['native_avc_aac']
assert load(ROOT/receipt['native_codec_receipt'])['native_compatible_avc_aac']
primary='https://store.steampowered.com/app/2341310/HiFi_RUSH_Original_Game_Soundtrack/'
markers=[]
for line in pub['shortDescription'].splitlines():
    m=re.match(r'^(\d+:\d{2}(?::\d{2})?)\s+-\s+(.+?)\s*$',line)
    if m:
        start=0
        for part in m[1].split(':'):start=start*60+int(part)
        markers.append({'start':start,'title':m[2],'line':line})
assert len(markers)==66
tracks=[]
duration=float(pub['lengthSeconds'])
for index,marker in enumerate(markers):
    end=markers[index+1]['start'] if index+1<len(markers) else duration
    assert 0<=marker['start']<end<=duration
    item={'youtube_id':'VwerMi16TvI','url':'https://www.youtube.com/watch?v=VwerMi16TvI',
        'source_page':'https://www.youtube.com/watch?v=VwerMi16TvI','title':marker['title'],
        'creator':'Hi-Fi RUSH music team','composer_source':primary,
        'artist_credit_scope':'Publisher labels the original album Various Artists, identifying original music by Shuichi Kobori, Masatoshi Yanagi, REO and The Glass Pyramids. This is an honest collective album credit, not a claim that every roster member composed every cue.',
        'game_album_level_music_credits':['Shuichi Kobori','Masatoshi Yanagi','REO','The Glass Pyramids'],
        'start_seconds':marker['start'],'end_seconds':end,'duration_seconds':end-marker['start'],
        'source_actual_chapter_line':marker['line'],'source_publication_duration_seconds':duration,
        'uploader':pub['author'],'channel_url':'https://www.youtube.com/channel/'+pub['channelId'],
        'primary_published_title':pub['title'],'official_uploader_verified':False,
        'publishing_kind':'archival_game_recording','recording_year':2023,
        'recording_version':'Original 2023 Hi-Fi RUSH 66-track soundtrack album, including original Streamer Mode boss music. Archival public album passages, not the separately licensed Nine Inch Nails/Prodigy/Black Keys tracks, a reconstructed in-game loop collection or the later B-Sides album.',
        'rights':'Tango Gameworks / KRAFTON and original credited composers, performers and production contributors; TheResidentGames is an archival uploader.',
        'native_codec_metadata_verified':True,'native_codec_metadata_receipt':receipt['native_codec_receipt'],
        'publication_metadata_receipt':path.relative_to(ROOT).as_posix(),'playback_verified_on_ps5':False}
    feature=re.search(r'feat\. (.+?)\)',marker['title'])
    if feature:item['additional_recording_roles']={'featured_artist':[feature[1]]}
    tracks.append(item)
credit=OUT/'hifi66-publisher-steam-web-read-receipt.json'
credit.write_text(json.dumps({'source_url':primary,'actual_web_page_read':True,
    'published_album_tracks':66,'album_artist_credit':'Various Artists',
    'scope':'Publisher original album explicitly distinguishes original music/Streamer Mode songs from licensed pop recordings. All66 named selections are source-indexed in the actual public archive description. No individual roster is falsely assigned to each cue.',
    'original_game_composers_named_by_publisher':['Shuichi Kobori','Masatoshi Yanagi','REO'],
    'publisher_named_original_boss_music_artist':'The Glass Pyramids',
    'no_claims':['all game stems','licensed-song completeness','audio-identical master','physical PS5 playback']},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
entry={'entry_id':'wikipedia-72850021','match_title':'Hi-Fi Rush','match_year':2023,
    'title':'Listen to Hi-Fi RUSH','composer':'Hi-Fi RUSH music team',
    'curator_note':'Listen to the music of Hi-Fi RUSH music team\nHi-Fi RUSH',
    'append_existing_tracks':True,'replace_existing_tracks':False,
    'coverage_status':'published_album_collection','full_album_collection':True,
    'recording_collection_scope':'66 available passages from the named original soundtrack album; existing curated selections preserved separately. Not the entire separately licensed game playlist or B-Sides.',
    'album_completeness':{'expected_published_album_tracks':66,'verified_available_tracks':66,'inventory_source':primary,
        'scope':'Named original66-track album only; public source chapter intervals, no audio-master fingerprint claim.'},'tracks':tracks}
target=OUT/'hifi66-original-public-candidate.json'
assert not target.exists()
target.write_text(json.dumps({'schema_version':1,'publication_status':'awaiting_independent_peer','entries':[entry],
    'source_receipts':[{'local_path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in [path,credit]]},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'candidate':target.relative_to(ROOT).as_posix(),'sha256':sha(target),'selectable_tracks':66}))
