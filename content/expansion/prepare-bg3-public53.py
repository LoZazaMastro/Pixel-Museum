"""Available original composer's collection, preserving actual variants and lyricists."""
import collections
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/modern-public-albums'
load = lambda path: json.loads(path.read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
research_path = OUT / 'baldursgate3-available-publication-research.json'
label_path = OUT / 'baldursgate3-label-roles.json'
research, label = load(research_path), load(label_path)
assert label['actual_body_retrieved'] and len(label['tracks']) == 43
assert sha(ROOT / label['local_path']) == label['sha256']
tracks, holds, excluded = [], [], []
for row in sorted(research['tracks'], key=lambda item: item['source_playlist_position']):
    if row['status'] != 'metadata_candidate':
        holds.append({'youtube_id': row['source']['id'], 'title': row['source']['title'], 'reason': row.get('error')})
        continue
    publication, video_id = row['publication'], row['source']['id']
    if video_id == 'H_ETzap9c9g':
        excluded.append({'youtube_id': video_id, 'reason': 'Additional lyrics-video upload of Down By The River omitted to avoid repeating the same titled recording; numbered original-album publication retained.'})
        continue
    assert publication['author'] == 'Borislav Slavov (Bobby)'
    assert publication['title'] == row['source']['title'] and "Baldur's Gate 3" in publication['title']
    assert load(ROOT / row['native_codec_receipt'])['native_compatible_avc_aac'] is True
    duration = float(publication['lengthSeconds'])
    assert duration > 0 and abs(duration-float(row['source']['duration'])) <= 3
    match = re.match(r'^(\d+)\s+', publication['title'])
    album_number = int(match[1]) if match else None
    title = re.sub(r'^\d+\s+', '', publication['title'])
    title = re.sub(r"^Baldur's Gate 3\s*(?:Original Soundtrack|OST)\s*-\s*", '', title)
    title = re.sub(r"^Baldur's Gate 3\s*-\s*(?:OST\s*-\s*)?", '', title).strip(' "')
    description = publication['shortDescription']
    roles, label_role_lines = {}, []
    if album_number:
        assert 1 <= album_number <= 43
        record = label['tracks'][album_number-1]
        label_role_lines = record['credits']
        for line in record['credits']:
            for chunk in line.split(' - '):
                fields = [part.strip() for part in chunk.split(',') if part.strip()]
                if len(fields) > 1 and 'Lyricist' in fields[1:]:
                    roles.setdefault('lyrics', []).append(fields[0])
                if len(fields) > 1 and 'Composer' in fields[1:]:
                    assert fields[0] == 'Borislav Slavov', fields
    for line in description.splitlines():
        match = re.match(r'^Vocal(?:ist|s)?:\s*(.+?)\s*$', line)
        if match:
            # Keep the composer's literal public credits, removing handle/link suffixes only.
            roles.setdefault('vocals', []).extend(part.strip().split(' - @', 1)[0] for part in match[1].split(','))
    version = 'Original-composer public Baldur\'s Gate 3 score collection, including source-named album, camp, city and update variants. Not a claim that every game stem or exact commercial album master is covered.'
    if 'Early Access, Patch 6' in description:
        title += ' (Early Access Patch 6)'
        version = 'Original-composer Early Access Patch 6 camp/credits-menu version, explicitly identified in the publication. Not mislabeled as the final2023 album recording.'
        roles['lyrics'] = ['Sarah Baylus']
        label_role_lines = label['tracks'][41]['credits']
    if 'Extended & Remastered' in publication['title']:
        version = 'Original-composer Harpy Song extended and remastered public version, explicitly titled by the artist. Not a fan remaster or an untouched launch master.'
    elif 'Remastered' in publication['title']:
        version = 'Original-composer Endless Spring remastered public version, explicitly titled by the artist. Not a fan remaster or an untouched launch master.'
    if '*REMIX*' in description:
        version = 'Original-composer public Song of Balduran ghostly remix, explicitly identified by the artist with2024rights context. Separate version, not mislabeled as the original album performance.'
        roles['lyrics'] = ['Lawrence Schick']
        label_role_lines = label['tracks'][30]['credits']
    tracks.append({'youtube_id': video_id, 'url': 'https://www.youtube.com/watch?v=' + video_id,
                   'source_page': 'https://www.youtube.com/watch?v=' + video_id,
                   'title': title, 'creator': 'Borislav Slavov', 'composer_source': label['url'],
                   'artist_credit_scope': 'Original composer publishes this exact recording. Numbered original-album lyricist credits are preserved from actual label delivery; later variants do not imply a fresh lyricist or original-album recording date.',
                   'additional_recording_roles': roles, 'publisher_music_role_lines': label_role_lines,
                   'label_role_receipt': label_path.relative_to(ROOT).as_posix(),
                   'duration_seconds': duration, 'source_playlist_position': row['source_playlist_position'],
                   'uploader': publication['author'], 'channel_url': 'https://www.youtube.com/channel/' + publication['channelId'],
                   'primary_published_title': publication['title'], 'official_uploader_verified': True,
                   'publishing_kind': 'official_game_recording', 'recording_version': version,
                   'rights': 'Wizards of the Coast / Larian Studios / Borislav Slavov and credited original songwriters and performers. Composer-issued source, not an archival impersonation.',
                   'native_codec_metadata_verified': True, 'native_codec_metadata_receipt': row['native_codec_receipt'],
                   'publication_metadata_receipt': (OUT / 'baldursgate3-public-individuals' / (video_id + '.json')).relative_to(ROOT).as_posix(),
                   'playback_verified_on_ps5': False})
assert len(tracks) == 52 and len(holds) == 1
assert len({track['youtube_id'] for track in tracks}) == 52
assert len({track['title'] for track in tracks}) == 52, {title: [track['youtube_id'] for track in tracks if track['title'] == title] for title, count in collections.Counter(track['title'] for track in tracks).items() if count > 1}
entry = {'entry_id': 'wikipedia-60979422', 'match_title': "Baldur's Gate 3", 'match_year': 2023,
         'title': "Listen to Baldur's Gate 3", 'composer': 'Borislav Slavov',
         'curator_note': "Listen to the music of Borislav Slavov\nBaldur's Gate 3",
         'replace_existing_tracks': True, 'full_album_collection': False, 'coverage_status': 'partial',
         'recording_collection_scope': '52 available original-composer recordings, including declared early-access, city/camp and artist-remaster/remix variants. One cached native-unavailable source remains held. Not every game stem or complete all-version discography.',
         'album_completeness': {'verified_available_tracks': 52, 'native_unavailable': 1,
                                'inventory_source': 'https://www.youtube.com/playlist?list=PLi1CK-rsvz1Nfz83RMBp_9YaIgBWd0l9x',
                                'scope': 'Available original-composer public collection. An additional symphonic-song remix is deliberately outside this selection.'},
         'tracks': tracks}
target = OUT / 'baldursgate3-available52-public-candidate.json'
assert not target.exists(), 'Immutable checkpoint exists'
target.write_text(json.dumps({'schema_version': 1, 'publication_status': 'awaiting_independent_peer', 'entries': [entry],
                              'held_source_recordings': holds, 'excluded_duplicate_publications': excluded,
                              'source_receipts': [{'local_path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)}
                                                  for path in (research_path, label_path)]}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'candidate': target.relative_to(ROOT).as_posix(), 'sha256': sha(target), 'selectable_tracks': len(tracks)}))
