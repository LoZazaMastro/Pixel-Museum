"""Preserve real public source chapter boundaries; never invent unindexed tails."""
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/nintendo-full'
load = lambda path: json.loads(path.read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
credit_url = 'https://www.mariowiki.com/List_of_Super_Mario_Maker_2_staff'
feature_url = 'https://play.nintendo.com/news-tips/tips-tricks/super-mario-maker-2-tips-tricks/'
roles = {'music': ['Atsuko Asahi', 'Toru Minegishi', 'Sayako Doi'],
         'sound_director': ['Koji Kondo'], 'sound_adviser': ['Koichi Kyuma']}
credit_receipt = {'publication_status': 'research_only', 'sources': [
    {'url': credit_url, 'actual_web_page_read': True,
     'source_type': 'Transcription of original Nintendo Switch game staff roll',
     'game_level_music_roles': roles},
    {'url': feature_url, 'actual_web_page_read': True, 'source_type': 'Nintendo publisher game guide',
     'verified_context': 'Night themes add music; the Soundfrog feature includes music/sound effects from other Mario games; Super Mario 3D World is a distinct supported game style.'}],
    'credit_scope': 'Collective game-level Nintendo credit, including legacy Mario themes. Original staff music/direction/adviser roles are preserved separately; no allocation of every cue to every staff member. Uploader typo Asashi is not propagated.'}
credit_path = OUT / 'mariomaker2-original-game-role-web-read-receipt.json'
credit_path.write_text(json.dumps(credit_receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
tracks, holds, source_receipts = [], [], []
for video_id, expected_count, safe_last in [('LDfHgbdtkVY', 111, False), ('f6Rrpk7Kqrg', 132, False), ('PQYOM8R3SX0', 41, True)]:
    path = OUT / (video_id + '-actual-publication-research.json')
    receipt = load(path)
    pub = receipt['publication']
    assert receipt['native_avc_aac'] is True
    assert pub['author'] == 'Philip J. Fry II' and 'Super Mario Maker 2 OST Disc' in pub['title']
    assert load(ROOT / receipt['native_codec_receipt'])['native_compatible_avc_aac'] is True
    markers, section = [], None
    for line in pub['shortDescription'].splitlines():
        if re.fullmatch(r'\[.+\]', line.strip()):
            section = line.strip()[1:-1]
        match = re.match(r'^\s*(\d+:\d{2}:\d{2})\s+(\d+)\.\s*(.+?)\s*$', line)
        if not match:
            continue
        timestamp, number, title = match.groups()
        seconds = 0
        for part in timestamp.split(':'):
            seconds = seconds * 60 + int(part)
        markers.append({'number': int(number), 'title': title, 'start_seconds': seconds,
                        'source_line': line, 'section': section})
    assert len(markers) == expected_count
    assert [row['number'] for row in markers] == list(range(1, expected_count + 1))
    duration = float(pub['lengthSeconds'])
    for index, marker in enumerate(markers):
        if index + 1 == len(markers) and not safe_last:
            holds.append({'youtube_id': video_id, 'marker': marker, 'reason': 'Last indexed chapter has over one hour of unindexed source tail. No cue end is inferred from the full-video duration.'})
            continue
        end = markers[index + 1]['start_seconds'] if index + 1 < len(markers) else duration
        assert 0 <= marker['start_seconds'] < end <= duration
        if marker['title'] == '10 Mario Challenge':
            holds.append({'youtube_id': video_id, 'marker': marker, 'reason': 'Legacy/unused identity is unclear for this sequel. Not admitted merely because collector places it in the second game playlist.'})
            continue
        title = marker['title'] if marker['section'] == 'Super Mario Maker 2' else marker['section'] + ': ' + marker['title']
        tracks.append({'youtube_id': video_id, 'url': 'https://www.youtube.com/watch?v=' + video_id,
                       'source_page': 'https://www.youtube.com/watch?v=' + video_id,
                       'title': title, 'creator': 'Nintendo sound team', 'composer_source': credit_url,
                       'game_level_music_roles': roles,
                       'artist_credit_scope': credit_receipt['credit_scope'],
                       'start_seconds': marker['start_seconds'], 'end_seconds': end,
                       'duration_seconds': end-marker['start_seconds'],
                       'source_actual_chapter_line': marker['source_line'],
                       'source_game_style': marker['section'],
                       'source_publication_duration_seconds': duration,
                       'uploader': pub['author'], 'channel_url': 'https://www.youtube.com/channel/' + pub['channelId'],
                       'primary_published_title': pub['title'], 'official_uploader_verified': False,
                       'publishing_kind': 'archival_game_recording',
                       'recording_version': 'Super Mario Maker 2 Nintendo Switch archive: ' + marker['section'] + ' game-style music and named play/editor/night variants. Collector part, not an official CD release or certified album master.',
                       'recording_platform': 'Nintendo Switch',
                       'rights': 'Nintendo and credited original and legacy Mario music authors, arrangers and performers; Philip J. Fry II is an archival uploader.',
                       'native_codec_metadata_verified': True,
                       'native_codec_metadata_receipt': receipt['native_codec_receipt'],
                       'publication_metadata_receipt': path.relative_to(ROOT).as_posix(),
                       'playback_verified_on_ps5': False})
    source_receipts.append({'local_path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)})
assert len(tracks) == 281 and len(holds) == 3
assert len({(t['youtube_id'], t['start_seconds'], t['end_seconds']) for t in tracks}) == 281
entry = {'entry_id': 'wikipedia-59947382', 'match_title': 'Super Mario Maker 2', 'match_year': 2019,
         'title': 'Listen to Super Mario Maker 2', 'composer': 'Nintendo sound team',
         'curator_note': 'Listen to the music of Nintendo sound team\nSuper Mario Maker 2',
         'replace_existing_tracks': True, 'full_album_collection': False, 'coverage_status': 'partial',
         'recording_collection_scope': '281 available real source-indexed game-score passages from three archival collector parts. Missing unindexed tails and an unclear legacy/unused challenge cue remain excluded. Not a complete official album or exhaustive game-stem inventory.',
         'album_completeness': {'verified_available_tracks': 281, 'held_source_passages': 3,
                                'scope': 'Available public score and game-style variants, with real source boundaries; no audio-identical or physical console-playback claim.'},
         'tracks': tracks}
result = {'schema_version': 1, 'publication_status': 'awaiting_independent_peer', 'entries': [entry],
          'held_source_passages': holds,
          'source_receipts': source_receipts + [{'local_path': credit_path.relative_to(ROOT).as_posix(), 'sha256': sha(credit_path)}],
          'scope': 'Useful available public originals without chasing complete album order. All boundaries are literal source timestamps or the credible indexed end of Disc3; no fabricated segmentation of Disc1/2 tails.'}
target = OUT / 'mariomaker2-available281-public-candidate.json'
assert not target.exists(), 'Immutable checkpoint exists'
target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'candidate': target.relative_to(ROOT).as_posix(), 'sha256': sha(target), 'selectable_tracks': len(tracks)}))
