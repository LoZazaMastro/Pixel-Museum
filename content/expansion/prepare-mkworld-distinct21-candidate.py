"""Freeze 21 clearly distinct battle/fanfare/menu cues, not an album claim."""
import copy
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/nintendo-full'
load = lambda p: json.loads(p.read_text(encoding='utf-8'))
base = load(OUT / 'mkworld253-clean-original-archive-candidate.json')
old = base['entries'][0]
assert len(old['tracks']) == 253
rows = load(OUT / 'mkworld-inventory-exact-gaps-publication-research.json')['tracks']
fallback = {row['source']['id']: row for row in load(OUT / 'mkworld-inventory-exact-gaps-public-oembed-fallback-research.json')['tracks']}
expected = {row['number']: row for row in load(OUT / 'mkworld-nintendo-music-secondary-inventory.json')['tracks']}
selected_numbers = {73, *range(75, 83), *range(94, 102), 111, 112, 118, 119}
tracks, checks = [], []
for initial in rows:
    if initial['album_track_number'] not in selected_numbers:
        continue
    row = fallback.get(initial['source']['id'], initial)
    assert row['status'] == 'metadata_candidate'
    publication, source = row['publication'], row['source']
    number = row['album_track_number']
    inventory = expected[number]
    native = load(ROOT / row['native_codec_receipt'])
    assert native['native_compatible_avc_aac'] and native.get('avc_format_count') and native.get('aac_format_count')
    duration = float(publication['lengthSeconds'])
    difference = abs(duration - inventory['length_seconds'])
    assert difference <= 3 or (number == 75 and duration == 276 and inventory['length_seconds'] == 280)
    assert publication['title'] == source['title'] and publication['author'] == 'Mario Kart Music Channel'
    assert 'Mario Kart World Soundtrack' in publication['title']
    record = copy.deepcopy(old['tracks'][0])
    video_id = source['id']
    record.update(
        youtube_id=video_id, url='https://www.youtube.com/watch?v=' + video_id,
        source_page='https://www.youtube.com/watch?v=' + video_id,
        title=re.sub(r'\s*\[\s*[a-z]\s*\]', '', inventory['title']),
        uploader=publication['author'], channel_url='https://www.youtube.com/channel/' + source['channel_id'],
        primary_published_title=publication['title'], duration_seconds=duration,
        recording_context_source='https://www.youtube.com/playlist?list=PLZ9xtCtT5SXlzgmYuY32LOtcV959wH8jT',
        native_codec_metadata_receipt=row['native_codec_receipt'],
        publication_metadata_receipt=row.get('publication_metadata_receipt') or 'build/research/soundtrack-broad/watch/' + video_id + '.json',
        inventory_title_source='https://www.mariowiki.com/Mario_Kart_World_(Nintendo_Music)',
        inventory_source_kind='Community transcription of the Nintendo Music edited release; not an authenticated publisher metadata endpoint.',
        inventory_track_number=number,
    )
    if number == 75:
        record['recording_version'] += ' Battle Course (Super Mario Kart) is a276-second game-archive version; the later edited Nintendo Music listing is280 seconds. It is not asserted to be the same released master or fade.'
    assert (ROOT / record['publication_metadata_receipt']).exists()
    tracks.append(record)
    checks.append({'number': number, 'title': record['title'], 'youtube_id': video_id,
                   'inventory_duration': inventory['length_seconds'], 'publication_duration': duration,
                   'difference_seconds': abs(duration - inventory['length_seconds']),
                   'actual_publication_title': publication['title'], 'native_avc_aac': True})
assert len(tracks) == 21
assert not ({track['youtube_id'] for track in tracks} & {track['youtube_id'] for track in old['tracks']})
entry = {key: copy.deepcopy(value) for key, value in old.items() if key != 'tracks'}
entry.update(tracks=tracks, replace_existing_tracks=False,
             recording_collection_scope='Supplemental21 distinct battle-course, start/finish fanfare and menu cues. Requires the separately frozen253 archive checkpoint for a274-recording partial union; not a complete348-track album.')
entry['completeness'] = {
    'status': 'partial_supplement', 'verified_supplemental_recordings': 21,
    'requires_base_archival_recordings': 253, 'candidate_union_recordings': 274,
    'expected_published_album_tracks_secondary': 348,
    'all_game_music_complete': False,
}
candidate = {'schema_version': 1, 'publication_status': 'awaiting_independent_review',
             'requires_base_candidate_sha256': '5053224e5fa05acd0a4c701c97a90c2f6f425af2a1986972adf4882d80547271',
             'entries': [entry]}
destination = OUT / 'mkworld-distinct21-battle-fanfare-candidate.json'
destination.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
report = {'status': 'AWAITING_INDEPENDENT_REVIEW', 'candidate_sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
          'distinct_cues': 21, 'all_native_avc_aac': True, 'checks': checks,
          'scope': '21 individually named distinct cues. No whole album, audio-fingerprint or physical console playback assertion.'}
(OUT / 'mkworld-distinct21-battle-fanfare-editorial-review.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({key: value for key, value in report.items() if key != 'checks'}))
