"""Replace uncertain BOTW album passages with independently sourced full cues.

Freeze for independent review only. Duration agreement is metadata evidence,
never an audio fingerprint or proof of a byte-identical publisher CD master.
"""
import copy
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/nintendo-full'
original_path = OUT / 'botw-211-boundary-review-candidate.json'
original = json.loads(original_path.read_text(encoding='utf-8'))
research = json.loads((OUT / 'botw126-cd-individual-publication-research.json').read_text(encoding='utf-8'))['tracks']
assert len(research) == 126
cd = [t for medium in json.loads((OUT / 'botw-cd-english-translated-inventory.json').read_text(encoding='utf-8'))['media'] for t in medium['tracks']]
entry = copy.deepcopy(original['entries'][0])
tracks = entry['tracks']
reviewed = []
holds = []
for row in research:
    n = row['album_track_number']
    if row['status'] != 'metadata_candidate':
        holds.append({'track': n, 'youtube_id': row['source']['id'], 'reason': row.get('error') or row['status'], 'fallback': 'Previously timestamped same-cue archive passage; retained only if not among the duration review flags.'})
        continue
    watch = row['publication']
    native = json.loads((ROOT / row['native_codec_receipt']).read_text(encoding='utf-8'))
    assert native['native_compatible_avc_aac']
    assert abs(float(watch['lengthSeconds']) - cd[n - 1]['length'] / 1000) <= 3
    t = tracks[n - 1]
    assert t['album_track_number'] == n and t['title'] == row['title']
    video_id = row['source']['id']
    for key in ('start_seconds', 'end_seconds', 'archival_published_cue_label'):
        t.pop(key, None)
    t.update(
        youtube_id=video_id,
        url='https://www.youtube.com/watch?v=' + video_id,
        source_page='https://www.youtube.com/watch?v=' + video_id,
        uploader=watch['author'], channel_url='https://www.youtube.com/channel/' + watch['channelId'],
        duration_seconds=float(watch['lengthSeconds']),
        recording_version='Individual archival same-game score recording, matched to the published2018album cue identity and duration. Capture hardware and CD-master identity are not independently established.',
        primary_published_title=watch['title'],
        native_codec_metadata_receipt=row['native_codec_receipt'],
        publication_metadata_receipt=f'build/research/soundtrack-broad/watch/{video_id}.json',
    )
    reviewed.append({'album_track_number': n, 'title': t['title'], 'youtube_id': video_id,
                     'actual_published_title': watch['title'], 'expected_seconds': cd[n - 1]['length'] / 1000,
                     'actual_seconds': float(watch['lengthSeconds']), 'native_avc_aac': True,
                     'actual_description': watch['shortDescription']})

fixed = {r['album_track_number'] for r in reviewed}
flagged = {r['track'] for r in original['duration_review_flags']}
assert flagged <= fixed, ('Unresolved former duration flags', flagged - fixed)
assert 137 in fixed  # The unreliable supplemental upload is removed entirely.
assert not any(t['youtube_id'] == 'eV3lW-l9SFE' for t in tracks)
remaining_passages = []
for t in tracks:
    n = t['album_track_number']
    native = json.loads((ROOT / t['native_codec_metadata_receipt']).read_text(encoding='utf-8'))
    assert native['native_compatible_avc_aac']
    if 'start_seconds' in t:
        assert t['youtube_id'] == 'zncStfmvIA4'
        delta = t['duration_seconds'] - cd[n - 1]['length'] / 1000
        assert abs(delta) <= 7
        remaining_passages.append({'track': n, 'title': t['title'], 'start_seconds': t['start_seconds'],
                                   'end_seconds': t['end_seconds'], 'published_cd_seconds': cd[n - 1]['length'] / 1000,
                                   'duration_delta_seconds': delta, 'chapter_as_published': t['archival_published_cue_label']})
assert len(tracks) == 211
assert [t['album_track_number'] for t in tracks] == list(range(1, 212))
entry.update(full_album_collection=True, album_completeness={
    'expected_tracks': 211,
    'source': 'Published2018Nintendo/Columbia211-composition original-game album inventory, including its labelled DLC and trailer compositions; actual individual recordings or explicitly published archival chapter passages. Not a CD-master fingerprint assertion.',
    'inventory_receipt': 'build/research/soundtrack-broad/nintendo-full/botw211-repaired-editorial-review.json',
})
candidate = {'schema_version': 1, 'publication_status': 'awaiting_independent_review', 'entries': [entry],
             'scope': 'Complete211published-composition inventory candidate, with all13formerly ambiguous duration passages and the missing137cue replaced by individually verified full-duration archival recordings. No listening/fingerprint/physicalPS5playback assertion.'}
destination = OUT / 'botw211-repaired-individual-hybrid-candidate.json'
destination.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
review = {'status': 'awaiting_independent_review', 'candidate_sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
          'expected_tracks': 211, 'individual_recordings': len(reviewed), 'actual_timestamped_passages': len(remaining_passages),
          'former13_duration_flags_all_replaced': True, 'removed_unreliable_supplement': True,
          'replaced_flag_track_numbers': sorted(flagged), 'individuals': reviewed, 'passages': remaining_passages,
          'alternate_candidates_held': holds,
          'remaining_limitations': ['Published chapter labels and duration agreement are metadata identity evidence; no listening/audio-fingerprint assertion.', 'Archival game-score recordings are not falsely labelled Nintendo publisher uploads or proven byte-identical CDmasters.', 'Some continuous game recordings may differ in fade/tail or adaptive arrangement from the commercial album, as disclosed.']}
(OUT / 'botw211-repaired-editorial-review.json').write_text(json.dumps(review, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('FREEZE211', review['candidate_sha256'], 'individual', len(reviewed), 'passages', len(remaining_passages))
