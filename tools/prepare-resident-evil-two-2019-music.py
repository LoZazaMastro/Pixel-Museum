"""Freeze available original 2019 album passages, not the 1998 game score."""
from pathlib import Path
import hashlib
import html
import json
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
F = ROOT / 'build/research/soundtrack-broad/modern-following'
load = lambda p: json.loads(p.read_text(encoding='utf8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
identifier = 'MJcCyOD62M8'
watch_path = ROOT / 'build/research/soundtrack-broad/watch' / (identifier + '.json')
native_path = ROOT / 'build/research/video-discovery' / ('video-' + identifier + '.json')
label_path = F / 're2-2019-label-album.json'
watch, native, label = load(watch_path), load(native_path), load(label_path)
album, published = label['results'][0], label['results'][1:]
assert album['collectionId'] == 1451575319 and album['trackCount'] == len(published) == 59
assert album['releaseDate'].startswith('2019-02-25')
assert native['native_compatible_avc_aac'] and native['title'] == watch['title']
assert watch['channelId'] == native['channel_id'] and float(watch['lengthSeconds']) == native['duration']
primary = 'https://prtimes.jp/main/html/rd/p/000000454.000013450.html'
saudade = 'https://emperiasound.com/resident-evil/'
assert '59' in (F / 're2-capcom-release.html').read_text(encoding='utf8')
assert 'Cody Matthew Johnson' in (F / 're2-saudade-creator.html').read_text(encoding='utf8')

def seconds(value):
    result = 0
    for part in value.split(':'):
        result = result * 60 + int(part)
    return result

def normalize(value):
    return re.sub('[^a-z0-9]', '', unicodedata.normalize('NFKC', value).lower())

chapters = []
for line in watch['shortDescription'].splitlines():
    match = re.match(r'(.+?)\s+-\s+(\d+(?::\d+){1,2})\s*$', line)
    if match:
        chapters.append((match[1], seconds(match[2]), line))
assert len(chapters) == 59 and chapters[0][1] == 0
tracks = []
for number, ((title, start, line), song) in enumerate(zip(chapters, published), 1):
    assert song['trackNumber'] == number and normalize(title) == normalize(song['trackName'])
    end = chapters[number][1] if number < len(chapters) else int(native['duration'])
    assert 0 <= start < end <= int(native['duration'])
    tracks.append({
        'youtube_id': identifier, 'url': 'https://www.youtube.com/watch?v=' + identifier,
        'title': song['trackName'],
        'creator': 'Cody Matthew Johnson feat. Shim' if number == 1 else 'Capcom Sound Team',
        'label_artist_credit': song['artistName'],
        'artist_credit_scope': ('Composer/performer spelling from the creator studio\'s own song page; raw label artist string retained without its duplicated delivery text.' if number == 1 else
            'Collective album artist display. Individual label artist credit is preserved in the source record; no assertion that every contributor composed every cue.'),
        'uploader': watch['author'], 'channel_url': 'https://www.youtube.com/channel/' + watch['channelId'],
        'source_page': 'https://www.youtube.com/watch?v=' + identifier,
        'composer_source': saudade if number == 1 else song['trackViewUrl'],
        'published_album_track_number': number,
        'recording_album': 'Resident Evil 2 (2019) Original Soundtrack',
        'recording_album_release_year': 2019, 'original_game_year': 2019,
        'recording_version': 'Public archival passages of the 2019 remake soundtrack, matched to the original 59-title digital album; not the 1998 soundtrack or an exact retail audio-master claim.',
        'source_actual_chapter_title': title, 'source_actual_chapter_line': line,
        'start_seconds': start, 'end_seconds': end, 'duration_seconds': end - start,
        'source_publication_duration_seconds': int(native['duration']),
        'publishing_kind': 'archival_game_recording', 'official_uploader_verified': False,
        'rights': 'Capcom and the credited music composers, arrangers, performers and recording owners retain their respective rights. The archival uploader is not an official publisher delivery.',
        'publication_metadata_receipt': watch_path.relative_to(ROOT).as_posix(),
        'native_codec_metadata_receipt': native_path.relative_to(ROOT).as_posix(),
        'native_codec_metadata_verified': True, 'playback_verified_on_ps5': False,
    })
candidate = {
    'schema_version': 1, 'publication_status': 'NEXT_PENDING_INDEPENDENT_PEER',
    'entries': [{
        'entry_id': 'wikipedia-57661331', 'match_title': 'Resident Evil 2', 'match_year': 2019,
        'title': 'Listen to Resident Evil 2', 'composer': 'Capcom Sound Team and Cody Matthew Johnson',
        'curator_note': 'Listen to the music of Capcom Sound Team and Cody Matthew Johnson from Resident Evil 2.',
        'replace_existing_tracks': True, 'full_album_collection': False,
        'coverage_status': 'AVAILABLE_59_ORIGINAL_2019_ALBUM_ARCHIVAL_PASSAGES',
        'album_completeness': {'published_title_inventory': 59, 'available_passages': 59,
            'qualification': 'All 59 published titles have an actual matching archival chapter and valid bounded passage. This is not an audio fingerprint verification of retail masters or every game file.'},
        'tracks': tracks,
    }],
    'source_receipts': [{'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)} for path in
        [watch_path, native_path, label_path, F / 're2-capcom-release.html', F / 're2-saudade-creator.html']],
    'source_album_publication': primary,
    'audio_downloaded': False, 'source_catalog_or_runtime_changed': False,
}
path = F / 'resident-evil-two-2019-fifty-nine-passages-candidate.json'
path.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(path.relative_to(ROOT), sha(path))
