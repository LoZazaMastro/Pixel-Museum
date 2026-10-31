"""Available Switch-family archive passages and franchise suites, without full-score claims."""
import hashlib
import json
import pathlib
import re

ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=ROOT/'build/research/soundtrack-broad/modern-public-albums'
load=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
profiles=[
    ('4iZf3qaJBAo','wikipedia-54294075','Metroid Prime 4: Beyond',2025,'Nintendo sound team',47,
     'https://www.ndw.jp/metroidprime-interview-260211/'),
    ('AI7LaeFPcS0','wikipedia-57665928','Super Smash Bros. Ultimate',2018,'Various artists',30,
     'https://www.smashbros.com/en_US/sound/index.html')]
entries=[]
holds=[]
source_paths=[]
for video_id,entry_id,name,year,composer,expected,primary in profiles:
    path=OUT/(video_id+'-actual-publication-research.json')
    receipt=load(path)
    pub=receipt['publication']
    assert receipt['native_avc_aac'] and load(ROOT/receipt['native_codec_receipt'])['native_compatible_avc_aac']
    duration=float(pub['lengthSeconds'])
    markers=[]
    for line in pub['shortDescription'].splitlines():
        m=re.match(r'^(\d+:\d{2}(?::\d{2})?)\s+(.+?)\s*$',line)
        if not m:continue
        start=0
        for part in m[1].split(':'):start=start*60+int(part)
        markers.append({'title':m[2],'start':start,'line':line})
    tracks=[]
    for index,marker in enumerate(markers):
        end=markers[index+1]['start'] if index+1<len(markers) else duration
        assert 0<=marker['start']<end<=duration
        if name=='Super Smash Bros. Ultimate' and marker['title']=='Kingdom Hearts':
            holds.append({'game':name,'title':marker['title'],'actual_source_line':marker['line'],
                'actual_remaining_source_seconds':end-marker['start'],
                'reason':'Last source marker leaves only9seconds, insufficient for the named franchise suite. Held without inventing an ending or treating it as a complete theme.'})
            continue
        title=marker['title'] if name=='Metroid Prime 4: Beyond' else marker['title']+' — arrangement suite'
        creator=composer if name=='Metroid Prime 4: Beyond' else 'Nintendo and partner music artists'
        scope='First-person Nintendo music developer interview distinguishes Nintendo composition from Retro Studios sound effects/voices. Honest collective score credit; no inference that every individual cue is by the entire staff roster.' if name=='Metroid Prime 4: Beyond' else 'Official Nintendo music site documents the large original arrangement collaboration, including external composers/arrangers and original rightsholders. These long source sections contain multiple pieces; no sole Nintendo authorship or individual cue composition inferred.'
        version='Original 2025 Metroid Prime 4: Beyond game music, public archive selection. Source game labels and real chapter intervals retained; not a fan remaster, full Nintendo Music album inventory or certified identical hardware capture.' if name=='Metroid Prime 4: Beyond' else 'Super Smash Bros. Ultimate official in-game arrangements, available archival franchise suite from the original 2018 game and official 2019–2021 DLC. A multi-piece suite, not an individual track or the complete 37-hour inherited music library. No fan-arrangement claim.'
        item={'youtube_id':video_id,'url':'https://www.youtube.com/watch?v='+video_id,
            'source_page':'https://www.youtube.com/watch?v='+video_id,'title':title,'creator':creator,
            'composer_source':primary,'artist_credit_scope':scope,
            'start_seconds':marker['start'],'end_seconds':end,'duration_seconds':end-marker['start'],
            'source_actual_chapter_line':marker['line'],'source_publication_duration_seconds':duration,
            'uploader':pub['author'],'channel_url':'https://www.youtube.com/channel/'+pub['channelId'],
            'primary_published_title':pub['title'],'official_uploader_verified':False,
            'publishing_kind':'archival_game_recording','recording_version':version,
            'recording_platform':'Capture hardware not identified',
            'rights':'Nintendo and original credited composers, arrangers, performers and recording rightsholders; '+pub['author']+' is an archival uploader, not an official publisher.',
            'native_codec_metadata_verified':True,'native_codec_metadata_receipt':receipt['native_codec_receipt'],
            'publication_metadata_receipt':path.relative_to(ROOT).as_posix(),'playback_verified_on_ps5':False}
        if name=='Metroid Prime 4: Beyond':item['recording_year']=2025
        else:item['recording_collection_year_range']=[2018,2021]
        tracks.append(item)
    assert len(tracks)==expected,(name,len(tracks))
    entries.append({'entry_id':entry_id,'match_title':name,'match_year':year,'title':'Listen to '+name,
        'composer':composer,'curator_note':'Listen to the music of '+composer+'\n'+name,
        'replace_existing_tracks':True,'coverage_status':'partial','full_album_collection':False,
        'recording_collection_scope':('47 available source-indexed original-game selections; no complete album/game master inventory claimed.' if name=='Metroid Prime 4: Beyond' else '30 available franchise suites of new in-game arrangements, not30individual songs or the entire inherited soundtrack. Final KingdomHearts9-second marker held.'),
        'album_completeness':{'verified_available_source_selections':expected,'inventory_source':primary,
            'scope':'Available public archive selection only. Suites are explicitly distinguished from individually selectable original songs.'},'tracks':tracks})
    source_paths.append(path)
primary_path=OUT/'switch-prime-smash-primary-web-read-receipt.json'
primary_path.write_text(json.dumps({'actual_web_pages_read':[
    {'url':profiles[0][-1],'source_type':'First-person interview with Nintendo music developer Kenji Yamamoto','context':'Music composition is done at Nintendo; Retro handles sound effects and voices. Not a claim that every cue is solely Yamamoto.'},
    {'url':profiles[1][-1],'source_type':'Official Nintendo game music site','context':'Names original arrangement contributors from Nintendo and many external composers/studios; not a Nintendo-exclusive individual authorship claim.'}],
    'additional_primary_public_excerpt':{'url':'https://www.nintendo.com/us/whatsnew/metroid-prime-4-beyond-tracks-added-to-nintendo-music/','context':'Nintendo documents a special selection of MetroidPrime4 music, not proof that archival47 equals a complete official album.'},
    'scope':'Actual public source markers and native metadata availability, not listening/fingerprinting or physicalPS5 playback. Smash final9-second tail remains excluded.'},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
source_paths.append(primary_path)
target=OUT/'switch-prime-smash77-readable-public-candidate.json'
assert not target.exists()
target.write_text(json.dumps({'schema_version':1,'publication_status':'awaiting_independent_peer','entries':entries,
    'held_source_records':holds,'source_receipts':[{'local_path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in source_paths]},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'candidate':target.relative_to(ROOT).as_posix(),'sha256':sha(target),'tracks_per_game':[len(e['tracks']) for e in entries]}))
