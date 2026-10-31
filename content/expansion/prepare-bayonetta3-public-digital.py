"""Original publisher-linked digital album, honest collective and specific vocal roles."""
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/modern-public-albums'
load = lambda path: json.loads(path.read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
research_path = OUT / 'bayonetta3-available-publication-research.json'
research = load(research_path)
assert len(research['tracks']) == 263 and not research['not_requested_after_breaker'], 'Discovery batch not finished'
primary = {'album_developer_article': 'https://www.platinumgames.com/official-blog/article/13291',
           'publisher_service_page': 'https://lnk.to/bayonetta3',
           'publisher_linked_public_album': 'https://music.youtube.com/playlist?list=OLAK5uy_n3_kNtSWXmxJI2yxEpjj53YmypsY-hTRE',
           'physical_album_tracks': 265, 'available_digital_playlist_items': 263,
           'actual_web_pages_read': True,
           'scope': 'Developer explicitly distinguishes physical265 from digital release with omitted licensed selections. Actual publisher service HTML links this precise YouTubeMusic album; generic Topic channel naming alone is not used as proof of authority.'}
roles = {
    'lead_composer': ['Naofumi Harada'], 'music_supervisor': ['Hiroshi Yamaguchi'],
    'named_game_level_composers_in_developer_article': ['Takumi Higuchi', 'Takashi Nakabeppu', 'Masahiro Miyauchi', 'Tomoki Kameyama', 'Aoba Nakanishi', 'Seiji Hotta', 'Hyun Kim', 'Hitomi Kurokawa', 'Hiroshi Yamaguchi'],
}
credit_path = OUT / 'bayonetta3-primary-digital-and-vocal-role-receipt.json'
credit = {'publication_status': 'research_only', 'album_context': primary, 'game_level_roles': roles,
          'publisher_service_html': {'local_path': (OUT / 'bayonetta3-publisher-services.html').relative_to(ROOT).as_posix(), 'sha256': sha(OUT / 'bayonetta3-publisher-services.html')},
          'vocal_primary_sources': [
              {'url': 'https://www.platinumgames.com/official-blog/article/13238', 'actual_web_page_read': True,
               'composition': ['Hitomi Kurokawa'], 'arrangement': ['Hitomi Kurokawa', 'Naofumi Harada'], 'vocals_and_lyrics': ['Chess Galea'],
               'scope': 'Al Fine. Developer explicitly says Harada did not compose this song; We Are As One motif by Yamaguchi is retained as underlying theme context.'},
              {'url': 'https://www.platinumgames.com/official-blog/article/13258', 'actual_web_page_read': True,
               'composition': ['Tomoki Kameyama'], 'lyrics': ['Cody Matthew Johnson', 'Gina Kouyoumdjian'], 'vocals': ['Mikaila Delgado'], 'vocal_production': ['Steve Knight'], 'mixing': ['Andrew Scheps']},
              {'url': 'https://www.platinumgames.com/official-blog/article/12643', 'actual_web_page_read': True,
               'composition': ['Hiroshi Yamaguchi'], 'vocals_and_lyrics': ['Rachael Hawnt'], 'orchestration_and_conducting': ['John R. Graham'], 'recording_and_mixing': ['Daniel Kresco']}],
          'scope': 'Non-vocal cues carry honest album/game-level collective credit, not every member of the staff roster as individual co-writer. Original source credit lines and legacy-title context are retained without inventing precise roles from repeated unlabeled names.'}
credit_path.write_text(json.dumps(credit, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
tracks, holds = [], []
for row in sorted(research['tracks'], key=lambda item: item['source_playlist_position']):
    if row['status'] != 'metadata_candidate':
        holds.append({'youtube_id': row['source']['id'], 'source_title': row['source']['title'], 'reason': row.get('error') or 'Incomplete public identity'})
        continue
    pub, video_id = row['publication'], row['source']['id']
    description = pub['shortDescription']
    assert pub['title'] == row['source']['title']
    assert 'Provided to YouTube by NexTone Inc.' in description and 'BAYONETTA 3 ORIGINAL SOUNDTRACK' in description
    assert load(ROOT / row['native_codec_receipt'])['native_compatible_avc_aac'] is True
    duration = float(pub['lengthSeconds'])
    assert duration > 0 and abs(duration-float(row['source']['duration'])) <= 3
    creator, additional, composer_source = 'Bayonetta music team', {}, primary['album_developer_article']
    if video_id == '78USyGr7bJU':
        creator = 'Hitomi Kurokawa'
        additional = {'arrangement': ['Hitomi Kurokawa', 'Naofumi Harada'], 'lyrics': ['Chess Galea'], 'vocals': ['Chess Galea'], 'underlying_theme_motif': ['Hiroshi Yamaguchi']}
        composer_source = credit['vocal_primary_sources'][0]['url']
    elif video_id == 'ye0CoTnqzZ8':
        creator = 'Tomoki Kameyama'
        additional = {'lyrics': ['Cody Matthew Johnson', 'Gina Kouyoumdjian'], 'vocals': ['Mikaila Delgado'], 'vocal_production': ['Steve Knight'], 'mixing': ['Andrew Scheps']}
        composer_source = credit['vocal_primary_sources'][1]['url']
    elif video_id == 'Eb6AlhXJrJg':
        creator = 'Hiroshi Yamaguchi'
        additional = {'lyrics': ['Rachael Hawnt'], 'vocals': ['Rachael Hawnt'], 'orchestration': ['John R. Graham'], 'conducting': ['John R. Graham'], 'recording_and_mixing': ['Daniel Kresco']}
        composer_source = credit['vocal_primary_sources'][2]['url']
    source_credit_line = next((line for line in description.splitlines() if ' · ' in line), '')
    assert source_credit_line
    tracks.append({'youtube_id': video_id, 'url': 'https://www.youtube.com/watch?v=' + video_id,
                   'source_page': 'https://www.youtube.com/watch?v=' + video_id,
                   'title': pub['title'], 'creator': creator, 'composer_source': composer_source,
                   'artist_credit_scope': credit['scope'], 'game_level_music_roles': roles,
                   'additional_recording_roles': additional, 'publisher_music_role_lines': [source_credit_line],
                   'publisher_linked_album_source': primary['publisher_linked_public_album'],
                   'duration_seconds': duration, 'source_playlist_position': row['source_playlist_position'],
                   'uploader': pub['author'], 'channel_url': 'https://www.youtube.com/channel/' + pub['channelId'],
                   'primary_published_title': pub['title'], 'official_uploader_verified': True,
                   'publishing_kind': 'official_game_recording',
                   'recording_version': 'Bayonetta 3 original digital soundtrack, NexTone-delivered2023 album of the2022 game. Includes source-named earlier-series material reused in this game. Not the larger physical265-track set or a claim of exact per-cue staff allocation where the delivery supplies only unlabeled names.',
                   'recording_year': 2023, 'recording_platform': 'Nintendo Switch original game soundtrack album',
                   'rights': 'Nintendo / SEGA / PlatinumGames / WAVEMASTER and credited authors, legacy-theme writers, lyricists, arrangers and performers. Publisher-linked original digital album.',
                   'native_codec_metadata_verified': True, 'native_codec_metadata_receipt': row['native_codec_receipt'],
                   'publication_metadata_receipt': (OUT / 'bayonetta3-public-individuals' / (video_id + '.json')).relative_to(ROOT).as_posix(),
                   'playback_verified_on_ps5': False})
assert len(tracks) >= 240 and len(tracks)+len(holds) == 263
assert len({track['youtube_id'] for track in tracks}) == len(tracks)
entry = {'entry_id': 'wikipedia-70079987', 'match_title': 'Bayonetta 3', 'match_year': 2022,
         'title': 'Listen to Bayonetta 3', 'composer': 'Bayonetta music team',
         'curator_note': 'Listen to the music of Bayonetta music team\nBayonetta 3',
         'replace_existing_tracks': True, 'full_album_collection': not holds, 'coverage_status': 'partial' if holds else 'published_digital_album_collection',
         'recording_collection_scope': str(len(tracks)) + ' available original digital album recordings from the precise publisher-linked collection. Native-unavailable/incomplete items remain held; physical-only selections are outside this digital collection. Not a claim to all265 physical masters or every game stem.',
         'album_completeness': {'expected_public_digital_items': 263, 'physical_album_tracks': 265,
                                'verified_available_tracks': len(tracks), 'held_source_items': len(holds),
                                'inventory_source': primary['publisher_linked_public_album'],
                                'scope': 'Published digital album, availability-qualified. No media download, listening, audio fingerprint or physical-console claim.'},
         'tracks': tracks}
target = OUT / 'bayonetta3-available-digital-public-candidate.json'
assert not target.exists(), 'Immutable checkpoint exists'
target.write_text(json.dumps({'schema_version': 1, 'publication_status': 'awaiting_independent_peer', 'entries': [entry],
                              'held_source_recordings': holds,
                              'source_receipts': [{'local_path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)} for path in (research_path, credit_path)]}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'candidate': target.relative_to(ROOT).as_posix(), 'sha256': sha(target), 'selectable_tracks': len(tracks), 'held': len(holds)}))
