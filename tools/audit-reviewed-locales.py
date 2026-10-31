"""Verify actual partial overlays, source binding, fallback positions and package gates."""
from pathlib import Path
import copy, json, runpy, hashlib

ROOT = Path(__file__).resolve().parents[1]
projection = runpy.run_path(str(ROOT / 'tools/project-reviewed-locales.py'))
catalogs = [json.loads((ROOT / 'content' / filename).read_text(encoding='utf8')) for filename in ('catalog.json', 'human-history.json')]
owners = {owner['id']: owner for catalog in catalogs for entry in catalog['entries'] for owner in [entry] + entry.get('editorial_features', [])}
report = {'schema_version': 1, 'scope': 'Actual published overlay source hashes, exact paragraph positions, explicit English fallback and stale-owner rejection. This is not a linguistic review of every reused translation.', 'languages': {}}
for language in ('it', 'es', 'fr', 'de'):
    path = ROOT / 'content/museum-locales' / (language + '.json')
    document = json.loads(path.read_text(encoding='utf8'))
    assert path.stat().st_size < 16 << 20
    _, audit = projection['project'](document, catalogs, language)
    assert not audit['stale'] and not audit['not_in_package']
    checked_units = fallback_units = 0
    for identity, row in document['entries'].items():
        owner = owners[identity]
        fields = projection['source_fields'](owner)
        for field, expected in row['provenance']['source_field_hashes'].items():
            assert hashlib.sha256(json.dumps(fields[field], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest() == expected, (identity, field)
        for field in ('body', 'story_headings'):
            if field in row:
                assert len(row[field]) == len(fields[field]), (identity, field)
        for unit in row['provenance']['english_fallback_units']:
            field, n = unit['field'], unit['index']
            if field in row:
                actual = row[field][n] if isinstance(row[field], list) else row[field]
                expected = fields[field][n] if isinstance(fields[field], list) else fields[field]
                assert actual == expected, (identity, field, n, 'Untranslated fallback was overwritten')
            fallback_units += 1
        checked_units += len(row['provenance']['source_units'])
    # A real translated article must be rejected if its English source changes.
    identity = next(key for key in document['entries'] if key in owners and owners[key].get('body'))
    changed = copy.deepcopy(catalogs)
    found = False
    for catalog in changed:
        for entry in catalog['entries']:
            for owner in [entry] + entry.get('editorial_features', []):
                if owner['id'] == identity:
                    owner['body'][0] += ' Source-change regression fixture.'
                    found = True
    assert found
    projected, changed_audit = projection['project'](document, changed, language)
    assert identity in changed_audit['stale'] and identity not in projected['entries']
    report['languages'][language] = {'status': 'PASS', 'owners': len(document['entries']), 'source_bound_units': checked_units, 'explicit_fallback_units': fallback_units, 'stale_owner_rejection_fixture': 'PASS', 'bytes': path.stat().st_size}
path = ROOT / 'build/research/translation-planning/overlay-integrity-audit.json'
path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
print(json.dumps(report, indent=2))
