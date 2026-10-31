"""Apply exact source-bound modern cover corrections after generic discovery."""
import copy, hashlib, json


def apply(entries, root, filename='museum-modern-cover-corrections-reviewed.json'):
    source = root / 'content/expansion' / filename
    if not source.exists():
        return {'status': 'not_published', 'applied': []}
    data = json.loads(source.read_text(encoding='utf8'))
    if data.get('publication_status') != 'visual_validated':
        return {'status': 'not_published', 'applied': []}
    candidate = root / data['reviewed_candidate']['local_path']
    actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
    if actual != data['reviewed_candidate']['sha256']:
        raise ValueError('Reviewed modern cover candidate changed')
    original = json.loads(candidate.read_text(encoding='utf8'))
    if original['entries'] != data['entries']:
        raise ValueError('Reviewed modern cover fields changed after peer')
    targets = {e['id']: e for e in entries}
    applied = []
    for identifier, change in data['entries'].items():
        target = targets.get(identifier)
        if target is None:
            raise ValueError('Reviewed modern cover target missing: ' + identifier)
        image = change['image']
        if image['url'] == change['supersedes_preferred_url']:
            raise ValueError('Modern cover correction is a no-op: ' + identifier)
        local = root / image['recovery_local_source']
        expected = image['verification']['sha256']
        if hashlib.sha256(local.read_bytes()).hexdigest() != expected:
            raise ValueError('Reviewed modern cover bytes changed: ' + identifier)
        removed_urls = {change['supersedes_preferred_url'], image['url']}
        removed = [copy.deepcopy(i) for i in target.get('images', [])
                   if i['url'] == change['supersedes_preferred_url'] and i['url'] != image['url']]
        target['images'] = [copy.deepcopy(image)] + [i for i in target.get('images', [])
                                                   if i['url'] not in removed_urls]
        target['preferred_image'] = 0
        provenance = target.setdefault('provenance', {})
        if not isinstance(provenance, dict):
            provenance = {'original_record': provenance}
            target['provenance'] = provenance
        provenance['reviewed_modern_cover_correction'] = {
            'candidate_sha256': actual,
            'excluded_preferred_images': removed,
            'reason': 'Prefer original-game artwork without later-edition or platform banners; preserve rejected evidence outside display media.'}
        applied.append(identifier)
    return {'status': 'PASS', 'applied': applied, 'candidate_sha256': actual}
