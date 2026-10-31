"""Make real publisher chapters playable; preserve performer/arranger credit roles."""
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/modern-public-albums'
load = lambda path: json.loads(path.read_text(encoding='utf-8'))


def main():
    entries = []
    for entry_id, name, year, video_id, expected_count in [
        ('wikipedia-59284486', 'Hades', 2020, '3GRKJ87S5cI', 30),
        ('wikipedia-72448598', 'Hades II', 2025, 'jfIuPRP94WI', 52),
    ]:
        receipt = load(OUT / (video_id + '-actual-publication-research.json'))
        publication = receipt['publication']
        assert publication['author'] == 'Supergiant Games' and receipt['native_avc_aac'] is True
        assert 'Music and Lyrics by Darren Korb' in publication['shortDescription']
        markers = []
        for line in publication['shortDescription'].splitlines():
            match = re.match(r'^\s*(\d+)\.\s+(.+?)\s+\[(\d+:\d+(?::\d+)?)[\]}]\s*$', line)
            if not match:
                continue
            number, title, timestamp = match.groups()
            seconds = 0
            for piece in timestamp.split(':'):
                seconds = seconds * 60 + int(piece)
            markers.append({'number': int(number), 'title': title, 'start_seconds': seconds, 'source_line': line})
        assert len(markers) == expected_count
        assert [row['number'] for row in markers] == list(range(1, expected_count + 1))
        tracks = []
        for index, marker in enumerate(markers):
            end = markers[index + 1]['start_seconds'] if index + 1 < len(markers) else int(publication['lengthSeconds'])
            assert end > marker['start_seconds']
            roles = {'composition_and_lyrics': ['Darren Korb']}
            feature = re.search(r'\((?:ft\.|feat\.)\s+(.+?)\)', marker['title'])
            if feature:
                roles['featured_performers'] = [value.strip() for value in re.split(r'\s+and\s+', feature[1])]
            if name == 'Hades' and marker['number'] in [27, 28]:
                roles['orchestral_arrangement'] = ['Austin Wintory']
                roles['production'] = ['Austin Wintory', 'Darren Korb']
                roles['mixing'] = ['Steve Kempster'] + (['Darren Korb'] if marker['number'] == 28 else [])
            row = {
                'album_track_number': marker['number'], 'youtube_id': video_id,
                'url': 'https://www.youtube.com/watch?v=' + video_id,
                'title': marker['title'], 'creator': 'Darren Korb',
                'start_seconds': marker['start_seconds'], 'end_seconds': end,
                'duration_seconds': end - marker['start_seconds'],
                'source_actual_chapter_line': marker['source_line'],
                'source_publication_duration_seconds': int(publication['lengthSeconds']),
                'composer_source': 'https://www.youtube.com/watch?v=' + video_id,
                'additional_recording_roles': roles,
                'uploader': publication['author'], 'channel_url': 'https://www.youtube.com/channel/' + publication['channelId'],
                'source_page': 'https://www.youtube.com/watch?v=' + video_id,
                'primary_published_title': publication['title'],
                'official_uploader_verified': True, 'publishing_kind': 'official_game_recording',
                'recording_version': f'Official Supergiant Games{year} original soundtrack album; real publisher chapter passage, including explicitly named album mixes and featured performers.',
                'recording_year': year, 'recording_album': name + ': Original Soundtrack',
                'rights': f'Music and recording copyright{year} Supergiant Games and credited authors/performers; original publisher upload.',
                'native_codec_metadata_verified': True, 'native_codec_metadata_receipt': receipt['native_codec_receipt'],
                'publication_metadata_receipt': str((OUT / (video_id + '-actual-publication-research.json')).relative_to(ROOT)).replace('\\', '/'),
                'playback_verified_on_ps5': False,
                'artist_credit_scope': 'Music/lyrics credit follows the actual publisher description. Featured performer names are not silently recast as composers; real timestamp markers, not reconstructed cumulative cuts.',
            }
            if name == 'Hades II':
                row['album_level_music_roles'] = {'primary_music_and_lyrics': ['Darren Korb'],
                                                  'orchestral_choir_production_co_composer_and_conductor': ['Austin Wintory']}
                row['artist_credit_scope'] += ' Publisher also names Austin Wintory as Co-Composer/Conductor within orchestral/choir recording credits. His contribution is preserved honestly at album level; no unsupported per-cue joint-authorship split is invented.'
            tracks.append(row)
        entries.append({'entry_id': entry_id, 'match_title': name, 'match_year': year,
                        'title': 'Listen to ' + name,
                        'composer': 'Darren Korb' if name == 'Hades' else 'Darren Korb and Austin Wintory',
                        'curator_note': 'Listen to the music of Darren Korb' + (' and the Hades II score team' if name == 'Hades II' else '') + '\n' + name,
                        'replace_existing_tracks': True, 'full_album_collection': True,
                        'coverage_status': 'COMPLETE_AVAILABLE_PUBLISHER_ALBUM_COLLECTION',
                        'album_completeness': {'expected_tracks': expected_count, 'verified_album_tracks': len(tracks),
                                               'inventory_source': 'https://www.youtube.com/watch?v=' + video_id,
                                               'scope': 'All real chapters in the publisher\'s public full original album. Not a claim of all possible unreleased stems, future updates or platform variants; no audio fingerprint or physical-console playback assertion.'},
                        'tracks': tracks})
    result = {'schema_version': 1, 'publication_status': 'awaiting_independent_peer',
              'scope': 'Two primary publisher full albums,82 selectable real chapter passages; no exhaustive-order/master research beyond actual published index.',
              'entries': entries}
    target = OUT / 'hades-two-publisher-albums82-candidate.json'
    assert not target.exists(), 'Immutable checkpoint already exists'
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'candidate': str(target), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'games': 2, 'tracks': 82}))


if __name__ == '__main__':
    main()
