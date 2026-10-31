"""Prepare original KHII album checkpoint using actual individual public recordings."""
import copy
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/kingdom-hearts-complete'


def main():
    research = json.loads((OUT / 'kh2-original89-final-publication-research.json').read_text(encoding='utf-8'))
    rows = research['tracks']
    assert len(rows) == 89
    assert all(row['status'] == 'metadata_candidate' and row['native_compatible_avc_aac'] for row in rows)
    primary = 'https://coverartarchive.org/release/18994f7c-1d7a-3b74-8e04-6e35e87372b9/5046229074.jpg'
    sources = ['https://www.khwiki.com/Kingdom_Hearts_II_Original_Soundtrack', primary]
    tracks = []
    for row in rows:
        expected = row['expected']
        disc, number = expected['disc'], expected['disc_track']
        key = (disc, number)
        composer = 'Yoko Shimomura'
        if key in [(1, 2), (1, 3), (2, 33)]: composer = 'Hikaru Utada'
        if key in [(1, 34), (2, 4), (2, 5)]: composer = 'Alan Menken'
        if key == (1, 45): composer = 'Jimmie Dodd'
        if key == (1, 50): composer = 'Richard M. Sherman, Robert B. Sherman'
        if key == (2, 9): composer = 'Klaus Badelt, Geoff Zanelli, Hans Zimmer'
        if key == (2, 14): composer = 'Danny Elfman'
        if key == (2, 24): composer = 'Nobuo Uematsu'
        roles = {}
        if key in [(1, 1), (1, 2), (2, 23), (2, 34), (2, 35), (2, 36), (2, 37)]: roles['orchestral_arrangement'] = ['Kaoru Wada']
        if key == (2, 38): roles.update(piano_arrangement=['Kaoru Wada'], piano=['Shinko Ogata'])
        if key in [(1, 2), (2, 34)]: roles['orchestra'] = ['Tokyo Philharmonic']
        if key in [(1, 3), (2, 33)]: roles['vocals'] = ['Hikaru Utada']
        if key in [(1, 34), (2, 4), (2, 5)]: roles['original_work_lyrics'] = ['Howard Ashman']
        if key in [(1, 34), (1, 45), (1, 50), (2, 4), (2, 5), (2, 9), (2, 14), (2, 24)]: roles['arrangement'] = ['Yoko Shimomura']
        if key == (1, 4): roles['saxophone'] = ['Hitoshi Ohori']
        publication = row['publication']
        duration = float(publication['lengthSeconds'])
        assert abs(duration - expected['duration_seconds']) <= 4
        video_id = row['source']['id']
        tracks.append({
            'album_track_number': expected['number'], 'album_disc': disc, 'disc_track_number': number,
            'youtube_id': video_id, 'url': 'https://www.youtube.com/watch?v=' + video_id,
            'title': expected['title'], 'creator': composer, 'composer_source': primary,
            'additional_context_sources': sources,
            'primary_printed_roles_receipt': str((OUT / 'kh2-complete2007-printed-primary-roles-receipt.json').relative_to(ROOT)).replace('\\', '/'),
            'additional_recording_roles': roles,
            'artist_credit_scope': 'Original-game composition and named recording-role exceptions corroborated against actual printed2007 COMPLETE booklet pp15–16. This does not claim that later/longer2007 edits are used: source recordings follow the original89item2006 two-disc order and durations. Unspecified vocal cast and per-recording engineering roles are not invented.',
            'uploader': publication['author'], 'channel_url': 'https://www.youtube.com/channel/' + publication['channelId'],
            'source_page': 'https://www.youtube.com/watch?v=' + video_id,
            'primary_published_title': publication['title'], 'official_uploader_verified': False,
            'publishing_kind': 'archival_game_recording', 'duration_seconds': duration,
            'recording_version': 'Original 2006 Japanese two-disc89track soundtrack album; original PlayStation 2 game score, not HD2.5 rerecording. Public archival publication.',
            'recording_album': 'KINGDOM HEARTS II Original Soundtrack (TOCT-25871/2)', 'recording_year': 2006,
            'rights': 'Composition, performance and recording rights remain with the named authors, Disney, Square Enix and original recording owners; archival uploads are not official publisher deliveries.',
            'native_codec_metadata_verified': True, 'native_codec_metadata_receipt': row['native_codec_receipt'],
            'publication_metadata_receipt': row.get('publication_metadata_receipt') or str((OUT / 'kh2-original89-individuals' / (video_id + '.json')).relative_to(ROOT)).replace('\\', '/'),
            'publication_metadata_scope': publication.get('metadata_source', 'Actual public publication identity, description and duration'),
            'playback_verified_on_ps5': False,
        })
    baseline = json.loads((ROOT / 'content/expansion/soundtrack-independent-approved.json').read_text(encoding='utf-8'))
    old = next(entry for entry in baseline['entries'] if entry.get('entry_id') == 'wikipedia-1745270')
    retained = copy.deepcopy(old['tracks'])
    for row in retained:
        row['collection_section'] = 'Previously independently approved original-theme/official alternate-version supplement, outside the original89item album inventory.'
    entry = {'entry_id': old['entry_id'], 'match_title': 'Kingdom Hearts II', 'match_year': 2005,
             'title': 'Listen to Kingdom Hearts II', 'composer': 'Yoko Shimomura, Hikaru Utada and guest composers',
             'curator_note': 'Listen to the music of Yoko Shimomura, Hikaru Utada and guest composers\nKingdom Hearts II',
             'replace_existing_tracks': True, 'full_album_collection': True,
             'coverage_status': 'COMPLETE_PUBLISHED_ORIGINAL_JAPANESE_TWO_DISC_ALBUM_WITH_PRIOR_SUPPLEMENTS',
             'album_completeness': {'expected_tracks': 89, 'verified_album_tracks': 89, 'retained_supplements': len(retained),
                                    'source': sources[0], 'scope': 'Original2006 two-disc album; later2007 expanded album, FinalMix, HD rerecordings and regional vocal variants are not all covered by this89track completeness claim.',
                                    'qualification': 'Actual publication metadata, printed primary work-role credits, original album order/duration comparison and native-codec compatibility; no fingerprint/listening/PS5 playback claim.'},
             'tracks': tracks + retained}
    target = OUT / 'kh2-original89-plus-prior-supplements-candidate.json'
    assert not target.exists(), 'Immutable checkpoint already exists'
    target.write_text(json.dumps({'schema_version': 1, 'publication_status': 'awaiting_independent_peer', 'entries': [entry]}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'path': str(target), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'album_tracks': 89, 'prior_supplements': len(retained)}))


if __name__ == '__main__':
    main()
