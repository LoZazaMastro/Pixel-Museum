"""Curate available public Switch recordings with transparent collective credits."""
import hashlib
import copy
import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/nintendo-full'
load = lambda path: json.loads(path.read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()

SOURCES = {
    'echoes-primary-team': ('https://www.nintendo.com/au/news-and-articles/ask-the-developer-vol-13-the-legend-of-zelda-echoes-of-wisdom-chapter-4/', 'sound team'),
    'mk8booster-primary-update': ('https://en-americas-support.nintendo.com/app/answers/detail/a_id/26098/', 'Music'),
    'calamity-primary-interview': ('https://m2.4gamer.net/games/528/G052831/20201112110/', '\u30b5\u30a6\u30f3\u30c9'),
    'calamity-original-game': ('https://en.wikipedia.org/wiki/Hyrule_Warriors:_Age_of_Calamity', 'Age of Calamity'),
}


def sources():
    receipts = []
    for key, (url, expected) in SOURCES.items():
        target = OUT / (key + '.html')
        try:
            if target.exists():
                data = target.read_bytes()
            else:
                with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=25) as response:
                    data = response.read()
                assert expected.casefold() in data.decode('utf-8', errors='replace').casefold(), 'Expected content missing'
                target.write_bytes(data)
            text = data.decode('utf-8', errors='replace')
            assert expected.casefold() in text.casefold()
            assert not ('Client Challenge' in text[:3000] or 'Just a moment...' in text[:3000])
            receipts.append({'url': url, 'actual_body_retrieved': True, 'local_path': target.relative_to(ROOT).as_posix(), 'sha256': sha(target)})
        except Exception as error:
            receipts.append({'url': url, 'actual_body_retrieved': False, 'error': str(error)})
    (OUT / 'next-switch-collective-source-receipts.json').write_text(json.dumps(receipts, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return receipts


def main():
    primary_receipts = sources()
    research_path = OUT / 'next-switch-public-collections-research.json'
    research = load(research_path)
    rows = research['tracks']
    fallbacks_path = OUT / 'next-switch-public-public-oembed-fallback-research.json'
    replacements = {row['source']['id']: row for row in load(fallbacks_path)['tracks'] if row['status'] == 'metadata_candidate'}
    rows = [replacements.get(row['source']['id'], row) for row in rows]
    entries, held = [], []
    settings = [
        ('echoes', 'wikipedia-77176762', 'The Legend of Zelda: Echoes of Wisdom', 2024, 'Nintendo sound team',
         'Original2024 Nintendo Switch game-score archive',
         SOURCES['echoes-primary-team'][0], 'PLmjsKrke8etqrBOXARwjIw8Kt736IaWFj'),
        ('mk8booster', 'wikipedia-38323830', 'Mario Kart 8', 2014, 'Nintendo sound team',
         'Mario Kart 8 Deluxe, Nintendo Switch: Booster Course Pass2022–2023 game-score archive',
         SOURCES['mk8booster-primary-update'][0], 'PLmjsKrke8etoziVFGGTiA6czhQirtSk1y'),
        ('calamity', 'wikipedia-65259792', 'Hyrule Warriors: Age of Calamity', 2020, 'Hyrule Warriors: Age of Calamity music team',
         'Original2020 Nintendo Switch game-score archive',
         SOURCES['calamity-primary-interview'][0], 'PLmjsKrke8etp5G_98ABIWOEx7nvU0Hn6S'),
    ]
    for key, entry_id, name, year, team, version, composer_source, playlist_id in settings:
        selected = sorted((row for row in rows if row['collection'] == key), key=lambda row: row['source_playlist_position'])
        tracks = []
        for row in selected:
            source, publication = row['source'], row.get('publication', {})
            if row['status'] != 'metadata_candidate':
                held.append({'game': name, 'id': source['id'], 'reason': row.get('error') or row['status']})
                continue
            assert publication['title'] == source['title']
            assert publication['author'] == 'The Nintendo Music Channel'
            assert publication['channelId'] == 'UCiKzE8Objh2sJfWLU5mxx8w'
            suffix = {'echoes': 'The Legend of Zelda: Echoes of Wisdom Soundtrack',
                      'mk8booster': 'Mario Kart 8 Deluxe: Booster Course Pack Soundtrack',
                      'calamity': 'Hyrule Warriors: Age of Calamity Soundtrack'}[key]
            track_version, recording_year = version, year
            if key == 'echoes' and not source['title'].endswith(suffix):
                held.append({'game': name, 'id': source['id'], 'reason': 'Raw internal asset filename without a documented readable cue/game title; no invented title or identity assumption.'})
                continue
            if key == 'calamity' and not source['title'].endswith(suffix):
                assert source['title'].endswith(('Hyrule Warriors Age of Calamity: Pulse of the Ancients Soundtrack',
                                                'Hyrule Warriors Age of Calamity: Guardian of Remembrance'))
                extension = 'Pulse of the Ancients' if 'Pulse of the Ancients' in source['title'] else 'Guardian of Remembrance'
                track_version = 'Hyrule Warriors: Age of Calamity, Nintendo Switch: ' + extension + ' official 2021 expansion game-score archive'
                recording_year = 2021
            elif key != 'echoes':
                assert source['title'].endswith(suffix)
            assert abs(float(publication['lengthSeconds']) - source['duration']) <= 3
            native = load(ROOT / row['native_codec_receipt'])
            assert native.get('native_compatible_avc_aac') is True
            title = source['title'].split('\u2014', 1)[0].strip()
            assert title and title != source['title']
            tracks.append({'youtube_id': source['id'], 'url': source['url'], 'title': title,
                           'creator': team, 'uploader': publication['author'],
                           'channel_url': 'https://www.youtube.com/channel/' + publication['channelId'],
                           'source_page': source['url'], 'primary_published_title': publication['title'],
                           'source_playlist_position': row['source_playlist_position'],
                           'composer_source': composer_source,
                           'artist_credit_scope': 'Collective game/album-level credit, not an assertion that every named member composed this individual cue. Individual cue authorship is not separately documented.',
                           'recording_version': track_version + '; public archival recording, not a publisher-issued upload or certified edited album master.',
                           'recording_year': recording_year if key != 'mk8booster' else 2022,
                           'recording_release_scope': '2022–2023 Booster Course Pass; individual course-wave year not separately assigned.' if key == 'mk8booster' else 'Original game version named by this publication.',
                           'recording_platform': 'Nintendo Switch',
                           'duration_seconds': float(publication['lengthSeconds']),
                           'official_uploader_verified': False, 'publishing_kind': 'archival_game_recording',
                           'rights': 'Original music and game recordings belong to Nintendo' + (', Koei Tecmo' if key == 'calamity' else '') + ', the credited game music authors and other applicable rightsholders; archival uploader credited separately.',
                           'native_codec_metadata_verified': True, 'native_codec_metadata_receipt': row['native_codec_receipt'],
                           'publication_metadata_receipt': row.get('publication_metadata_receipt') or (OUT / 'next-switch-public-individuals' / (source['id'] + '.json')).relative_to(ROOT).as_posix(),
                           'playback_verified_on_ps5': False})
        preserved = []
        if key == 'mk8booster':
            baseline = load(ROOT / 'content/expansion/soundtrack-independent-approved.json')
            old = next((entry for entry in baseline['entries'] if entry.get('entry_id') == entry_id), None)
            if old:
                preserved = [copy.deepcopy(track) for track in old['tracks'] if track['youtube_id'] not in {new['youtube_id'] for new in tracks}]
                for track in preserved:
                    track['collection_section'] = 'Previously independently approved Mario Kart 8 score selection'
                tracks = preserved + tracks
        assert len({track['youtube_id'] for track in tracks}) == len(tracks)
        entries.append({'entry_id': entry_id, 'match_title': name, 'match_year': year,
                        'title': 'Listen to ' + name, 'composer': team,
                        'curator_note': 'Listen to the music of ' + team + '\n' + name,
                        'replace_existing_tracks': True, 'full_album_collection': False, 'coverage_status': 'partial',
                        'recording_collection_scope': version + '; available public archive selections, without an exhaustive-game or exact commercial-album completeness claim.',
                        'album_completeness': {'verified_available_tracks': len(tracks),
                                               'previous_approved_selections_preserved': len(preserved),
                                               'source_public_visible_records': len(selected),
                                               'inventory_source': 'https://www.youtube.com/playlist?list=' + playlist_id,
                                               'scope': 'Available original-game recordings and explicitly identified official DLC version. Failed/private items omitted, not described as absent music.'},
                        'tracks': tracks})
    result = {'schema_version': 1, 'publication_status': 'awaiting_independent_peer', 'entries': entries,
              'source_receipts': primary_receipts, 'held_publications': held,
              'scope': 'Public archive collections with correct game/version identity, transparent collective credits and actual native metadata; no exhaustive order/master or listening/physical-console assertion.'}
    target = OUT / 'echoes-mk8booster-calamity-available-public-candidate.json'
    assert not target.exists(), 'Immutable candidate already exists'
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'candidate': target.relative_to(ROOT).as_posix(), 'sha256': sha(target), 'counts': {entry['match_title']: len(entry['tracks']) for entry in entries}, 'held': len(held)}))


if __name__ == '__main__':
    main()
