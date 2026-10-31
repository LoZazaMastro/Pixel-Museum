"""Guarded recognition chapter and two dated views of one canonical story."""
import copy
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def comparable(entry):
    return {k: v for k, v in entry.items() if k != 'publication_readiness'}


def apply(entries, root):
    root = Path(root)
    manifest = root / 'content/expansion/museum-miyamoto-shared-story-reviewed.json'
    if not manifest.exists():
        return {'status': 'not_admitted'}
    plan = json.loads(manifest.read_text(encoding='utf8'))
    assert plan['publication_status'] == 'independently_reviewed'
    candidate_path = root / plan['candidate_path']
    assert digest(candidate_path) == plan['candidate_sha256']
    candidate = json.loads(candidate_path.read_text(encoding='utf8'))
    peer_path = root / plan['peer_path']
    assert digest(peer_path) == plan['peer_sha256']
    peer = json.loads(peer_path.read_text(encoding='utf8'))
    assert peer['status'].startswith('PASS') and peer['candidate_sha256'] == plan['candidate_sha256']
    # The native alias is a separately reviewed schema binding, not a modified candidate.
    runtime_path = root / plan['runtime_approval_path']
    assert digest(runtime_path) == plan['runtime_approval_sha256']
    runtime = json.loads(runtime_path.read_text(encoding='utf8'))
    assert runtime['status'].startswith('PASS')
    for source in candidate['source_checks']:
        assert digest(root / source['path']) == source['sha256']
    original = candidate['old_entry']
    approved = candidate['entry_after']
    event_template = candidate['new_event_entry_after']
    assert original['id'] == approved['id'] == 'daily-11-16'
    assert event_template['id'] == 'miyamoto-order-of-culture-2026'
    assert approved['body'][:len(original['body'])] == original['body']
    assert len(approved['body']) == len(original['body']) + 1
    assert approved['images'][:len(original['images'])] == original['images']
    owner = next(e for e in entries if e['id'] == original['id'])
    if comparable(owner) != comparable(approved):
        assert comparable(owner) == comparable(original), 'Canonical Miyamoto source drift'
        owner.clear()
        owner.update(copy.deepcopy(approved))
    # Derive the event on every generation from the updated canonical article.
    # Only timeline identity/display fields may differ; story fields cannot drift.
    independent = {'id', 'title', 'subtitle', 'year', 'date', 'kind', 'era_id',
                   'event_semantics', 'summary', 'related_ids', 'preferred_image'}
    assert {k for k in approved if approved.get(k) != event_template.get(k)} <= independent
    event = copy.deepcopy(owner)
    for key in independent:
        if key in event_template:
            event[key] = copy.deepcopy(event_template[key])
        else:
            event.pop(key, None)
    event['story_entry_id'] = owner['id']
    event.pop('publication_readiness', None)
    assert event['preferred_image'] == 14 and event['year'] == 2026
    for key in ('body', 'story_headings', 'images', 'videos', 'editorial_features'):
        assert event.get(key) == owner.get(key)
    existing = next((e for e in entries if e['id'] == event['id']), None)
    if existing is None:
        entries.append(event)
    else:
        assert comparable(existing) == comparable(event), 'Recognition event source drift'
    return {'status': 'PASS', 'canonical_story': owner['id'], 'event': event['id'],
            'story_entry_id': event['story_entry_id'], 'preferred_event_image': 14}
