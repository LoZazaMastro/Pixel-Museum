"""Available original publisher album recordings, explicit composition/arrangement roles."""
import hashlib
import json
import pathlib
import re

ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=ROOT/'build/research/soundtrack-broad/modern-public-albums'
load=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
research_path=OUT/'ff16-available-publication-research.json'
research=load(research_path)
assert len(research['tracks'])==181
primary='https://www.jp.square-enix.com/music/en/lineup/item/SQEX-11039-45.html'
tracks=[]
held=[]
for row in sorted(research['tracks'],key=lambda r:r['source_playlist_position']):
    if row['status']!='metadata_candidate':
        held.append({'youtube_id':row['source']['id'],'title':row['source']['title'],'reason':row.get('error','Public identity unresolved')})
        continue
    pub=row['publication']
    assert pub['author']=='SQUARE ENIX MUSIC Channel'
    assert 'FINAL FANTASY XVI Original Soundtrack' in pub['title']
    assert '2023 SQUARE ENIX CO., LTD.' in pub['shortDescription']
    assert row['native_compatible_avc_aac'] and load(ROOT/row['native_codec_receipt'])['native_compatible_avc_aac']
    assert float(pub['lengthSeconds'])>0 and abs(float(pub['lengthSeconds'])-float(row['source']['duration']))<=3
    roles={}
    for role,key in [('Composer','composition'),('Arranger','arrangement')]:
        m=re.search('^'+role+r'[:\uff1a]\s*([^\n]+)',pub['shortDescription'],re.M)
        assert m and m[1].strip(),(row['source']['id'],role)
        roles[key]=list(dict.fromkeys(s.strip() for s in m[1].split('/') if s.strip()))
    video_id=row['source']['id']
    title=re.split(r'\s*\(FINAL FANTASY XVI Original Soundtrack\)',pub['title'])[0].strip()
    # One publisher title omits the closing parenthesis; trim only its exact album suffix.
    title=re.split(r'\s*\(FINAL FANTASY XVI Original Soundtrack',title)[0].strip()
    tracks.append({'youtube_id':video_id,'url':'https://www.youtube.com/watch?v='+video_id,
        'source_page':'https://www.youtube.com/watch?v='+video_id,'title':title,
        'creator':', '.join(roles['composition']),'composer_source':'https://www.youtube.com/watch?v='+video_id,
        'artist_credit_scope':'Exact original publisher Composer and Arranger fields preserved separately for this recording. Album roster is not assigned to every cue; no unlabeled producer/performer inferred as composer.',
        'additional_recording_roles':{'arrangement':roles['arrangement']},
        'publisher_music_role_lines':[s for s in pub['shortDescription'].splitlines() if re.match(r'^(Composer|Arranger)[:\uff1a]',s)],
        'duration_seconds':float(pub['lengthSeconds']),'source_playlist_position':row['source_playlist_position'],
        'uploader':pub['author'],'channel_url':'https://www.youtube.com/channel/'+pub['channelId'],
        'primary_published_title':pub['title'],'official_uploader_verified':True,
        'publishing_kind':'official_game_recording','recording_year':2023,
        'recording_version':'Original 2023 FINAL FANTASY XVI standard 181-track album recording, published directly by SQUARE ENIX MUSIC. Not the Ultimate bonus disc, From Spire to Sea DLC album or a fan arrangement. Moongazing is a separately released theme not included in this standard album.',
        'rights':'2023 SQUARE ENIX CO., LTD. and credited original music authors, arrangers, performers and recording contributors.',
        'native_codec_metadata_verified':True,'native_codec_metadata_receipt':row['native_codec_receipt'],
        'publication_metadata_receipt':(OUT/'ff16-public-individuals'/(video_id+'.json')).relative_to(ROOT).as_posix(),
        'playback_verified_on_ps5':False})
assert len(tracks)==179 and len(held)==2
credit_path=OUT/'ff16-publisher-primary-web-read-receipt.json'
credit_path.write_text(json.dumps({'actual_web_pages_read':[
    {'url':primary,'context':'Original SquareEnix standard seven-disc album,2023-07-19; original tracklist. Explicitly excludes the separately released KenshiYonezu theme.'},
    {'url':'https://www.jp.square-enix.com/music/sem/page/FFXVI/ost/en/','context':'Publisher distinguishes standard album, Ultimatebonusdisc and later18-trackDLC album. None silently merged or relabeled.'}],
    'scope':'181 original publisher playlist records,179 available nativeAVC/AAC publications; two existing login failures held without retry. Explicit per-publication Composer/Arranger fields, no all-game or audio-fingerprint claim.',
    'separate_vocal_attempt':{'youtube_id':'NEnuVWbXhJg','native_receipt':'build/research/video-discovery/video-NEnuVWbXhJg.json','status':'held_unavailable_without_retry','not_in_standard_album':True}},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
entry={'entry_id':'wikipedia-26382718','match_title':'Final Fantasy XVI','match_year':2023,
    'title':'Listen to Final Fantasy XVI','composer':'Square Enix music team',
    'curator_note':'Listen to the music of Square Enix music team\nFinal Fantasy XVI',
    'replace_existing_tracks':True,'full_album_collection':False,'coverage_status':'partial',
    'recording_collection_scope':'179 available direct-publisher original standard-album recordings; two native-unresolved publications held. Named181-track album only, not every game stem, Ultimatebonusdisc, DLC or separately released vocal theme.',
    'album_completeness':{'expected_published_album_tracks':181,'verified_available_tracks':179,
        'held_source_recordings':2,'inventory_source':primary,'scope':'Original standard album availability, not all game soundtrack editions.'},'tracks':tracks}
target=OUT/'ff16-available179-readable-publisher-candidate.json'
assert not target.exists()
target.write_text(json.dumps({'schema_version':1,'publication_status':'awaiting_independent_peer','entries':[entry],
    'held_source_recordings':held,'source_receipts':[{'local_path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in [research_path,credit_path]]},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'candidate':target.relative_to(ROOT).as_posix(),'sha256':sha(target),'selectable_tracks':179}))
