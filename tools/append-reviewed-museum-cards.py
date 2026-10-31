"""Append prepared five-language cards while leaving existing prose unchanged."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANGS = ('en', 'it', 'fr', 'de', 'es')


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, value):
    tmp = path.with_suffix('.append.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+')
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('prose_helpers', ROOT / 'tools/apply-editorial-recovery-patches.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    catalog = read(ROOT / 'content/catalog.json')
    owners = {entry['id']: entry for entry in catalog['entries']}
    locales = {lang: read(ROOT / f'content/museum-locales/{lang}.json') for lang in LANGS[1:]}
    report = {'appended': [], 'before': []}
    for filename in args.files:
        path = ROOT / filename
        for patch in read(path)['entries']:
            owner = owners[patch['entry_id']]
            count = patch['expected_existing_main_cards']
            target = patch['target_main_cards']
            cards = patch['append_cards']
            assert len(cards) == target - count
            assert [c['card_id'] for c in cards] == [f'main:{i}' for i in range(count, target)]
            report['before'].append({'entry_id': owner['id'], 'entry': copy.deepcopy(owner),
                                    'locales': {lang: copy.deepcopy(locales[lang]['entries'][owner['id']]) for lang in LANGS[1:]}})
            for lang in LANGS:
                row = owner if lang == 'en' else locales[lang]['entries'][owner['id']]
                additions = [c[lang]['text'] for c in cards]
                headings = [c[lang]['heading'] for c in cards]
                assert all(text.strip() for text in additions + headings)
                if len(row['body']) == target:
                    assert row['body'][count:] == additions and row['story_headings'][count:] == headings
                else:
                    assert len(row['body']) == count == len(row['story_headings']), (owner['id'], lang, 'baseline changed')
                    row['body'].extend(additions)
                    row['story_headings'].extend(headings)
            known = {s.get('url', '') if isinstance(s, dict) else s
                     for s in owner.get('sources', [])}
            owner.setdefault('sources', []).extend(s for s in patch.get('append_sources', []) if s['url'] not in known)
            record = {'source': path.relative_to(ROOT).as_posix(), 'start_index': count, 'end_index': target,
                      'cards': [{'card_id': c['card_id'], 'media_subject': c.get('media_subject', '')} for c in cards]}
            if record not in owner.setdefault('editorial_appendices', []):
                owner['editorial_appendices'].append(record)
            helper.refresh(owner, locales, path.relative_to(ROOT).as_posix())
            report['appended'].append({'entry_id': owner['id'], 'cards_added': len(cards), 'total': target})
    receipt = hashlib.sha256('|'.join(args.files).encode()).hexdigest()[:10]
    audit = ROOT / 'build/research/app-editorial-recovery-20261030' / f'append-integration-{receipt}.json'
    write(audit, report)
    write(ROOT / 'content/catalog.json', catalog)
    for lang, doc in locales.items():
        write(ROOT / f'content/museum-locales/{lang}.json', doc)
    print(json.dumps({'entries': len(report['appended']), 'cards_added_per_language': sum(e['cards_added'] for e in report['appended'])}))


if __name__ == '__main__':
    main()
