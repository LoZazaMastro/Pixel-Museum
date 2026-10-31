"""Prepare an immutable research checkpoint, never publish without peer review."""
import copy
import hashlib
import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/kingdom-hearts-complete'
spec = importlib.util.spec_from_file_location('reconcile', ROOT / 'content/expansion/reconcile-kingdom-hearts-original-albums.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


def main():
    chapters, publication = r.chapters('1xwQs5gKTo4')
    inventory = r.kh1_inventory()
    original_scan = OUT / 'kh1-original-printed-credits.png'
    tracklist_scan = OUT / 'kh1-original-printed-tracklist.png'
    primary = 'https://coverartarchive.org/release/cc716887-be12-3d0c-a7ae-34d2c6fa5613/15777195764.png'
    tracklist_source = 'https://coverartarchive.org/release/cc716887-be12-3d0c-a7ae-34d2c6fa5613/15777191101.png'
    receipt = {
        'source_kind': 'Actual original Toshiba EMI TOCT-24768/9 printed booklet, original artifact scan hosted by Cover Art Archive',
        'original_product_release': '2002-03-27',
        'primary_credits_image': str(original_scan.relative_to(ROOT)).replace('\\', '/'),
        'primary_credits_source': primary,
        'primary_credits_sha256': hashlib.sha256(original_scan.read_bytes()).hexdigest(),
        'primary_tracklist_image': str(tracklist_scan.relative_to(ROOT)).replace('\\', '/'),
        'primary_tracklist_source': tracklist_source,
        'primary_tracklist_sha256': hashlib.sha256(tracklist_scan.read_bytes()).hexdigest(),
        'actual_visual_read': True,
        'credit_summary': {
            'default_composition_and_arrangement': 'Yoko Shimomura',
            'composition_exceptions': {'1-02,1-03,2-23,2-30': 'Hikaru Utada', '1-07': 'Jimmie Dodd',
                                       '1-35,1-38': 'Richard M. Sherman; Robert B. Sherman',
                                       '2-07': 'Alan Menken', '2-12': 'Danny Elfman'},
            'role_exceptions': {'1-02,2-31': 'Kaoru Wada: orchestral arrangement; New Japan Philharmonic: orchestra',
                                '1-03': 'Russell McNamara: production and remix (PLANITb)',
                                '2-30': 'Kei Kawano; Hikaru Utada: arrangement; Hikaru Utada: all vocals',
                                '2-32': 'Takahito Eguchi: arrangement',
                                '2-35': 'Tokyo Philharmonic Chorus: chorus',
                                '2-07': 'Howard Ashman: words of original licensed work, not composer'},
        },
        'scope': 'Printed primary work/recording roles, not proof of audio fingerprint equivalence of the public archival upload.',
    }
    (OUT / 'kh1-original-printed-primary-roles-receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    tracks = []
    for expected, passage in zip(inventory, chapters):
        number, disc, disc_track = expected['number'], expected['disc'], expected['disc_track']
        key = (disc, disc_track)
        creator = 'Yoko Shimomura'
        if key in [(1, 2), (1, 3), (2, 23), (2, 30)]: creator = 'Hikaru Utada'
        if key == (1, 7): creator = 'Jimmie Dodd'
        if key in [(1, 35), (1, 38)]: creator = 'Richard M. Sherman, Robert B. Sherman'
        if key == (2, 7): creator = 'Alan Menken'
        if key == (2, 12): creator = 'Danny Elfman'
        roles = {'arrangement': ['Yoko Shimomura']}
        if key in [(1, 2), (2, 31)]: roles = {'orchestral_arrangement': ['Kaoru Wada'], 'orchestra': ['New Japan Philharmonic']}
        if key == (1, 3): roles = {'production_and_remix': ['Russell McNamara (PLANITb)'], 'vocals': ['Hikaru Utada']}
        if key == (2, 30): roles = {'arrangement': ['Kei Kawano', 'Hikaru Utada'], 'vocals': ['Hikaru Utada'],
                                   'production': ['Akira Miyake', 'Hikaru Utada', 'Teruzane Utada']}
        if key == (2, 32): roles = {'arrangement': ['Takahito Eguchi']}
        if key == (2, 35): roles['chorus'] = ['Tokyo Philharmonic Chorus']
        if key == (2, 7): roles['original_work_lyrics'] = ['Howard Ashman']
        video_id = 'cIcOIdoMrcg' if number == 76 else '1xwQs5gKTo4'
        actual = json.loads((OUT / (video_id + '-actual-publication-research.json')).read_text(encoding='utf-8'))
        assert actual['native_avc_aac'] is True
        source = actual['publication']
        row = {
            'album_track_number': number, 'album_disc': disc, 'disc_track_number': disc_track,
            'youtube_id': video_id, 'url': 'https://www.youtube.com/watch?v=' + video_id,
            'title': passage['title'], 'creator': creator,
            'composer_source': primary, 'original_album_tracklist_source': tracklist_source,
            'primary_printed_roles_receipt': str((OUT / 'kh1-original-printed-primary-roles-receipt.json').relative_to(ROOT)).replace('\\', '/'),
            'additional_recording_roles': roles,
            'uploader': source['author'], 'channel_url': 'https://www.youtube.com/channel/' + source['channelId'],
            'source_page': 'https://www.youtube.com/watch?v=' + video_id,
            'official_uploader_verified': False, 'publishing_kind': 'archival_game_recording',
            'duration_seconds': int(source['lengthSeconds']) if number == 76 else passage['duration_seconds'],
            'recording_version': 'Original 2002 Japanese PlayStation 2 soundtrack album, TOCT-24768/9; public archival recording.',
            'recording_year': 2002, 'recording_album': 'KINGDOM HEARTS Original Soundtrack (Japanese original 2002)',
            'rights': 'Composition, performance and recording rights remain with the credited authors, Disney, Square Enix and original recording owners. Public archival upload is not an official publisher delivery.',
            'native_codec_metadata_verified': True,
            'native_codec_metadata_receipt': actual['native_codec_receipt'],
            'publication_metadata_receipt': str((OUT / (video_id + '-actual-publication-research.json')).relative_to(ROOT)).replace('\\', '/'),
            'primary_published_title': source['title'], 'source_publication_duration_seconds': int(source['lengthSeconds']),
            'artist_credit_scope': 'Cue-specific composition and role exceptions follow the original printed booklet. Source-declared recording identity, not audio fingerprint or physical-console playback verification.',
            'playback_verified_on_ps5': False,
        }
        if number < 76:
            row['start_seconds'] = passage['start_seconds']
            row['end_seconds'] = passage['end_seconds']
            row['source_actual_chapter_title'] = passage['title']
            assert abs(row['duration_seconds'] - expected['expected_seconds']) <= 3
        else:
            row['replacement_context'] = 'Actual individual D2/T35 publication explicitly identifies TOCT-24768/9, 27 March 2002;175sec matches originalCD reference. Avoids the full-video187sec ending/padding passage without inventing a cut.'
        tracks.append(row)
    baseline = json.loads((ROOT / 'content/expansion/soundtrack-independent-approved.json').read_text(encoding='utf-8'))
    old = next(entry for entry in baseline['entries'] if entry.get('entry_id') == 'workbook-03-28-kingdom-hearts')
    retained = [copy.deepcopy(row) for row in old['tracks'] if row['youtube_id'] != '1xwQs5gKTo4']
    assert len(retained) == 5
    for row in retained:
        row['collection_section'] = 'Previously independently approved artist/official alternate-version supplement; not counted in the76item original Japanese album inventory.'
    entry = {
        'entry_id': old['entry_id'], 'match_title': 'Kingdom Hearts', 'match_year': 2002,
        'title': 'Listen to Kingdom Hearts',
        'composer': 'Yoko Shimomura, Hikaru Utada and Disney composers',
        'curator_note': 'Listen to the music of Yoko Shimomura, Hikaru Utada and Disney composers\nKingdom Hearts',
        'replace_existing_tracks': True, 'full_album_collection': True,
        'coverage_status': 'COMPLETE_PUBLISHED_ORIGINAL_JAPANESE_ALBUM_PLUS_DOCUMENTED_SUPPLEMENTS',
        'album_completeness': {'expected_tracks': 76, 'verified_album_tracks': 76, 'retained_alternate_version_supplements': 5,
                               'inventory_source': tracklist_source,
                               'recording_scope': '75actual source chapter passages plus1individual original album recording; no timestamp reconstruction. Five prior approved supplements preserved after album, not counted as extra originalCDtracks.',
                               'qualification': 'Metadata, primary printed-work credits and public native-codec compatibility; not audio fingerprint, exhaustive every regional/gamerip variant, or PS5 playback.'},
        'tracks': tracks + retained,
    }
    result = {'schema_version': 1, 'publication_status': 'awaiting_independent_peer',
              'scope': 'Original Japanese album76, each selectable, with5previously approved official supplements preserved. No automatic source admission.',
              'entries': [entry], 'primary_roles_receipt': str((OUT / 'kh1-original-printed-primary-roles-receipt.json').relative_to(ROOT)).replace('\\', '/')}
    target = OUT / 'kh1-original76-plus5-preserved-candidate.json'
    assert not target.exists(), 'Immutable research checkpoint already exists'
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'candidate': str(target), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'album_tracks': 76, 'supplements': len(retained)}))


if __name__ == '__main__':
    main()
