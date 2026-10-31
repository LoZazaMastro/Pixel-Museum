"""Real public original-score chapters; no claim of perfect exhaustive CD inventory."""
import copy
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/classic-trilogy-complete'
load = lambda path: json.loads(path.read_text(encoding='utf-8'))
SOURCES = [
    ('wikipedia-8960133', '1GZZdIed_qw', 'Josh Mancell', 1996),
    ('wikipedia-1305157', 'NJu9vcvfn0Y', 'Josh Mancell', 1997),
    ('wikipedia-1305244', 'Xd_lMN-9ZK4', 'Josh Mancell', 1998),
    ('wikipedia-1353538', 'hJSqzqXXkt0', 'Stewart Copeland', 1998),
    ('wikipedia-2146647', 't0uOn0fxrT0', 'Stewart Copeland', 1999),
    ('wikipedia-2146652', 'uo4msAPEpEA', 'Spyro: Year of the Dragon music team', 2000),
]


def parse_chapters(publication):
    chapters = []
    for line in publication['shortDescription'].splitlines():
        match = re.search(r'(?<![0-9])([0-9]+:[0-9]{2}(?::[0-9]{2})?)(?![0-9])', line)
        if not match:
            continue
        before, after = line[:match.start()].strip(' -\t'), line[match.end():].strip(' -\t')
        title = after or re.sub(r'^\s*\d+[.)]?\s*[-–]?\s*', '', before).strip()
        if not title:
            continue
        seconds = 0
        for piece in match.group(1).split(':'):
            seconds = seconds * 60 + int(piece)
        chapters.append({'source_chapter_number': len(chapters) + 1, 'title': title, 'start_seconds': seconds})
    for index, row in enumerate(chapters):
        row['end_seconds'] = chapters[index + 1]['start_seconds'] if index + 1 < len(chapters) else int(publication['lengthSeconds'])
        row['duration_seconds'] = row['end_seconds'] - row['start_seconds']
        assert row['duration_seconds'] > 0
    return chapters


def main():
    baseline = load(ROOT / 'content/expansion/soundtrack-independent-approved.json')
    old_by_id = {row['entry_id']: row for row in baseline['entries']}
    publications = load(OUT / 'actual-watch.json')
    entries, report = [], []
    for entry_id, video_id, creator, year in SOURCES:
        old = old_by_id[entry_id]
        publication = publications[video_id]
        native_path = ROOT / f'build/research/video-discovery/video-{video_id}.json'
        assert load(native_path)['native_compatible_avc_aac'] is True
        chapters = parse_chapters(publication)
        assert len(chapters) == {'1GZZdIed_qw': 31, 'NJu9vcvfn0Y': 33, 'Xd_lMN-9ZK4': 28,
                                 'hJSqzqXXkt0': 37, 't0uOn0fxrT0': 43, 'uo4msAPEpEA': 39}[video_id]
        tracks, excluded = [], []
        for chapter in chapters:
            if re.search(r'\b(?:Unused|Demo Version)\b', chapter['title'], re.I):
                excluded.append(copy.deepcopy(chapter))
                continue
            recording_version = 'Original-game public archival score collection; source-declared original game version, not N. Sane/Reignited reconstruction. Capture hardware/CD-master equivalence not independently certified.'
            if 'Japanese Version' in chapter['title']:
                recording_version += ' Japanese original-game regional variant, as explicitly labeled by the source.'
            if 'Greatest Hits' in chapter['title']:
                recording_version += ' Original PlayStation Greatest Hits release variant explicitly labeled by the source.'
            if 'PAL Version' in chapter['title'] or 'NTSC Version' in chapter['title']:
                recording_version += ' Original-game regional version explicitly labeled in the track title.'
            composer_source = old['tracks'][0]['composer_source']
            if creator == 'Stewart Copeland':
                composer_source = 'https://investor.activision.com/news-releases/news-release-details/spyro-reignited-trilogy-brings-beat-fans-san-diego-comic-con'
            if entry_id == 'wikipedia-2146652':
                composer_source = 'https://www.ryanbeveridgemusic.com/bio'
            row = {
                'youtube_id': video_id, 'url': 'https://www.youtube.com/watch?v=' + video_id,
                'title': chapter['title'], 'creator': creator,
                'start_seconds': chapter['start_seconds'], 'end_seconds': chapter['end_seconds'],
                'duration_seconds': chapter['duration_seconds'], 'source_publication_duration_seconds': int(publication['lengthSeconds']),
                'source_chapter_number': chapter['source_chapter_number'],
                'source_actual_chapter_title': chapter['title'],
                'composer_source': composer_source,
                'uploader': publication['author'], 'channel_url': 'https://www.youtube.com/channel/' + publication['channelId'],
                'source_page': 'https://www.youtube.com/watch?v=' + video_id,
                'primary_published_title': publication['title'],
                'official_uploader_verified': False, 'publishing_kind': 'archival_game_recording',
                'recording_version': recording_version, 'original_game_year': year,
                'native_codec_metadata_verified': True,
                'native_codec_metadata_receipt': str(native_path.relative_to(ROOT)).replace('\\', '/'),
                'publication_metadata_receipt': str((OUT / 'actual-watch.json').relative_to(ROOT)).replace('\\', '/'),
                'playback_verified_on_ps5': False,
                'rights': 'Original composition, performance and recording rights remain with the credited game music authors, Sony, Universal/Activision and recording owners. Public archive uploaders are credited without claiming publisher endorsement.',
                'artist_credit_scope': 'Original-game composer attribution corroborated separately from the archive. Every selection uses a real published timestamp and next actual chapter/end duration; no invented cuts, every-track completeness or audio fingerprint claim.',
            }
            if entry_id == 'wikipedia-2146652':
                row['game_score_composers'] = ['Stewart Copeland', 'Ryan Beveridge']
                row['artist_credit_scope'] = 'COLLECTIVE GAME-SCORE TEAM CREDIT ONLY. Ryan Beveridge personally confirms collaboration with Stewart Copeland on this original game. Individual cue authorship is not separately documented; neither person is falsely assigned sole or joint authorship of each archival cue. Named2022 artist-release supplements retain their independently documented individual credits.'
            tracks.append(row)
        retained = copy.deepcopy(old['tracks']) if creator != 'Josh Mancell' else []
        for row in retained:
            row['collection_section'] = 'Previously independently reviewed2022 artist-issued alternate-version supplement; distinct from the original-game archival chapter collection.'
        entry = {'entry_id': entry_id, 'match_title': old['match_title'], 'match_year': year,
                 'title': 'Listen to ' + old['match_title'],
                 'composer': 'Stewart Copeland and Ryan Beveridge (game score team)' if entry_id == 'wikipedia-2146652' else creator,
                 'curator_note': 'Listen to the music of ' + ('the Spyro: Year of the Dragon music team' if entry_id == 'wikipedia-2146652' else creator) + '\n' + old['match_title'],
                 'replace_existing_tracks': True, 'full_album_collection': False, 'coverage_status': 'partial',
                 'completeness': {'available_public_score_passages': len(tracks), 'retained_artist_version_supplements': len(retained),
                                   'all_game_music_complete': False, 'excluded_demo_or_unused_passages': excluded,
                                   'scope': 'Playable public original-game score collection with real chapter markers. No perfect album-order/inventory or all regional/short stinger/game-loop completeness assertion.'},
                 'tracks': tracks + retained}
        entries.append(entry)
        report.append({'entry_id': entry_id, 'game': old['match_title'], 'source_video_id': video_id,
                       'actual_chapters': len(chapters), 'selected_score_passages': len(tracks),
                       'excluded': excluded, 'retained_artist_supplements': len(retained)})
    result = {'schema_version': 1, 'publication_status': 'awaiting_independent_peer',
              'scope': 'Six publicly available original-game score collections. User prefers usable available music rather than exhaustive album-order/master hunting. Demo/unused explicitly excluded; Greatest Hits/regional variants disclosed; no false complete claim.',
              'entries': entries, 'research_summary': report,
              'independent_old_selected_credit_context': 'build/research/soundtrack-broad/bananza-crash-spyro/independent-23-cue-review.json',
              'primary_bio_receipt': 'build/research/soundtrack-broad/classic-trilogy-complete/public-original-composer-source-receipts.json',
              'publisher_web_read_receipt': 'build/research/soundtrack-broad/classic-trilogy-complete/spyro-publisher-web-read-original-score-receipt.json'}
    target = OUT / 'six-public-classic-score-collections-candidate.json'
    assert not target.exists(), 'Immutable checkpoint already exists'
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'path': str(target), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'summary': report,
                      'total_tracks': sum(len(row['tracks']) for row in entries)}))


if __name__ == '__main__':
    main()
