"""Public available KHIII score collection, with primary per-cue credits."""
import copy
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/kingdom-hearts-complete'
load = lambda path: json.loads(path.read_text(encoding='utf-8'))

NAMES = {
    '下村 陽子': 'Yoko Shimomura', '宇多田ヒカル': 'Hikaru Utada',
    '石元 丈晴': 'Takeharu Ishimoto', '関戸 剛': 'Tsuyoshi Sekito',
    '島 翔太朗': 'Shotaro Shima', '福井 健一郎': 'Kenichiro Fukui',
    '鈴木 克崇': 'Yoshitaka Suzuki',
}


def main():
    research = load(OUT / 'kh3-original136-final-publication-research.json')
    assert len(research['tracks']) == 136
    assert all(row['status'] == 'metadata_candidate' and row['native_compatible_avc_aac'] for row in research['tracks'])
    primary = load(OUT / 'kh3-publisher-original-per-cue-roles.json')
    by_key = {(row['disc'], row['disc_track']): row for row in primary['tracks']}
    source = 'https://www.jp.square-enix.com/music/sem/page/kh3/'
    native_umg_channels = {row['publication']['channelId'] for row in research['tracks']
                           if 'Provided to YouTube by Universal Music Group' in row['publication']['shortDescription']}
    tracks = []
    for row in research['tracks']:
        expected = row['expected']
        disc, number = expected['disc'], expected['disc_track']
        # Original Japanese publisher includes CHIKAI vocal at6.14; English product page omits it.
        primary_key = (disc, number + 1 if disc == 6 and number >= 14 else number)
        credit = by_key[primary_key]
        composers = [NAMES.get(name.strip(), name.strip()) for name in credit['published_roles']['作曲'].split('、')]
        assert all(not any('\u3040' <= char <= '\u9fff' for char in name) for name in composers), composers
        publication = row['publication']
        video_id = row['source']['id']
        if not publication['shortDescription']:
            assert publication['channelId'] in native_umg_channels
        else:
            assert ('Provided to YouTube by Universal Music Group' in publication['shortDescription']
                    or publication['author'] in ['HollywoodRecordsVEVO', 'DisneyMusicJapanVEVO'])
        version = 'Official2020 original soundtrack album publication; Kingdom Hearts III game score.'
        if disc == 7:
            version = 'Official2020 Re Mind DLC soundtrack publication for the same Kingdom Hearts III game.'
        if disc == 4 and number == 5:
            version = 'Official Disney Japanese Frozen song recording by Takako Matsu, reused in Kingdom Hearts III; full public music-video audio version, not an invented exact CD cut.'
        roles = {}
        if '編曲' in credit['published_roles']:
            roles['arrangement_original_publisher_names'] = credit['published_roles']['編曲'].split('、')
        if disc == 4 and number == 5:
            roles['vocals'] = ['Takako Matsu']
        track = {
            'album_track_number': row['album_track_number'], 'album_disc': disc,
            'disc_track_number': primary_key[1], 'youtube_id': video_id,
            'url': 'https://www.youtube.com/watch?v=' + video_id,
            'title': expected['title'], 'creator': ', '.join(composers),
            'composer_source': source, 'publisher_per_cue_credit_line': credit['published_credit_line'],
            'publisher_original_title': credit['title'], 'additional_recording_roles': roles,
            'uploader': publication['author'], 'channel_url': 'https://www.youtube.com/channel/' + publication['channelId'],
            'source_page': 'https://www.youtube.com/watch?v=' + video_id,
            'primary_published_title': publication['title'], 'official_uploader_verified': True,
            'publishing_kind': 'official_game_recording', 'duration_seconds': float(publication['lengthSeconds']),
            'recording_version': version, 'recording_year': 2020,
            'recording_album': 'KINGDOM HEARTS - III, II.8, Unchained χ & Union χ [Cross] - Original Soundtrack (III/Re Mind selections only)',
            'identity_context': row['identity_context'],
            'artist_credit_scope': 'Actual original Square Enix product site supplies per-cue composition/arrangement fields; arranger names are preserved in publisher spelling rather than guessed romanization. No blanket Shimomura or entire-game-roster credit.',
            'native_codec_metadata_verified': True, 'native_codec_metadata_receipt': row['native_codec_receipt'],
            'publication_metadata_receipt': row.get('publication_metadata_receipt') or str((OUT / 'kh3-original-album-individuals' / (video_id + '.json')).relative_to(ROOT)).replace('\\', '/'),
            'metadata_scope': publication.get('metadata_source'), 'playback_verified_on_ps5': False,
            'rights': 'Composition, arrangement, performance and recording rights remain with the named authors, Disney, Square Enix, Sony and original recording owners; public publisher/label/artist publications are credited.',
        }
        if disc == 4 and number == 5:
            track['recording_year'] = 2013
            track['recording_album'] = 'Frozen original Japanese licensed song, reused in Kingdom Hearts III'
        tracks.append(track)
    baseline = load(ROOT / 'content/expansion/soundtrack-independent-approved.json')
    old = next(entry for entry in baseline['entries'] if entry.get('entry_id') == 'wikipedia-10007933')
    # Existing Xion is the exact same ID now inside the score; existing Dearly is another publication of this same III version.
    retained = [copy.deepcopy(row) for row in old['tracks'] if row['youtube_id'] in ['GPI-pLBjmf4', 'vZGgZotzvXs']]
    assert len(retained) == 2
    for row in retained:
        row['collection_section'] = 'Previously independently approved original English vocal-theme supplement.'
    entry = {'entry_id': old['entry_id'], 'match_title': 'Kingdom Hearts III', 'match_year': 2019,
             'title': 'Listen to Kingdom Hearts III',
             'composer': 'Yoko Shimomura, Hikaru Utada, Takeharu Ishimoto, Tsuyoshi Sekito and guest composers',
             'curator_note': 'Listen to the music of Yoko Shimomura and the Kingdom Hearts III composers\nKingdom Hearts III',
             'replace_existing_tracks': True, 'full_album_collection': False, 'coverage_status': 'partial',
             'album_completeness': {'verified_public_score_recordings': 136, 'prior_english_vocal_supplements': 2,
                                    'all_game_music_complete': False,
                                    'source': source,
                                    'scope': 'Available official III/Re Mind score publications; other-gameII.8/Unchained/Union/BackCover material excluded. Japanese FaceMyFears/CHIKAI album vocal versions not pursued further; previously verified original English vocals preserved. Exact order/master completeness is not asserted.'},
             'tracks': tracks + retained}
    result = {'schema_version': 1, 'publication_status': 'awaiting_independent_peer',
              'scope': 'Available public publisher/label score collection, not a false full-album/master claim. User prioritizes available music over exhaustive album-order perfection.',
              'publisher_primary_html_receipt': {'source': source, 'path': str((OUT / 'kh3-official-original-site.html').relative_to(ROOT)).replace('\\', '/'),
                                                 'sha256': hashlib.sha256((OUT / 'kh3-official-original-site.html').read_bytes()).hexdigest(), 'actual_body_retrieved': True},
              'entries': [entry]}
    target = OUT / 'kh3-public136-plus2-vocals-primary-roles-candidate.json'
    assert not target.exists(), 'Immutable checkpoint already exists'
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'candidate': str(target), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'score_recordings': len(tracks), 'vocal_supplements': len(retained)}))


if __name__ == '__main__':
    main()
