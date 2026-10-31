"""Available unextended public Luigi's Mansion3 archive, with distinct staff roles."""
import collections
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/nintendo-full'
load = lambda path: json.loads(path.read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
research_path = OUT / 'luigi3-available-publication-research.json'
fallback_path = OUT / 'luigi3-public-public-oembed-fallback-research.json'
research, fallback = load(research_path), load(fallback_path)
fallback_by_id = {row['source']['id']: row for row in fallback['tracks']}
credit_url = "https://www.mariowiki.com/List_of_Luigi%27s_Mansion_3_staff"
credit = {'sources': [{'url': credit_url, 'actual_web_page_read': True,
                       'source_type': 'Transcription of original2019 game staff roll; original credit roles, not a guessed per-cue list'},
                      {'url': 'https://themushroomkingdom.net/credits/lm3/USA',
                       'source_type': 'Independent transcription of the original USA Switch staff roll',
                       'actual_public_search_excerpt_read': True}],
          'game_level_music_roles': {'music_composition': ['Chad York', 'Darren Radtke'],
                                     'audio_director': ['Chad York'],
                                     'additional_musicians': ['Meghan Verdejo', 'Mike Peacock'],
                                     'nintendo_sound_supervisors': ['Kazumi Totaka', 'Toru Asakawa', 'Megumi Inoue']},
          'scope': 'Next Level Games music team is a collective original-game credit. Composition, additional performance and sound-supervision roles remain distinct; no claim that every named person composed every individual cue or later mode variant.'}
credit_path = OUT / 'luigi3-original-game-music-role-web-read-receipt.json'
credit_path.write_text(json.dumps(credit, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
tracks, holds = [], []
for original in sorted(research['tracks'], key=lambda row: row['source_playlist_position']):
    row = original if original['status'] == 'metadata_candidate' else fallback_by_id.get(original['source']['id'], original)
    if row['status'] != 'metadata_candidate':
        holds.append({'youtube_id': row['source']['id'], 'source_title': row['source']['title'], 'reason': row.get('error') or 'Presentation identity incomplete'})
        continue
    pub, source = row['publication'], row['source']
    video_id = source['id']
    assert pub['author'] == source['channel'] == "Metaru's Mansion"
    assert pub['title'] == source['title']
    match = re.match(r"Luigi's Mansion 3 Music\s*-\s*(.+)", pub['title'])
    assert match and not re.search(r'extended|remix|mashup|\bcover\b', pub['title'], re.I)
    assert row['native_compatible_avc_aac'] is True
    native = load(ROOT / row['native_codec_receipt'])
    assert native['native_compatible_avc_aac'] is True
    duration = float(pub['lengthSeconds'])
    assert duration > 0 and abs(duration-float(source['duration'])) <= 3
    tracks.append({'youtube_id': video_id, 'url': 'https://www.youtube.com/watch?v=' + video_id,
                   'source_page': 'https://www.youtube.com/watch?v=' + video_id,
                   'title': match.group(1).strip(), 'creator': 'Next Level Games music team',
                   'composer_source': credit_url, 'game_level_music_roles': credit['game_level_music_roles'],
                   'artist_credit_scope': credit['scope'],
                   'duration_seconds': duration, 'source_playlist_position': row['source_playlist_position'],
                   'uploader': pub['author'], 'channel_url': 'https://www.youtube.com/channel/' + pub['channelId'],
                   'primary_published_title': pub['title'], 'official_uploader_verified': False,
                   'publishing_kind': 'archival_game_recording',
                   'recording_version': "Luigi's Mansion 3 Nintendo Switch game-score archive, including source-named hotel, ghost-catching, ScareScraper and ScreamPark mode variants. Later mode/update cues are not all asserted to be2019 launch recordings.",
                   'recording_platform': 'Nintendo Switch',
                   'rights': "Nintendo / Next Level Games and credited music authors and performers; Metaru's Mansion is an archival uploader.",
                   'native_codec_metadata_verified': True, 'native_codec_metadata_receipt': row['native_codec_receipt'],
                   'publication_metadata_receipt': row.get('publication_metadata_receipt') or (OUT / 'luigi3-public-individuals' / (video_id + '.json')).relative_to(ROOT).as_posix(),
                   'public_presentation_fallback': 'oEmbed' if 'oEmbed' in pub.get('metadata_source', '') else '',
                   'playback_verified_on_ps5': False})
assert len(tracks) == 318 and len(holds) == 3
assert len({track['youtube_id'] for track in tracks}) == 318
duplicates = {title: count for title, count in collections.Counter(t['title'] for t in tracks).items() if count > 1}
assert not duplicates, duplicates
entry = {'entry_id': 'workbook-10-31-luigi-s-mansion-3', 'match_title': "Luigi's Mansion 3", 'match_year': 2019,
         'title': "Listen to Luigi's Mansion 3", 'composer': 'Next Level Games music team',
         'curator_note': "Listen to the music of Next Level Games music team\nLuigi's Mansion 3",
         'replace_existing_tracks': True, 'full_album_collection': False, 'coverage_status': 'partial',
         'recording_collection_scope': '318 available unextended archival game/mode recordings from the cited public collection. Three cached native-unavailable recordings remain excluded; no claim of a complete official album or every game stem.',
         'album_completeness': {'verified_available_tracks': 318, 'native_unavailable': 3,
                                'inventory_source': 'https://www.youtube.com/playlist?list=PLOrEojpA3r6TX_SYLqVmmJWmQbyucAy6v',
                                'scope': 'Available public score and gameplay/mode variations. Extended duplicates and fan edits excluded; later modes retained with honest scope rather than false launch-year claims.'},
         'tracks': tracks}
result = {'schema_version': 1, 'publication_status': 'awaiting_independent_peer', 'entries': [entry],
          'held_source_recordings': holds, 'excluded_extended_or_other_edits': len(research['excluded_extended_edits']),
          'source_receipts': [{'local_path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)}
                              for path in (research_path, fallback_path, credit_path)],
          'scope': 'Actual-publication identity and native AVC/AAC metadata verification; six ordinary public oEmbed presentation fallbacks do not fabricate descriptions. No listening, fingerprint, CD-master or physical-console assertion.'}
target = OUT / 'luigi3-available318-public-candidate.json'
assert not target.exists(), 'Immutable checkpoint exists'
target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'candidate': target.relative_to(ROOT).as_posix(), 'sha256': sha(target), 'selectable_tracks': len(tracks)}))
