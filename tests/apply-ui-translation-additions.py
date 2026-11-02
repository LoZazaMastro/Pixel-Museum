from pathlib import Path
import json
import re

root = Path('content/ui-locales')
locales = ['it', 'es', 'fr', 'de']
data = {locale: json.loads((root / (locale + '.json')).read_text(encoding='utf-8')) for locale in ['en'] + locales}
additions = json.loads(Path('tests/ui-translation-additions.json').read_text(encoding='utf-8'))
help_keys = sorted(set(data['en']['strings']) - set(data['it']['strings']))
assert len(help_keys) == 20, help_keys
for locale in locales:
    assert len(additions['help'][locale]) == len(help_keys)
    data[locale]['strings'].update(zip(help_keys, additions['help'][locale]))
for key, values in additions['messages'].items():
    assert len(values) == 4
    data['en']['strings'][key] = key
    for locale, value in zip(locales, values):
        data[locale]['strings'][key] = value
tokens = re.compile(r'\{(?:left_stick|right_stick|dpad|touchpad|cross|circle|square|triangle|l1|r1|l2|r2|options)\}')
for locale, document in data.items():
    assert set(document['strings']) == set(data['en']['strings']), locale
    for key, value in document['strings'].items():
        assert tokens.findall(key) == tokens.findall(value), (locale, key)
        assert not re.search(r'\{\{(?:left_stick|right_stick|dpad|touchpad|cross|circle|square|triangle|l1|r1|l2|r2|options)\}\}', value), (locale, key)
for locale, document in data.items():
    (root / (locale + '.json')).write_text(json.dumps(document, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('All five UI key sets match:', len(data['en']['strings']), 'keys; controller token audit clean.')
