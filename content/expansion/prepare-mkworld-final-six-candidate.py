"""Freeze six remaining named compositions with honest version/source context."""
import copy
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/nintendo-full'
load = lambda p: json.loads(p.read_text(encoding='utf-8'))
module_path = ROOT / 'content/expansion/soundtrack-multitrack-priority-overrides.json'
base = next(entry for entry in load(module_path)['entries'] if entry['entry_id'] == 'wikipedia-79613463')
assert len(base['tracks']) == 342
inventory = {row['number']: row for row in load(OUT / 'mkworld-nintendo-music-secondary-inventory.json')['tracks']}
source_rows = load(OUT / 'mkworld-inventory-exact-gaps-publication-research.json')['tracks']
fallback = {row['source']['id']: row for row in load(OUT / 'mkworld-inventory-exact-gaps-public-oembed-fallback-research.json')['tracks']}
by_number = {row['album_track_number']: fallback.get(row['source']['id'], row) for row in source_rows}
by_number.update({row['album_track_number']: row for row in load(OUT / 'mkworld-bonus-two-publication-research.json')['tracks']})
tracks, checks = [], []
for number in (236, 240, 247, 253, 347, 348):
    row = by_number[number]
    assert row['status'] == 'metadata_candidate'
    source, actual, expected = row['source'], row['publication'], inventory[number]
    video_id = source['id']
    duration = float(actual['lengthSeconds'])
    native = load(ROOT / row['native_codec_receipt'])
    assert native['native_compatible_avc_aac'] and native.get('avc_format_count') and native.get('aac_format_count')
    assert actual['title'] == source['title'] and actual['author'] == source['channel']
    assert abs(duration - expected['length_seconds']) <= 3 or (number == 347 and duration == 100 and expected['length_seconds'] == 96)
    record = copy.deepcopy(base['tracks'][0])
    record.update(
        youtube_id=video_id, url='https://www.youtube.com/watch?v=' + video_id,
        source_page='https://www.youtube.com/watch?v=' + video_id,
        title=expected['title'], primary_published_title=actual['title'],
        duration_seconds=duration, uploader=actual['author'],
        channel_url='https://www.youtube.com/channel/' + source['channel_id'],
        official_uploader_verified=number == 347,
        publishing_kind='official_publisher_studio_performance' if number == 347 else 'archival_game_score_publication',
        recording_context_source='https://www.youtube.com/watch?v=' + video_id,
        native_codec_metadata_receipt=row['native_codec_receipt'],
        publication_metadata_receipt=row.get('publication_metadata_receipt') or 'build/research/soundtrack-broad/watch/' + video_id + '.json',
        inventory_track_number=number,
        inventory_title_source='https://www.mariowiki.com/Mario_Kart_World_(Nintendo_Music)',
        inventory_source_kind='Community transcription of the Nintendo Music release, not an authenticated publisher metadata endpoint.',
    )
    if number == 347:
        record['recording_version'] = 'Official Nintendo of America In the Studio performance of Title Theme, full100-second public video including publisher presentation. The Nintendo Music bonus edit is listed as96 seconds; exact edited-master identity is not asserted and no undocumented cut is invented.'
        record['bonus_recording_context_source'] = 'https://www.mariowiki.com/Mario_Kart_World_(Nintendo_Music)'
        record['bonus_recording_context_scope'] = 'Secondary release documentation explicitly identifies the Title Theme and Crown City In the Studio performances with the two August24,2026 Nintendo Music bonus tracks. The first-party video description independently identifies this as a studio performance of the game theme.'
    elif number == 348:
        record['recording_version'] = 'Archival67-second publication explicitly titled Crown City (Bonus Track), matching the secondary Nintendo Music bonus inventory. Publisher upload and identical-master fingerprint are not asserted.'
    else:
        record['recording_version'] = 'Archival individual Mario Kart World game-score publication. Named version and duration match the Nintendo Music research inventory within3 seconds; exact publisher-master identity is not asserted.'
    assert (ROOT / record['publication_metadata_receipt']).exists()
    tracks.append(record)
    checks.append({'inventory': expected, 'youtube_id': video_id, 'actual_title': actual['title'],
                   'actual_author': actual['author'], 'actual_duration_seconds': duration,
                   'native_avc_aac': True, 'actual_description_present': bool(actual.get('shortDescription')),
                   'version_context': record['recording_version']})
assert len({track['youtube_id'] for track in tracks}) == 6
assert not ({track['youtube_id'] for track in tracks} & {track['youtube_id'] for track in base['tracks']})
assert not ({track['title'] for track in tracks} & {track['title'] for track in base['tracks']})
entry = {field: copy.deepcopy(value) for field, value in base.items() if field not in ('tracks', 'independent_review_receipt')}
entry.update(tracks=tracks, replace_existing_tracks=False,
             completeness={'status': 'partial_supplement', 'verified_supplemental_recordings': 6,
                           'requires_base_archival_recordings': 342, 'candidate_union_recordings': 348,
                           'expected_published_album_tracks_secondary': 348,
                           'all_game_music_complete': False,
                           'edited_master_equivalence': False,
                           'semantic_alias_mapping_independent_review': 'Open: matching348recordingcount alone does not certify every edited-master or historical level-name alias.'},
             recording_collection_scope='Six remaining named game-score/bonus compositions. A348-recording union would still retain explicit version and semantic-mapping qualifications rather than automatically claiming complete edited masters.')
candidate = {'schema_version': 1, 'publication_status': 'awaiting_independent_review', 'entries': [entry],
             'requires_base_module_sha256': hashlib.sha256(module_path.read_bytes()).hexdigest()}
destination = OUT / 'mkworld-final-six-compositions-candidate.json'
destination.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
report = {'status': 'AWAITING_INDEPENDENT_REVIEW', 'candidate_sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
          'new_recordings': 6, 'all_native_avc_aac': True, 'checks': checks,
          'no_native_login_retry': 'DaisyCircuit/RainbowRoad use other independently public positive publications, never the two prior login-held IDs.',
          'scope': 'Exact game-score/bonus publication identity, collective game-level Nintendo credit, actual source durations. No audio fingerprint or physical console playback assertion; no automatic whole-album completeness claim.'}
(OUT / 'mkworld-final-six-compositions-editorial-review.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({field: value for field, value in report.items() if field != 'checks'}))
