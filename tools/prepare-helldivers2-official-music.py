"""Freeze Sony's available thirteen-recording digital soundtrack edition."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
F = ROOT / 'build/research/soundtrack-broad/modern-following'
load = lambda p: json.loads(p.read_text(encoding='utf8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
label_path = F / 'helldivers2-label-album.json'
label = load(label_path)
album, titles = label['results'][0], label['results'][1:]
research_path = F / 'helldivers2-native-research.json'
research = load(research_path)
assert album['collectionId'] == 1811175755 and album['trackCount'] == len(titles) == 13
assert album['releaseDate'].startswith('2025-05-02')
assert len(research['records']) == 13 and len(research['excluded']) == 3
tracks, receipts = [], []
for index, (published, row) in enumerate(zip(titles, research['records']), 1):
    assert published['trackNumber'] == index and row['status'] == 'verified_pending_peer'
    identifier = row['youtube_id']
    watch_path = ROOT / 'build/research/soundtrack-broad/watch' / (identifier + '.json')
    native_path = ROOT / 'build/research/video-discovery' / ('video-' + identifier + '.json')
    watch, native = load(watch_path), load(native_path)
    assert published['trackName'] in watch['title']
    assert watch['title'] == native['title'] and watch['channelId'] == native['channel_id']
    assert float(watch['lengthSeconds']) == float(native['duration'])
    assert native['native_compatible_avc_aac']
    assert watch['channelId'] in ['UCGkX_HCD_T5XOwxi_KR6YoQ', 'UCEdikMFtocqFOnPYOuEKqUw']
    assert published['artistName'] == ('Wilbert Roget, II' if index <= 11 else 'Ross Tregenza')
    tracks.append({
        'youtube_id': identifier, 'url': 'https://www.youtube.com/watch?v=' + identifier,
        'title': published['trackName'], 'creator': published['artistName'],
        'source_page': 'https://www.youtube.com/watch?v=' + identifier,
        'channel_url': 'https://www.youtube.com/channel/' + watch['channelId'],
        'uploader': watch['author'], 'publishing_kind': 'official_game_recording',
        'official_uploader_verified': True,
        'composer_source': 'https://milanrecords.com/release/helldivers-2-original-game-soundtrack/',
        'artist_credit_scope': 'Exact digital-album artist credit; the label credits Wilbert Roget, II with additional music by Ross Tregenza. No inferred credit from the playlist owner.',
        'recording_album': album['collectionName'], 'original_game_year': 2024,
        'recording_album_release_year': 2025, 'published_album_track_number': index,
        'recording_version': 'The thirteen-track digital album edition released on 2 May 2025, including The Illuminate Cult; not presented as the earlier eleven-track edition or every evolving in-game cue.',
        'duration_seconds': int(native['duration']),
        'rights': 'Sony Interactive Entertainment, Milan Records and the credited musicians retain their respective composition, performance and recording rights.',
        'publication_metadata_receipt': watch_path.relative_to(ROOT).as_posix(),
        'native_codec_metadata_receipt': native_path.relative_to(ROOT).as_posix(),
        'native_codec_metadata_verified': True, 'playback_verified_on_ps5': False,
    })
    for path in (watch_path, native_path):
        receipts.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)})
for path in (label_path, research_path, F / 'helldivers2-sony-official-playlist.json', F / 'helldivers2-milan-primary.html'):
    receipts.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)})
candidate = {
    'schema_version': 1, 'publication_status': 'NEXT_PENDING_INDEPENDENT_PEER',
    'entries': [{
        'entry_id': 'wikipedia-75025557', 'match_title': 'Helldivers 2', 'match_year': 2024,
        'title': 'Listen to Helldivers 2', 'composer': 'Wilbert Roget, II and Ross Tregenza',
        'curator_note': 'Listen to the music of Wilbert Roget, II and Ross Tregenza from Helldivers 2.',
        'replace_existing_tracks': True, 'full_album_collection': True,
        'coverage_status': 'OFFICIAL_DIGITAL_ALBUM_13_RECORDINGS',
        'album_completeness': {'published_title_inventory': 13, 'available_recordings': 13,
            'qualification': 'Thirteen-track 2 May 2025 digital edition, including The Illuminate Cult. No assertion that this contains every later live-service update or separate EP.'},
        'tracks': tracks,
    }],
    'source_receipts': receipts, 'excluded_playlist_items': research['excluded'],
    'metadata_check_correction': 'The Sony playlist includes one legitimate label-delivered Wilbert Roget, II Topic recording. Its exact channel and Milan/Sony provided-label description were checked instead of falsely requiring Sony VEVO ownership of every playlist item.',
    'audio_downloaded': False, 'source_catalog_or_runtime_changed': False,
}
path = F / 'helldivers2-thirteen-official-album-candidate.json'
path.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(path.relative_to(ROOT), sha(path))
