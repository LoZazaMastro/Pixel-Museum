"""Freeze forty public licensed songs, with all source editions and one hold explicit."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'build/research/soundtrack-broad/burnout-revenge-licensed-original'
def load(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=load(BASE/'native41-recording-reviewed-research.json');inventory=load(BASE/'licensed-original41-research-inventory.json')
assert len(rows)==41
owner=next(e for e in load(ROOT/'content/catalog.json')['entries'] if e['id']=='burnout-revenge');assert owner['year']==2005 and not owner.get('soundtrack')
tracks=[];held=[];sources={}
special={
6:'Official 2014 Hits compilation delivery of Red Flag. No exact2005 game-edit claim.',
8:'Official Hand of Blood EP reissue audio; artist publication describes the anniversary reissue context. No exact game-master claim.',
11:'Original official2005 music video, not the separately excluded 2015 Rain City Sessions performance.',
20:'Official 2004 Adam Freeland mix, full single version rather than an unverified game edit.',
22:'Official Soulwax Shibuya mix of the licensed LCD Soundsystem song, not the unremixed album track.',
24:'Official 2006 remix release retaining the licensed KMFDM mix; exact game edit not fingerprinted.',
25:'Official label album delivery dated 2006 with 2005 phonogram; original song publication metadata preserved.',
34:'Official 2006 You Smash It, We?ll Build Around It album delivery; no assertion of an identical2005 game edit.',
36:'Official 2006 Hopelessly Devoted to You Vol. 6 compilation delivery of the licensed song.',
37:'Official 2005 General Midi remix; Brian Molko vocal credit retained in delivered roles.',
}
for row in rows:
    if row['status']=='HELD':held.append(dict(ordinal=row['ordinal'],artist=row['artist'],title=row['title'],youtube_id=row['youtube_id'],reason=row['reason']));continue
    w=load(ROOT/row['watch_path']);v=load(ROOT/row['native_path']);vid=row['youtube_id'];desc=w['shortDescription'];n=row['ordinal']
    assert v['native_compatible_avc_aac'] and int(w['lengthSeconds'])==v['duration']
    assert w['channelId']==v['channel_id']
    lines=[s.strip() for s in desc.splitlines() if s.strip()];provided=lines[0] if lines and lines[0].startswith('Provided to YouTube by ') else ''
    roles=[s for s in lines if ':' in s and re.search(r'composer|lyricist|writer|producer|arrang|vocal|remix',s.split(':',1)[0],re.I)]
    release=next((s.split(': ',1)[1] for s in lines if s.startswith('Released on: ')),None)
    phonograms=[s for s in lines if s.startswith(('℗','(C)','(c)'))]
    archive=w['author'] in ['Opfafest10','EpicSkill']
    title='Hand Of Blood (official EP reissue)' if n==8 else ('Nü Rock' if n==25 else row['title'])
    version=special.get(n,('Public archival recording of the named licensed song; exact game audio master not fingerprinted.' if archive else ('Official label-delivered recording of the licensed song.' if provided else 'Artist or label music-video publication of the licensed song.')))
    if n==14:version='Public archival BT vs. The Doors remix of Break On Through; not the unremixed 1967 recording.'
    if n==33:version='Public full Superdiscount remix; original unremixed song and later fan-remasters are excluded.'
    t=dict(youtube_id=vid,url='https://www.youtube.com/watch?v='+vid,source_page='https://www.youtube.com/watch?v='+vid,title=title,creator=row['artist'],recording_artists=[row['artist']],music_kind='licensed_song',credit_scope='Named recording artist; delivered songwriter and production roles preserved separately, no generic game composer allocation.',delivered_music_roles=roles,game_association_source='https://www.mobygames.com/game/19356/burnout-revenge/',game_tracklist_announcement_source=inventory['gamespot_publisher_announcement_url'],composer_source='https://www.mobygames.com/game/19356/burnout-revenge/credits/ps2/',recording_version=version,uploader=w['author'],channel_url='https://www.youtube.com/channel/'+w['channelId'],source_actual_publication_title=w['title'],official_uploader_verified=bool(provided),publishing_kind='archival_licensed_song_recording' if archive else ('official_label_delivered_song_recording' if provided else 'artist_or_label_music_video'),duration_seconds=int(w['lengthSeconds']),rights='Composition and recording rights remain with the artists, songwriters, publishers and record labels.',publication_metadata_receipt=row['watch_path'],native_codec_metadata_receipt=row['native_path'],native_codec_metadata_verified=True,playback_verified_on_ps5=False,original_game_tracklist_ordinal=n)
    if release:t['label_delivery_release_date']=release
    if phonograms:t['label_delivered_phonogram_lines']=phonograms
    if provided:t['provided_to_youtube_line']=provided
    tracks.append(t)
    for name in [row['watch_path'],row['native_path']]:sources[name]=dict(path=name,sha256=sha(ROOT/name))
assert len(tracks)==40 and len(held)==1 and held[0]['artist']=='The Starting Line'
# Yellowcard's debut single leads this listening curation, not a claim of menu order.
tracks.sort(key=lambda t:(t['creator']!='Yellowcard',t['original_game_tracklist_ordinal']))
entry=dict(entry_id='burnout-revenge',match_title='Burnout Revenge',match_year=2005,title='Listen to Burnout Revenge',composer='Various artists',music_kind='licensed_playlist',replace_existing_tracks=True,curator_note='Listen to the licensed songs of Burnout Revenge.',tracks=tracks,full_album_collection=False,coverage_status='40_PUBLIC_RECORDINGS_FOR_41_ORIGINAL_LICENSED_SONGS',album_completeness=dict(published_original_licensed_inventory=41,available_named_songs=40,qualification='One login-required public recording is held. Official reissues, full single remixes and music videos are explicitly identified; no exact censored in-game edits or complete audio-master equivalence claimed.'))
for p in [BASE/'licensed-original41-research-inventory.json',BASE/'indexed-original-game-tracklist-source.json',BASE/'ea-2007-trax-primary.html',BASE/'source-fetch-receipts.json']:
    name=p.relative_to(ROOT).as_posix();sources[name]=dict(path=name,sha256=sha(p))
out=BASE/'forty-original-licensed-songs-candidate.json'
candidate=dict(schema_version=1,publication_status='NEXT_PENDING_INDEPENDENT_REVIEW',scope='Forty named licensed song publications from the original 2005 EA Trax inventory. No composed-score filler, retail fingerprint, chronology mutation or physical-console playback claim.',entries=[entry],held_recordings=held,excluded_alternatives=[dict(artist='Comeback Kid',title='Wake The Dead',youtube_id='l1T3MiVC7oQ',reason='Actual label metadata identifies2015 Rain City Sessions +1, a later performance; replaced with official original 2005 music video2NTyyCwwDfY.')],source_receipts=list(sources.values()),source_access_limits=['Direct GameSpot and Moby HTTP403 are not claimed as acquired publisher HTML. The contemporary announcement identity and full41-title Moby inventory were read via the public web-search reader; a factual indexed tracklist receipt is frozen locally.','The actual2007 EA press-release HTML corroborates EA Trax licensing and linked purchases for the series, not every individual recording/artist mapping. Song-level mappings use the separately declared original game tracklist.','Artist/label recording dates are retained independently from the game year. Remasters/reissues and full named remixes are allowed with declared edition context; cover/live/unlicensed-remix performances are not selected. Starting Line login restriction remains held without retry.'],catalog_sha256_at_discovery=sha(ROOT/'content/catalog.json'),source_catalog_or_runtime_changed=False)
out.write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(out.relative_to(ROOT),sha(out),len(tracks))
