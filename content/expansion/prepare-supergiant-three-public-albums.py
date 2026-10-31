"""Original publisher collections: real individual videos or explicit chapter ranges."""
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/modern-public-albums'
load = lambda path: json.loads(path.read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def seconds(value):
    total = 0
    for piece in value.split(':'):
        total = total * 60 + int(piece)
    return total


def base_track(video_id, publication, title, year, native_receipt, publication_receipt):
    assert publication['author'] == 'Supergiant Games' and publication['channelId'] == 'UCBq8CLRcJN8rgqHOkyL1ozg'
    assert 'Composed by Darren Korb.' in publication['shortDescription']
    assert load(ROOT / native_receipt).get('native_compatible_avc_aac') is True
    return {'youtube_id': video_id, 'url': 'https://www.youtube.com/watch?v=' + video_id,
            'title': title, 'creator': 'Darren Korb',
            'composer_source': 'https://www.youtube.com/watch?v=' + video_id,
            'uploader': publication['author'], 'channel_url': 'https://www.youtube.com/channel/' + publication['channelId'],
            'source_page': 'https://www.youtube.com/watch?v=' + video_id,
            'primary_published_title': publication['title'],
            'official_uploader_verified': True, 'publishing_kind': 'official_game_recording',
            'recording_version': 'Original ' + str(year) + ' Supergiant Games soundtrack; actual publisher publication, not a fan cover or later live arrangement.',
            'recording_year': year,
            'rights': 'Music and recordings copyright ' + str(year) + ' Supergiant Games, LLC and credited authors/performers. Original publisher upload.',
            'native_codec_metadata_verified': True, 'native_codec_metadata_receipt': native_receipt,
            'publication_metadata_receipt': publication_receipt,
            'playback_verified_on_ps5': False}


entries = []
for entry_id, name, year, count, video_id in [
    ('wikipedia-30602654', 'Bastion', 2011, 22, None),
    ('workbook-05-20-transistor', 'Transistor', 2014, 23, '-zA1jRmAYfU'),
    ('wikipedia-50237418', 'Pyre', 2017, 39, 'uH3Aoj1nw58'),
]:
    tracks = []
    if video_id is None:
        rows = load(OUT / 'bastion-publisher22-publication-research.json')['tracks']
        for row in rows:
            assert row['status'] == 'metadata_candidate'
            publication = row['publication']
            assert publication['title'] == row['source']['title']
            title = publication['title'].removeprefix('Bastion Original Soundtrack - ')
            track = base_track(row['source']['id'], publication, title, year, row['native_codec_receipt'],
                               (OUT / 'bastion-publisher-individuals' / (row['source']['id'] + '.json')).relative_to(ROOT).as_posix())
            track['album_track_number'] = row['source_playlist_position']
            track['duration_seconds'] = float(publication['lengthSeconds'])
            roles = {}
            for token, role in [('Lyrics by', 'lyrics'), ('Vocals by', 'vocals')]:
                match = re.search(re.escape(token) + r' (.+?)\.', publication['shortDescription'])
                if match:
                    roles[role] = [part.strip() for part in match[1].split(' and ')]
            track['additional_recording_roles'] = roles
            tracks.append(track)
        inventory = 'https://www.youtube.com/playlist?list=PL53mjgVKFq7yPfCiSJaA_aI2SPKrnEmmJ'
    else:
        receipt_path = OUT / (video_id + '-actual-publication-research.json')
        receipt = load(receipt_path)
        assert receipt['native_avc_aac'] is True
        publication = receipt['publication']
        description = publication['shortDescription']
        for line in description.splitlines():
            match = re.match(r'^\s*(\d+)\.\s+(.+?)\s+\[(\d+:\d+(?::\d+)?)\s+-\s+(\d+:\d+(?::\d+)?)\](.*)$', line)
            if not match:
                continue
            number, title, start, end, tail = match.groups()
            start_seconds, end_seconds = seconds(start), seconds(end)
            assert 0 <= start_seconds < end_seconds <= float(publication['lengthSeconds'])
            track = base_track(video_id, publication, title.strip(), year, receipt['native_codec_receipt'], receipt_path.relative_to(ROOT).as_posix())
            track.update(album_track_number=int(number), start_seconds=start_seconds, end_seconds=end_seconds,
                         duration_seconds=end_seconds-start_seconds, source_actual_chapter_line=line,
                         source_publication_duration_seconds=float(publication['lengthSeconds']))
            roles = {}
            if name == 'Transistor' and '*' in tail:
                roles['vocals'] = ['Ashley Barrett']
            elif name == 'Pyre' and 'Feat.' in tail:
                roles['vocals'] = [piece.strip() for piece in tail.split('Feat.', 1)[1].split('&')]
            track['additional_recording_roles'] = roles
            tracks.append(track)
        inventory = 'https://www.youtube.com/watch?v=' + video_id
    assert len(tracks) == count and [row['album_track_number'] for row in tracks] == list(range(1, count + 1))
    entries.append({'entry_id': entry_id, 'match_title': name, 'match_year': year,
                    'title': 'Listen to ' + name, 'composer': 'Darren Korb',
                    'curator_note': 'Listen to the music of Darren Korb\n' + name,
                    'replace_existing_tracks': True, 'full_album_collection': True,
                    'coverage_status': 'complete_available_publisher_album_collection',
                    'album_completeness': {'expected_tracks': count, 'verified_album_tracks': len(tracks),
                                           'inventory_source': inventory,
                                           'scope': 'All named tracks in this real publisher original soundtrack collection. Not every game-state variation, unreleased cue or later live/extended release. Publisher chapter ends used literally, without reconstructed cumulative timing.'},
                    'tracks': tracks})
result = {'schema_version': 1, 'publication_status': 'awaiting_independent_peer', 'entries': entries,
          'scope': 'Three original Supergiant Games publisher collections,84 selectable real recordings/passages. GregKasavin lyrics and LoganCunningham narration/vocals preserved in Bastion; AshleyBarrett/DarrenKorb vocal roles kept separate from composition. No audio fingerprint or physical-console assertion.'}
target = OUT / 'bastion-transistor-pyre84-publisher-candidate.json'
assert not target.exists(), 'Immutable checkpoint exists'
target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'candidate': target.relative_to(ROOT).as_posix(), 'sha256': sha(target), 'games': len(entries), 'selectable_tracks': 84}))
