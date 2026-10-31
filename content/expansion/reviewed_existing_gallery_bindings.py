"""Bind reviewed, already bundled photographs without changing article wording."""
import hashlib
import json
import runpy


def apply(entries, root):
    path = root / 'content/expansion/museum-existing-gallery-bindings-reviewed.json'
    if not path.exists():
        return {'changed': []}
    by_id = {entry['id']: entry for entry in entries}
    excluded = runpy.run_path(str(root / 'content/expansion/user_sports_policy.py'))['excluded_ids'](root)
    changed = []
    for batch in json.loads(path.read_text(encoding='utf8'))['batches']:
        candidate_path = root / batch['candidate_path']
        assert hashlib.sha256(candidate_path.read_bytes()).hexdigest() == batch['candidate_sha256']
        candidate = json.loads(candidate_path.read_text(encoding='utf8'))
        for binding in candidate['bindings']:
            if binding['entry_id'] not in by_id and binding['entry_id'] in excluded:
                continue
            entry = by_id[binding['entry_id']]
            body_bytes = json.dumps(entry['body'], ensure_ascii=False, separators=(',', ':')).encode('utf8')
            assert hashlib.sha256(body_bytes).hexdigest() == binding['body_sha256']
            matches = [image for image in entry['images'] if image['url'] == binding['image_url']]
            assert len(matches) == 1
            preferred = entry.get('preferred_image', 0)
            assert not (isinstance(preferred, int) and 0 <= preferred < len(entry['images']) and entry['images'][preferred]['url'] == binding['image_url']), 'Cover cannot illustrate its own article'
            assert matches[0].get('role') != 'video-poster'
            assert all(video.get('poster_url') != binding['image_url'] for video in entry.get('videos', []))
            index = binding['story_paragraph']
            assert isinstance(index, int) and 0 <= index < len(entry['body'])
            # Review pins the existing original, not a newly downloaded or altered image.
            assert hashlib.sha256((root / binding['local_path']).read_bytes()).hexdigest() == binding['sha256']
            matches[0]['story_paragraph'] = index
            changed.append({'entry_id': entry['id'], 'image_url': binding['image_url'], 'story_paragraph': index})
    return {'changed': changed}
