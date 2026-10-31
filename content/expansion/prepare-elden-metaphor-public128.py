"""Two available named original-game collections, not all stems or all later editions."""
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/modern-public-albums'
load = lambda path: json.loads(path.read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
profiles = [
    ('QvbDgcA9nSU', 'wikipedia-61002621', 'Elden Ring', 2022, 'Eduardo Tomazzoni', 'FromSoftware sound team', 67,
     'https://gamemusic.bn-ent.net/en/gametitle/', 'Original 2022 base-game soundtrack. Public archival recording of the named 67-track album; not Shadow of the Erdtree, Nightreign, a fan arrangement, or an official uploader.'),
    ('2UF3IyhC7Ys', 'wikipedia-74017718', 'Metaphor: ReFantazio', 2024, 'Compendium', 'Shoji Meguro', 61,
     'https://www.nintendo.com/en-ca/store/products/metaphor-refantazio-digital-soundtrack-70050000076564-switch-2/', 'Original 2024 Special Soundtrack, 61-track selection, public archival recording. Not the larger 131-track 2025 album or a 2026 Switch 2 game-capture claim.'),
]
entries, sources = [], []
for video_id, entry_id, name, year, author, composer, expected, source, version in profiles:
    path = OUT / (video_id + '-actual-publication-research.json')
    receipt = load(path)
    pub = receipt['publication']
    assert pub['author'] == author and receipt['native_avc_aac'] is True
    assert load(ROOT / receipt['native_codec_receipt'])['native_compatible_avc_aac'] is True
    markers = []
    for line in pub['shortDescription'].splitlines():
        match = re.match(r'^(\d+:\d{2}(?::\d{2})?)\s+(?:-\s*)?(.+?)\s*$', line)
        if not match:
            continue
        timestamp, title = match.groups()
        start = 0
        for piece in timestamp.split(':'):
            start = start*60 + int(piece)
        markers.append({'start': start, 'title': title, 'line': line})
    assert len(markers) == expected
    duration = float(pub['lengthSeconds'])
    tracks = []
    for index, marker in enumerate(markers):
        end = markers[index+1]['start'] if index+1 < len(markers) else duration
        assert 0 <= marker['start'] < end <= duration
        scope = 'Primary publisher album is credited collectively to FromSoftware Sound Team. The five-name original-game roster is not assigned as individual co-authors of every cue.' if name == 'Elden Ring' else 'Primary publisher special 61-track soundtrack explicitly identifies Shoji Meguro. Not a claim that he alone composed the entire larger game score or that every later album performance is identical.'
        tracks.append({'youtube_id': video_id, 'url': 'https://www.youtube.com/watch?v=' + video_id,
                       'source_page': 'https://www.youtube.com/watch?v=' + video_id,
                       'title': marker['title'], 'creator': composer, 'composer_source': source,
                       'artist_credit_scope': scope,
                       'start_seconds': marker['start'], 'end_seconds': end,
                       'duration_seconds': end-marker['start'], 'source_actual_chapter_line': marker['line'],
                       'source_publication_duration_seconds': duration,
                       'uploader': author, 'channel_url': 'https://www.youtube.com/channel/' + pub['channelId'],
                       'primary_published_title': pub['title'], 'official_uploader_verified': False,
                       'publishing_kind': 'archival_game_recording', 'recording_version': version,
                       'recording_year': year, 'recording_platform': 'Capture hardware not identified',
                       'rights': 'FromSoftware / Bandai Namco and credited authors and recording contributors; Eduardo Tomazzoni is an archival uploader.' if name == 'Elden Ring' else 'ATLUS / SEGA / Shoji Meguro and credited performers/production contributors; Compendium is an archival uploader.',
                       'native_codec_metadata_verified': True, 'native_codec_metadata_receipt': receipt['native_codec_receipt'],
                       'publication_metadata_receipt': path.relative_to(ROOT).as_posix(),
                       'playback_verified_on_ps5': False})
    entries.append({'entry_id': entry_id, 'match_title': name, 'match_year': year, 'title': 'Listen to ' + name,
                    'composer': composer, 'curator_note': 'Listen to the music of ' + composer + '\n' + name,
                    'replace_existing_tracks': True, 'full_album_collection': True, 'coverage_status': 'published_album_collection',
                    'recording_collection_scope': str(expected) + ' available source-indexed passages from ' + ('the original 2022 base-game album.' if name == 'Elden Ring' else 'the original 2024 Special Soundtrack selection, not the later 131-track full album.') + ' Not every game stem, an audio-identical master certification or physical console playback.',
                    'album_completeness': {'verified_available_tracks': expected, 'inventory_source': source,
                                           'scope': 'Named published album/selection only, using real public source boundaries. Original archival uploader clearly distinguished from publisher.'},
                    'tracks': tracks})
    sources.append({'local_path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)})
credit_path = OUT / 'elden-metaphor-publisher-context-web-read-receipt.json'
credit_path.write_text(json.dumps({'sources': [
    {'url': profiles[0][7], 'actual_web_page_read': True,
     'verified_context': 'Bandai Namco Game Music lists the original2022 Elden Ring album as FromSoftware Sound Team, separately from Erdtree and Nightreign.'},
    {'url': profiles[1][7], 'actual_web_page_read': True,
     'verified_context': 'SEGA-provided Nintendo store description explicitly calls it a61-track special soundtrack by Shoji Meguro. The2026 Switch2 store release is not treated as the2024 recording date.'},
    {'url': 'https://asia.sega.com/metaphor/en/', 'actual_public_search_excerpt_read': True,
     'verified_context': 'Original publisher game site identifies Shoji Meguro and the separately named Special Soundtrack.'},
    {'url': 'https://www.famitsu.com/article/202411/24340', 'actual_public_search_excerpt_read': True,
     'source_type': 'First-person composer interview with editorial album note',
     'verified_context': 'Special selection contains Meguro pieces; other ATLUS music staff also worked on the larger game score. Do not copy their roster to every special-album cue.'}],
    'scope': 'Primary publisher album identity/author context plus literal archival source chapters, without an exhaustive master-matching claim.'}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
sources.append({'local_path': credit_path.relative_to(ROOT).as_posix(), 'sha256': sha(credit_path)})
target = OUT / 'elden-metaphor128-readable-public-candidate.json'
assert not target.exists(), 'Immutable checkpoint exists'
target.write_text(json.dumps({'schema_version': 1, 'publication_status': 'awaiting_independent_peer', 'entries': entries,
                              'source_receipts': sources}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'candidate': target.relative_to(ROOT).as_posix(), 'sha256': sha(target), 'selectable_tracks': sum(len(entry['tracks']) for entry in entries)}))
