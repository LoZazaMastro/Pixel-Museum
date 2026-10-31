"""Available publisher-album recordings; preserve discordant presentations as holds."""
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/modern-public-albums'
load = lambda path: json.loads(path.read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
research_path = OUT / 'ff7rebirth-available-publication-research.json'
fallback_path = OUT / 'ff7rebirth-public-public-oembed-fallback-research.json'
reconcile_path = OUT / 'ff7rebirth-channel-reconciled-public-research.json'
research, fallback, reconciled = load(research_path), load(fallback_path), load(reconcile_path)
replacements = {row['source']['id']: row for dataset in [fallback, reconciled] for row in dataset['tracks'] if row['status'] == 'metadata_candidate'}
source_url = 'https://www.square-enix-games.com/en_US/home/final-fantasy-vii-rebirth-original-soundtrack-available-now'
album_url = 'https://www.jp.square-enix.com/music/sem/page/FF7rebirth/ost/en/'
tracks, holds = [], []
for original in sorted(research['tracks'], key=lambda row: row['source_playlist_position']):
    video_id = original['source']['id']
    row = original if original['status'] == 'metadata_candidate' else replacements.get(video_id, original)
    if row['status'] != 'metadata_candidate':
        holds.append({'youtube_id': video_id, 'source_title': row['source']['title'], 'reason': 'Public channel/presentation readings not fully reconciled; not claimed absent from the soundtrack.'})
        continue
    pub, source = row['publication'], row['source']
    assert pub['title'] == source['title'] and 'FF7 Rebirth OST Ver.' in pub['title']
    if pub['author'] != source['channel']:
        assert row.get('public_channel_reading_scope') and row.get('corroborated_public_author') == pub['author']
    assert row['native_compatible_avc_aac'] is True
    assert load(ROOT / row['native_codec_receipt'])['native_compatible_avc_aac'] is True
    duration = float(pub['lengthSeconds'])
    assert duration > 0 and abs(duration-float(source['duration'])) <= 3
    description = pub.get('shortDescription') or ''
    lines = []
    if description:
        distributor = 'Provided to YouTube by NexTone Inc.' in description and 'FINAL FANTASY VII REBIRTH Original Soundtrack' in description
        publisher_channel = pub['author'] == 'SQUARE ENIX MUSIC Channel' and '2024 SQUARE ENIX CO., LTD.' in description and re.search(r'^Composer[:：]', description, re.M)
        assert distributor or publisher_channel, (video_id, pub['author'], description[:500])
        lines = [line for line in description.splitlines() if ' · ' in line or re.match(r'^(?:Composer|Arranger|Lyricist)[:：]', line)]
    else:
        # Preserve actual earlier publisher role lines where the same exact ID/title was read.
        old_path = ROOT / 'build/research/soundtrack-broad/watch' / (video_id + '.json')
        if old_path.exists():
            cached = load(old_path)
            if cached['title'] == pub['title'] and 'Provided to YouTube by NexTone Inc.' in cached.get('shortDescription', '') and 'FINAL FANTASY VII REBIRTH Original Soundtrack' in cached.get('shortDescription', ''):
                lines = [line for line in cached['shortDescription'].splitlines() if ' · ' in line]
    creator, additional, credit_source = 'Square Enix music team', {}, album_url
    explicit_composer = re.search(r'^Composer[:：]\s*(.+)$', description, re.M)
    if explicit_composer:
        creator = ', '.join(part.strip() for part in explicit_composer[1].split('/'))
        credit_source = 'https://www.youtube.com/watch?v=' + video_id
        explicit_arranger = re.search(r'^Arranger[:：]\s*(.+)$', description, re.M)
        if explicit_arranger:
            additional['arrangement'] = [part.strip() for part in explicit_arranger[1].split('/')]
    if video_id == 'NKLdUNSxOTE':
        creator = 'Nobuo Uematsu'
        additional = {'vocals': ['Loren Allred']}
        credit_source = source_url
    title = re.sub(r'\s*\(FF7 Rebirth OST Ver\.\)\s*$', '', pub['title'])
    tracks.append({'youtube_id': video_id, 'url': 'https://www.youtube.com/watch?v=' + video_id,
                   'source_page': 'https://www.youtube.com/watch?v=' + video_id,
                   'title': title, 'creator': creator, 'composer_source': credit_source,
                   'artist_credit_scope': 'Collective original album/game music credit. Unlabeled repeated NexTone names are retained literally, not silently interpreted as individual composer/arranger/producer roles. No Promises to Keep composition and performance follow the original publisher announcement.',
                   'additional_recording_roles': additional, 'publisher_music_role_lines': lines,
                   'duration_seconds': duration, 'source_playlist_position': row['source_playlist_position'],
                   'uploader': pub['author'], 'channel_url': 'https://www.youtube.com/channel/' + pub['channelId'],
                   'source_flat_channel': source['channel'], 'source_flat_channel_id': source['channel_id'],
                   'public_channel_reading_scope': row.get('public_channel_reading_scope', ''),
                   'original_android_metadata_receipt': row.get('original_android_metadata_receipt', ''),
                   'primary_published_title': pub['title'], 'official_uploader_verified': True,
                   'publishing_kind': 'official_game_recording',
                   'recording_version': 'Original 2024 Final Fantasy VII Rebirth soundtrack album recording. Full-length available publications, not the similarly named Preview Version, the 1997 original score, Remake or a fan arrangement. Source titles are preserved in their published language.',
                   'recording_year': 2024,
                   'rights': '2024 SQUARE ENIX CO., LTD. and credited original composers, lyricists, arrangers and performers. Original publisher digital album.',
                   'native_codec_metadata_verified': True, 'native_codec_metadata_receipt': row['native_codec_receipt'],
                   'publication_metadata_receipt': row.get('publication_metadata_receipt') or (OUT / 'ff7rebirth-public-individuals' / (video_id + '.json')).relative_to(ROOT).as_posix(),
                   'public_presentation_fallback': 'oEmbed' if 'oEmbed' in pub.get('metadata_source', '') or row.get('public_channel_reading_scope') else '',
                   'playback_verified_on_ps5': False})
assert len(tracks) == 150 and len(holds) == 25, (len(tracks), len(holds))
assert len({track['youtube_id'] for track in tracks}) == 150
entry = {'entry_id': 'wikipedia-71040722', 'match_title': 'Final Fantasy VII Rebirth', 'match_year': 2024,
         'title': 'Listen to Final Fantasy VII Rebirth', 'composer': 'Square Enix music team',
         'curator_note': 'Listen to the music of Square Enix music team\nFinal Fantasy VII Rebirth',
         'replace_existing_tracks': True, 'full_album_collection': False, 'coverage_status': 'partial',
         'recording_collection_scope': '150 verified available publications from the original publisher 175-track album. Twenty-five discordant presentation records remain held; no claim that those compositions are absent or that this is the complete 175-track album.',
         'album_completeness': {'expected_published_album_tracks': 175, 'verified_available_tracks': 150, 'unresolved_source_presentations': 25,
                                'inventory_source': album_url,
                                'scope': 'Available original-album recordings, not every game stem, bonus-disc edition or audio-identical master claim.'},
         'tracks': tracks}
credit_path = OUT / 'ff7rebirth-publisher-album-context-web-read-receipt.json'
credit_path.write_text(json.dumps({'sources': [
    {'url': source_url, 'actual_web_page_read': True, 'verified_context': 'Publisher names the original 175-track April2024 soundtrack and No Promises to Keep LOVELESS version, composed by Nobuo Uematsu.'},
    {'url': album_url, 'actual_web_page_read': True, 'verified_context': 'Publisher original album page distinguishes the seven-disc album, bonus disc and the shorter Preview Version; the LOVELESS performance is distinct from the separate Sony single.'},
    {'url': 'https://press.na.square-enix.com/en-US/FINAL-FANTASY-VII-REBIRTH-Original-Soundtrack-Available-April-10-Selec', 'actual_public_search_excerpt_read': True,
     'verified_context': 'Publisher press release identifies Loren Allred and Nobuo Uematsu for the original game theme, not an invented contribution by the full score roster.'}],
    'scope': 'Primary album context plus exact current-publication identity/duration/native receipts. Consolidated artist presentation differences are retained explicitly, not made generic aliases.'}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
target = OUT / 'ff7rebirth150-available-public-candidate.json'
assert not target.exists(), 'Immutable checkpoint exists'
target.write_text(json.dumps({'schema_version': 1, 'publication_status': 'awaiting_independent_peer', 'entries': [entry],
                              'held_source_recordings': holds,
                              'source_receipts': [{'local_path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)} for path in [research_path, fallback_path, reconcile_path, credit_path]]}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'candidate': target.relative_to(ROOT).as_posix(), 'sha256': sha(target), 'selectable_tracks': len(tracks)}))
