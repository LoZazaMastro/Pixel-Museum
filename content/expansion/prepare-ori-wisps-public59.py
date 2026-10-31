"""Available original-score passages; original source boundaries, no invented missing cue."""
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/modern-public-albums'
load = lambda p: json.loads(p.read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
path = OUT / 'eCbyqm9jcBA-actual-publication-research.json'
receipt = load(path)
pub = receipt['publication']
assert pub['author'] == 'Hyversal' and receipt['native_avc_aac']
assert load(ROOT / receipt['native_codec_receipt'])['native_compatible_avc_aac']
source = 'https://garethcoker.bandcamp.com/album/ori-and-the-will-of-the-wisps-original-soundtrack-recording'
markers = []
for line in pub['shortDescription'].splitlines():
    m = re.match(r'^(\d+:\d{2}(?::\d{2})?)\s+-\s+(.+?)\s*$', line)
    if m:
        start = 0
        for part in m[1].split(':'):
            start = start*60 + int(part)
        markers.append({'start': start, 'title': m[2], 'line': line})
assert len(markers) == 59
duration = float(pub['lengthSeconds'])
tracks = []
for index, marker in enumerate(markers):
    end = markers[index+1]['start'] if index+1 < len(markers) else duration
    assert 0 <= marker['start'] < end <= duration
    tracks.append({'youtube_id': 'eCbyqm9jcBA', 'url': 'https://www.youtube.com/watch?v=eCbyqm9jcBA',
                   'source_page': 'https://www.youtube.com/watch?v=eCbyqm9jcBA',
                   'title': marker['title'], 'creator': 'Gareth Coker', 'composer_source': source,
                   'artist_credit_scope': 'The composer-issued original album names Gareth Coker as music author. Featured performers and production contributors below are album-level credits, not assigned to every individual cue.',
                   'album_level_recording_roles': {'featured_vocals': ['Aeralie Brighton', 'Kelsey Mira'],
                       'woodwinds': ['Kristin Naigus'], 'bass_clarinet': ['Laurent Ben Slimane'],
                       'orchestra': ['Philharmonia Orchestra'], 'choir': ['Pinewood Voices'],
                       'orchestra_conductor': ['Alexander Rudd'], 'choir_conductor': ['Allan Wilson'],
                       'supervising_orchestrator': ['Zach Lemmon'],
                       'orchestrators': ['David Peacock', 'Eric Buchholz'],
                       'string_designs': ['David Peacock', 'Justin Bell'],
                       'mix_engineers': ['Steve Kempster', 'John Kurlander']},
                   'start_seconds': marker['start'], 'end_seconds': end,
                   'duration_seconds': end-marker['start'], 'source_actual_chapter_line': marker['line'],
                   'source_publication_duration_seconds': duration,
                   'uploader': pub['author'], 'channel_url': 'https://www.youtube.com/channel/' + pub['channelId'],
                   'primary_published_title': pub['title'], 'official_uploader_verified': False,
                   'publishing_kind': 'archival_game_recording', 'recording_year': 2020,
                   'recording_version': 'Original 2020 soundtrack, available archival album passages. The source indexes 59 selections and omits Kwolok\'s Hollow from the 60-track composer album; no invented replacement or complete-album claim.',
                   'recording_platform': 'Capture hardware not identified',
                   'rights': 'Gareth Coker / Moon Studios / Microsoft and credited performers and recording contributors; Hyversal is an archival uploader.',
                   'native_codec_metadata_verified': True, 'native_codec_metadata_receipt': receipt['native_codec_receipt'],
                   'publication_metadata_receipt': path.relative_to(ROOT).as_posix(),
                   'playback_verified_on_ps5': False})
credit = OUT / 'ori-wisps-primary-album-web-read-receipt.json'
credit.write_text(json.dumps({'source_url': source, 'actual_web_page_read': True,
    'published_album_tracks': 60, 'original_album_release': '2020-03-10',
    'verified_composer': 'Gareth Coker',
    'available_archive_tracks': 59, 'missing_source_selection': "Kwolok's Hollow",
    'scope': 'The original artist album explicitly distinguishes music, featured performers, orchestration and engineering. Only available public archive passages are selected; no audio-identical-master or physical PS5 claim.'}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
entry = {'entry_id': 'wikipedia-54280556', 'match_title': 'Ori and the Will of the Wisps', 'match_year': 2020,
    'title': 'Listen to Ori and the Will of the Wisps', 'composer': 'Gareth Coker',
    'curator_note': 'Listen to the music of Gareth Coker\nOri and the Will of the Wisps',
    'replace_existing_tracks': True, 'full_album_collection': False, 'coverage_status': 'partial',
    'recording_collection_scope': '59 available source-indexed original-album passages. The 60-track composer album includes one additional selection not indexed by this archive.',
    'album_completeness': {'expected_published_album_tracks': 60, 'verified_available_tracks': 59,
                           'missing_source_selections': ["Kwolok's Hollow"], 'inventory_source': source},
    'tracks': tracks}
target = OUT / 'ori-wisps59-available-public-candidate.json'
assert not target.exists(), 'Immutable checkpoint exists'
target.write_text(json.dumps({'schema_version': 1, 'publication_status': 'awaiting_independent_peer',
    'entries': [entry], 'source_receipts': [{'local_path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p)} for p in [path, credit]]}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'candidate': target.relative_to(ROOT).as_posix(), 'sha256': sha(target), 'selectable_tracks': len(tracks)}))
