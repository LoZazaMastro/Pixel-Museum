"""Available original HAL album archive, honest collective credits and identity-only receipts."""
import hashlib
import json
import pathlib
import re

ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=ROOT/'build/research/soundtrack-broad/modern-public-albums'
load=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
research_path=OUT/'kirbystarallies-available-publication-research.json'
research=load(research_path)
assert len(research['tracks'])==233
primary='https://www.hallab.co.jp/products/201801/'
tracks=[]
holds=[]
for row in sorted(research['tracks'],key=lambda r:r['source_playlist_position']):
    if row['status']!='metadata_candidate':
        holds.append({'youtube_id':row['source']['id'],'title':row['source']['title'],'reason':row.get('error') or 'Original public metadata identity unresolved; not an absence-of-music finding.'})
        continue
    pub=row['publication']
    assert pub['author'] in ['Eternal','KIRBY CHANNEL']
    assert pub['title']==row['source']['title']
    assert row['native_compatible_avc_aac'] and load(ROOT/row['native_codec_receipt'])['native_compatible_avc_aac']
    assert float(pub['lengthSeconds'])>0 and abs(float(pub['lengthSeconds'])-float(row['source']['duration']))<=3
    title=re.sub(r'^\d+[ -]+\d+\.?\s*','',pub['title'])
    title=re.sub(r'\s*[-–—]?\s*KIRBY STAR ALLIES\s*:?\s*THE ORIGINAL SOUNDTRACK\s*$','',title,flags=re.I).strip()
    video_id=row['source']['id']
    tracks.append({'youtube_id':video_id,'url':'https://www.youtube.com/watch?v='+video_id,
        'source_page':'https://www.youtube.com/watch?v='+video_id,'title':title,
        'creator':'HAL Laboratory sound team','composer_source':primary,
        'artist_credit_scope':'Primary HAL staff roundtable and album context support a collective HAL music credit. Individual cue authorship is not separately inferred from the original game staff roster or a missing source description.',
        'album_level_music_staff':{'lead_sound':['Hirokazu Ando'],'sound':['Jun Ishikawa','Yuuta Ogasawara']},
        'source_description_present':bool(pub.get('shortDescription')),
        'publication_evidence_scope':'Actual public Android title, uploader, channelId and duration, matched to the independently acquired public album playlist. Description is empty unless source_description_present is true; no description or per-cue role lines invented.',
        'duration_seconds':float(pub['lengthSeconds']),'source_playlist_position':row['source_playlist_position'],
        'uploader':pub['author'],'channel_url':'https://www.youtube.com/channel/'+pub['channelId'],
        'primary_published_title':pub['title'],'official_uploader_verified':False,
        'publishing_kind':'archival_game_recording','recording_year':2019,
        'recording_version':'Original Kirby Star Allies 2019 six-disc soundtrack for the 2018 Switch game and its official free updates through version4.0.0. Archive English titles retained as uploader titles, not asserted as official translated CD text. Not the separate eight-track Kirby Arrange Selection bonus player.',
        'rights':'2018–2019 HAL Laboratory, Inc. / Nintendo and credited original composers, arrangers and recording contributors; Eternal and KIRBY CHANNEL are archival uploaders, not verified publisher channels.',
        'native_codec_metadata_verified':True,'native_codec_metadata_receipt':row['native_codec_receipt'],
        'publication_metadata_receipt':(OUT/'kirbystarallies-public-individuals'/(video_id+'.json')).relative_to(ROOT).as_posix(),
        'playback_verified_on_ps5':False})
assert len(tracks)==226 and len(holds)==7
credit=OUT/'kirbystarallies226-primary-context-receipt.json'
credit.write_text(json.dumps({'actual_web_pages_read':[
    {'url':primary,'context':'HAL original233-track six-disc album and official update scope. Actual primary staff discussion identifies lead Ando, Ishikawa and Ogasawara sound work without assigning every cue to everyone.'},
    {'url':'https://www.hallab.co.jp/works/detail/003262/','context':'HAL original product,2019-02-14 and2018–2019 rights. Separate eight-track bonus player is not merged into the six-disc game album.'}],
    'available_tracks':226,'actual_public_android_identity_without_description':sum(not t['source_description_present'] for t in tracks),
    'actual_public_android_identity_with_description':sum(t['source_description_present'] for t in tracks),
    'oembed_fallbacks':0,'held_tracks':7,
    'scope':'Available archived album recordings with actual public identity and native metadata. No listening/fingerprinting or physicalPS5 assertion; absent descriptions remain empty.'},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
sources=[research_path,credit,OUT/'kirbystarallies-hal-primary.html']
entry={'entry_id':'workbook-03-16-kirby-star-allies','match_title':'Kirby Star Allies','match_year':2018,
    'title':'Listen to Kirby Star Allies','composer':'HAL Laboratory sound team',
    'curator_note':'Listen to the music of HAL Laboratory sound team\nKirby Star Allies',
    'replace_existing_tracks':True,'full_album_collection':False,'coverage_status':'partial',
    'recording_collection_scope':'226 available archival original-album recordings; seven public metadata/native cases remain held. Includes official free-update material present in the233-track HAL album; no claim of complete233 coverage or audio-identical CD masters.',
    'album_completeness':{'expected_published_album_tracks':233,'verified_available_tracks':226,'held_source_tracks':7,
        'inventory_source':primary,'scope':'Original six-disc HAL album availability, not the separate bonus Arrange Selection player.'},'tracks':tracks}
target=OUT/'kirbystarallies226-available-public-candidate.json'
assert not target.exists()
target.write_text(json.dumps({'schema_version':1,'publication_status':'awaiting_independent_peer','entries':[entry],
    'held_source_tracks':holds,'source_receipts':[{'local_path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in sources]},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'candidate':target.relative_to(ROOT).as_posix(),'sha256':sha(target),'selectable_tracks':226}))
