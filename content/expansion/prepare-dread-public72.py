"""MetroidDread real archival score chapters with role-aware collective credit."""
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/nintendo-full'
load = lambda path: json.loads(path.read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
video_id = 'nQXjGlRUwLo'
receipt_path = OUT / (video_id + '-actual-publication-research.json')
receipt = load(receipt_path)
pub = receipt['publication']
assert receipt['native_avc_aac'] is True and pub['author'] == 'SoundTracks'
assert pub['title'] == 'Metroid Dread Original SoundTrack'
assert load(ROOT / receipt['native_codec_receipt']).get('native_compatible_avc_aac') is True
credit_url = 'https://www.mobygames.com/game/172841/metroid-dread/credits/switch/'
credit_receipt_path = OUT / 'dread-original-staff-role-web-read-receipt.json'
credit_receipt = {'url': credit_url, 'actual_web_page_read': True,
                  'source_type': 'Transcription of original2021 NintendoSwitch staff credits, corroborated by Wikitroid and Nintendo staff-roll transcriptions.',
                  'game_level_music_roles': {'music_and_arrangement': ['Soshi Abe', 'Sayako Doi'],
                                             'music_director': ['Kenji Yamamoto'],
                                             'original_metroid_music': ['Kenji Yamamoto'],
                                             'sound_coordination': ['Minako Hamano']},
                  'scope': 'Roles retained separately. Uploader generic Artists line is not used to recast the director as composer of every individual cue.'}
credit_receipt_path.write_text(json.dumps(credit_receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
markers = []
for line in pub['shortDescription'].splitlines():
    match = re.match(r'^\s*(\d+)\s+(.+?)\s+(\d{1,2}:\d{2}(?::\d{2})?)\s*$', line)
    if not match:
        continue
    number, title, timestamp = match.groups()
    start = 0
    for part in timestamp.split(':'):
        start = start * 60 + int(part)
    markers.append({'number': int(number), 'title': title, 'start_seconds': start, 'source_line': line})
assert len(markers) == 72 and [row['number'] for row in markers] == list(range(1, 73))
tracks = []
for index, marker in enumerate(markers):
    end = markers[index + 1]['start_seconds'] if index + 1 < len(markers) else float(pub['lengthSeconds'])
    assert 0 <= marker['start_seconds'] < end <= float(pub['lengthSeconds'])
    tracks.append({'youtube_id': video_id, 'url': 'https://www.youtube.com/watch?v=' + video_id,
                   'source_page': 'https://www.youtube.com/watch?v=' + video_id,
                   'title': marker['title'], 'creator': 'Nintendo sound team',
                   'composer_source': credit_url,
                   'game_level_music_roles': credit_receipt['game_level_music_roles'],
                   'artist_credit_scope': 'Collective original-game score credit. SoshiAbe/SayakoDoi music-and-arrangement and KenjiYamamoto direction/legacy-theme roles retained distinctly at game level; no unsupported per-cue writer allocation.',
                   'start_seconds': marker['start_seconds'], 'end_seconds': end,
                   'duration_seconds': end-marker['start_seconds'],
                   'source_actual_chapter_line': marker['source_line'], 'source_publication_duration_seconds': float(pub['lengthSeconds']),
                   'uploader': pub['author'], 'channel_url': 'https://www.youtube.com/channel/' + pub['channelId'],
                   'primary_published_title': pub['title'], 'official_uploader_verified': False,
                   'publishing_kind': 'archival_game_recording',
                   'recording_version': 'Metroid Dread original2021 NintendoSwitch game-score archive, with source-named stage/encounter variants. Not an official publisher upload or certified edited album master.',
                   'recording_year': 2021, 'recording_platform': 'Nintendo Switch',
                   'rights': 'Nintendo / MercurySteam and credited music authors, arrangers and performers; SoundTracks is an archival uploader.',
                   'native_codec_metadata_verified': True, 'native_codec_metadata_receipt': receipt['native_codec_receipt'],
                   'publication_metadata_receipt': receipt_path.relative_to(ROOT).as_posix(),
                   'playback_verified_on_ps5': False})
entry = {'entry_id': 'wikipedia-2369138', 'match_title': 'Metroid Dread', 'match_year': 2021,
         'title': 'Listen to Metroid Dread', 'composer': 'Nintendo sound team',
         'curator_note': 'Listen to the music of Nintendo sound team\nMetroid Dread',
         'replace_existing_tracks': True, 'full_album_collection': False, 'coverage_status': 'partial',
         'recording_collection_scope': '72 available source-declared archive passages, with actual timestamp boundaries and role-aware game-level credits. Not all possible game stems or a certified NintendoMusic edited-album inventory.',
         'album_completeness': {'verified_available_tracks': 72,
                                'inventory_source': 'https://www.youtube.com/watch?v=' + video_id,
                                'scope': 'Available original-game archival collection; no commercial-master completeness or audio-identical certification.'},
         'tracks': tracks}
result = {'schema_version': 1, 'publication_status': 'awaiting_independent_peer', 'entries': [entry],
          'source_receipts': [{'local_path': credit_receipt_path.relative_to(ROOT).as_posix(), 'sha256': sha(credit_receipt_path)}],
          'scope': '72 selectable real public original-game passages, nativeAVC/AAC; no audio fingerprint or physical-console playback assertion.'}
target = OUT / 'dread72-available-public-candidate.json'
assert not target.exists(), 'Immutable checkpoint exists'
target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'candidate': target.relative_to(ROOT).as_posix(), 'sha256': sha(target), 'selectable_tracks': 72}))
