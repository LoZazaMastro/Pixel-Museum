"""Prepare playable published score/song collections using real official videos."""
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/spider-complete'
load = lambda path: json.loads(path.read_text(encoding='utf-8'))


def composer_names(credits):
    result = []
    for line in credits:
        for segment in line.split(' - '):
            fields = [value.strip() for value in segment.split(',')]
            if any(role in ['Composer', 'ComposerLyricist', 'Composer Lyricist'] for role in fields[1:]):
                if fields[0] not in result:
                    result.append(fields[0])
    return result


def main():
    rows = load(OUT / 'three-public-albums67-publication-research.json')['tracks']
    assert len(rows) == 67 and all(row['status'] == 'metadata_candidate' and row['native_compatible_avc_aac'] for row in rows)
    albums = load(OUT / 'original-three-albums-inventory.json')['albums']
    entries = []
    for album in albums:
        year = album['year']
        tracks = []
        for row in [row for row in rows if row['game_year'] == year]:
            expected, publication = row['expected'], row['publication']
            video_id = row['source']['id']
            credits = expected['credits']
            composers = composer_names(credits)
            creator = ', '.join(composers)
            roles = {}
            credit_scope = 'Per-cue composer fields follow the actual original Hollywood/Marvel Music album credits. Other producer, performer, arranger and engineering roles remain distinct in the retained label credit lines.'
            if year == 2020 and row['album_track_number'] == 17:
                creator = 'Jaden'
                composers = [line.split(':', 1)[1].strip() for line in publication['shortDescription'].splitlines() if line.startswith('Composer Lyricist:')]
                assert composers == ['Jaden Smith', 'Omarr Rambert', 'Josiah Bell']
                roles['composition_and_lyrics'] = composers
                roles['recording_artist'] = ['Jaden']
                credit_scope = 'Licensed original game song: creator is the recording artist Jaden. Actual Universal delivery separately identifies all three ComposerLyricist names; no assignment to John Paesano.'
            elif year == 2020 and row['album_track_number'] in [18, 19]:
                creator = 'Lecrae'
                roles['recording_artist'] = ['Lecrae']
                credit_scope = 'Licensed original game song: Lecrae is credited as the recording artist named by his actual official lyric-video publication, which explicitly identifies Miles Morales. Cue-specific songwriter names are not separately supplied in this public metadata and are not guessed; Ritual Film Co. is video production, not music-composition credit.'
            elif year == 2023 and row['album_track_number'] == 20:
                creator = 'EARTHGANG feat. Benji.'
                assert len(composers) == 4
                roles['composition_and_lyrics'] = composers
                roles['recording_artists'] = ['EARTHGANG', 'Benji.']
                credit_scope = 'Licensed game-song recording artists shown as EARTHGANG feat.Benji.; the four exact label ComposerLyricist names are preserved separately, not replaced by John Paesano.'
            else:
                assert composers == ['John Paesano'], (year, expected['item_name'], composers)
            if year == 2023 and row['album_track_number'] == 21:
                roles['version_production'] = ['Surkin']
            assert creator
            version = f'Official original{year} published game soundtrack recording; full available public label/artist video retained without fabricated album-edit cuts.'
            if year == 2023 and row['album_track_number'] == 21:
                version = 'Official2023 album-listed SURKIN remix/version of John Paesano\'s original game score, published by Marvel Music; not a fan remix.'
            actual_seconds = float(publication['lengthSeconds'])
            track = {
                'album_track_number': row['album_track_number'], 'youtube_id': video_id,
                'url': 'https://www.youtube.com/watch?v=' + video_id,
                'title': expected['item_name'], 'creator': creator,
                'composition_credits': composers, 'composer_source': album['url'] if credits else 'https://www.youtube.com/watch?v=' + video_id,
                'artist_credit_scope': credit_scope, 'additional_recording_roles': roles,
                'label_published_track_credits': credits,
                'uploader': publication['author'], 'channel_url': 'https://www.youtube.com/channel/' + publication['channelId'],
                'official_uploader_verified': True, 'publishing_kind': 'official_game_recording',
                'source_page': 'https://www.youtube.com/watch?v=' + video_id,
                'primary_published_title': publication['title'],
                'duration_seconds': actual_seconds, 'recording_year': year,
                'recording_version': version, 'recording_album': album['title'] + ' (Original Video Game Soundtrack)',
                'native_codec_metadata_verified': True, 'native_codec_metadata_receipt': row['native_codec_receipt'],
                'publication_metadata_receipt': str((OUT / 'official-album-individuals' / (video_id + '.json')).relative_to(ROOT)).replace('\\', '/'),
                'playback_verified_on_ps5': False,
                'rights': 'Composition, performance and recording rights remain with the credited authors, artists, Marvel Music, Hollywood Records, Disney, Sony and relevant recording owners; official label/artist publications are credited.',
            }
            if year == 2020 and row['album_track_number'] >= 17 or year == 2023 and row['album_track_number'] == 20:
                track['publishing_kind'] = 'official_licensed_song_recording'
            tracks.append(track)
        assert len(tracks) == album['expected_tracks']
        title = album['title']
        entry = {'entry_id': album['entry_id'], 'match_title': title, 'match_year': year,
                 'title': 'Listen to ' + title,
                 'composer': 'John Paesano' if year == 2018 else 'John Paesano and guest artists',
                 'curator_note': 'Listen to the music of John Paesano' + (' and guest artists' if year != 2018 else '') + '\n' + title,
                 'replace_existing_tracks': True, 'full_album_collection': True,
                 'coverage_status': 'COMPLETE_PUBLISHED_TRACK_INVENTORY_WITH_PUBLIC_VERSION_QUALIFICATION',
                 'album_completeness': {'expected_tracks': album['expected_tracks'], 'verified_album_tracks': len(tracks),
                                        'inventory_source': album['url'],
                                        'scope': 'Every named cue/song in the cited27/19/21 published album has a selectable official public recording; not every unreleased in-game stem, cutscene variation or DLC score. Full public videos may retain label intro/outro padding and named official versions; no identical-CD-master/fingerprint claim.'},
                 'tracks': tracks}
        entries.append(entry)
    source_receipts = [{'source': album['url'], 'path': str((OUT / f"{album['year']}-label.html").relative_to(ROOT)).replace('\\', '/'),
                        'sha256': hashlib.sha256((OUT / f"{album['year']}-label.html").read_bytes()).hexdigest(),
                        'actual_original_album_table': True, 'tracks': album['expected_tracks']} for album in albums]
    result = {'schema_version': 1, 'publication_status': 'awaiting_independent_peer', 'entries': entries,
              'scope': 'Public official versions of all27+19+21 published album cues/songs. Licensed recording artists and songwriters distinguished from Paesano score. No composer inferred from a video-production credit.',
              'source_receipts': source_receipts, 'excluded_source_items': ['74second Swing teaser -i6zFGObBjQ', 'Unreleased collector fillers by ahdukejk', 'wrong-film SpiderVerse releases and gameplay uploads'],
              'previous_selected_cue_policy': 'Prior curated album cues are represented inside these expanded playlists; duplicate uploads of the same cue/version are not appended again.'}
    target = OUT / 'three-public-albums67-candidate.json'
    assert not target.exists(), 'Immutable checkpoint already exists'
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'candidate': str(target), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'games': 3, 'recordings': 67}))


if __name__ == '__main__':
    main()
