"""Freeze the clean original-game archive checkpoint, explicitly partial.

The Nintendo Music community transcription is a reconciliation target, not
evidence that differently looped archival recordings are the same masters.
"""
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/nintendo-full'


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


staff = [
    {'name': 'Atsuko Asahi', 'role': 'Music Lead'},
    {'name': 'Maasa Miyoshi', 'role': 'Music'},
    {'name': 'Takuhiro Honda', 'role': 'Music'},
    {'name': 'Yutaro Takakuwa', 'role': 'Music'},
]
fallbacks = {row['source']['id']: row for row in load(OUT / 'mkworld-clean-freeroam-public-oembed-fallback-research.json')['tracks']}
tracks, decisions = [], []
seen = set()
for archive in ('mkworld-clean-grandprix', 'mkworld-clean-freeroam'):
    document = load(OUT / (archive + '-archive-publication-research.json'))
    for initial in document['tracks']:
        row = fallbacks.get(initial['source']['id'], initial)
        video_id = row['source']['id']
        if row['status'] != 'metadata_candidate':
            decisions.append({'youtube_id': video_id, 'status': 'hold', 'reason': row.get('error', row['status'])})
            continue
        actual = row['publication']
        assert actual['title'] == row['source']['title']
        assert actual['author'] == 'The Nintendo Music Channel'
        assert 'Mario Kart World Soundtrack' in actual['title']
        # The source explicitly joins four race phases. Do not substitute a
        # curator-made seamless compilation for a literal individually named cue.
        if video_id == 'l5XuwkNdcug':
            decisions.append({'youtube_id': video_id, 'status': 'hold', 'reason': 'Curator seamless four-lap compilation; not an individual in-game cue.'})
            continue
        assert video_id not in seen
        seen.add(video_id)
        native_path = ROOT / row['native_codec_receipt']
        native = load(native_path)
        assert native['native_compatible_avc_aac'] and native.get('avc_format_count', 0) > 0 and native.get('aac_format_count', 0) > 0
        duration = float(actual['lengthSeconds'])
        assert abs(duration - row['source']['duration']) <= 3
        title = re.sub(r'\s*\u2014\s*Mario Kart World Soundtrack$', '', actual['title'])
        source_playlist = load(OUT / document['source_playlist'])['playlist_id']
        if not source_playlist.startswith('PL'):
            raise ValueError('Expected actual public playlist identifier')
        metadata_receipt = row.get('publication_metadata_receipt') or 'build/research/soundtrack-broad/watch/' + video_id + '.json'
        assert (ROOT / metadata_receipt).exists()
        tracks.append({
            'youtube_id': video_id, 'url': 'https://www.youtube.com/watch?v=' + video_id,
            'source_page': 'https://www.youtube.com/watch?v=' + video_id,
            'title': title, 'creator': 'Nintendo sound team',
            'composer_source': 'https://www.mariowiki.com/List_of_Mario_Kart_World_staff',
            'uploader': actual['author'],
            'channel_url': 'https://www.youtube.com/channel/UCiKzE8Objh2sJfWLU5mxx8w',
            'official_uploader_verified': False, 'publishing_kind': 'archival_game_recording',
            'recording_version': 'Original 2025 game score archive. Source loop and fade may differ from the later edited Nintendo Music release.',
            'credit_scope': 'Nintendo sound team is a collective game/collection-level credit. Individual cue and arrangement authorship is not separately documented here; no named full roster is assigned to every cue. Earlier themes retain their original authorship.',
            'duration_seconds': duration, 'primary_published_title': actual['title'],
            'recording_context_source': 'https://www.youtube.com/playlist?list=' + source_playlist,
            'rights': 'Music and original game recording rights retained by Nintendo and the credited contributors. The public archival channel is credited without publisher endorsement.',
            'native_codec_metadata_verified': True,
            'native_codec_metadata_receipt': row['native_codec_receipt'],
            'publication_metadata_receipt': metadata_receipt,
            'game_level_music_staff': staff,
            'music_staff_credit_scope': 'Original-game staff roles, not proof that all four people wrote each cue or the earlier compositions it arranges.',
            'playback_verified_on_ps5': False,
        })
        decisions.append({'youtube_id': video_id, 'title': title, 'status': 'metadata_identity_and_codec_pass', 'source_ordinal': row['album_track_number'], 'archive': archive})

assert len(tracks) == 253
entry = {
    'entry_id': 'wikipedia-79613463', 'match_title': 'Mario Kart World', 'match_year': 2025,
    'title': 'Listen to Mario Kart World', 'composer': 'Nintendo sound team',
    'curator_note': 'Listen to the music of the Nintendo sound team\nMario Kart World',
    'replace_existing_tracks': True, 'tracks': tracks,
    'full_album_collection': False, 'coverage_status': 'partial',
    'completeness': {
        'status': 'partial', 'verified_archival_recordings': 253,
        'expected_published_album_tracks_secondary': 348,
        'inventory_source': 'https://www.mariowiki.com/Mario_Kart_World_(Nintendo_Music)',
        'inventory_scope': 'Community transcription of the edited Nintendo Music release; not authenticated primary service metadata.',
        'published_album_reconciliation': 'Open: differently named, looped and faded game archive versions are not silently counted as identical published album tracks.',
        'all_game_music_complete': False,
    },
    'recording_collection_scope': '253 individually identified original-game archival recordings:30 Grand Prix/replay selections and223 Free Roam arrangements. Two native-login failures and one curator-made seamless Rainbow Road compilation remain excluded. This is partial coverage, not a complete348-track Nintendo Music album or a CD-master fingerprint assertion.',
    'staff_source_receipt': 'build/research/soundtrack-broad/nintendo-full/mkworld-original-staff-source-receipt.json',
}
candidate = {'schema_version': 1, 'publication_status': 'awaiting_independent_review', 'entries': [entry]}
destination = OUT / 'mkworld253-clean-original-archive-candidate.json'
destination.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
report = {
    'status': 'AWAITING_INDEPENDENT_REVIEW', 'candidate_sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
    'actual_source_identity_rows_read': 253, 'native_avc_aac_positive': 253,
    'oembed_fallback_presentation_rows': len([row for row in fallbacks.values() if row['status'] == 'metadata_candidate']),
    'description_scope': 'Actual descriptions are preserved as received; public oEmbed recovery has no description and does not invent one.',
    'staff_scope': 'Original-game staff transcription actually read; Nintendo collective credit is game/album level only.',
    'inventory_equivalence_not_asserted': True, 'all_audio_independently_listened': False,
    'physical_ps5_playback_verified': False, 'decisions': decisions,
}
(OUT / 'mkworld253-clean-original-archive-editorial-review.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({key: value for key, value in report.items() if key != 'decisions'}))
