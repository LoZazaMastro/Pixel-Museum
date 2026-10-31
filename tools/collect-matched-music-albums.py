"""Expand existing verified leads using bounded public album metadata lookups.

This collector never edits the catalogue and never downloads media. An album is
retained only when it contains a previously verified recording for that game.
"""
from pathlib import Path
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
import argparse, json, sys, time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'build/tools/ytmusicapi'))
from ytmusicapi import YTMusic

parser = argparse.ArgumentParser()
parser.add_argument('--start', type=int, default=0)
parser.add_argument('--limit', type=int, default=25)
parser.add_argument('--base', default='build/research/app-audio-matched-albums-20261030')
parser.add_argument('--year-min', type=int, default=2020)
parser.add_argument('--year-max', type=int, default=2025)
parser.add_argument('--review-candidates', action='store_true', help='Also cache unmatched album candidates for an explicit publisher/edition review; do not admit them automatically.')
parser.add_argument('--include-unverified', action='store_true')
args = parser.parse_args()
BASE = ROOT / args.base
BASE.mkdir(parents=True, exist_ok=True)
state_path = ROOT / 'build/research/youtube-metadata-rate-limit-state.json'
entries = json.loads((ROOT / 'content/catalog.json').read_text(encoding='utf-8'))['entries']
jobs = []
for entry in entries:
    soundtrack = entry.get('soundtrack') or {}
    tracks = soundtrack.get('tracks', [])
    if entry.get('kind') == 'game' and args.year_min <= entry['year'] <= args.year_max and len(tracks) <= 3 and (tracks or args.include_unverified):
        verified = {track['youtube_id'] for track in tracks if track.get('official_uploader_verified') is True}
        if verified or args.include_unverified:
            jobs.append((entry, verified))
client = YTMusic()
jobs_path = BASE / 'jobs.json'
if jobs_path.exists():
    order = json.loads(jobs_path.read_text(encoding='utf-8'))
    current = {entry['id']: entry for entry in entries}
    jobs = [(current[eid], {track['youtube_id'] for track in (current[eid].get('soundtrack') or {}).get('tracks', []) if track.get('official_uploader_verified') is True}) for eid in order]
else:
    jobs_path.write_text(json.dumps([entry['id'] for entry, _ in jobs], indent=2) + '\n', encoding='utf-8')

def save(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)

def fetch(path, callback):
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    state = json.loads(state_path.read_text(encoding='utf-8'))
    now = datetime.now(timezone.utc)
    if state.get('status') == 'RATE_LIMITED' and datetime.fromisoformat(state['retry_after_utc']) > now:
        raise RuntimeError('ACTIVE_RATE_LIMIT_COOLDOWN')
    try:
        data = callback()
    except Exception as error:
        save(path.with_suffix('.attempt.json'), {'error': str(error), 'metadata_only': True, 'observed_at_utc': now.isoformat()})
        if '429' in str(error) or 'too many requests' in str(error).lower():
            value = getattr(getattr(error, 'response', None), 'headers', {}).get('Retry-After', '300')
            try:
                seconds = max(300, int(value))
            except ValueError:
                try:
                    seconds = max(300, (parsedate_to_datetime(value) - now).total_seconds())
                except (ValueError, TypeError):
                    seconds = 300
            state.update(status='RATE_LIMITED', retry_after_utc=(now + timedelta(seconds=seconds)).isoformat(), last_rate_limit_utc=now.isoformat())
            save(state_path, state)
            raise RuntimeError('ACTIVE_RATE_LIMIT_COOLDOWN') from error
        raise
    save(path, data)
    time.sleep(1)
    return data

completed = []
for entry, verified in jobs[args.start:args.start + args.limit]:
    folder = BASE / entry['id']
    folder.mkdir(exist_ok=True)
    query = entry['title'] + ' Original Soundtrack'
    try:
        candidates = fetch(folder / 'search.json', lambda: client.search(query, filter='albums', limit=3))
        selected, review = [], []
        for candidate in candidates[:2]:
            browse_id = candidate.get('browseId')
            if not browse_id:
                continue
            album_path = folder / (browse_id + '.json')
            album = fetch(album_path, lambda: client.get_album(browse_id))
            available = [track for track in album.get('tracks', []) if track.get('videoId') and track.get('isAvailable', True)]
            matched = verified & {track['videoId'] for track in available}
            summary = {'receipt': album_path.relative_to(ROOT).as_posix(), 'title': album['title'], 'artists': [artist['name'] for artist in album.get('artists', [])], 'year': album.get('year'), 'tracks': len(available), 'matched_existing_verified_ids': sorted(matched)}
            if not matched:
                if args.review_candidates:
                    review.append(summary)
                continue
            selected.append(summary)
            # The main published album is enough; distinct prior songs remain.
            break
        result = {'entry_id': entry['id'], 'title': entry['title'], 'previous_tracks': len((entry.get('soundtrack') or {}).get('tracks', [])), 'albums': selected, 'unmatched_candidates_require_review': review, 'metadata_only': True, 'media_downloaded': False}
        save(folder / 'result.json', result)
        completed.append(result)
        print(json.dumps(result, ensure_ascii=True), flush=True)
    except Exception as error:
        if 'ACTIVE_RATE_LIMIT_COOLDOWN' in str(error):
            print(json.dumps({'status': 'COOLDOWN', 'completed': len(completed)}), flush=True)
            break
        print(json.dumps({'entry_id': entry['id'], 'error': str(error)[:140]}), flush=True)
save(BASE / ('results-' + str(args.start) + '.json'), completed)
