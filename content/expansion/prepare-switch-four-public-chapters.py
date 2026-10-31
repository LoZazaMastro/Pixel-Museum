"""Useful available Switch score collections, with original source timing and scope."""
import hashlib
import json
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/nintendo-full'
load = lambda path: json.loads(path.read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def sec(value):
    result = 0
    for part in value.split(':'):
        result = result * 60 + int(part)
    return result


source_settings = {
    'xeno3': ('https://www.procyon-studio.co.jp/special/xbostportal/en/xb3ost.html', '142'),
    'xenode': ('https://procyon-studio.co.jp/special/xbostportal/en/xbdeost.html', 'Yoko Shimomura'),
    'threehouses': ('https://www.intsys.co.jp/works/sound/202102soundtrack.html', '\u98a8\u82b1\u96ea\u6708'),
    'tropicalfreeze': ('https://www.nintendolife.com/news/2014/02/month_of_kong_tropical_freeze_composer_david_wise_on_working_with_the_ape_again', 'David Wise'),
}
source_receipts = []
for key, (url, expected) in source_settings.items():
    path = OUT / (key + '-score-publisher-primary.html')
    try:
        if not path.exists():
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=20) as response:
                data = response.read()
            text = data.decode('utf-8', errors='replace')
            assert expected.casefold() in text.casefold()
            assert b'Client Challenge' not in data[:5000]
            path.write_bytes(data)
        source_receipts.append({'url': url, 'actual_body_retrieved': True, 'local_path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)})
    except Exception as error:
        source_receipts.append({'url': url, 'actual_body_retrieved': False, 'error': str(error)})

entries, held = [], []
for key, entry_id, name, game_year, recording_year, video_id, expected, author in [
    ('xeno3', 'wikipedia-70031621', 'Xenoblade Chronicles 3', 2022, 2022, 'X03xaFdQCgo', 138, '\ubaa8\ub358\ubba4\uc988 '),
    ('xenode', 'wikipedia-25992553', 'Xenoblade Chronicles', 2010, 2020, 'XXKckBSscmY', 99, 'Nasenmann'),
    ('threehouses', 'wikipedia-57665862', 'Fire Emblem: Three Houses', 2019, 2019, 'tZKm_1T_zxs', 134, 'Full Game Soundtracks'),
    ('tropicalfreeze', 'wikipedia-39645494', 'Donkey Kong Country: Tropical Freeze', 2014, 2014, 'WO1gOFL2fq8', 59, 'DarQ Redd'),
]:
    receipt_path = OUT / (video_id + '-actual-publication-research.json')
    receipt = load(receipt_path)
    pub = receipt['publication']
    assert pub['author'] == author and receipt['native_avc_aac'] is True
    assert load(ROOT / receipt['native_codec_receipt']).get('native_compatible_avc_aac') is True
    markers = []
    future_connected = False
    section = ''
    for line in pub['shortDescription'].splitlines():
        if key == 'xenode' and line.strip() == 'Future Connected:':
            future_connected = True
        if key == 'threehouses' and re.match(r'^\*\d+\*$', line.strip()):
            section = line.strip()
        source_line = line
        if key == 'tropicalfreeze':
            # The actual uploader writes '56 ;43' for HornTopHop; punctuation normalization only.
            normalized = line.replace('56 ;43', '56:43')
            match = re.match(r'^\s*(\d+)\.\s*(.+?)(\d{1,2}:\d{2}(?::\d{2})?)\s*$', normalized)
            if match:
                number, title, timestamp = match.groups()
                title = title.rstrip(' -')
        elif key in ['xeno3', 'xenode']:
            match = re.match(r'^(\d{1,2}:\d{2}(?::\d{2})?)\s*-\s*(\d+)\.\s*(.+)$', line)
            if match:
                timestamp, number, title = match.groups()
        else:
            match = re.match(r'^(\d{1,2}:\d{2}(?::\d{2})?)\s*-\s*(.+)$', line)
            if match:
                timestamp, title = match.groups()
                number = len(markers) + 1
        if match:
            markers.append({'number': int(number), 'title': title.strip(), 'start': sec(timestamp),
                            'source_line': source_line, 'future_connected': future_connected, 'section': section})
    assert len(markers) == expected, (name, len(markers), expected)
    tracks, known_titles = [], set()
    team = name + ' music team'
    for index, marker in enumerate(markers):
        end = markers[index + 1]['start'] if index + 1 < len(markers) else float(pub['lengthSeconds'])
        assert 0 <= marker['start'] < end <= float(pub['lengthSeconds'])
        if key == 'threehouses' and marker['start'] >= sec('8:01:05') and marker['title'] != 'Jingle Selection':
            held.append({'game': name, 'title': marker['title'], 'reason': 'Cross-game amiibo legacy track held outside this original ThreeHouses score selection; no false attribution to current game composer roster.'})
            continue
        if key == 'tropicalfreeze' and marker['title'] in known_titles:
            held.append({'game': name, 'title': marker['title'], 'reason': 'Second same-title archive passage omitted instead of inventing an unverified variant name.'})
            continue
        known_titles.add(marker['title'])
        version = ('2020 Definitive Edition Nintendo Switch score; remastered/original-data variants as individually labelled by the archive.' if key == 'xenode' else
                   'Original 2014 WiiU game score, also associated with the official same-game 2018 Nintendo Switch port; this archive does not certify a Switch capture.' if key == 'tropicalfreeze' else
                   str(recording_year) + ' Nintendo Switch game-score archive, including source-labelled event/battle variations; not edited commercial-album masters.')
        track_year = recording_year
        if key == 'xenode' and marker['future_connected']:
            version += ' Future Connected additional 2020 episode score.'
        if key == 'threehouses' and any(word in marker['title'] for word in ['Legend of the Chalice', 'The Forgotten', 'Woven by Fate', 'Shackled Wolves', 'Shackeld Wolves', 'At What Cost', 'Corridor of the Tempest', 'Steam Baths Respite']):
            version += ' Official Cindered Shadows/update-era 2020 section or variant; not attributed to the 2019 launch-only score.'
            track_year = 2020
        track = {'youtube_id': video_id, 'url': 'https://www.youtube.com/watch?v=' + video_id,
                 'title': marker['title'], 'creator': team,
                 'start_seconds': marker['start'], 'end_seconds': end, 'duration_seconds': end-marker['start'],
                 'source_actual_chapter_line': marker['source_line'],
                 'source_publication_duration_seconds': float(pub['lengthSeconds']),
                 'composer_source': source_settings[key][0],
                 'artist_credit_scope': 'Collective original game/album music-team credit, not a claim that every named composer in the source wrote this individual cue. Individual cue authorship is not separately documented here. Existing-series motifs retain their original authors; named album composer/arranger roles are retained in the linked source.',
                 'uploader': pub['author'], 'channel_url': 'https://www.youtube.com/channel/' + pub['channelId'],
                 'source_page': 'https://www.youtube.com/watch?v=' + video_id,
                 'primary_published_title': pub['title'],
                 'official_uploader_verified': False, 'publishing_kind': 'archival_game_recording',
                 'recording_version': version, 'recording_year': track_year,
                 'recording_platform': 'WiiU' if key == 'tropicalfreeze' else 'Nintendo Switch',
                 'rights': 'Original game music and recordings belong to Nintendo, ' + ('MonolithSoft' if key in ['xeno3', 'xenode'] else 'Intelligent Systems / Koei Tecmo' if key == 'threehouses' else 'Retro Studios') + ' and the credited composers/performers. The archive channel is not an official publisher.',
                 'native_codec_metadata_verified': True, 'native_codec_metadata_receipt': receipt['native_codec_receipt'],
                 'publication_metadata_receipt': receipt_path.relative_to(ROOT).as_posix(), 'playback_verified_on_ps5': False}
        if key == 'tropicalfreeze':
            track['game_level_music_credit_context'] = 'David Wise is the principal music author; additional Nintendo music and legacy-series themes are not silently assigned to him cue-by-cue. Collective score-team display preserves that distinction.'
        tracks.append(track)
    entry = {'entry_id': entry_id, 'match_title': name, 'match_year': game_year,
             'title': 'Listen to ' + name, 'composer': team,
             'curator_note': 'Listen to the music of ' + team + '\n' + name,
             'replace_existing_tracks': key != 'xenode', 'append_existing_tracks': key == 'xenode',
             'full_album_collection': False, 'coverage_status': 'partial',
             'recording_collection_scope': 'Available named game-score archive passages with real uploader markers; not every commercial-master track or all game stems.' + (' Definitive Edition is explicit supplementary 2020 port music, preserving existing original 2010 selections.' if key == 'xenode' else ''),
             'album_completeness': {'verified_available_tracks': len(tracks), 'source_timestamp_passages': len(markers),
                                    'inventory_source': 'https://www.youtube.com/watch?v=' + video_id,
                                    'scope': 'Available source-declared game-loop variants, not an exact editedCD album completeness assertion.'},
             'tracks': tracks}
    entries.append(entry)
result = {'schema_version': 1, 'publication_status': 'awaiting_independent_peer', 'entries': entries,
          'source_receipts': source_receipts, 'held_passages': held,
          'scope': 'Available public Switch game-score collections with genuine timestamp boundaries and transparent game-level collective credits. No audio-fingerprint/listening or physical-console playback assertion.'}
target = OUT / 'xeno3-definitive-threehouses-tropical-public-v2-candidate.json'
assert not target.exists(), 'Immutable checkpoint exists'
target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'candidate': target.relative_to(ROOT).as_posix(), 'sha256': sha(target),
                  'counts': {e['match_title']: len(e['tracks']) for e in entries}, 'held_passages': len(held)}))
