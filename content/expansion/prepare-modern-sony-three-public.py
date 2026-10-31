"""Available publisher albums, exact games; collector padding never admitted."""
import hashlib
import json
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/modern-public-albums'
load = lambda path: json.loads(path.read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
research = load(OUT / 'sony-three-publication-research.json')
primary = {
    'gow2018': ('https://bearmccreary.com/god-of-war/', 'God of War'),
    'ragnarok': ('https://bearmccreary.com/god-of-war-ragnarok/', 'Hozier'),
    'returnal': ('https://www.milanrecords.com/release/returnal-vinyl/', 'Bobby Krlic'),
}
receipts = []
for key, (url, needle) in primary.items():
    destination = OUT / (key + '-composer-publisher-primary.html')
    receipt = {'url': url}
    try:
        if not destination.exists():
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=20) as response:
                data = response.read()
            assert needle.casefold() in data.decode('utf-8', errors='replace').casefold()
            assert b'Client Challenge' not in data[:4000]
            destination.write_bytes(data)
        receipt.update(actual_body_retrieved=True, local_path=destination.relative_to(ROOT).as_posix(), sha256=sha(destination))
    except Exception as error:
        receipt.update(actual_body_retrieved=False, actual_web_page_read=True, error=str(error),
                       web_read_scope='Composer first-person / label primary page actually read through web tool; no false saved-HTML claim.')
    receipts.append(receipt)

entries, held = [], []
for key, entry_id, name, year in [
    ('gow2018', 'wikipedia-50810460', 'God of War', 2018),
    ('ragnarok', 'wikipedia-65333536', 'God of War Ragnar\u00f6k', 2022),
    ('returnal', 'workbook-04-30-returnal', 'Returnal', 2021),
]:
    tracks = []
    for row in research['tracks']:
        if row['collection'] != key:
            continue
        source = row['source']
        if row['status'] != 'metadata_candidate':
            held.append({'game': name, 'youtube_id': source['id'], 'reason': row.get('error') or 'Public identity incomplete; not retried or invented.'})
            continue
        publication = row['publication']
        description = publication.get('shortDescription') or ''
        assert publication['title'] == source['title'] and publication['author'] == source['channel']
        assert load(ROOT / row['native_codec_receipt']).get('native_compatible_avc_aac') is True
        assert abs(float(publication['lengthSeconds']) - source['duration']) <= 3
        title = source['title']
        composer = 'Bobby Krlic' if key == 'returnal' else 'Bear McCreary'
        roles = {}
        if key == 'gow2018':
            assert 'Ragnar' not in title and publication['author'] in ['Bear McCreary, Composer', 'SonySoundtracksVEVO']
            title = title.removeprefix('Bear McCreary - ').split(' | God of War ')[0].split(' (From "God of War" Soundtrack)')[0]
            assert 'Composer' in description or 'Music by Bear McCreary' in description
            version = 'God of War original 2018 score; official Sony Classical / Sony Soundtracks publication.'
            if 'Farewell to Faye Version' in title:
                version += ' Farewell to Faye version, 2021 digital single delivery (2018 recording copyright), distinct from the main album version.'
            if 'Memories of Mother' in title:
                roles['vocals'] = ['Eiv\u00f8r']
        elif key == 'ragnarok':
            assert publication['author'] == 'SonySoundtracksVEVO'
            if 'Valhalla' in title:
                held.append({'game': name, 'youtube_id': source['id'], 'reason': 'Official Valhalla expansion publication kept outside this base2022 album selection.'})
                continue
            if source['id'] == '-32-6FqGW2E':
                title = 'Blood Upon the Snow'
                composer = 'Hozier and Bear McCreary'
                assert 'Music by Hozier and Bear McCreary' in description
                roles['vocals'] = ['Hozier']
            else:
                assert 'Music by Bear McCreary' in description
                title = title.removeprefix('Bear McCreary - ').split(' | God of War Ragnar')[0]
                if 'ft. Eiv\u00f8r' in source['title']:
                    roles['vocals'] = ['Eiv\u00f8r']
            version = 'God of War Ragnar\u00f6k original 2022 soundtrack; official Sony Soundtracks audio / Blood Upon the Snow lyric-video publication. No Valhalla tracks included.'
        else:
            assert publication['author'] == 'Bobby Krlic'
            assert 'Returnal (Original Soundtrack)' in description
            assert any('Composer' in line.partition(':')[0] and line.partition(':')[2].strip() == 'Bobby Krlic' for line in description.splitlines() if ':' in line)
            version = 'Returnal original 2021 soundtrack album; official Milan / Sony licensed recording.'
        role_lines = [line for line in description.splitlines() if re.match(r'^(?:Composer[^:]*|Associated Performer[^:]*|Producer[^:]*|Music by[^:]*|Lyricist[^:]*):?\s', line)]
        track = {'youtube_id': source['id'], 'url': source['url'], 'title': title,
                 'creator': composer, 'composer_source': primary[key][0],
                 'additional_recording_roles': roles, 'source_music_role_lines': role_lines,
                 'uploader': publication['author'], 'channel_url': 'https://www.youtube.com/channel/' + publication['channelId'],
                 'source_page': source['url'], 'primary_published_title': publication['title'],
                 'official_uploader_verified': True, 'publishing_kind': 'official_game_recording',
                 'recording_version': version, 'recording_year': year,
                 'duration_seconds': float(publication['lengthSeconds']),
                 'rights': 'Original Sony Interactive Entertainment game music and recordings, licensed to Sony Music / Sony Classical / Milan, and credited authors and performers. Original publisher/artist upload.',
                 'native_codec_metadata_verified': True, 'native_codec_metadata_receipt': row['native_codec_receipt'],
                 'publication_metadata_receipt': (OUT / 'sony-three-public-individuals' / (source['id'] + '.json')).relative_to(ROOT).as_posix(),
                 'playback_verified_on_ps5': False}
        if 'Farewell to Faye Version' in title:
            track['recording_year'] = 2021
        tracks.append(track)
    assert len({track['youtube_id'] for track in tracks}) == len(tracks)
    if key == 'ragnarok':
        assert len(tracks) == 28
        listing = next(row['publication']['shortDescription'] for row in research['tracks'] if row['source']['id'] == '-32-6FqGW2E')
        marker = {match.group(2): int(match.group(1)) for match in re.finditer(r'(?m)^(\d+)\. (.+?) - (?:Bear McCreary|Hozier and Bear McCreary)', listing)}
        assert len(marker) == 28 and {track['title'] for track in tracks} == set(marker)
        for track in tracks:
            track['album_track_number'] = marker[track['title']]
        tracks.sort(key=lambda track: track['album_track_number'])
    complete = key in ['ragnarok', 'returnal']
    entries.append({'entry_id': entry_id, 'match_title': name, 'match_year': year,
                    'title': 'Listen to ' + name, 'composer': 'Bobby Krlic' if key == 'returnal' else 'Bear McCreary' + (' and Hozier' if key == 'ragnarok' else ''),
                    'curator_note': 'Listen to the music of ' + ('Bobby Krlic' if key == 'returnal' else 'Bear McCreary') + '\n' + name,
                    'replace_existing_tracks': True, 'full_album_collection': complete,
                    'coverage_status': 'complete_published_album_inventory' if complete else 'partial',
                    'album_completeness': {'expected_tracks': 28 if key == 'ragnarok' else 9 if key == 'returnal' else 21,
                                           'verified_album_tracks': len(tracks) if key != 'gow2018' else len(tracks) - 1,
                                           'verified_available_tracks': len(tracks), 'inventory_source': primary[key][0],
                                           'scope': 'Named original published album, with available official public recordings. Not all game stems, future DLC or platform variants. GodofWar2018 includes separately identified FarewelltoFaye single.'},
                    'tracks': tracks})
assert sum(len(entry['tracks']) for entry in entries) == 53
result = {'schema_version': 1, 'publication_status': 'awaiting_independent_peer', 'entries': entries,
          'source_receipts': receipts, 'held_publications': held,
          'excluded_collector_padding': research['excluded_playlist_padding'],
          'scope': 'Three available real publisher/artist collections,53 selectable publications. No unrelated collector padding, fan covers or false full-game completeness.'}
target = OUT / 'godofwar-ragnarok-returnal53-public-candidate.json'
assert not target.exists(), 'Immutable checkpoint already exists'
target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'candidate': target.relative_to(ROOT).as_posix(), 'sha256': sha(target), 'counts': {entry['match_title']: len(entry['tracks']) for entry in entries}}))
