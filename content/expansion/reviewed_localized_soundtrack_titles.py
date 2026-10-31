"""Publisher-localized English track names; recordings and credits are immutable."""
import hashlib
import json


def apply(entries, root):
    path = root / 'build/research/requested-catalog-music-corrections/remaining-english-names/remaining-210-publisher-localized-candidate.json'
    plan = json.loads(path.read_text(encoding='utf-8'))
    for rel, expected in plan['source_files'].items():
        assert hashlib.sha256((root / rel).read_bytes()).hexdigest() == expected, rel
    by_id = {entry['id']: entry for entry in entries}
    changed = []
    for patch in plan['patches']:
        entry = by_id[patch['entry_id']]
        rooms = entry.get('soundtrack_rooms') or [entry['soundtrack']]
        matches = [track for room in rooms for track in room['tracks'] if track['youtube_id'] == patch['youtube_id']]
        assert len(matches) == 1, patch['youtube_id']
        track = matches[0]
        assert track['title'] in (patch['before'], patch['after']), patch
        if track['title'] == patch['before']:
            track['title'] = patch['after']
            track['display_title_source'] = patch['english_source']
            changed.append({'entry_id': entry['id'], 'youtube_id': track['youtube_id']})
    return {'policy': plan['policy'], 'changed': changed, 'count': len(changed)}
