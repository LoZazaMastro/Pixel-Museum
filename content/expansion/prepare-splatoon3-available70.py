import hashlib,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=ROOT/'build/research/soundtrack-broad/modern-public-albums'
load=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rpath=OUT/'splatoon3-available-publication-research.json'
research=load(rpath)
primary='https://www.famitsu.com/news/202303/15295623.html'
tracks=[];holds=[]
for row in sorted(research['tracks'],key=lambda r:r['source_playlist_position']):
    vid=row['source']['id']
    if row['status']!='metadata_candidate' or vid in ['itfV0h0mg0s','Dv6wwH2Ucxk']:
        reason=row.get('error') or ('Pure test-noise item excluded from music curation.' if vid=='itfV0h0mg0s' else 'Apparent duplicate Smeared Canvas selection, without documented distinct recording; not an audio fingerprint claim.')
        holds.append({'youtube_id':vid,'title':row['source']['title'],'reason':reason});continue
    p=row['publication'];assert p['title']==row['source']['title']
    assert row['native_compatible_avc_aac'] and load(ROOT/row['native_codec_receipt'])['native_compatible_avc_aac']
    assert abs(float(p['lengthSeconds'])-row['source']['duration'])<=3
    title=re.sub(r'\s*[-|]\s*Splatoon\s*3\s*(?:OST|Soundtrack).*$', '',p['title'],flags=re.I).strip()
    title=re.sub(r'^Splatoon\s*3\s*(?:OST|Soundtrack)\s*[-:|]\s*','',title,flags=re.I).strip()
    rolelines=[l for l in p.get('shortDescription','').splitlines() if re.search(r'composer|music by|arrang',l,re.I)]
    tracks.append({'youtube_id':vid,'url':'https://www.youtube.com/watch?v='+vid,'source_page':'https://www.youtube.com/watch?v='+vid,'title':title,
      'creator':'Nintendo sound team','composer_source':primary,
      'artist_credit_scope':'Collective original-game music credit. Individual cue authorship is not separately documented; uploader staff rosters are retained as source statements, not attributed to every cue. In-game band names are fictional band attribution.',
      'uploader_music_credit_lines':rolelines,'source_description_present':bool(p.get('shortDescription')),
      'publication_evidence_scope':'Actual public Android title, uploader, channel and duration; source descriptions preserved only when present. Archival uploads are not verified Nintendo channels.',
      'duration_seconds':float(p['lengthSeconds']),'source_playlist_position':row['source_playlist_position'],'uploader':p['author'],
      'channel_url':'https://www.youtube.com/channel/'+p['channelId'],'primary_published_title':p['title'],'official_uploader_verified':False,
      'publishing_kind':'archival_game_recording','recording_year':2022,
      'recording_version':'Available original Splatoon 3 Switch game recording or named in-game musical variant/jingle. Uploader game loops and ambient phase versions are retained; not asserted as identical edited Splatune 3 CD masters.',
      'rights':'Nintendo and original credited music contributors. Archival uploader: '+p['author']+'.',
      'native_codec_metadata_verified':True,'native_codec_metadata_receipt':row['native_codec_receipt'],
      'publication_metadata_receipt':(OUT/'splatoon3-public-individuals'/(vid+'.json')).relative_to(ROOT).as_posix(),'playback_verified_on_ps5':False})
assert len(tracks)==70
context=OUT/'splatoon3-available70-primary-context-receipt.json'
context.write_text(json.dumps({'actual_web_pages_read':[{'url':primary,'publisher':'KADOKAWA Game Linkage / Famitsu, physical album publisher','context':'Original Splatune 3 announcement and 147-track three-disc inventory, published April 26 2023; Nintendo rights. Provides original game and album context, not a per-cue human composer split.'}],
'coverage_scope':'70 available archival original-game music selections. Game loops and variants differ from edited CD tracks. No complete147-album or230 Nintendo Music claim.',
'actual_public_descriptions':sum(t['source_description_present'] for t in tracks),'identity_without_description':sum(not t['source_description_present'] for t in tracks),'oembed_fallbacks':0,
'held_or_curated_out':len(holds),'scope_limits':'Public metadata/native compatibility verification only; no listening, fingerprinting or physical PS5 playback claim.'},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
entry={'entry_id':'wikipedia-68802923','match_title':'Splatoon 3','match_year':2022,'title':'Listen to Splatoon 3','composer':'Nintendo sound team',
'curator_note':'Listen to the music of Nintendo sound team\nSplatoon 3','replace_existing_tracks':True,'full_album_collection':False,'coverage_status':'partial',
'recording_collection_scope':'70 available original-game music selections, including named ambient, battle, story, festival and Tableturf variants. Archive game recordings are not asserted as the complete147-track edited Splatune 3 album or the larger Nintendo Music collection.',
'album_completeness':{'expected_published_album_tracks':147,'verified_available_music_selections':70,'inventory_source':primary,'scope':'Game recordings and named variants do not map one-to-one to edited CD masters.'},'tracks':tracks}
target=OUT/'splatoon3-available70-public-candidate.json';assert not target.exists()
target.write_text(json.dumps({'schema_version':1,'publication_status':'awaiting_independent_peer','entries':[entry],'held_source_tracks':holds,'source_receipts':[{'local_path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in [rpath,context]]},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'candidate':target.relative_to(ROOT).as_posix(),'sha256':sha(target),'tracks':70,'held_or_curated_out':len(holds)}))
