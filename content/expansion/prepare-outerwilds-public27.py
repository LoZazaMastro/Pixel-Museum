"""Available original artist album recordings; retain one native failure honestly."""
import hashlib
import json
import pathlib

ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=ROOT/'build/research/soundtrack-broad/modern-public-albums'
load=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
research_path=OUT/'outerwilds-available-publication-research.json'
research=load(research_path)
primary='https://store.steampowered.com/app/1286760/Outer_Wilds__Original_Soundtrack/'
tracks=[]
held=[]
for row in sorted(research['tracks'],key=lambda r:r['source_playlist_position']):
    if row['status']!='metadata_candidate':
        held.append({'youtube_id':row['source']['id'],'title':row['source']['title'],'reason':row.get('error','Public metadata unresolved')})
        continue
    pub=row['publication']
    assert pub['author']=='Andrew Prahlow - Topic'
    assert 'Outer Wilds (Original Soundtrack)' in pub['shortDescription'] and '2019 Annapurna Interactive' in pub['shortDescription']
    assert row['native_compatible_avc_aac'] and load(ROOT/row['native_codec_receipt'])['native_compatible_avc_aac']
    assert abs(float(pub['lengthSeconds'])-float(row['source']['duration']))<=3
    video_id=row['source']['id']
    tracks.append({'youtube_id':video_id,'url':'https://www.youtube.com/watch?v='+video_id,
        'source_page':'https://www.youtube.com/watch?v='+video_id,'title':pub['title'],
        'creator':'Andrew Prahlow','composer_source':primary,
        'artist_credit_scope':'Original publisher album credits Andrew Prahlow; actual artist delivery names the same original2019 Annapurna album, not a cover, live performance, Echoes of the Eye or Lost Reels release.',
        'uploader':pub['author'],'channel_url':'https://www.youtube.com/channel/'+pub['channelId'],
        'primary_published_title':pub['title'],'official_uploader_verified':True,
        'publishing_kind':'official_game_recording','recording_year':2019,
        'recording_version':'Original2019 Outer Wilds soundtrack album publication. Trailer-named bonus selections are part of the original publisher album; no later live rearrangement or DLC score substituted.',
        'rights':'2019 Annapurna Interactive / Andrew Prahlow and credited recording contributors.',
        'duration_seconds':float(pub['lengthSeconds']),'native_codec_metadata_verified':True,
        'native_codec_metadata_receipt':row['native_codec_receipt'],
        'publication_metadata_receipt':(OUT/'outerwilds-public-individuals'/(video_id+'.json')).relative_to(ROOT).as_posix(),
        'playback_verified_on_ps5':False})
assert len(tracks)==27 and len(held)==1
credit_path=OUT/'outerwilds-original-publisher-web-read-receipt.json'
credit_path.write_text(json.dumps({'source_url':primary,'actual_web_page_read':True,
    'published_tracks':28,'publisher':'Annapurna Interactive','original_artist':'Andrew Prahlow',
    'available_tracks':27,'held_selection':'Let There Be Light',
    'scope':'Actual publisher album inventory and original artist digital delivery identity. One existing native login failure retained; no retry, media download, fingerprinting or physical PS5 claim.'},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
entry={'entry_id':'wikipedia-45641123','match_title':'Outer Wilds','match_year':2019,
    'title':'Listen to Outer Wilds','composer':'Andrew Prahlow',
    'curator_note':'Listen to the music of Andrew Prahlow\nOuter Wilds','replace_existing_tracks':True,
    'full_album_collection':False,'coverage_status':'partial',
    'recording_collection_scope':'27 available original artist album recordings; one native-unresolved selection retained as a hold, not declared absent from the score.',
    'album_completeness':{'expected_published_album_tracks':28,'verified_available_tracks':27,
        'inventory_source':primary,'held_selections':['Let There Be Light']},'tracks':tracks}
target=OUT/'outerwilds27-available-public-candidate.json'
assert not target.exists()
target.write_text(json.dumps({'schema_version':1,'publication_status':'awaiting_independent_peer','entries':[entry],
    'held_source_recordings':held,'source_receipts':[{'local_path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in [research_path,credit_path]]},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'candidate':target.relative_to(ROOT).as_posix(),'sha256':sha(target),'selectable_tracks':27}))
