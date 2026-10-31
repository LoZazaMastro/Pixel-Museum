"""Freeze available original 2018 album recordings with publisher English titles."""
from pathlib import Path
import hashlib
import html
import json
import re

ROOT = Path(__file__).resolve().parents[1]
F = ROOT / 'build/research/soundtrack-broad/modern-following'
load = lambda p: json.loads(p.read_text(encoding='utf8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
label_path = F / 'mhw-original-label-album.json'
playlist_path = F / 'mhw-original-archive-playlist.json'
research_path = F / 'mhw-original-native-research.json'
steam_path = F / 'mhw-original-steam-store.html'
label, playlist, research = load(label_path), load(playlist_path), load(research_path)
published = label['results'][1:]
official_titles = [html.unescape(re.sub('<[^>]+>', '', value)).strip() for value in
    re.findall(r'<div class="music_album_track_name">(.*?)</div>', steam_path.read_text(encoding='utf8'), re.S)]
assert len(published) == len(playlist['entries'][1:]) == len(research['records']) == len(official_titles) == 83
assert label['results'][0]['collectionId'] == 1336356191
assert label['results'][0]['releaseDate'].startswith('2018-02-14')
tracks, held, receipts = [], [], []
for ordinal, (song, row, checked, title) in enumerate(zip(published, playlist['entries'][1:], research['records'], official_titles), 1):
    assert row['id'] == checked['youtube_id'] and ordinal == checked['album_ordinal']
    assert song['trackName'] == checked['published_title']
    if checked['status'] == 'held':
        held.append({'album_ordinal': ordinal, 'youtube_id': row['id'], 'title': title, 'reason': checked['reason']})
        continue
    watch_path = ROOT / 'build/research/soundtrack-broad/watch' / (row['id'] + '.json')
    native_path = ROOT / 'build/research/video-discovery' / ('video-' + row['id'] + '.json')
    watch, native = load(watch_path), load(native_path)
    assert native['native_compatible_avc_aac']
    assert watch['title'] == native['title'] == row['title']
    assert watch['channelId'] == native['channel_id'] == 'UCFQh_mbkLL1Chm0HrU0YWHA'
    assert native['duration'] == float(watch['lengthSeconds'])
    tracks.append({
        'youtube_id': row['id'], 'url': 'https://www.youtube.com/watch?v=' + row['id'],
        'title': title, 'creator': song['artistName'], 'label_artist_credit': song['artistName'],
        'source_page': 'https://www.youtube.com/watch?v=' + row['id'],
        'source_actual_publication_title': watch['title'], 'published_original_language_title': song['trackName'],
        'uploader': watch['author'], 'channel_url': 'https://www.youtube.com/channel/' + watch['channelId'],
        'publishing_kind': 'archival_game_recording', 'official_uploader_verified': False,
        'composer_source': song['trackViewUrl'],
        'artist_credit_scope': 'Exact label-delivered recording artist; no extra per-cue composition or performance roles inferred.',
        'title_display_scope': 'Exact English title published by Capcom on the original soundtrack Steam page; original Japanese label title and actual uploader title retained separately.',
        'recording_context_source': 'https://store.steampowered.com/app/912540/Monster_Hunter_World_Original_Soundtrack/?l=english',
        'recording_album': 'Monster Hunter: World Original Soundtrack',
        'recording_album_release_year': 2018, 'original_game_year': 2018,
        'recording_version': 'Original 2018 base-game album public archival recording; not Iceborne, the film score, or an exact retail audio-master equivalence claim.',
        'published_album_ordinal': ordinal, 'published_album_disc': song.get('discNumber'),
        'published_album_track_number': song['trackNumber'], 'published_duration_ms': song['trackTimeMillis'],
        'duration_seconds': int(native['duration']),
        'rights': 'Capcom and the credited musicians retain their respective music and recording rights. The archive uploader is not an official publisher delivery.',
        'publication_metadata_receipt': watch_path.relative_to(ROOT).as_posix(),
        'native_codec_metadata_receipt': native_path.relative_to(ROOT).as_posix(),
        'native_codec_metadata_verified': True, 'playback_verified_on_ps5': False,
    })
    for path in (watch_path, native_path):
        receipts.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)})
assert len(tracks) == 82 and len(held) == 1 and held[0]['album_ordinal'] == 75
for path in (label_path, playlist_path, research_path, steam_path, F / 'mhw-steam-publisher.json'):
    receipts.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)})
candidate = {
    'schema_version': 1, 'publication_status': 'NEXT_PENDING_INDEPENDENT_PEER',
    'entries': [{
        'entry_id': 'wikipedia-54289600', 'match_title': 'Monster Hunter: World', 'match_year': 2018,
        'title': 'Listen to Monster Hunter: World', 'composer': 'Capcom Sound Team',
        'curator_note': 'Listen to the music of Capcom Sound Team from Monster Hunter: World.',
        'replace_existing_tracks': True, 'full_album_collection': False,
        'coverage_status': '82_AVAILABLE_ORIGINAL_BASE_GAME_ALBUM_RECORDINGS',
        'album_completeness': {'published_title_inventory': 83, 'available_recordings': 82,
            'qualification': 'One original public recording requires login and is held without retry. The actual archive includes short original-album cues; none are filtered solely for being brief. No every-game-file or retail-audio-fingerprint claim.'},
        'tracks': tracks,
    }],
    'held_recordings': held, 'source_receipts': receipts,
    'source_access_limits': ['Direct e-Capcom album request returned503; publisher Steam original-album page and label metadata were read instead. The whole-album video has no real chapters, so no83 cue timestamps were invented from retail durations.'],
    'semantic_peer_required': 'Check the six Japanese title punctuation/abbreviation differences flagged in research against actual Steam English and Japanese listing; preserve English publisher display names rather than copying archive name errors.',
    'audio_downloaded': False, 'source_catalog_or_runtime_changed': False,
}
path = F / 'monster-hunter-world-eighty-two-original-recordings-candidate.json'
path.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(path.relative_to(ROOT), sha(path))
