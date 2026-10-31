"""Freeze actual newly sourced intros, laps and core cues for independent peer."""
import copy
import hashlib
import json
import pathlib
import re
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/nintendo-full'
load = lambda p: json.loads(p.read_text(encoding='utf-8'))


def key(text):
    text = re.sub(r'\s*[-\u2014]\s*Mario Kart World OST$', '', text)
    text = re.sub(r'\[\s*[a-z]\s*\]', '', text)
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode().lower())


module_path = ROOT / 'content/expansion/soundtrack-multitrack-priority-overrides.json'
base = next(entry for entry in load(module_path)['entries'] if entry['entry_id'] == 'wikipedia-79613463')
assert len(base['tracks']) == 274
base_keys = {key(track['title']) for track in base['tracks']}
# Already independently reviewed replay names identify these same two cues.
base_keys.update({key('DK Spaceport'), key('Rainbow Road (Finale)')})
inventory = load(OUT / 'mkworld-nintendo-music-secondary-inventory.json')['tracks']
by_title = {key(row['title']): row for row in inventory}
fallbacks = {row['source']['id']: row for row in load(OUT / 'mkworld-koopasaurus-core-public-oembed-fallback-research.json')['tracks']}
tracks, checks = [], []
for initial in load(OUT / 'mkworld-koopasaurus-core-archive-publication-research.json')['tracks']:
    row = fallbacks.get(initial['source']['id'], initial)
    assert row['status'] == 'metadata_candidate'
    actual = row['publication']
    title = re.sub(r'\s*-\s*Mario Kart World OST$', '', actual['title'])
    if key(title) in base_keys:
        continue
    expected = by_title[key(title)]
    duration = float(actual['lengthSeconds'])
    assert abs(duration - expected['length_seconds']) <= 3
    video_id = row['source']['id']
    native = load(ROOT / row['native_codec_receipt'])
    assert native['native_compatible_avc_aac'] and native.get('avc_format_count') and native.get('aac_format_count')
    assert actual['author'] == 'Koopasaurus' and actual['title'] == row['source']['title']
    record = copy.deepcopy(base['tracks'][0])
    record.update(
        youtube_id=video_id, url='https://www.youtube.com/watch?v=' + video_id,
        source_page='https://www.youtube.com/watch?v=' + video_id,
        title=re.sub(r'\s*\[\s*[a-z]\s*\]', '', expected['title']),
        uploader='Koopasaurus', channel_url='https://www.youtube.com/channel/UCUdI_-cax8sRsplbrldQbJA',
        primary_published_title=actual['title'], duration_seconds=duration,
        recording_context_source='https://www.youtube.com/channel/UCUdI_-cax8sRsplbrldQbJA/videos',
        recording_version='2025 game composition, archival publication. Actual available descriptions identify Nintendo Music as the recording source; matching title/order/duration does not certify publisher endorsement or bit-identical masters.',
        native_codec_metadata_receipt=row['native_codec_receipt'],
        publication_metadata_receipt=row.get('publication_metadata_receipt') or 'build/research/soundtrack-broad/watch/' + video_id + '.json',
        inventory_track_number=expected['number'],
        inventory_title_source='https://www.mariowiki.com/Mario_Kart_World_(Nintendo_Music)',
        inventory_source_kind='Community transcription of the Nintendo Music release, not an authenticated publisher metadata endpoint.',
    )
    assert (ROOT / record['publication_metadata_receipt']).exists()
    tracks.append(record)
    checks.append({'youtube_id': video_id, 'title': record['title'], 'inventory_number': expected['number'],
                   'inventory_duration': expected['length_seconds'], 'publication_duration': duration,
                   'duration_difference_seconds': abs(duration - expected['length_seconds']),
                   'actual_description_present': bool(actual.get('shortDescription')),
                   'actual_description_declares_nintendo_music_source': 'taken directly from the Nintendo Music website' in actual.get('shortDescription', '')})
assert len(tracks) == 57
assert not ({track['youtube_id'] for track in tracks} & {track['youtube_id'] for track in base['tracks']})
entry = {field: copy.deepcopy(value) for field, value in base.items() if field not in ('tracks', 'independent_review_receipt')}
entry.update(tracks=tracks, replace_existing_tracks=False,
             recording_collection_scope='Supplemental57 distinct intros, race-lap phases, title/menu/opening and victory cues. Requires the separately reviewed274-recording base for a331-recording partial union; not a complete348-track edited album.',
             completeness={'status': 'partial_supplement', 'verified_supplemental_recordings': 57,
                           'requires_base_archival_recordings': 274, 'candidate_union_recordings': 331,
                           'expected_published_album_tracks_secondary': 348, 'all_game_music_complete': False})
candidate = {'schema_version': 1, 'publication_status': 'awaiting_independent_review', 'entries': [entry],
             'requires_base_module_sha256': hashlib.sha256(module_path.read_bytes()).hexdigest()}
destination = OUT / 'mkworld-distinct57-core-candidate.json'
destination.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
report = {'status': 'AWAITING_INDEPENDENT_REVIEW', 'candidate_sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
          'new_distinct_cues': 57, 'all_native_avc_aac': True, 'checks': checks,
          'scope': 'Actual public source identity/title/duration/native only. Per-cue arranger/individual composition not guessed; collective game-level Nintendo staff retained. No audio fingerprint or physical console playback assertion.'}
(OUT / 'mkworld-distinct57-core-editorial-review.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({field: value for field, value in report.items() if field != 'checks'}))
