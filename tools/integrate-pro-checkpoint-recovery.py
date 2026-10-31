"""Recover finished five-language prose from the user's interrupted Pro export.

Only touches the two recovered batches. Existing media, dates and other prose
remain in place; each English owner must still match its exported input.
"""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[1]
RECOVERY = ROOT / 'build/research/app-editorial-recovery-20261030'
PACKAGE = RECOVERY / 'pro-package'
BASE = ROOT / 'content/external-editorial/sol-pro-20261030'
FIELDS = ('title', 'subtitle', 'summary', 'body', 'story_headings')
LANGS = ('en', 'it', 'fr', 'de', 'es')


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def converted(value):
    return {**{k: value[k] for k in FIELDS[:3]},
            'body': [c['text'] for c in value['cards']],
            'story_headings': [c['heading'] for c in value['cards']]}


def main():
    spec = importlib.util.spec_from_file_location('recovery_validator', PACKAGE / 'TOOLS/validate_editorial.py')
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    catalog = read(ROOT / 'content/catalog.json')
    owners = {}
    for entry in catalog['entries']:
        owners[entry['id']] = entry
        owners.update({f['id']: f for f in entry.get('editorial_features', [])})
    locales = {lang: read(ROOT / f'content/museum-locales/{lang}.json') for lang in LANGS[1:]}
    report = {'batches': [], 'entries': [], 'owners': 0, 'cards_per_language': 0,
              'note': 'Recovered user-supplied Pro writing. Structural validation does not close outstanding media or expansion work.'}
    for batch, draft in [
        ('108-catalog', 'worker_b_108/108_working.json'),
        ('110-catalog', 'worker_a_110/110-five-languages-reviewed.json'),
    ]:
        source = read(PACKAGE / batch / 'INPUT.json')
        output = read(PACKAGE / 'IN_CORSO_CHECKPOINT' / draft)
        output['completed'] = True
        staged = RECOVERY / batch / f'OUTPUT-{batch}.json'
        write(staged, output)
        result = validator.validate(PACKAGE / batch / 'TEMPLATE_OUTPUT.json', PACKAGE / batch / 'INPUT.json', staged)
        write(RECOVERY / batch / 'validation.json', result)
        assert result['valid'], result['failures']
        originals = {e['entry_id']: e for e in source['entries']}
        pending = []
        for entry in output['entries']:
            old = originals[entry['entry_id']]
            old_units = {u['feature_id']: u for u in [old['main'], *old['features']]}
            for unit in [entry['main'], *entry['features']]:
                owner_id = unit['feature_id'] or entry['entry_id']
                owner = owners[owner_id]
                replacement = converted(unit['en'])
                current = {k: owner.get(k, [] if k in FIELDS[3:] else '') for k in FIELDS}
                if not current['story_headings']:
                    current['story_headings'] = [''] * len(current['body'])
                assert current in (converted(old_units[unit['feature_id']]), replacement), (owner_id, 'changed since export')
                pending.append((owner, unit, replacement))
            report['entries'].append(entry['entry_id'])
        target = BASE / batch / f'OUTPUT-{batch}.json'
        for name in ('INPUT.json', 'TEMPLATE_OUTPUT.json'):
            if not (BASE / batch / name).exists():
                write(BASE / batch / name, read(PACKAGE / batch / name))
        write(target, output)
        for owner, unit, english in pending:
            owner.update(english)
            owner['external_editorial'] = {
                'batch_id': batch, 'output_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                'source_fields_sha256': digest(english),
                'source': 'User-supplied GPT Sol Pro interrupted checkpoint recovered locally; original media retained',
            }
            for lang in LANGS[1:]:
                row = converted(unit[lang])
                row['editorial_credit'] = owner.get('editorial_credit', '')
                row['provenance'] = {
                    'source_fields_sha256': digest(english),
                    'source_field_hashes': {k: digest(v) for k, v in english.items()},
                    'mode': 'user_supplied_external_editorial', 'batch_file': target.relative_to(ROOT).as_posix(),
                    'source_units': [], 'english_fallback_units': [],
                }
                locales[lang]['entries'][owner['id']] = row
            report['owners'] += 1
            report['cards_per_language'] += len(english['body'])
        report['batches'].append(batch)
    for name in ['catalog', *LANGS[1:]]:
        path = ROOT / ('content/catalog.json' if name == 'catalog' else f'content/museum-locales/{name}.json')
        backup = RECOVERY / 'before-checkpoints' / path.name
        if not backup.exists():
            write(backup, read(path))
        write(path, catalog if name == 'catalog' else locales[name])
    write(RECOVERY / 'checkpoint-integration.json', report)
    print(json.dumps({k: len(v) if isinstance(v, list) else v for k, v in report.items()}, ensure_ascii=True))


if __name__ == '__main__':
    main()
