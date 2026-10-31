"""Useful public collections without guessing broken timestamp rows or unindexed tails."""
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/modern-public-albums'
load = lambda path: json.loads(path.read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
profiles = [
    ('0REXCITfjI0', 'workbook-09-06-starfield', 'Starfield', 2023, 'Bethesda Softworks', 'Inon Zur', 79,
     'https://www.youtube.com/watch?v=0REXCITfjI0', {'score_composition': ['Inon Zur']}),
    ('tDP6j8JB_hc', 'workbook-01-28-pok-mon-legends-arceus', 'Pokémon Legends: Arceus', 2022, 'Vyntwon', 'Game Freak sound team', 107,
     'https://docs.pokeamice.com/credits/legends-arceus/',
     {'game_level_composers': ['Go Ichinose', 'Hitomi Sato', 'Hiromitsu Maeba'],
      'sound_team_lead': ['Go Ichinose'], 'music_coordination': ['Hiromitsu Maeba'],
      'mixing_and_mastering': ['Hiromitsu Maeba']}),
    ('VzG7oP2oSUQ', 'wikipedia-70181775', 'Pokémon Scarlet and Violet', 2022, 'Vyntwon', 'Game Freak sound team', 137,
     'https://docs.pokeamice.com/credits/scarlet-violet/',
     {'game_level_composers': ['Minako Adachi', 'Junichi Masuda', 'Go Ichinose', 'Hiromitsu Maeba', 'Teruo Taniguchi', 'Hitomi Sato', 'Toby Fox'],
      'sound_coordination': ['Hiromitsu Maeba'], 'music_recording_engineer': ['Takahiro Oshima'],
      'musicians': ['Sorao Mori', 'Junnosuke Fujita']}),
]
entries, holds, source_receipts = [], [], []
for video_id, entry_id, name, year, author, composer, count, credit_url, roles in profiles:
    path = OUT / (video_id + '-actual-publication-research.json')
    receipt = load(path)
    pub = receipt['publication']
    assert receipt['native_avc_aac'] is True and pub['author'] == author
    assert load(ROOT / receipt['native_codec_receipt'])['native_compatible_avc_aac'] is True
    duration = float(pub['lengthSeconds'])
    markers = []
    for line in pub['shortDescription'].splitlines():
        match = re.match(r'^(\d+:\d{2}(?::\d{2})?)\s+(.+?)\s*$', line)
        if not match:
            continue
        timestamp, title = match.groups()
        start = 0
        for piece in timestamp.split(':'):
            start = start*60 + int(piece)
        if name == 'Starfield':
            title = re.sub(r'^\d+\s+', '', title)
        markers.append({'start': start, 'title': title, 'line': line})
    assert len(markers) == {'Starfield': 79, 'Pokémon Legends: Arceus': 109, 'Pokémon Scarlet and Violet': 138}[name]
    tracks = []
    for index, marker in enumerate(markers):
        if index > 0 and marker['start'] < markers[index-1]['start']:
            holds.append({'game': name, 'source_line': marker['line'], 'reason': 'Source timestamp runs backwards. No hour correction or invented cue range is supplied.'})
            continue
        if name == 'Pokémon Scarlet and Violet' and index+1 == len(markers):
            holds.append({'game': name, 'source_line': marker['line'], 'reason': 'Last indexed Main Game title-screen marker is followed by over two hours of unindexed DLC audio. No two-hour title-screen cut or guessed DLC chapters.'})
            continue
        end = markers[index+1]['start'] if index+1 < len(markers) else duration
        if end <= marker['start']:
            holds.append({'game': name, 'source_line': marker['line'], 'reason': 'Next source timestamp runs backwards, so this preceding cue has no verified end.'})
            continue
        assert 0 <= marker['start'] < end <= duration
        if name == 'Starfield':
            version = 'Original 2023 Starfield base-game soundtrack, from the actual Bethesda publisher album. No Shattered Space expansion or other-game score.'
            scope = 'Publisher explicitly identifies Inon Zur as original score composer.'
        elif name == 'Pokémon Scarlet and Violet':
            version = 'Original Nintendo Switch main-game score archive. Only source-indexed Main Game passages selected; the unindexed DLC tail is excluded. Uploader global Ed Sheeran roster is not assigned to these score cues.'
            scope = 'Honest original-game collective music credit, including guest writers. Original staff roster and engineering/performance roles retained at game level only; individual cue authorship is not separately asserted.'
        else:
            version = 'Original Nintendo Switch Pokémon Legends: Arceus game-score archive, with source-named areas, battle phases and legacy themes. Uploader Switch2 platform claim is not adopted as capture evidence.'
            scope = 'Honest original-game collective music credit, including legacy Pokémon themes. Original staff roster and coordination roles retained at game level only; individual cue authorship is not separately asserted.'
        tracks.append({'youtube_id': video_id, 'url': 'https://www.youtube.com/watch?v=' + video_id,
                       'source_page': 'https://www.youtube.com/watch?v=' + video_id,
                       'title': marker['title'], 'creator': composer, 'composer_source': credit_url,
                       'artist_credit_scope': scope, 'game_level_music_roles': roles,
                       'start_seconds': marker['start'], 'end_seconds': end,
                       'duration_seconds': end-marker['start'], 'source_actual_chapter_line': marker['line'],
                       'source_publication_duration_seconds': duration,
                       'uploader': author, 'channel_url': 'https://www.youtube.com/channel/' + pub['channelId'],
                       'primary_published_title': pub['title'], 'official_uploader_verified': name == 'Starfield',
                       'publishing_kind': 'official_game_recording' if name == 'Starfield' else 'archival_game_recording',
                       'recording_version': version, 'recording_year': year,
                       'recording_platform': 'Capture hardware not identified' if name == 'Starfield' else 'Nintendo Switch game; capture hardware not identified',
                       'rights': 'Bethesda Softworks / Inon Zur and credited recording contributors.' if name == 'Starfield' else 'Nintendo / The Pokémon Company / Game Freak and credited original and legacy music authors. Vyntwon is an archival uploader.',
                       'native_codec_metadata_verified': True,
                       'native_codec_metadata_receipt': receipt['native_codec_receipt'],
                       'publication_metadata_receipt': path.relative_to(ROOT).as_posix(),
                       'playback_verified_on_ps5': False})
    assert len(tracks) == count, (name, len(tracks))
    assert len({(track['youtube_id'], track['start_seconds'], track['end_seconds']) for track in tracks}) == count
    entries.append({'entry_id': entry_id, 'match_title': name, 'match_year': year, 'title': 'Listen to ' + name,
                    'composer': composer, 'curator_note': 'Listen to the music of ' + composer + '\n' + name,
                    'replace_existing_tracks': True, 'full_album_collection': name == 'Starfield',
                    'coverage_status': 'published_album_collection' if name == 'Starfield' else 'partial',
                    'recording_collection_scope': str(count) + ' available selectable real source passages. ' + ('Named original publisher album, not every game stem or later expansion.' if name == 'Starfield' else 'Original-game archival collection, not a complete commercial-master or NintendoMusic album claim. Broken markers/unindexed tails remain excluded.'),
                    'album_completeness': {'verified_available_tracks': count,
                                           'inventory_source': 'https://www.youtube.com/watch?v=' + video_id,
                                           'scope': 'Published source-indexed collection; no listening, audio-fingerprint or physical-console claim.'},
                    'tracks': tracks})
    source_receipts.append({'local_path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)})
credit_path = OUT / 'pokemon-original-game-role-web-read-receipt.json'
credit_path.write_text(json.dumps({'sources': [{'url': row[7], 'actual_web_page_read': True,
    'source_type': 'Transcription of original game staff roll, corroborated by MobyGames indexed credit fields (direct Moby body returned403; not falsely claimed read).',
    'game': row[2], 'game_level_music_roles': row[8]} for row in profiles if row[2] != 'Starfield'],
    'scope': 'Original Game Freak sound team and guest-composer roster is credited collectively at game level only. Licensed vocal tracks are not invented from the uploader global roster; no cue here is called an Ed Sheeran composition.'}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
source_receipts.append({'local_path': credit_path.relative_to(ROOT).as_posix(), 'sha256': sha(credit_path)})
target = OUT / 'pokemon-starfield323-available-public-candidate.json'
assert not target.exists(), 'Immutable checkpoint exists'
target.write_text(json.dumps({'schema_version': 1, 'publication_status': 'awaiting_independent_peer',
                              'entries': entries, 'source_receipts': source_receipts, 'held_source_passages': holds}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'candidate': target.relative_to(ROOT).as_posix(), 'sha256': sha(target), 'selectable_tracks': sum(len(entry['tracks']) for entry in entries)}))
