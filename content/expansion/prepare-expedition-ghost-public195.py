"""Actual publisher score publications with literal, role-aware music credits."""
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/modern-public-albums'
load = lambda path: json.loads(path.read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
entries, holds, source_receipts = [], [], []
for key, entry_id, name, year, composer, count in [
    ('expedition33', 'wikipedia-77750771', 'Clair Obscur: Expedition 33', 2025, 'Lorien Testard, Alice Duport-Percier', 173),
    ('ghosttsushima', 'wikipedia-55667140', 'Ghost of Tsushima', 2020, 'Ilan Eshkeri, Shigeru Umebayashi', 22),
]:
    research_path = OUT / (key + '-available-publication-research.json')
    research = load(research_path)
    tracks = []
    for row in sorted(research['tracks'], key=lambda record: record['source_playlist_position']):
        if row['status'] != 'metadata_candidate':
            holds.append({'game': name, 'youtube_id': row['source']['id'], 'source_title': row['source']['title'],
                          'reason': row.get('error') or 'Actual individual publication metadata incomplete; no invented credit.'})
            continue
        pub, video_id = row['publication'], row['source']['id']
        assert pub['title'] == row['source']['title']
        assert row['native_compatible_avc_aac'] is True
        assert load(ROOT / row['native_codec_receipt'])['native_compatible_avc_aac'] is True
        duration = float(pub['lengthSeconds'])
        assert duration > 0 and abs(duration-float(row['source']['duration'])) <= 3
        description = pub['shortDescription']
        additional_roles = {}
        raw_role_lines = []
        if key == 'expedition33':
            assert pub['author'] == 'Sandfall Interactive'
            match = re.search(r'^Composed by\s+(.+?)\s*$', description, re.M)
            assert match, video_id
            credit_text = match[1].strip().rstrip('.')
            # Preserve featured credit literally instead of inventing an individual co-writer role.
            creator = re.sub(r'\s+(?:ft\.|feat\.)\s+', ' feat. ', credit_text)
            title = re.sub(r'^Clair Obscur:\s*Expedition 33\s*\(Original Soundtrack\)\s*(?:-\s*)?', '', pub['title'])
            title = re.sub(r'^\d+\s*-\s*', '', title)
            title = re.sub(r'^Clair Obscur:\s*Expedition 33\s*-\s*', '', title)
            title = re.sub(r'\s*\(Original Soundtrack\)\s*$', '', title).strip()
            for line in description.splitlines():
                role = re.match(r'^(Composer(?:s)?(?:\s*&\s*Lyrics)?|Lyrics|Singer|Vocals|Arranger(?:\s*&\s*Conductor)?|Piano|Violin|Viola|Cello|Double Bass|Mixing Engineer|Choir(?:\s*Conductor)?):\s*(.+?)\s*$', line)
                if role:
                    raw_role_lines.append(line)
                    additional_roles.setdefault(role[1], []).append(role[2])
            role_scope = 'Literal composer/featured credit from the original publisher. A featured singer is not silently converted into a separately documented individual co-writer. Detailed publisher role lines are preserved verbatim.'
            credit_source = 'https://www.youtube.com/watch?v=' + video_id
            version = 'Original Sandfall Interactive public soundtrack recording, including publisher-labeled bonus/instrumental/music-box selections. Available public collection, not a promise that every album edition, demo or later update is covered.'
            rights = '2025 Sandfall Interactive and credited composers, lyricists, arrangers, musicians and recording contributors.'
        else:
            assert pub['author'] in ['Ilan Eshkeri', 'Shigeru Umebayashi - Topic', 'SonySoundtracksVEVO']
            assert 'Ghost of Tsushima' in description
            composer_rows = []
            for line in description.splitlines():
                match = re.match(r'^([^:\n]+):\s*(.+?)\s*$', line)
                if match and any(token in match[1] for token in ['Composer', 'Producer', 'Performer']):
                    raw_role_lines.append(line)
                    additional_roles.setdefault(match[1], []).append(match[2])
                    if 'Composer' in [part.strip() for part in match[1].split(',')]:
                        composer_rows.append(match[2])
            if pub['author'] == 'SonySoundtracksVEVO':
                # These three original album publications explicitly name their individual artist in the title.
                assert row['source_playlist_position'] in [12, 16, 17] and pub['title'].startswith('Ilan Eshkeri - ')
                creator = 'Ilan Eshkeri'
                title = pub['title'].split(' - ', 1)[1].split(' | ', 1)[0]
                if row['source_playlist_position'] == 17:
                    title += ' (feat. Clare Uchima)'
                    additional_roles['vocals'] = ['Clare Uchima']
            else:
                assert len(composer_rows) == 1, video_id
                creator = composer_rows[0]
                title = pub['title'].split(' (from "Ghost of Tsushima"', 1)[0]
            credit_text = creator
            role_scope = 'Individual original-album writer credit from Sony/Masterworks delivery or its explicitly named artist publication. Opposite-album composer listed solely as Producer remains a producer, never added as co-composer of this cue.'
            credit_source = 'https://www.youtube.com/watch?v=' + video_id
            version = 'Original 2020 Ghost of Tsushima (Music from the Video Game) Sony/Masterworks album. Base-game album, not Iki Island, Legends or the separate Ghost of Yotei score.'
            rights = '2020 Sony Interactive Entertainment, LLC., under exclusive license to Sony Music Entertainment, and credited authors/performers.'
        tracks.append({'youtube_id': video_id, 'url': 'https://www.youtube.com/watch?v=' + video_id,
                       'source_page': 'https://www.youtube.com/watch?v=' + video_id,
                       'title': title, 'creator': creator, 'composer_source': credit_source,
                       'artist_credit_scope': role_scope, 'publisher_composition_credit': credit_text,
                       'publisher_music_role_lines': raw_role_lines,
                       'additional_recording_roles': additional_roles,
                       'duration_seconds': duration, 'source_playlist_position': row['source_playlist_position'],
                       'uploader': pub['author'], 'channel_url': 'https://www.youtube.com/channel/' + pub['channelId'],
                       'primary_published_title': pub['title'], 'official_uploader_verified': True,
                       'publishing_kind': 'official_game_recording', 'recording_version': version,
                       'rights': rights,
                       'native_codec_metadata_verified': True, 'native_codec_metadata_receipt': row['native_codec_receipt'],
                       'publication_metadata_receipt': (OUT / (key + '-public-individuals') / (video_id + '.json')).relative_to(ROOT).as_posix(),
                       'playback_verified_on_ps5': False})
        if key == 'ghosttsushima':
            tracks[-1]['recording_year'] = year
    assert len(tracks) == count, (name, len(tracks))
    entry = {'entry_id': entry_id, 'match_title': name, 'match_year': year, 'title': 'Listen to ' + name,
             'composer': composer, 'curator_note': 'Listen to the music of ' + composer + '\n' + name,
             'replace_existing_tracks': True, 'full_album_collection': key == 'ghosttsushima',
             'coverage_status': 'published_album_collection' if key == 'ghosttsushima' else 'partial',
             'recording_collection_scope': str(count) + ' available original publisher/artist recordings. ' + ('The named 22-track base album, not every game stem or expansion.' if key == 'ghosttsushima' else 'Public original collection and explicitly labeled bonus variants; one incomplete public-identity recording remains held. Not an exhaustive all-edition album promise.'),
             'album_completeness': {'verified_available_tracks': count,
                                    'scope': 'Actual public recording metadata and native AVC/AAC, not physical console playback or audio fingerprint certification.'},
             'tracks': tracks}
    entries.append(entry)
    source_receipts.append({'local_path': research_path.relative_to(ROOT).as_posix(), 'sha256': sha(research_path)})
context_path = OUT / 'expedition-ghost-primary-context-web-read-receipt.json'
context_path.write_text(json.dumps({'sources': [
    {'url': 'https://www.expedition33.com/post/composing-the-music', 'actual_web_page_read': True,
     'verified_context': 'Publisher first-person composer article by Lorien Testard; Alice voice role is distinguished, with cue-specific joint composition retained where actual publisher credits name it.'},
    {'url': 'https://www.milanrecords.com/release/ghost-of-tsushima-music-from-the-video-game/', 'actual_web_page_read': True,
     'verified_context': 'Original record label identifies Eshkeri narrative score and Umebayashi exploratory music, original base-game Sony album.'}],
    'scope': 'Individual publication roles retained; album-level author roster is not copied to every cue.'}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
source_receipts.append({'local_path': context_path.relative_to(ROOT).as_posix(), 'sha256': sha(context_path)})
target = OUT / 'expedition-ghost195-qualified-public-candidate.json'
assert not target.exists(), 'Immutable checkpoint exists'
target.write_text(json.dumps({'schema_version': 1, 'publication_status': 'awaiting_independent_peer',
                              'entries': entries, 'source_receipts': source_receipts,
                              'held_source_recordings': holds}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'candidate': target.relative_to(ROOT).as_posix(), 'sha256': sha(target), 'selectable_tracks': sum(len(e['tracks']) for e in entries)}))
