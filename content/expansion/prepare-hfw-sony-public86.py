"""Available original Sony album publications, preserving vocals and In the Flood authorship."""
import hashlib
import json
import pathlib
import re

ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=ROOT/'build/research/soundtrack-broad/modern-public-albums'
load=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
research_path=OUT/'hfw-available-publication-research.json'
research=load(research_path)
assert len(research['tracks'])==88
primary='https://blog.playstation.com/2022/10/06/horizon-forbidden-west-ost-physical-pre-orders-and-a-music-video-debut/'
tracks=[]
holds=[]
for row in sorted(research['tracks'],key=lambda r:r['source_playlist_position']):
    if row['status']!='metadata_candidate':
        holds.append({'youtube_id':row['source']['id'],'title':row['source']['title'],'reason':row.get('error','Public metadata unresolved')})
        continue
    pub=row['publication']
    assert pub['author']=='SonySoundtracksVEVO' and 'Horizon Forbidden West (Original Soundtrack)' in pub['title']
    assert row['native_compatible_avc_aac'] and load(ROOT/row['native_codec_receipt'])['native_compatible_avc_aac']
    assert abs(float(pub['lengthSeconds'])-float(row['source']['duration']))<=3
    raw=next(s for s in pub['shortDescription'].splitlines() if re.search(r'Music by ',s,re.I))
    music=re.search(r'Music by (.+)$',raw,re.I)[1].strip()
    if '____' in music:
        holds.append({'youtube_id':row['source']['id'],'title':pub['title'],'reason':'Publisher music-credit field remains a template placeholder; no individual composer inferred from its artist-prefix title.'})
        continue
    split=re.split(r'\s+(?:feat\.|featuring)\s+',music,maxsplit=1,flags=re.I)
    composer=split[0].strip().replace('Niels van deer Leest','Niels van der Leest')
    assert composer in ['Joris de Man','The Flight','Oleksa Lozowchuk','Niels van der Leest','Lovisa Bergdahl'],(row['source']['id'],music)
    roles={}
    if len(split)>1:roles['featured_artist']=[s.strip() for s in split[1].split(' and ')]
    video_id=row['source']['id']
    credit='https://www.youtube.com/watch?v='+video_id
    title=pub['title'].split(' | Horizon Forbidden West')[0]
    for prefix in ['Joris de Man - ','The Flight - ','Oleksa Lozowchuk - ','Niels van der Leest - ','Lovisa Bergdahl - ']:
        if title.startswith(prefix):title=title[len(prefix):]
    if video_id=='9H8zNzSC5Cg':
        composer='Lovisa Bergdahl'
        credit=primary
        roles={'co_production':['Lovisa Bergdahl','Oleksa Lozowchuk'],'vocals':['Ariana Gillis']}
    elif 'In the Flood' in title and composer=='Lovisa Bergdahl':
        roles['vocals']=['Lovisa Bergdahl']
        credit=primary
    tracks.append({'youtube_id':video_id,'url':'https://www.youtube.com/watch?v='+video_id,
        'source_page':'https://www.youtube.com/watch?v='+video_id,'title':title,'creator':composer,
        'composer_source':credit,'additional_recording_roles':roles,
        'artist_credit_scope':'Original Sony publication Music by field, featuring performers kept separately. In the Flood composition follows Guerrilla audio director identifying original author Lovisa Bergdahl; Oleksa is co-producer, not substituted as sole composer. One publisher spelling typo in Niels van der Leest is normalized while the raw line remains intact.',
        'publisher_music_role_lines':[raw],'duration_seconds':float(pub['lengthSeconds']),
        'source_playlist_position':row['source_playlist_position'],'uploader':pub['author'],
        'channel_url':'https://www.youtube.com/channel/'+pub['channelId'],'primary_published_title':pub['title'],
        'official_uploader_verified':True,'publishing_kind':'official_game_recording','recording_year':2022,
        'recording_version':'Original 2022 Horizon Forbidden West Sony soundtrack publication. Explicit named variants retained; not Horizon Zero Dawn, Burning Shores or the expanded complete six-disc collection. Stale pre-release dates in uploader promotional boilerplate are not adopted.',
        'rights':'Sony Interactive Entertainment / Sony Music Masterworks / Milan Records and credited original music authors, performers and recording contributors.',
        'native_codec_metadata_verified':True,'native_codec_metadata_receipt':row['native_codec_receipt'],
        'publication_metadata_receipt':(OUT/'hfw-public-individuals'/(video_id+'.json')).relative_to(ROOT).as_posix(),
        'playback_verified_on_ps5':False})
assert len(tracks)==86 and len(holds)==2
credit_path=OUT/'hfw-sony-primary-web-read-receipt.json'
credit_path.write_text(json.dumps({'source_url':primary,'actual_web_page_read':True,
    'scope':'Guerrilla audio director names Lovisa as In the Flood original writer, Oleksa as co-producer and Ariana as performer, distinguishing Lovisa end-credit version. Original score album is separate from later Burning Shores.',
    'available_publisher_playlist_tracks':86,'held_source_records':2,
    'collection_scope':'Available original Sony playlist selections, not the larger130-plus-track physical/digital edition or an audio master/playback certification.'},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
entry={'entry_id':'workbook-02-18-horizon-forbidden-west','match_title':'Horizon Forbidden West','match_year':2022,
    'title':'Listen to Horizon Forbidden West','composer':'Horizon music team',
    'curator_note':'Listen to the music of Horizon music team\nHorizon Forbidden West',
    'replace_existing_tracks':True,'full_album_collection':False,'coverage_status':'partial',
    'recording_collection_scope':'86 available original Sony soundtrack publications. One native-unresolved and one unresolved publisher credit-template record remain held; not the larger complete soundtrack collection.',
    'album_completeness':{'public_source_playlist_records':88,'verified_available_tracks':86,'held_source_records':2,
        'inventory_source':'https://www.youtube.com/playlist?list=PLRW80bBvVD3Ui0GDXmPiHWgaLOnWcxAYq',
        'scope':'Available publisher playlist, not a complete original-game score count.'},'tracks':tracks}
target=OUT/'hfw86-available-sony-candidate.json'
assert not target.exists()
target.write_text(json.dumps({'schema_version':1,'publication_status':'awaiting_independent_peer','entries':[entry],
    'held_source_records':holds,'source_receipts':[{'local_path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in [research_path,credit_path]]},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'candidate':target.relative_to(ROOT).as_posix(),'sha256':sha(target),'selectable_tracks':86}))
