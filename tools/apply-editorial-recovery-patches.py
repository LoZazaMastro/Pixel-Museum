"""Apply prepared editorial patches without replacing unrelated media or prose."""
import argparse
import copy
import hashlib
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / 'build/research/app-editorial-recovery-20261030'
FIELDS = ('title', 'subtitle', 'summary', 'body', 'story_headings')
LANGS = ('en', 'it', 'fr', 'de', 'es')


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    # Windows readers can briefly hold a file without delete sharing. Keep the
    # atomic replacement and wait for that reader, rather than losing a batch.
    for attempt in range(10):
        try:
            tmp.replace(path)
            break
        except PermissionError:
            if attempt == 9:
                raise
            time.sleep(0.2 * (attempt + 1))


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def refresh(owner, locales, origin):
    # A rewritten article must not retain the former literal-reproduction notice.
    def adapted_credit(row):
        credit = row.get('editorial_credit', '')
        if credit.startswith('Text reproduced from ') and 'Wikipedia contributors' in credit:
            credit = credit.replace('Text reproduced from ', 'Text adapted from ', 1)
            credit = credit.replace('No substantive text changes; lead paragraphs selected and formatting removed.',
                                    'Rewritten and expanded for Pixel Museum.')
            row['editorial_credit'] = credit
    adapted_credit(owner)
    fields = {k: owner.get(k, [] if k in FIELDS[3:] else '') for k in FIELDS}
    for lang in LANGS[1:]:
        row = locales[lang]['entries'][owner['id']]
        adapted_credit(row)
        assert len(row['body']) == len(owner['body']) == len(row['story_headings']), (owner['id'], lang, 'unaligned cards')
        assert all(isinstance(s, str) and s.strip() for s in row['body'] + row['story_headings'])
        row['provenance'] = {**row.get('provenance', {}),
                             'source_fields_sha256': digest(fields),
                             'source_field_hashes': {k: digest(v) for k, v in fields.items()},
                             'mode': 'targeted_editorial_recovery', 'patch_file': origin,
                             'english_fallback_units': []}
    owner['editorial_recovery'] = {'patch_file': origin, 'source_fields_sha256': digest(fields)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('patch_files', nargs='+')
    args = parser.parse_args()
    docs = {name: read(ROOT / f'content/{name}.json') for name in ('catalog', 'human-history')}
    locales = {lang: read(ROOT / f'content/museum-locales/{lang}.json') for lang in LANGS[1:]}
    owners = {}
    for collection, doc in docs.items():
        for entry in doc['entries']:
            owners[(collection, entry['id'])] = entry
            owners.update({(collection, f['id']): f for f in entry.get('editorial_features', [])})
    report = {'applied': [], 'before': [], 'unresolved': []}
    for filename in args.patch_files:
        path = ROOT / filename
        data = read(path)
        patches = data.get('patches', [data])
        report['unresolved'].extend(data.get('unresolved', []))
        for patch in patches:
            collection = patch.get('collection', 'catalog')
            eid = patch['entry_id']
            owner = owners[(collection, eid)]
            report['before'].append({'collection': collection, 'entry_id': eid, 'entry': copy.deepcopy(owner),
                                    'locales': {l: copy.deepcopy(locales[l]['entries'].get(eid)) for l in LANGS[1:]}})
            for k, expected in patch.get('before', {}).items():
                replacements = {**patch.get('set', {}), **patch.get('languages', {}).get('en', {})}
                assert owner.get(k) == expected or (k in replacements and owner.get(k) == replacements[k]), (eid, k, 'conflict')
            owner.update(patch.get('set', {}))
            if 'languages' in patch:
                assert set(patch['languages']) == set(LANGS)
                owner.update(patch['languages']['en'])
                for lang in LANGS[1:]:
                    row = locales[lang]['entries'].setdefault(eid, {})
                    row.update(patch['languages'][lang])
            for lang, title in patch.get('localized_titles', {}).items():
                if lang == 'en':
                    owner['title'] = title
                else:
                    locales[lang]['entries'][eid]['title'] = title
            for lang, prefix in patch.get('prefix_first_body_paragraph', {}).items():
                assert '?' not in prefix, (eid, lang, 'damaged encoding')
                row = owner if lang == 'en' else locales[lang]['entries'][eid]
                if not row['body'][0].startswith(prefix):
                    row['body'][0] = prefix + ' ' + row['body'][0]
            known = {x.get('url') if isinstance(x, dict) else x for x in owner.get('sources', [])}
            for source in patch.get('append_sources', []):
                if source['url'] not in known:
                    owner.setdefault('sources', []).append(source)
                    known.add(source['url'])
            for index, title in patch.get('image_titles', {}).items():
                owner['images'][int(index)]['title'] = title
            # Date/classification-only fixes do not invalidate good translations.
            if 'languages' in patch or 'localized_titles' in patch or 'prefix_first_body_paragraph' in patch:
                refresh(owner, locales, path.relative_to(ROOT).as_posix())
            report['applied'].append({'collection': collection, 'entry_id': eid})
    for collection, doc in docs.items():
        doc['entries'].sort(key=lambda e: (e['year'], e.get('date', {}).get('month') or 0, e.get('date', {}).get('day') or 0))
        write(ROOT / f'content/{collection}.json', doc)
    for lang, doc in locales.items():
        write(ROOT / f'content/museum-locales/{lang}.json', doc)
    receipt = hashlib.sha256('|'.join(args.patch_files).encode()).hexdigest()[:10]
    write(AUDIT / f'targeted-prose-integration-{receipt}.json', report)
    print(json.dumps({'applied': len(report['applied']), 'unresolved': len(report['unresolved'])}))


if __name__ == '__main__':
    main()
