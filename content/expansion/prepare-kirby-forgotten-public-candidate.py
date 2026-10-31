"""Expose the available original2022 game-rip, not the2025 expansion."""
import hashlib
import json
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/nintendo-full'
load = lambda path: json.loads(path.read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
research = load(OUT / 'kirby-forgotten-public-research.json')
fallbacks = load(OUT / 'kirby-forgotten-public-public-oembed-fallback-research.json')
by_id = {row['source']['id']: row for row in fallbacks['tracks'] if row['status'] == 'metadata_candidate'}
rows = sorted([by_id.get(row['source']['id'], row) for row in research['tracks']], key=lambda row: row['source_playlist_position'])
primary_url = 'https://www.kirby.jp/news/19352/'
primary_path = OUT / 'kirby-original-official-soundtrack-announcement.html'
if not primary_path.exists():
    # The browser/web reader actually opened this publisher page; directHTTP is503.
    # A receipt is labelled as a web-read summary, never fabricated saved HTML.
    primary_path = OUT / 'kirby-original-official-soundtrack-web-read-receipt.json'
    if not primary_path.exists():
        receipt = {'url': primary_url, 'actual_web_page_read': True,
                   'direct_http_body_retrieved': False, 'direct_http_error': 'HTTP503',
                   'source_title': 'Kirby and the Forgotten Land soundtrack general-sale announcement',
                   'read_page_lines': '28–31,55,81',
                   'publisher_facts_read': 'HAL-published2024 complete soundtrack has115 CD-mastered game BGM/SFX tracks across4discs;33-track selection also released. Original music/game copyrightNintendo/HALLaboratory. This is not a per-cue composer source.'}
        primary_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
tracks, held = [], []
for row in rows:
    source = row['source']
    if row['status'] != 'metadata_candidate':
        held.append({'id': source['id'], 'reason': row.get('error') or row['status']})
        continue
    publication = row['publication']
    assert publication['title'] == source['title']
    assert publication['author'] == 'J.O.E. VGM' and publication['channelId'] == 'UCfb7SiX9k7y1LkGyepdEGdg'
    assert 'Kirby and the Forgotten Land OST [' in source['title']
    assert abs(float(publication['lengthSeconds']) - source['duration']) <= 3
    assert load(ROOT / row['native_codec_receipt']).get('native_compatible_avc_aac') is True
    title = re.sub(r'\s+(?:-\s*)?Kirby and the Forgotten Land OST \[\d+\]$', '', source['title']).strip()
    assert title and title != source['title']
    tracks.append({'youtube_id': source['id'], 'url': source['url'], 'title': title,
                   'creator': 'HAL Laboratory sound team', 'uploader': publication['author'],
                   'channel_url': 'https://www.youtube.com/channel/' + publication['channelId'],
                   'source_page': source['url'], 'primary_published_title': publication['title'],
                   'source_playlist_position': row['source_playlist_position'],
                   'composer_source': primary_url,
                   'artist_credit_scope': 'Honest collective original-game/album credit. The archive gives a game-wide composer roster, not individual cue divisions; no automatic attribution of every cue to every listed person. Individual cue authorship is not separately documented.',
                   'game_score_credit_context': 'Uploader game-wide roster: Hirokazu Ando, Jun Ishikawa, Yuuta Ogasawara and Yuki Shimooka. Kept as contextual uploader evidence, not an exhaustive per-cue authorship assertion.',
                   'recording_version': 'Original 2022 Nintendo Switch game-rip publication; not the 2024 edited CD master or 2025 Star-Crossed World expansion.',
                   'recording_year': 2022, 'recording_platform': 'Nintendo Switch',
                   'duration_seconds': float(publication['lengthSeconds']),
                   'official_uploader_verified': False, 'publishing_kind': 'archival_game_recording',
                   'rights': 'Original game music and recordings: Nintendo / HAL Laboratory, Inc. and credited authors/performers. J.O.E. VGM is the archival uploader, not an official publisher.',
                   'native_codec_metadata_verified': True, 'native_codec_metadata_receipt': row['native_codec_receipt'],
                   'publication_metadata_receipt': row.get('publication_metadata_receipt') or (OUT / 'kirby-forgotten-public-individuals' / (source['id'] + '.json')).relative_to(ROOT).as_posix(),
                   'playback_verified_on_ps5': False})
assert len({track['youtube_id'] for track in tracks}) == len(tracks) == 92
entry = {'entry_id': 'wikipedia-69752856', 'match_title': 'Kirby and the Forgotten Land', 'match_year': 2022,
         'title': 'Listen to Kirby and the Forgotten Land', 'composer': 'HAL Laboratory sound team',
         'curator_note': 'Listen to the music of HAL Laboratory sound team\nKirby and the Forgotten Land',
         'replace_existing_tracks': True, 'full_album_collection': False, 'coverage_status': 'partial',
         'recording_collection_scope': '92 available original2022 public game-score recordings; original collection held4 native-incompatible publications. Not all115 editedCD tracks or the2025 expansion.',
         'album_completeness': {'verified_available_tracks': len(tracks), 'source_public_visible_records': 96,
                                'published_edited_album_reference_count': 115,
                                'inventory_source': 'https://www.youtube.com/playlist?list=PLIpqsKgkQEvNiCJtfwvBd6FL0kiuxB_AL',
                                'scope': 'Public gamerip collection, not a claim of identity or completeness against the115-track2024 officialCD edition.'},
         'tracks': tracks}
result = {'schema_version': 1, 'publication_status': 'awaiting_independent_peer', 'entries': [entry],
          'held_publications': held,
          'source_receipts': [{'url': primary_url, 'actual_web_page_read': True, 'local_path': primary_path.relative_to(ROOT).as_posix(), 'sha256': sha(primary_path)}],
          'scope': 'Real original2022 public archive publications; transparent collective music credit, no audio fingerprint or console-playback assertion.'}
target = OUT / 'kirby-forgotten92-public-candidate.json'
assert not target.exists(), 'Immutable candidate already exists'
target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'candidate': target.relative_to(ROOT).as_posix(), 'sha256': sha(target), 'tracks': len(tracks), 'held': len(held)}))
