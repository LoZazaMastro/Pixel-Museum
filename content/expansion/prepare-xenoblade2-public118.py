"""Available exact-game recordings, with explicit Torna expansion versions."""
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/nintendo-full'
load = lambda path: json.loads(path.read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
research = load(OUT / 'xenoblade2-available-publication-research.json')
fallbacks = load(OUT / 'xenoblade2-public-public-oembed-fallback-research.json')
replacements = {row['source']['id']: row for row in fallbacks['tracks'] if row['status'] == 'metadata_candidate'}
rows = sorted([replacements.get(row['source']['id'], row) for row in research['tracks']], key=lambda row: row['source_playlist_position'])
base_primary = 'https://www.procyon-studio.co.jp/special/xbostportal/en/xb2ost.html'
torna_primary = 'https://new.procyon-studio.co.jp/special/xbostportal/en/xb2iraost.html'
primary_receipt_path = OUT / 'xenoblade2-original-publisher-web-read-receipt.json'
primary_receipt = {'sources': [base_primary, torna_primary], 'actual_web_pages_read': True,
                   'direct_http_body_retrieved': False,
                   'direct_http_note': 'Main host returned494-byte protocol/port landing page instead of album content. Preserved separately as raw-unverified, never used as composer evidence.',
                   'publisher_facts_read': 'Original base album:105 tracks,2018 publication for2017 NintendoSwitch game. Music composersYasunoriMitsuda,ACE(TOMOriKudo,CHiCO),KenjiHiramatsu,ManamiKiyota. Torna has its own explicitly separate2018 official expansion album. Composer/arranger credit distinctions are present on publisher pages; no invented per-cue mapping of archive game-rip variants to commercial masters.',
                   'collective_credit_scope': 'Game/album-level collective display, not every roster member assigned to every cue. Per-cue composer/arranger details retained in linked original publisher sources.'}
primary_receipt_path.write_text(json.dumps(primary_receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
tracks = []
for row in rows:
    assert row['status'] == 'metadata_candidate'
    source, pub = row['source'], row['publication']
    assert pub['title'] == source['title'] and pub['author'] == 'J.O.E. VGM'
    assert pub['channelId'] == 'UCfb7SiX9k7y1LkGyepdEGdg'
    assert load(ROOT / row['native_codec_receipt']).get('native_compatible_avc_aac') is True
    assert abs(float(pub['lengthSeconds']) - source['duration']) <= 3
    is_torna = 'Torna ~ The Golden Country OST' in source['title']
    title = re.split(r'\s+-\s+Xenoblade Chronicles 2(?:: Torna ~ The Golden Country)? OST\s+\[\d+\]', source['title'])[0].strip()
    assert title and title != source['title'] and '(beta)' not in title.lower()
    tracks.append({'youtube_id': source['id'], 'url': source['url'], 'source_page': source['url'],
                   'title': title, 'creator': 'Xenoblade Chronicles 2 music team',
                   'uploader': pub['author'], 'channel_url': 'https://www.youtube.com/channel/' + pub['channelId'],
                   'primary_published_title': pub['title'], 'source_playlist_position': row['source_playlist_position'],
                   'composer_source': torna_primary if is_torna else base_primary,
                   'game_album_composer_context': ['Yasunori Mitsuda', 'ACE (TOMOri Kudo, CHiCO)', 'Kenji Hiramatsu', 'Manami Kiyota'],
                   'artist_credit_scope': 'Collective game/album-level display. Names in game_album_composer_context are the independently publisher-credited game roster, not a claim that all of them wrote this individual cue. Exact publisher composition/arrangement divisions remain linked in Sources; unidentified archive variants are not assigned invented personal credits.',
                   'recording_version': 'Xenoblade Chronicles 2: Torna ~ The Golden Country official 2018 expansion, original public game-rip variant as named; not the base2017 album.' if is_torna else 'Original 2017 Nintendo Switch Xenoblade Chronicles 2 public game-rip publication; source-named cutscene/loop variants retained, not certified2018 editedCD masters.',
                   'recording_year': 2018 if is_torna else 2017, 'recording_platform': 'Nintendo Switch',
                   'collection_section': 'Torna ~ The Golden Country (2018 expansion)' if is_torna else 'Xenoblade Chronicles 2 (2017 game)',
                   'duration_seconds': float(pub['lengthSeconds']),
                   'official_uploader_verified': False, 'publishing_kind': 'archival_game_recording',
                   'rights': 'Nintendo / MONOLITHSOFT / Septima Ley and credited music authors, arrangers and performers. J.O.E. VGM is the archive uploader, not the official soundtrack publisher.',
                   'native_codec_metadata_verified': True, 'native_codec_metadata_receipt': row['native_codec_receipt'],
                   'publication_metadata_receipt': row.get('publication_metadata_receipt') or (OUT / 'xenoblade2-public-individuals' / (source['id'] + '.json')).relative_to(ROOT).as_posix(),
                   'playback_verified_on_ps5': False})
assert len(tracks) == 118 and len({row['youtube_id'] for row in tracks}) == 118
entry = {'entry_id': 'wikipedia-52857364', 'match_title': 'Xenoblade Chronicles 2', 'match_year': 2017,
         'title': 'Listen to Xenoblade Chronicles 2', 'composer': 'Xenoblade Chronicles 2 music team',
         'curator_note': 'Listen to the music of the Xenoblade Chronicles 2 music team\nXenoblade Chronicles 2',
         'replace_existing_tracks': True, 'full_album_collection': False, 'coverage_status': 'partial',
         'recording_collection_scope': '118 available original-game/official-expansion archival recordings, with each2017base/2018Torna version identified. Explicit beta publication excluded. Not an edited105-track base-album or all-game-exhaustiveness assertion.',
         'album_completeness': {'verified_available_tracks': len(tracks),
                                'base_game_archival_recordings': sum(row['recording_year'] == 2017 for row in tracks),
                                'torna2018_archival_recordings': sum(row['recording_year'] == 2018 for row in tracks),
                                'inventory_source': 'https://www.youtube.com/playlist?list=PLIpqsKgkQEvMUFbngp-GbW1JwDGXnxcm9',
                                'scope': 'Available named public original-game recordings and explicit same-game expansion variants; failed/private/not-in-collection music is not described as absent.'},
         'tracks': tracks}
result = {'schema_version': 1, 'publication_status': 'awaiting_independent_peer', 'entries': [entry],
          'source_receipts': [{'local_path': primary_receipt_path.relative_to(ROOT).as_posix(), 'sha256': sha(primary_receipt_path), 'actual_web_pages_read': True}],
          'held_publications': research['excluded_beta_publication'],
          'scope': 'Actual public archive metadata/native verification,2 honest publicoEmbed presentation fallbacks; no downloads, login workaround, audio fingerprint or physical-console playback claim.'}
target = OUT / 'xenoblade2-available118-public-candidate.json'
assert not target.exists(), 'Immutable checkpoint exists'
target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'candidate': target.relative_to(ROOT).as_posix(), 'sha256': sha(target), 'counts': entry['album_completeness']}))
