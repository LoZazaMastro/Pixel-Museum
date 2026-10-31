"""Freeze distinct original-game loop publications, without faking album edits."""
import copy
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/nintendo-full'
load = lambda p: json.loads(p.read_text(encoding='utf-8'))
module_path = ROOT / 'content/expansion/soundtrack-multitrack-priority-overrides.json'
base = next(entry for entry in load(module_path)['entries'] if entry['entry_id'] == 'wikipedia-79613463')
assert len(base['tracks']) == 331
rows = load(OUT / 'mkworld-final-core-loops-publication-research.json')['tracks']
inventory = {row['number']: row for row in load(OUT / 'mkworld-nintendo-music-secondary-inventory.json')['tracks']}
tracks, checks = [], []
for row in rows:
    assert row['status'] == 'metadata_candidate'
    source, actual = row['source'], row['publication']
    expected = inventory[row['album_track_number']]
    duration = float(actual['lengthSeconds'])
    assert actual['title'] == source['title'] and actual['author'] == source['channel'] == 'Mario Kart Music Channel'
    assert 'Mario Kart World Soundtrack' in actual['title']
    assert duration > expected['length_seconds'], 'These candidates must be disclosed longer loops, never unidentified short cuts'
    native = load(ROOT / row['native_codec_receipt'])
    assert native['native_compatible_avc_aac'] and native.get('avc_format_count') and native.get('aac_format_count')
    video_id = source['id']
    record = copy.deepcopy(base['tracks'][0])
    record.update(
        youtube_id=video_id, url='https://www.youtube.com/watch?v=' + video_id,
        source_page='https://www.youtube.com/watch?v=' + video_id,
        title=expected['title'], primary_published_title=actual['title'],
        duration_seconds=duration, uploader=actual['author'],
        channel_url='https://www.youtube.com/channel/' + source['channel_id'],
        publishing_kind='archival_game_score_publication',
        recording_version=f'Game-score archive loop version ({duration:g} seconds). The Nintendo Music research inventory lists a shorter {expected["length_seconds"]}-second edited version; this is not asserted to be that edited master. The full public recording is retained without invented cut points.',
        recording_context_source='https://www.youtube.com/watch?v=' + video_id,
        native_codec_metadata_receipt=row['native_codec_receipt'],
        publication_metadata_receipt='build/research/soundtrack-broad/watch/' + video_id + '.json',
        inventory_track_number=expected['number'],
        inventory_title_source='https://www.mariowiki.com/Mario_Kart_World_(Nintendo_Music)',
        original_publication_description_missing=not bool(actual.get('shortDescription')),
    )
    assert (ROOT / record['publication_metadata_receipt']).exists()
    tracks.append(record)
    checks.append({'inventory': expected, 'actual_title': actual['title'], 'actual_channel': actual['author'],
                   'youtube_id': video_id, 'actual_duration_seconds': duration,
                   'actual_description_missing': not bool(actual.get('shortDescription')), 'native_avc_aac': True})
assert len(tracks) == 11
assert not ({track['youtube_id'] for track in tracks} & {track['youtube_id'] for track in base['tracks']})
assert not ({track['title'] for track in tracks} & {track['title'] for track in base['tracks']})
entry = {field: copy.deepcopy(value) for field, value in base.items() if field not in ('tracks', 'independent_review_receipt')}
entry.update(tracks=tracks, replace_existing_tracks=False,
             completeness={'status': 'partial_supplement', 'verified_supplemental_recordings': 11,
                           'requires_base_archival_recordings': 331, 'candidate_union_recordings': 342,
                           'expected_published_album_tracks_secondary': 348, 'all_game_music_complete': False},
             recording_collection_scope='Supplemental11 distinct game-score loop publications, explicitly longer than the edited Nintendo Music versions. No fabricated time cuts or edited-album completeness claim.')
candidate = {'schema_version': 1, 'publication_status': 'awaiting_independent_review', 'entries': [entry],
             'requires_base_module_sha256': hashlib.sha256(module_path.read_bytes()).hexdigest()}
destination = OUT / 'mkworld-distinct11-long-loop-versions-candidate.json'
destination.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
report = {'status': 'AWAITING_INDEPENDENT_REVIEW', 'candidate_sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
          'distinct_game_score_publications': 11, 'all_native_avc_aac': True,
          'source_scope': 'Actual public titles/authors/durations plus native metadata; descriptions are genuinely empty and not fabricated. Original Nintendo sound-team credit remains collection/game level, not proof of individual cue authorship.',
          'edited_nintendo_music_master_equivalence': False, 'physical_ps5_playback_verified': False,
          'requires_independent_original_score_identity_review': True, 'checks': checks}
(OUT / 'mkworld-distinct11-long-loop-versions-editorial-review.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({field: value for field, value in report.items() if field != 'checks'}))
