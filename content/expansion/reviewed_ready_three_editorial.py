"""Final, source-bound editorial media join; derived readiness runs afterwards."""
from pathlib import Path
import copy
import hashlib
import json
import runpy


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def comparable(entry):
    # This derived field is absent before the assembler's final readiness pass.
    return {key: value for key, value in entry.items() if key != 'publication_readiness'}


def apply(entries, root, manifest_name='museum-ready-three-editorial-reviewed.json'):
    root = Path(root)
    manifest = root / 'content/expansion' / manifest_name
    plan = json.loads(manifest.read_text(encoding='utf8'))
    if plan.get('publication_status') != 'independently_reviewed':
        return {'status': 'not_admitted'}
    for source in plan['extra_sources']:
        if sha(root / source['path']) != source['sha256']:
            raise ValueError('Reviewed publisher receipt changed')
    changed = []
    excluded = runpy.run_path(str(root / 'content/expansion/user_sports_policy.py'))['excluded_ids'](root)
    for row in plan['rows']:
        if sha(root / row['candidate_path']) != row['candidate_sha256'] or sha(root / row['peer_path']) != row['peer_sha256']:
            raise ValueError('Reviewed editorial candidate or peer bytes changed')
        peer = json.loads((root / row['peer_path']).read_text(encoding='utf8'))
        if not peer['status'].startswith('PASS') or peer['candidate_sha256'] != row['candidate_sha256']:
            raise ValueError('Reviewed editorial peer mismatch')
        before = copy.deepcopy(row['old_entry'])
        after = copy.deepcopy(before)
        after.update(copy.deepcopy(row['changes']))
        owner = next((entry for entry in entries if entry['id'] == row['entry_id']), None)
        if owner is None and row['entry_id'] in excluded:
            continue
        if owner is None:
            raise ValueError('Reviewed editorial owner disappeared: ' + row['entry_id'])
        # Bundled model selections are maintained independently of immutable
        # editorial proposals. Only accept this drift when the actual model
        # equals the current authoritative index and the proposal does not
        # itself change models; every other owner field remains guarded.
        if 'models' not in row['changes']:
            authoring_models = runpy.run_path(str(root / 'content/expansion/user_console_png_policy.py'))['authoring_models'](root)
            indexed = next((model for model in authoring_models
                            if model['exhibit_id'] == row['entry_id']), None)
            authoritative = [{key: value for key, value in indexed.items() if key != 'exhibit_id'}] if indexed else None
            if authoritative is not None and owner.get('models') == authoritative:
                before['models'] = copy.deepcopy(authoritative)
                after['models'] = copy.deepcopy(authoritative)
        if comparable(owner) == comparable(after):
            continue
        if comparable(owner) != comparable(before):
            drift = sorted(key for key in set(comparable(owner)) | set(comparable(before)) if comparable(owner).get(key) != comparable(before).get(key))
            raise ValueError('Final reviewed editorial owner changed: ' + row['entry_id'] + '; fields=' + ','.join(drift))
        for image in row['changes'].get('images', []):
            verification = image.get('verification', {})
            local = image.get('recovery_local_source') or verification.get('local_file')
            expected = verification.get('sha256') or verification.get('source_sha256')
            if local and expected and sha(root / local) != expected:
                raise ValueError('Reviewed original illustration changed')
        owner.update(copy.deepcopy(row['changes']))
        changed.append(row['entry_id'])
    return {'status': 'PASS', 'changed_entries': changed, 'changed_count': len(changed)}
