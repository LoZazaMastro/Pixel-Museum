"""Freeze available original Wii U music publications for independent review."""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'build/research/soundtrack-broad/splatoon-original-2015'
load = lambda p: json.loads(p.read_text(encoding='utf8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
research = load(FOLDER / 'native-publication-research.json')
playlist = load(FOLDER / 'playlist-original-flat.json')
old_research = load(ROOT / 'build/research/soundtrack-broad/games/wikipedia-52874820.json')
assert old_research['composers'] == ['Toru Minegishi', 'Shiho Fujii']
tracks = []
sources = []
for record in research['records']:
    if record['status'] != 'native_metadata_verified_pending_semantic_peer':
        continue
    meta = record['metadata']
    title = re.sub(r'-Splatoon\s*\[OST\]\s*$', '', meta['title']).strip()
    receipt = ROOT / record['metadata_file']
    sources.append({'path': record['metadata_file'], 'sha256': sha(receipt)})
    tracks.append({
        'youtube_id': meta['id'], 'url': 'https://www.youtube.com/watch?v=' + meta['id'],
        'title': title, 'source_actual_publication_title': meta['title'],
        'creator': 'Nintendo sound team',
        'game_composer_credits': ['Toru Minegishi', 'Shiho Fujii'],
        'artist_credit_scope': 'Game-level music credits; no unsupported per-cue allocation or fictional-band attribution as a real composer.',
        'composer_source': old_research['composer_source'],
        'recording_year': 2015,
        'recording_version': 'Original Wii U game archival music publication.',
        'recording_context_source': 'https://www.youtube.com/playlist?list=' + playlist['id'],
        'uploader': meta['channel'], 'channel_url': 'https://www.youtube.com/channel/' + meta['channel_id'],
        'source_page': 'https://www.youtube.com/watch?v=' + meta['id'],
        'publishing_kind': 'archival_game_recording', 'official_uploader_verified': False,
        'duration_seconds': int(meta['duration']),
        'rights': 'Nintendo and the original composition, performance and recording contributors retain their rights. Everyday OST is the public archive uploader, not an official publisher delivery.',
        'publication_metadata_receipt': record['metadata_file'],
        'native_codec_metadata_receipt': record['metadata_file'],
        'native_codec_metadata_verified': True, 'playback_verified_on_ps5': False,
        'verification_method': 'Actual public YouTube title, uploader identity, duration and app TVHTML5 AVC/AAC format metadata; original Wii U collection context corroborated by Nintendo history and publisher Splatune listing. Publication description is empty and no description evidence is asserted.',
    })
assert len(tracks) == 48 and len({t['youtube_id'] for t in tracks}) == 48
for filename in ['playlist-original-flat.json', 'native-publication-research.json', 'publisher-splatune.html', 'nintendo-history.html']:
    path = FOLDER / filename
    sources.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)})
source = ROOT / 'build/research/soundtrack-broad/games/wikipedia-52874820.json'
sources.append({'path': source.relative_to(ROOT).as_posix(), 'sha256': sha(source)})
candidate = {
    'schema_version': 1, 'publication_status': 'candidate_pending_independent_review',
    'scope': '48 available original Wii U archival music publications. Different in-game phase/shop variants retained; live/extended performances and short jingles/SFX excluded. One unavailable recording held. This is not an exact retail Splatune 61-track master or completeness claim.',
    'entries': [{'entry_id': 'wikipedia-52874820', 'match_title': 'Splatoon', 'match_year': 2015,
                 'title': 'Listen to Splatoon', 'composer': 'Toru Minegishi and Shiho Fujii',
                 'curator_note': 'Listen to the music of Toru Minegishi and Shiho Fujii from Splatoon.',
                 'replace_existing_tracks': True, 'full_album_collection': False,
                 'coverage_status': 'AVAILABLE_ORIGINAL_WII_U_ARCHIVAL_MUSIC_COLLECTION', 'tracks': tracks}],
    'source_receipts': sources,
    'collection_limits': {
        'actual_playlist_entries_returned': len(playlist['entries']),
        'playlist_header_count_is_not_actual_available_count': playlist.get('playlist_count'),
        'publisher_album_tracks': 61, 'publisher_album_music': 37,
        'publisher_album_jingles': 10, 'publisher_album_sound_effects': 14,
        'unavailable_held': [r for r in research['records'] if r['status'] == 'held'],
        'excluded_publications': research['excluded'],
        'empty_descriptions': 'Explicitly empty optional field, not invented or used as evidence.',
        'audio_fingerprint_or_retail_master_equivalence_verified': False,
    },
    'checked_utc': datetime.now(timezone.utc).isoformat(),
    'catalog_or_source_music_modified': False, 'media_downloaded': False,
}
path = FOLDER / 'forty-eight-original-wiiu-publications-candidate.json'
path.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(json.dumps({'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path), 'tracks': len(tracks)}))
