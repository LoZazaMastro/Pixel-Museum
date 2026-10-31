"""Two modern scores: literal artist/archive timestamps, no invented chapter cuts."""
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/modern-public-albums'
load = lambda path: json.loads(path.read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
profiles = [('nnvjKf_mRYM', 'wikipedia-57651372', 'Tunic', 2022, 'Lifeformed', 'Lifeformed, Janice Kwan',
             'https://lifeformed.bandcamp.com/album/tunic-original-game-soundtrack', 61),
            ('nLa3dAYzkHo', 'wikipedia-64260079', 'Stray', 2022, 'EarthMen PlayGames', 'Yann van der Cruyssen',
             'https://store.steampowered.com/app/2086160/Stray__Original_Soundtrack/', 70)]
entries, source_receipts = [], []
for video_id, entry_id, name, year, author, composer, source, expected in profiles:
    path = OUT / (video_id + '-actual-publication-research.json')
    receipt = load(path)
    pub = receipt['publication']
    assert receipt['native_avc_aac'] is True and pub['author'] == author
    assert load(ROOT / receipt['native_codec_receipt'])['native_compatible_avc_aac'] is True
    markers = []
    for line in pub['shortDescription'].splitlines():
        if name == 'Tunic':
            match = re.match(r'^(\d{2}:\d{2}:\d{2})\s*/\s*(\d+)\s+(.+)$', line)
        else:
            match = re.match(r'^(\d+:\d{2}:\d{2})\s+(\d+)\s*-\s*(.+)$', line)
        if not match:
            continue
        timestamp, number, title = match.groups()
        start = 0
        for piece in timestamp.split(':'):
            start = start*60 + int(piece)
        markers.append({'start': start, 'title': title.strip(), 'number': int(number), 'line': line})
    assert len(markers) == expected, (name, len(markers))
    duration = float(pub['lengthSeconds'])
    tracks = []
    for index, marker in enumerate(markers):
        end = markers[index+1]['start'] if index+1 < len(markers) else duration
        assert 0 <= marker['start'] < end <= duration
        title = marker['title'].replace(' (See Below)', '')
        tracks.append({'youtube_id': video_id, 'url': 'https://www.youtube.com/watch?v=' + video_id,
                       'source_page': 'https://www.youtube.com/watch?v=' + video_id,
                       'title': title, 'creator': composer, 'composer_source': source,
                       'artist_credit_scope': 'Artist publication explicitly co-composed by Lifeformed and Janice Kwan.' if name == 'Tunic' else 'Publisher Steam soundtrack explicitly assigns all tracks to Yann van der Cruyssen.',
                       'additional_recording_roles': {'mastering': ['Matt Morgan']} if name == 'Tunic' else {},
                       'start_seconds': marker['start'], 'end_seconds': end,
                       'duration_seconds': end-marker['start'], 'source_actual_chapter_line': marker['line'],
                       'source_publication_duration_seconds': duration,
                       'uploader': author, 'channel_url': 'https://www.youtube.com/channel/' + pub['channelId'],
                       'primary_published_title': pub['title'], 'official_uploader_verified': name == 'Tunic',
                       'publishing_kind': 'official_game_recording' if name == 'Tunic' else 'archival_game_recording',
                       'recording_version': 'Original 2022 artist-issued soundtrack, with the source-labeled Arcane Arcade bonus track.' if name == 'Tunic' else 'Original 2022 Stray album: cinematic and in-world music, public archival recording. Uploader Official label is not treated as publisher authorization.',
                       'recording_year': year,
                       'rights': 'Lifeformed / Janice Kwan and credited production contributors.' if name == 'Tunic' else 'Annapurna Interactive / BlueTwelve Studio / Yann van der Cruyssen. EarthMen PlayGames is an archival uploader.',
                       'native_codec_metadata_verified': True,
                       'native_codec_metadata_receipt': receipt['native_codec_receipt'],
                       'publication_metadata_receipt': path.relative_to(ROOT).as_posix(),
                       'playback_verified_on_ps5': False})
    entry = {'entry_id': entry_id, 'match_title': name, 'match_year': year, 'title': 'Listen to ' + name,
             'composer': composer, 'curator_note': 'Listen to the music of ' + composer + '\n' + name,
             'replace_existing_tracks': True, 'full_album_collection': True, 'coverage_status': 'published_album_collection',
             'recording_collection_scope': str(expected) + ' selectable source-indexed passages from the cited 2022 soundtrack collection, not every possible in-game stem or later version.',
             'album_completeness': {'verified_available_tracks': expected, 'inventory_source': source,
                                    'scope': 'Named published soundtrack collection, using literal public recording chapter boundaries. No CD-master, listening or physical console-playback claim.'},
             'tracks': tracks}
    entries.append(entry)
    source_receipts.append({'local_path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)})
web_receipt = {'sources': [{'url': profiles[0][6], 'actual_web_page_read': True,
                            'verified_context': 'Artist Bandcamp page names Lifeformed x Janice Kwan, original game soundtrack; same artist YouTube publication explicitly says co-composed and names Matt Morgan mastering.'},
                           {'url': profiles[1][6], 'actual_web_page_read': True,
                            'verified_context': 'BlueTwelve/Annapurna original 2022 Steam soundtrack. About section explicitly says all tracks composed by Yann van der Cruyssen; two-disc tracklist distinguishes cinematic and in-world music.'}],
               'scope': 'Primary artist and publisher credits; no false archival uploader authorization or physical playback claim.'}
credit_path = OUT / 'tunic-stray-primary-role-web-read-receipt.json'
credit_path.write_text(json.dumps(web_receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
source_receipts.append({'local_path': credit_path.relative_to(ROOT).as_posix(), 'sha256': sha(credit_path)})
target = OUT / 'tunic-stray131-readable-public-candidate.json'
assert not target.exists(), 'Immutable checkpoint exists'
target.write_text(json.dumps({'schema_version': 1, 'publication_status': 'awaiting_independent_peer',
                              'entries': entries, 'source_receipts': source_receipts}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'candidate': target.relative_to(ROOT).as_posix(), 'sha256': sha(target), 'selectable_tracks': sum(len(e['tracks']) for e in entries)}))
