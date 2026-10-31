"""Available real scores: publisher chapters, composer album and artist singles."""
import hashlib
import json
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/modern-public-albums'
load = lambda path: json.loads(path.read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def sec(text):
    value = 0
    for part in text.split(':'):
        value = value * 60 + int(part)
    return value


def primary_receipt(key, url, expected):
    target = OUT / (key + '-original-album-primary.html')
    try:
        if not target.exists():
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=20) as response:
                data = response.read()
            assert expected.casefold() in data.decode('utf-8', errors='replace').casefold()
            assert b'Client Challenge' not in data[:5000]
            target.write_bytes(data)
        return {'url': url, 'actual_body_retrieved': True, 'local_path': target.relative_to(ROOT).as_posix(), 'sha256': sha(target)}
    except Exception as error:
        return {'url': url, 'actual_body_retrieved': False, 'actual_web_page_read': True,
                'error': str(error), 'scope': 'Actual primary page read through web; no saved HTML claim.'}


primaries = [
    primary_receipt('hollowknight', 'https://store.steampowered.com/app/598190?l=english', 'Christopher Larkin'),
    primary_receipt('doom2016', 'https://gear.bethesda.net/products/doom-deluxe-double-vinyl-record', 'Chris Hite'),
    primary_receipt('celeste', 'https://www.materiacollective.com/music/celeste-original-soundtrack', 'Lena Raine'),
]
entries = []
for key, entry_id, name, year, composer, video_id, expected_count in [
    ('doom2016', 'wikipedia-12915762', 'Doom', 2016, 'Mick Gordon', 'Jm932Sqwf5E', 31),
    ('silksong', 'wikipedia-59961092', 'Hollow Knight: Silksong', 2025, 'Christopher Larkin', 'Q6is6K8jbho', 53),
    ('hollowknight', 'wikipedia-53391134', 'Hollow Knight', 2017, 'Christopher Larkin', '0HbnqjGirFg', 26),
    ('celeste', 'celeste', 'Celeste', 2018, 'Lena Raine', None, 21),
]:
    tracks = []
    if video_id is None:
        research = load(OUT / 'celeste-artist21-publication-research.json')
        for row in research['tracks']:
            assert row['status'] == 'metadata_candidate'
            pub = row['publication']
            assert pub['author'] == 'Lena Raine' and pub['title'] == row['source']['title']
            native_receipt = row['native_codec_receipt']
            assert load(ROOT / native_receipt).get('native_compatible_avc_aac') is True
            match = re.match(r'^\[Official\] Celeste Original Soundtrack - (\d+) - (.+)$', pub['title'])
            assert match
            tracks.append({'album_track_number': int(match[1]), 'youtube_id': row['source']['id'],
                           'title': match[2], 'creator': composer,
                           'url': row['source']['url'], 'source_page': row['source']['url'],
                           'uploader': pub['author'], 'channel_url': 'https://www.youtube.com/channel/' + pub['channelId'],
                           'primary_published_title': pub['title'],
                           'composer_source': primaries[2]['url'],
                           'additional_recording_roles': {'composition': ['Lena Raine'], 'production': ['Lena Raine']},
                           'duration_seconds': float(pub['lengthSeconds']),
                           'official_uploader_verified': True, 'publishing_kind': 'official_game_recording',
                           'recording_version': 'Original 2018 Celeste soundtrack, original Lena Raine artist publication; not B-Sides, Farewell or fan piano arrangements.',
                           'recording_year': year, 'rights': '2018 Radical Dreamland / Lena Raine and applicable game rightsholders; original artist publication.',
                           'native_codec_metadata_verified': True, 'native_codec_metadata_receipt': native_receipt,
                           'publication_metadata_receipt': (OUT / 'celeste-artist-individuals' / (row['source']['id'] + '.json')).relative_to(ROOT).as_posix(),
                           'playback_verified_on_ps5': False})
        inventory_url = 'https://www.youtube.com/playlist?list=PLe1jcCJWvkWiWLp9h3ge0e5v7n6kxEfOG'
    else:
        receipt_path = OUT / (video_id + '-actual-publication-research.json')
        receipt = load(receipt_path)
        pub = receipt['publication']
        assert receipt['native_avc_aac'] is True
        assert pub['author'] == {'doom2016': 'Bethesda Softworks', 'silksong': 'Christopher Larkin', 'hollowknight': 'MindsAblaze2'}[key]
        markers = []
        for line in pub['shortDescription'].splitlines():
            if key == 'doom2016':
                match = re.match(r'^\s*(\d+)\.\s*(.+?)(\d{1,2}:\d{2}(?::\d{2})?)\s*$', line)
                if match:
                    number, title, timestamp = match.groups()
            elif key == 'silksong':
                match = re.match(r'^(\d{1,2}:\d{2}(?::\d{2})?)\s+(.+)$', line)
                if match:
                    timestamp, title = match.groups()
                    number = len(markers) + 1
            else:
                match = re.match(r'^(\d+)\.\)\s*\[(\d{1,2}:\d{2}(?::\d{2})?)\]\s*(.+)$', line)
                if match:
                    number, timestamp, title = match.groups()
            if match:
                markers.append({'number': int(number), 'title': title.strip(), 'start': sec(timestamp), 'source_line': line})
        assert len(markers) == expected_count
        for index, marker in enumerate(markers):
            end = markers[index + 1]['start'] if index + 1 < len(markers) else float(pub['lengthSeconds'])
            assert 0 <= marker['start'] < end <= float(pub['lengthSeconds'])
            roles = {}
            track_composer = composer
            if key == 'doom2016' and marker['number'] == 16:
                roles['remix'] = ['Chad Mossholder']
            if key == 'doom2016' and marker['number'] == 29:
                roles['original_music'] = ['Mick Gordon']
                roles['remix_and_additional_album_track_contribution'] = ['Chris Hite']
                track_composer = 'Mick Gordon and Chris Hite'
            if key == 'hollowknight' and marker['number'] == 9:
                roles['soprano'] = ['Amelia Jones']
            publishing_kind = 'archival_game_recording' if key == 'hollowknight' else 'official_game_recording'
            title = marker['title']
            if key == 'doom2016' and marker['number'] == 29:
                title += ' (Chris Hite Remix)'
            track = {'album_track_number': marker['number'], 'youtube_id': video_id,
                     'title': title, 'creator': track_composer,
                     'url': 'https://www.youtube.com/watch?v=' + video_id,
                     'source_page': 'https://www.youtube.com/watch?v=' + video_id,
                     'uploader': pub['author'], 'channel_url': 'https://www.youtube.com/channel/' + pub['channelId'],
                     'primary_published_title': pub['title'],
                     'composer_source': primaries[0]['url'] if key == 'hollowknight' else primaries[1]['url'] if key == 'doom2016' else 'https://www.youtube.com/watch?v=' + video_id,
                     'additional_recording_roles': roles,
                     'start_seconds': marker['start'], 'end_seconds': end,
                     'duration_seconds': end-marker['start'], 'source_actual_chapter_line': marker['source_line'],
                     'source_publication_duration_seconds': float(pub['lengthSeconds']),
                     'official_uploader_verified': key != 'hollowknight', 'publishing_kind': publishing_kind,
                     'recording_version': str(year) + ' original game soundtrack album; real source-published chapter boundaries. ' + ('Archival upload credited honestly, not an official publisher or certified CD master.' if key == 'hollowknight' else 'Original publisher/composer upload, with named official album remix versions retained.'),
                     'recording_year': year,
                     'rights': {'doom2016': 'DOOM music and recordings: id Software / Bethesda Softworks / ZeniMax and credited authors/remixers.',
                                'silksong': 'Hollow Knight: Silksong music and recordings: Christopher Larkin / Team Cherry and credited performers.',
                                'hollowknight': 'Hollow Knight music and recordings: Christopher Larkin / Team Cherry and credited performers; MindsAblaze2 is the archival uploader.'}[key],
                     'native_codec_metadata_verified': True, 'native_codec_metadata_receipt': receipt['native_codec_receipt'],
                     'publication_metadata_receipt': receipt_path.relative_to(ROOT).as_posix(),
                     'playback_verified_on_ps5': False}
            if key == 'silksong':
                track['album_level_music_roles'] = {'orchestration_and_typesetting': ['Nathan Cummins'],
                                                   'scope': 'Album-level publisher credit only; Nathan is not silently recast as every cue composer.'}
                track['album_production_credit_lines'] = pub['shortDescription'].split('Music production:', 1)[1].split('More information at', 1)[0].strip().splitlines()
            tracks.append(track)
        inventory_url = 'https://www.youtube.com/watch?v=' + video_id
    assert len(tracks) == expected_count
    assert [track['album_track_number'] for track in tracks] == list(range(1, expected_count + 1))
    entries.append({'entry_id': entry_id, 'match_title': name, 'match_year': year,
                    'title': 'Listen to ' + name, 'composer': composer,
                    'curator_note': 'Listen to the music of ' + composer + '\n' + name,
                    'replace_existing_tracks': True, 'full_album_collection': True,
                    'coverage_status': 'complete_available_published_album_collection',
                    'album_completeness': {'expected_tracks': expected_count, 'verified_album_tracks': len(tracks),
                                           'inventory_source': inventory_url,
                                           'scope': 'This named publicly available original album collection, using actual source chapter markers or individual artist videos. Not all possible game stems, regional editions, later DLC or audio-identical commercial masters. DOOM uses actual publisher-declared chapter boundaries, not independently audio-measured cuts.'},
                    'tracks': tracks})
result = {'schema_version': 1, 'publication_status': 'awaiting_independent_peer', 'entries': entries,
          'source_receipts': primaries,
          'scope': 'Four original available collections,131 selectable real publications/passages. DOOM remix credits preserved; Silksong orchestrator not promoted to composer; HollowKnight archive uploader not falsely official. No listening, fingerprint or physical-console playback assertion.'}
target = OUT / 'doom-silksong-hollowknight-celeste131-public-candidate.json'
assert not target.exists(), 'Immutable checkpoint exists'
target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'candidate': target.relative_to(ROOT).as_posix(), 'sha256': sha(target), 'selectable_tracks': sum(len(e['tracks']) for e in entries)}))
