"""Useful public original-score collections, retaining ambiguous source markers as holds."""
import hashlib
import json
import pathlib
import re

ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=ROOT/'build/research/soundtrack-broad/modern-public-albums'
load=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
profiles=[
    ('Ya4kC6qj8z0','wikipedia-36691288','Cyberpunk 2077',2020,'Cyberpunk 2077 music team',37,
     'https://cdn-s-cyberpunk.cdprojektred.com/cp2077-songbook-digital.pdf'),
    ('_B9Hruqz5fw','wikipedia-43011121','Cuphead',2017,'Kristofer Maddigan',54,
     'https://studiomdhr.bandcamp.com/album/cuphead-original-soundtrack'),
    ('DlbWg4AaF0U','workbook-08-21-bioshock','BioShock',2007,'Garry Schyman',23,
     'https://bioshockinfinite.ghoststorygames.com/news/the-game/music-composer-revealed-during-ken-levine-reddit-ama/'),
    ('Cpd1XaTsIb4','workbook-11-20-mass-effect','Mass Effect',2007,'Mass Effect music team',35,
     'https://eagames.bandcamp.com/album/mass-effect')]
entries=[]
sources=[]
holds=[]
for video_id,entry_id,name,year,composer,expected,primary in profiles:
    path=OUT/(video_id+'-actual-publication-research.json')
    receipt=load(path)
    pub=receipt['publication']
    assert receipt['native_avc_aac'] and load(ROOT/receipt['native_codec_receipt'])['native_compatible_avc_aac']
    markers=[]
    for line in pub['shortDescription'].splitlines():
        pattern=r'^\d+-\d+ (.+?) (\d+:\d{2}(?::\d{2})?)\s*$' if name=='Cyberpunk 2077' else r'^\d+\. (.+?) (\d+:\d{2}(?::\d{2})?)\s*$' if name=='Mass Effect' else r'^(\d+:\d{2}(?::\d{2})?)\s+(?:-\s+)?(?:Kristofer Maddigan - )?(.+?)\s*$'
        match=re.match(pattern,line)
        if not match:continue
        title,timestamp=(match[1],match[2]) if name in ['Cyberpunk 2077','Mass Effect'] else (match[2],match[1])
        start=0
        for piece in timestamp.split(':'):start=start*60+int(piece)
        if name=='Cuphead' and title=="Don't Deal With The Devil - Instrumental":
            holds.append({'game':name,'title':title,'actual_source_line':line,
                'reason':'42:29 is out of original album position and falls inside another indexed piece. No replacement or inferred42second cut invented.'})
            continue
        markers.append({'title':title,'start':start,'line':line})
    # Sorting literal positions is only used after retaining Cuphead's malformed marker as a hold.
    markers.sort(key=lambda r:r['start'])
    duration=float(pub['lengthSeconds'])
    tracks=[]
    for index,marker in enumerate(markers):
        end=markers[index+1]['start'] if index+1<len(markers) else duration
        reason=None
        if name=='Cuphead' and marker['start']==0:
            reason='Opening source interval combines the42second vocal and64second instrumental; no individually identifiable split marker.'
        if name=='Mass Effect' and marker['start']==330:
            reason='Battle at Eden Prime and Saren share the same5:30 source marker. Both held instead of guessing their internal boundary.'
        if name=='BioShock' and 'Rise, Rapture, Rise' in marker['title']:
            reason='Anthem has a separate Ken Levine authorship context; do not silently assign the album score author to this song.'
        if reason:
            holds.append({'game':name,'title':marker['title'],'actual_source_line':marker['line'],'reason':reason})
            continue
        assert 0<=marker['start']<end<=duration,(name,marker,end)
        creator,credit_source=composer,primary
        roles={}
        version=f'Original {year} {name} score, available archival album passage. Real source timestamp boundaries; not a fan arrangement, sequel score, recreated loop or physical audio-master certification.'
        if name=='BioShock':
            version='Original 2007 BioShock game score, archival passage from the later 2010 I Am Rapture, Rapture Is Me album selection. Uploader\'s erroneous 2007 PS3 release statement is not adopted; not the BioShock 2 score or licensed period-song collection.'
        if name=='Cyberpunk 2077' and marker['title'].startswith('Never Fade Away'):
            creator='P.T. Adamczyk, Olga Jankowska, Kristofer Steen, David Sandström'
            credit_source='https://www.shazam.com/en-gb/song/1544458149/never-fade-away-samurai-cover-feat-olga-jankowska'
            roles={'lyrics':['Dennis Lyxzén'],'lead_vocals':['Olga Jankowska'],'mixing':['Jason La Rocca'],
                   'recording_engineer':['Michał Rypień'],'mastering':['Rafał Smoleń']}
            version='Original 2020 Cyberpunk 2077 album/in-game credits version of Never Fade Away, officially named SAMURAI Cover, performed by P.T. Adamczyk and Olga Jankowska. This is the original game album recording, not a fan cover or the different Refused/SAMURAI single performance.'
        if name=='Mass Effect' and marker['title']=='M4 Part II':
            creator='Faunts'
            credit_source='https://fauntsmusic.bandcamp.com/album/m4'
            version='Original Mass Effect 2007 album end-credit selection M4 Part II by Faunts. Distinct band song, not attributed to the orchestral score composers or Mass Effect 2.'
        track={'youtube_id':video_id,'url':'https://www.youtube.com/watch?v='+video_id,
            'source_page':'https://www.youtube.com/watch?v='+video_id,'title':marker['title'],
            'creator':creator,'composer_source':credit_source,'additional_recording_roles':roles,
            'artist_credit_scope':'Single named original composer where documented; otherwise an honest game/album collective credit, with contributors kept at album-level rather than assigned as joint authors of every cue.',
            'start_seconds':marker['start'],'end_seconds':end,'duration_seconds':end-marker['start'],
            'source_actual_chapter_line':marker['line'],'source_publication_duration_seconds':duration,
            'uploader':pub['author'],'channel_url':'https://www.youtube.com/channel/'+pub['channelId'],
            'primary_published_title':pub['title'],'official_uploader_verified':False,
            'publishing_kind':'archival_game_recording','recording_year':year,
            'recording_version':version,'recording_platform':'Capture hardware not identified',
            'rights':f'Original {name} publisher and credited music authors, performers and recording contributors; {pub["author"]} is an archival uploader.',
            'native_codec_metadata_verified':True,'native_codec_metadata_receipt':receipt['native_codec_receipt'],
            'publication_metadata_receipt':path.relative_to(ROOT).as_posix(),'playback_verified_on_ps5':False}
        if name=='Cyberpunk 2077':track['game_album_level_music_credits']=['Marcin Przybyłowicz','P.T. Adamczyk','Paul Leonard-Morgan']
        if name=='Mass Effect':track['game_album_level_music_credits']=['Jack Wall','Sam Hulick','Richard Jacques','David Kates']
        if name=='Cuphead':track['album_level_recording_roles']={'music_and_lyrics':['Kristofer Maddigan'],'conductor':['John Herberman'],
            'engineering_mixing_editing':['Jeremy Darby'],'mastering':['Peter Letros'],
            'vocals':['Alana Bridgewater'],'barbershop_quartet':['Shoptimus Prime']}
        tracks.append(track)
    assert len(tracks)==expected,(name,len(tracks))
    entries.append({'entry_id':entry_id,'match_title':name,'match_year':year,'title':'Listen to '+name,
        'composer':composer,'curator_note':'Listen to the music of '+composer+'\n'+name,
        'replace_existing_tracks':True,'full_album_collection':False,'coverage_status':'partial',
        'recording_collection_scope':f'{expected} available original-score selections with actual public chapter boundaries. Source ambiguity/other authorship cases retained as explicit holds; no exhaustive game-stem or master-matching claim.',
        'album_completeness':{'verified_available_tracks':expected,'inventory_source':primary,
            'scope':'Available source-indexed original-game album selections, not all separately licensed music or later expansions.'},'tracks':tracks})
    sources.append(path)
credit=OUT/'modern-four-archive-primary-web-read-receipt.json'
credit.write_text(json.dumps({'actual_web_pages_read':[
    {'url':profiles[0][-1],'scope':'CDPR original-score songbook explicitly identifies the three original score authors. Piano arranger not assigned to the source recordings.'},
    {'url':'https://www.shazam.com/en-gb/song/1544458149/never-fade-away-samurai-cover-feat-olga-jankowska','scope':'Actual matching song page, original album and explicit Composition/Lyrics/Performance/Engineering roles. Not the previously encountered unrelated numerical redirect.'},
    {'url':profiles[1][-1],'scope':'StudioMDHR original2017 album, all music/lyrics Maddigan, original56 titles and clearly separated recording/performing roles.'},
    {'url':profiles[3][-1],'scope':'EA original37-track album inventory and2007 release. Two conflicting source timestamp rows held.'},
    {'url':'https://fauntsmusic.bandcamp.com/album/m4','scope':'Original band M4PartII recording identity, rather than assigning it to game-score roster.'},
    {'url':'https://garryschyman.com/wp-content/uploads/2013/05/garryschymanbioshock.pdf','scope':'Composer\'s original published BioShock score, composition credit GarrySchyman. TitleCohen\'sScherzoNo7 is distinct from a third-party piano cover.'}],
    'additional_source_excerpts_read':[
    {'url':profiles[2][-1],'scope':'Original developer quotes KenLevine identifying GarrySchyman as originalBioShock1/2 score composer; not source for album sequence.'},
    {'url':'https://www.squareenixmusic.com/albums/b/bioshock.shtml','source_type':'Independent archival album inventory, not SquareEnix publisher','scope':'24-track2010 IAmRapture album identifies originalBioShock2007score. RiseRapture held, not silently assigned toGarry.'}],
    'scope':'Editorial public-source identity/metadata verification, no listening/fingerprinting/physicalPS5 claim.'},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
sources.append(credit)
target=OUT/'modern-four-archive149-readable-candidate.json'
assert not target.exists()
target.write_text(json.dumps({'schema_version':1,'publication_status':'awaiting_independent_peer','entries':entries,
    'held_source_markers':holds,'source_receipts':[{'local_path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in sources]},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'candidate':target.relative_to(ROOT).as_posix(),'sha256':sha(target),'tracks_per_game':[len(e['tracks']) for e in entries]}))
