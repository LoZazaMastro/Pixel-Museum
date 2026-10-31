"""Source-only available Yakuza0 collection; no shared pipeline or runtime writes."""
from pathlib import Path
import hashlib
import json
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'build/research/soundtrack-broad/yakuza-zero-public-collection'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
progress_path=P/'research-progress-88-actual-chapter-bounds.json'
progress=json.loads(progress_path.read_text(encoding='utf8'))
watch_path=ROOT/progress['source_watch_receipt']
assert sha(watch_path)==progress['source_watch_sha256']
watch=json.loads(watch_path.read_text(encoding='utf8'))
codec_path=P/'native-compatibility-p025z6l57Z0.json'
codec=json.loads(codec_path.read_text(encoding='utf8'))
assert codec['native_compatible_avc_aac'] and codec['duration']==progress['source_duration_seconds']
assert codec['channel_id']==watch['channelId']
acquisition=json.loads((P/'primary-source-acquisition.json').read_text(encoding='utf8'))
assert all(r.get('http_status')==200 and r.get('body_contains_actual_subject') for r in acquisition)
albums={side:json.loads((P/f'apple-delivered-side{side}-metadata-whitelist.json').read_text(encoding='utf8')) for side in ['A','B']}
for side,album in albums.items():
    assert len([r for r in album['rows'] if r['wrapperType']=='track'])==44
    assert all(r.get('trackCount')==44 and 'Side '+side in r['collectionName'] for r in album['rows'])
catalog_path=ROOT/'content/catalog.json'
entry=next(e for e in json.loads(catalog_path.read_text(encoding='utf8'))['entries'] if e['id']==progress['entry_id'])
assert entry['title']=='Yakuza 0' and entry['year']==2015
tracks=[];reconciliation=[]
for chapter in progress['selected_actual_chapter_passages']:
    side,n=chapter['album_side'],chapter['side_track_number']
    label=next(r for r in albums[side]['rows'] if r.get('wrapperType')=='track' and r['trackNumber']==n)
    start,end=chapter['start_seconds'],chapter['end_seconds']
    assert 0<=start<end<=progress['source_duration_seconds']
    duration=end-start
    # Preserve the supplied archive's real chapter title and exact bounds.
    # Source labels/vocal variants remain explicit rather than pretending every
    # passage is fingerprint-identical to the separately published retail master.
    tracks.append({'youtube_id':'p025z6l57Z0','url':progress['source_watch'],
      'title':chapter['title'],'creator':label['artistName'],'uploader':watch['author'],
      'source_page':progress['source_watch'],'channel_url':'https://www.youtube.com/channel/'+watch['channelId'],
      'publishing_kind':'archival_game_recording','official_uploader_verified':False,
      'duration_seconds':duration,'start_seconds':start,'end_seconds':end,
      'source_actual_chapter_title':chapter['title'],'source_actual_chapter_line':chapter['source_actual_line'],
      'source_publication_duration_seconds':progress['source_duration_seconds'],
      'recording_year':2015,'recording_album':'Yakuza 0 / Ryu ga Gotoku 0 original soundtrack, Side '+side,
      'recording_version':'Original 2015 game score; public archival collection. Capture hardware not identified.',
      'album_disc':1 if side=='A' else 2,'disc_track_number':n,
      'album_track_number':n if side=='A' else 44+n,
      'original_album_tracklist_source':label['collectionViewUrl'],
      'published_album_track_title':label['trackName'],'published_album_artist_credit':label['artistName'],
      'artist_credit_scope':'Exact publisher-delivered album artist field; not an assertion that every listed performer is the cue composer.',
      'game_composer_source':'https://en.wikipedia.org/wiki/Yakuza_0',
      'composer_source':label['collectionViewUrl'],
      'recording_context_source':'https://prtimes.jp/main/html/rd/p/000000403.000005397.html',
      'rights':'SEGA and the credited composition, performance and recording contributors retain their respective rights. Public archival upload is not an official publisher delivery.',
      'publication_metadata_receipt':watch_path.relative_to(ROOT).as_posix(),
      'native_codec_metadata_verified':True,'native_codec_metadata_receipt':codec_path.relative_to(ROOT).as_posix(),
      'playback_verified_on_ps5':False})
    reconciliation.append({'side':side,'published_number':n,'published_title':label['trackName'],
      'source_chapter_title':chapter['title'],'published_artist_credit':label['artistName'],
      'source_start_seconds':start,'source_end_seconds':end,'source_passage_seconds':duration,
      'publisher_track_seconds':label['trackTimeMillis']/1000,
      'difference_seconds':round(duration-label['trackTimeMillis']/1000,3),
      'bounds_come_only_from_actual_source_description':True})
assert len(tracks)==88 and len({(t['youtube_id'],t['start_seconds']) for t in tracks})==88
longest_difference=max(reconciliation,key=lambda r:abs(r['difference_seconds']))
selection={'entry_id':entry['id'],'match_title':entry['title'],'match_year':2015,
 'title':'Listen to Yakuza 0','composer':'SEGA Sound Team and contributing musicians',
 'curator_note':'Listen to the music of SEGA Sound Team and contributing musicians from Yakuza 0.',
 'replace_existing_tracks':True,'full_album_collection':False,
 'coverage_status':'AVAILABLE_PUBLIC_COLLECTION_OF_88_PUBLISHED_SIDE_A_B_TITLES',
 'album_completeness':{'published_title_inventory':88,'available_archival_passages':88,
   'inventory_source':'https://prtimes.jp/main/html/rd/p/000000403.000005397.html',
   'qualification':'Publicly available source chapters corresponding to the original2015SideA/B album titles. No claim of exact retail-master identity, every game-file cue, all regional variants or2025DirectorsCut completeness.'},
 'tracks':tracks}
out={'schema_version':1,'publication_status':'awaiting_independent_peer_NEXT_not_admitted',
 'scope':'Available original2015Yakuza0 public soundtrack collection; exact supplied chapter bounds, no new times or audio download.',
 'catalog_sha256':sha(catalog_path),'entries':[selection],
 'source_receipts':acquisition+[
   {'path':(P/f'apple-delivered-side{side}-metadata-whitelist.json').relative_to(ROOT).as_posix(),
    'sha256':sha(P/f'apple-delivered-side{side}-metadata-whitelist.json')} for side in ['A','B']]+[
   {'path':watch_path.relative_to(ROOT).as_posix(),'sha256':sha(watch_path)},
   {'path':codec_path.relative_to(ROOT).as_posix(),'sha256':sha(codec_path)}],
 'title_and_boundary_reconciliation':reconciliation,
 'recording_identity_limits':[
   'Old research gate wrongly failed the Japanese album title; original SEGA release news and delivered2015SideA/B metadata establish the exact game identity.',
   'The shared upload includes other regional/bonus material. Only the88selectedSideA/B title passages enter this candidate; Bubble,Kurenai,Westernopening,additionalkaraoke/80sbonus andstoreloops are excluded.',
   'Actual source SideB order differs from the published album; this candidate exposes real separate chapter passages without inventing timestamp positions.',
   'The source marks some vocal takes explicitly, including ChikaFullVersion. Their names remain visible and published artist metadata is separately retained, without pretending a fingerprint-identical master.',
   'CuteGirl source passage is95s versus101.024s deliveredalbum metadata. The actual supplied interval remains intact; not advertised as an uncut original retail album master.',
   'All other supplied passage lengths differ from deliveredmetadata by under2seconds; this is supporting context, not audio fingerprinting or an excuse to manufacture bounds.',
   'Native resolver exposes AVC/AAC metadata for this shared source. PhysicalPS5 playback/cipher resolution is not asserted.'],
 'largest_retail_duration_difference':longest_difference,'checked_utc':datetime.now(timezone.utc).isoformat(),
 'master_or_SOURCE71_changed':False,'media_downloaded':False}
target=P/'yakuza-zero-88-public-chapters-candidate.json'
target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(target.relative_to(ROOT).as_posix(),sha(target),len(tracks))
