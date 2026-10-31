"""Make guarded music patches from reviewed, recording-ID-matched album results."""
from pathlib import Path
import argparse, copy, json, re, unicodedata

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument('result_file')
p.add_argument('--base', default='build/research/app-audio-matched-albums-20261030')
args = p.parse_args()
BASE = ROOT / args.base
owners = {e['id']: e for e in json.loads((ROOT / 'content/catalog.json').read_text(encoding='utf-8'))['entries']}
results = json.loads((BASE / args.result_file).read_text(encoding='utf-8'))
title_map_path = BASE / 'published-english-titles.json'
published_titles = json.loads(title_map_path.read_text(encoding='utf-8')) if title_map_path.exists() else {}
selection_path = BASE / 'album-track-selections.json'
album_selections = json.loads(selection_path.read_text(encoding='utf-8')) if selection_path.exists() else {}

def cjk(text):
    return bool(re.search('[\u3040-\u30ff\u4e00-\u9fff]', text))

def western_credit(name):
    # The studio publishes its artist name bilingually; retain its own Latin name.
    if name.startswith('sunset visitor '):
        return 'sunset visitor'
    return name

def published_latin_title(title):
    if cjk(title):
        parts = re.split(r'\s+[-\u2013\u2014]\s+', title)
        for n in range(1, len(parts)):
            suffix = ' - '.join(parts[n:])
            if not cjk(suffix) and re.search('[A-Za-z]', suffix):
                return suffix
    return title

def title_key(title):
    title = re.sub(r'\s*\(from\s+.*?\)\s*', '', title, flags=re.I)
    return ''.join(c for c in unicodedata.normalize('NFKC', title).casefold() if c.isalnum())

patches, report = [], []
for result in results:
    if not result['albums']:
        continue
    owner = owners[result['entry_id']]
    original_before = copy.deepcopy(owner.get('soundtrack'))
    before = copy.deepcopy(original_before or {'title': owner['title'] + ' — Original Soundtrack', 'composer': '', 'curator_note': '', 'tracks': []})
    old = {track['youtube_id']: track for track in before['tracks']}
    tracks, skipped, available_matched_ids = [], [], set()
    for selected in result['albums']:
        album = json.loads((ROOT / selected['receipt']).read_text(encoding='utf-8'))
        selection = album_selections.get(owner['id'], {}).get(Path(selected['receipt']).stem, {})
        url = 'https://music.youtube.com/playlist?list=' + album['audioPlaylistId']
        source = next((track.get('composer_source') or track.get('source_page') for track in before['tracks'] if track.get('official_uploader_verified') and track['youtube_id'] in selected['matched_existing_verified_ids']), url)
        for number, row in enumerate(album.get('tracks', []), 1):
            if selection.get('include_track_numbers') is not None and number not in selection['include_track_numbers']:
                continue
            if 'first_track' in selection and not selection['first_track'] <= number <= selection['last_track']:
                continue
            video_id = row.get('videoId')
            title = published_titles.get(owner['id'], {}).get(row['title'], published_latin_title(row['title']))
            if not video_id or not row.get('isAvailable', True):
                skipped.append({'title': title, 'reason': 'not_available_on_youtube'})
                continue
            assert re.fullmatch(r'[A-Za-z0-9_-]{11}', video_id), video_id
            if cjk(title):
                skipped.append({'title': title, 'reason': 'published_romanized_title_not_yet_collected'})
                continue
            artists = [western_credit(artist['name']) for artist in row.get('artists', [])]
            if any(cjk(name) for name in artists):
                artists = [western_credit(artist['name']) for artist in album.get('artists', [])]
            if not artists or any(cjk(name) for name in artists):
                skipped.append({'title': title, 'reason': 'published_romanized_artist_credit_not_yet_collected'})
                continue
            if video_id in selected['matched_existing_verified_ids']:
                available_matched_ids.add(video_id)
            if video_id in {track['youtube_id'] for track in tracks}:
                continue
            track = {
                'youtube_id': video_id, 'url': 'https://www.youtube.com/watch?v=' + video_id,
                'title': title, 'creator': ' / '.join(artists),
                'duration_seconds': row['duration_seconds'], 'source_page': url,
                'album_title': selection.get('album_title', album['title']), 'album_track_number': number,
                'album_metadata_receipt': selected['receipt'], 'album_source': source,
                'source_actual_publication_title': row['title'],
                'official_uploader_verified': True,
                'publishing_kind': 'official_label_original_game_recording',
                'native_codec_metadata_verified': False, 'playback_verified_on_ps5': False,
                'rights': 'YouTube streaming only. Original recording rights retained; no audio downloaded or packaged.'
            }
            artist_channels = [artist.get('id', '') for artist in row.get('artists', []) + album.get('artists', [])]
            channel = next((identifier for identifier in artist_channels if isinstance(identifier, str) and re.fullmatch(r'UC[A-Za-z0-9_-]{22}', identifier)), None)
            if channel:
                track['channel_url'] = 'https://www.youtube.com/channel/' + channel
            for key, value in old.get(video_id, {}).items():
                if key in ('verification_receipt', 'native_codec_metadata_receipt', 'native_codec_metadata_verified', 'start_seconds', 'end_seconds', 'gain'):
                    track[key] = value
            tracks.append(track)
    reviewed_album = all(selected.get('publisher_album_review') for selected in result['albums'])
    if not available_matched_ids and not reviewed_album:
        report.append({'entry_id': owner['id'], 'title': owner['title'], 'status': 'deferred_for_romanized_titles', 'skipped': skipped})
        continue
    ids, titles = {track['youtube_id'] for track in tracks}, {title_key(track['title']) for track in tracks}
    for track in before['tracks'] if result.get('retain_distinct_existing_tracks', True) else []:
        if track['youtube_id'] not in ids and title_key(track['title']) not in titles:
            tracks.append(copy.deepcopy(track))
            ids.add(track['youtube_id'])
            titles.add(title_key(track['title']))
    if len(tracks) <= len(before['tracks']) and result.get('retain_distinct_existing_tracks', True):
        continue
    if tracks == before['tracks']:
        continue
    after = copy.deepcopy(before)
    after['tracks'] = tracks
    after['curator_note'] = ('Original artist recordings from the game’s on-disc song selection.'
                             if not result.get('retain_distinct_existing_tracks', True)
                             else 'Published soundtrack recordings available on YouTube, arranged by album.')
    patches.append({'entry_id': owner['id'], 'field': 'soundtrack', 'before': original_before, 'after': after})
    report.append({'entry_id': owner['id'], 'title': owner['title'], 'before': len(before['tracks']), 'after': len(tracks), 'albums': [album['title'] for album in result['albums']], 'skipped': skipped})
stem = Path(args.result_file).stem
(BASE / (stem + '-patches.json')).write_text(json.dumps({'patches': patches}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(BASE / (stem + '-integration-report.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(BASE / 'no-cues.json').write_text('{"patches": []}\n', encoding='utf-8')
print(json.dumps({'games': len(patches), 'added_tracks': sum(row['after'] - row['before'] for row in report if 'after' in row), 'summary': [{key: value for key, value in row.items() if key != 'skipped'} for row in report]}, ensure_ascii=True))
