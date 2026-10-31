"""Freeze two source-bound music rooms; never download audio or admit data."""
from pathlib import Path
import hashlib
import json
import re
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'build/research/soundtrack-broad/modern-next-four'
load = lambda path: json.loads(path.read_text(encoding='utf8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
def seconds(value):
    total = 0
    for part in value.split(':'):
        total = total * 60 + int(part)
    return total

plans = [
    ('wikipedia-15676843', 'Tetris Effect', 2018, 'gL1FR5C8LOs', 'Hydelic', True),
    ('wikipedia-50574101', 'Resident Evil 7: Biohazard', 2017, 'exdVWe9J6Mw', 'Capcom Sound Team and contributing musicians', False),
]
sources = []
entries = []
label = load(FOLDER / 'resident-evil-seven-label-metadata.json')
album = label['results'][0]
published = {r['trackNumber']: r for r in label['results'][1:]}
assert len(published) == 81 and album['collectionId'] == 1193905100
primary = (FOLDER / 'tetris-original-2020-official.html').read_text(encoding='utf8')
assert 'UCtswPJbKycCoSBo_3K2ZReA' in primary and '40 songs' in primary
for identifier, game, year, video_id, credit, official in plans:
    watch_path = ROOT / 'build/research/soundtrack-broad/watch' / (video_id + '.json')
    metadata_path = FOLDER / ('native-' + video_id + '.json')
    watch, native = load(watch_path), load(metadata_path)
    assert native['native_compatible_avc_aac'] and watch['channelId'] == native['channel_id']
    assert watch['title'] == native['title'] and float(watch['lengthSeconds']) == native['duration']
    chapters = []
    for line in watch['shortDescription'].splitlines():
        if official:
            match = re.match(r'^(\d+(?::\d+){1,2})\s+(.+)$', line)
            if match: chapters.append((seconds(match[1]), match[2].strip(), line))
        else:
            match = re.match(r'^(\d+)\.\s*(.*?)\s*(?:\|\s*)?(\d+(?::\d+){1,2})\s*$', line)
            if match:
                assert int(match[1]) == len(chapters) + 1
                chapters.append((seconds(match[3]), match[2].strip().rstrip('|').strip(), line))
    assert len(chapters) == (40 if official else 81)
    assert chapters[0][0] == 0
    tracks = []
    for number, (start, source_title, line) in enumerate(chapters, 1):
        end = chapters[number][0] if number < len(chapters) else int(native['duration'])
        assert start < end <= int(native['duration'])
        title = source_title if official else published[number]['trackName']
        artist = 'Hydelic' if official else published[number]['artistName']
        track = {
            'youtube_id': video_id, 'url': 'https://www.youtube.com/watch?v=' + video_id,
            'title': title, 'creator': artist,
            'source_actual_chapter_title': source_title, 'source_actual_chapter_line': line,
            'start_seconds': start, 'end_seconds': end, 'duration_seconds': end - start,
            'source_publication_duration_seconds': int(native['duration']),
            'recording_album': 'Tetris Effect (Original Soundtrack)' if official else album['collectionName'],
            'recording_album_release_year': 2020 if official else 2017,
            'original_game_year': year,
            'recording_version': 'Hydelic official original soundtrack publication.' if official else 'Original 2017 soundtrack archival passage, including the album\'s Beginning Hour and VR Tutorial cues.',
            'uploader': native['channel'], 'channel_url': 'https://www.youtube.com/channel/' + native['channel_id'],
            'source_page': 'https://www.youtube.com/watch?v=' + video_id,
            'publishing_kind': 'official_game_recording' if official else 'archival_game_recording',
            'official_uploader_verified': official,
            'composer_source': 'https://www.tetriseffect.game/2020/05/28/1208/' if official else 'https://music.apple.com/us/album/resident-evil-7-biohazard-original-soundtrack/1193905100',
            'artist_credit_scope': 'Original music by Hydelic, as credited by the game publisher.' if official else 'Exact label-delivered recording artist credit preserved; not an invented composer/performer role allocation.',
            'rights': 'Enhance, Hydelic and the original music contributors retain their respective rights.' if official else 'Capcom and the credited composition, performance and recording contributors retain their respective rights. Archival uploader is not an official publisher delivery.',
            'publication_metadata_receipt': watch_path.relative_to(ROOT).as_posix(),
            'native_codec_metadata_receipt': metadata_path.relative_to(ROOT).as_posix(),
            'native_codec_metadata_verified': True, 'playback_verified_on_ps5': False,
        }
        if not official:
            track['published_album_track_number'] = number
            track['label_artist_credit'] = artist
            track['title_display_scope'] = 'Label title, with actual archive chapter title retained separately; no retail-master equivalence claim.'
        tracks.append(track)
    entries.append({'entry_id': identifier, 'match_title': game, 'match_year': year,
                    'title': 'Listen to ' + game, 'composer': credit,
                    'curator_note': 'Listen to the music of ' + credit + ' from ' + game + '.',
                    'replace_existing_tracks': True, 'full_album_collection': official,
                    'coverage_status': 'OFFICIAL_ORIGINAL_ALBUM_40_PASSAGES' if official else 'AVAILABLE_81_ORIGINAL_ALBUM_ARCHIVAL_PASSAGES',
                    'album_completeness': {'published_title_inventory': len(tracks), 'available_passages': len(tracks),
                        'qualification': 'Official full 40-song original album; this is the original game soundtrack, not the later Connected Volume 2.' if official else '81 label-listed titles matched to actual public archive chapter ordinals. No exact retail audio-master, fingerprint or every-game-file completeness claim.'},
                    'tracks': tracks})
    for path in [watch_path, metadata_path]:sources.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)})
for filename in ['tetris-original-2020-official.html', 'resident-evil-seven-steam-publisher.json', 'resident-evil-seven-label-metadata.json']:
    path = FOLDER / filename
    sources.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)})
candidate = {'schema_version': 1, 'publication_status': 'candidate_pending_independent_review',
             'scope': 'Two previously unscored game entries: official Hydelic40 original soundtrack and81 publicly available original Resident Evil7 album chapters. All real start/end boundaries retained; no audio media download or PS5 playback claim.',
             'entries': entries, 'source_receipts': sources,
             'checked_utc': datetime.now(timezone.utc).isoformat(),
             'catalog_or_source_music_changed': False, 'audio_downloaded': False}
path = FOLDER / 'tetris40-resident-evil-seven81-public-collections-candidate.json'
path.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(json.dumps({'candidate': path.relative_to(ROOT).as_posix(), 'sha256': sha(path), 'rooms': len(entries), 'tracks': sum(len(e['tracks']) for e in entries)}))
